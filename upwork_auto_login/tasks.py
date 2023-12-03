import uuid
import copy
import json
import logging

from django.conf import settings
from django.core.cache import caches
from django.utils import timezone

from server.celery import app
from drivers import SlackDriver

from upwork_auto_login.exceptions import NotFoundToken, NotFoundCookies
from upwork_auto_login.services.login import upwork_login_cookies
from upwork_auto_login.models import UpworkAccount
from upwork_auto_login.utils import get_dict_by_value


logger = logging.getLogger('upwork_auto_login')


@app.task
def upwork_scrape_account_tokens(username: str, password: str):
    for retry in range(settings.UPWORK_LOGIN_RETRIES):
        try:
            cookies = upwork_login_cookies(username, password)
            break
        except Exception as e:
            logger.error('Error upwork login err: %s retry: %s' % (retry, e))
            continue
    else:
        message = 'Something went wrong with login for %s' % username

        error_body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
        error_body['message'] = ':warning: Upwork Login Error'
        error_body['details'] = [message]
        error_body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
        SlackDriver().error_notification(error_body)

        logger.error(message)
        raise NotFoundCookies(message)

    auth_token_cookie = get_dict_by_value(
        data=cookies,
        key=settings.UPWORK_COOKIES_NAME_KEY,
        value=settings.UPWORK_AUTH_COOKIE_KEY
    )
    master_token_cookie = get_dict_by_value(
        data=cookies,
        key=settings.UPWORK_COOKIES_NAME_KEY,
        value=settings.UPWORK_MASTER_COOKIE_KEY
    )

    if not auth_token_cookie or not master_token_cookie:
        message = 'Account invalid, not found tokens in cookie for %s!' % username

        error_body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
        error_body['message'] = ':warning: Upwork Login Error'
        error_body['details'] = [message]
        error_body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
        SlackDriver().error_notification(error_body)

        UpworkAccount.add_invalid(username)
        logger.error(message)
        raise NotFoundToken(message)

    tokens = dict(
        usage_qty=0,
        auth_token=auth_token_cookie[settings.UPWORK_COOKIES_VALUE_KEY],
        master_token=master_token_cookie[settings.UPWORK_COOKIES_VALUE_KEY],
    )
    cache = caches[settings.UPWORK_TOKENS_CACHE_NAME]
    cache.set('uw_token_' + str(uuid.uuid4()), json.dumps(tokens), timeout=settings.UPWORK_TOKENS_EXPIRES_SECONDS)


@app.task
def update_upwork_tokens():
    upwork_accounts = UpworkAccount.objects.filter(invalid=False).order_by('?')

    if not upwork_accounts.exists():
        error_body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
        error_body['message'] = ':warning: Upwork account'
        error_body['details'] = ['You must create and add upwork account']
        error_body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
        SlackDriver().error_notification(error_body)
        return

    cache = caches[settings.UPWORK_TOKENS_CACHE_NAME]
    tokens_count = len(cache.keys('uw_token_*'))

    accounts_count = upwork_accounts.count()
    if tokens_count < accounts_count:
        tokens_delay = accounts_count - tokens_count

        for account in upwork_accounts[:tokens_delay]:
            upwork_scrape_account_tokens(account.username, account.password)
