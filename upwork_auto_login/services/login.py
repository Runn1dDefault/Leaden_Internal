import time
from typing import Any

from django.conf import settings
from playwright.sync_api import sync_playwright

from upwork_auto_login.services.login_actions import UpworkActionsLogin, UpworkActionsGoogleAuth

DRIVER_PARAMS = {
    'args': [
        "--disable-gpu",
        "--disable-web-security",
        "--disable-xss-auditor",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--allow-running-insecure-content",
        "--disable-webgl",
        "--disable-popup-blocking",
        "--disable-dev-shm-usage",
    ],
}


def upwork_login_cookies(username: str, password: str, headless: bool = None) -> list[dict, Any]:
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=headless, **DRIVER_PARAMS)
        context = browser.new_context()
        page = context.new_page()
        page.goto(settings.UPWORK_AUTH_URL)

        login_action = UpworkActionsLogin(page=page, username=username, password=password)
        login_action.wait_username_input()
        login_action.fill_username()
        login_action.click_continue()
        time.sleep(settings.UPWORK_LOGIN_WAIT_FOR_PAGE_SECONDS)
        login_action.wait_password_input()

        try:
            login_action.fill_password()
        except ValueError:
            google_page = login_action.click_google_auth_button(context=context)
            google_action = UpworkActionsGoogleAuth(google_page, email=username, password=password)
            google_action.wait_email_input()
            google_action.fill_google_email()
            google_action.click_google_continue_button(button_text=settings.UPWORK_GOOGLE_NEXT_BTN_TEXT)
            time.sleep(settings.UPWORK_LOGIN_WAIT_FOR_PAGE_SECONDS)
            google_action.wait_password_input()
            google_action.fill_google_password()
            google_action.click_google_continue_button(button_text=settings.UPWORK_GOOGLE_NEXT_BTN_TEXT)
        else:
            login_action.click_submit()

        time.sleep(settings.UPWORK_LOGIN_WAIT_FOR_PAGE_SECONDS)
        page.locator(settings.UPWORK_WAIT_AFTER_LOGIN_XPATH).first.wait_for(state='attached')
        cookies = context.cookies()
        browser.close()
    return cookies
