import copy
import json
import time
import logging

from django.utils import timezone
from django.core.cache import cache, caches
from django.conf import settings
from httpx import HTTPStatusError
# from pyairtable.formulas import match

from server.celery import app
from drivers import AirTableDriver, SlackDriver
from services.api.clients import UpworkJob
from converters.fields_names_converter import NamesConverter
from services.proposals import build_proposals_item, search_job_ciphertext
from upwork_auto_login.tasks import update_upwork_tokens
from upwork_auto_login.utils import get_rotated_auth_tokens, remove_auth_tokens_data

from leadgen_management.scrapers.xml_scraper import XmlScraper
from leadgen_management.tasks_handler import TasksHandler
from leadgen_management.models import Projects, Proposals
from leadgen_management.utils import update_object_attrs, wait_tasks, add_user_id_to_cache, get_user_id_from_cache

tasks_handler = TasksHandler()
logger = logging.getLogger('leadgen_management')


@app.task
def scrape_job_proposals(job_url: str, update_fields=None) -> None:
    proposals_instance = Proposals.objects.get(url=job_url)
    proposals_instance.no_link = not Projects.objects.filter(url=job_url).exists()
    proposals_instance.save(update_fields=('no_link',))

    job_ciphertext = search_job_ciphertext(job_url)
    slack_driver = SlackDriver()
    notification_cache = caches[settings.PROPOSALS_NOTIFICATION_CACHE]

    if not job_ciphertext:
        proposals_instance.save_invalid_url()
        slack_driver.save_notification_to_cache(
            notification_cache=notification_cache,
            level='warning',
            msg_header='Job identifier in Proposals URL does not exists',
            message=job_url
        )

        error_msg = 'Job identifier in Proposals %s does not exists' % job_url
        logger.critical(error_msg)
        raise ValueError(error_msg)

    job_details = http_error = None
    tokens_data = get_rotated_auth_tokens()

    for _ in range(settings.UPWORK_SCRAPING_RETRIES):
        auth_token, master_token = tokens_data.get('auth_token', 'default'), tokens_data.get('master_token')
        assert master_token, 'master_token is required for sending request to Upwork!'

        upwork_job_client = UpworkJob(auth_token, master_token)

        try:
            job_details = upwork_job_client.job_details(job_ciphertext)
        except HTTPStatusError as request_error:
            logger.error(request_error)
            http_error = request_error

            if http_error.response.status_code in settings.CODES_TO_REMOVE_TOKENS:
                remove_auth_tokens_data(tokens_data)

            tokens_data = get_rotated_auth_tokens()
            time.sleep(.2)
            continue
        else:
            break

    if not job_details and http_error and tokens_data:
        error_header = 'Failure requests to Upwork'

        match http_error.response.status_code:
            case 403:
                proposals_instance.job_private = True
                proposals_instance.invalid_url = True
                proposals_instance.save(update_fields={'job_private', 'invalid_url'})
                return
            case 404:
                proposals_instance.job_removed = True
                proposals_instance.job_removed_date = timezone.now().date()
                proposals_instance.invalid_url = True
                proposals_instance.save(update_fields={'invalid_url', 'job_removed', 'job_removed_date'})
                return
            case 400:
                response_data = http_error.response.json()
                error_header = response_data.get('message') or error_header
                logger.critical(http_error)
            case _:
                logger.critical(http_error)

        slack_driver.save_notification_to_cache(
            notification_cache=notification_cache,
            level='info',
            msg_header=error_header,
            message=job_url
        )
        raise http_error

    proposals_item = build_proposals_item(job_details)
    updated_data = proposals_item.dict()

    updated_fields, updated = update_object_attrs(obj=proposals_instance, update_data=updated_data)
    if not updated:
        logger.debug('Proposals scraping don\'t update any fields for job %s' % job_url)
        return

    send_update_fields = updated_fields if not update_fields else set(update_fields)
    if proposals_instance.project_type is not None:
        proposals_instance.scraped = True
        send_update_fields.add('scraped')
    else:
        logger.error(f'project_type case Job details: {job_details} HTTP Error: {http_error}')

    proposals_instance.save(update_fields=send_update_fields)


@app.task
def update_private_proposals_responsible_on_at():
    at_driver = AirTableDriver()
    records = at_driver.get_records(
        table_name=settings.PROPOSALS_PRIVATE_TABLE_NAME,
        max_retries=settings.MAX_RETRIES,
        # formula=match({"Responsible": ""})
    )
    if not records:
        logger.info('Not found records of Private Proposals for updating Responsible!')
        return

    at_saved_urls = {
        record["fields"]["URL"]: (record["id"], record['fields'].get('Responsible', {}).get('name'))
        for record in records if record.get('fields', {}).get('URL')
    }
    private_proposals = Proposals.objects.filter(job_private=True, url__in=at_saved_urls.keys())

    if not private_proposals:
        logger.info('Not found private proposals for updating Responsible on Airtable!')
        return

    update_data = []

    for proposal in private_proposals:
        responsible_old = at_saved_urls[proposal.url][1]
        if proposal.proposal_owner == responsible_old:
            continue

        record_id = at_saved_urls[proposal.url][0]
        if not proposal.proposal_owner:
            update_data.append({'id': record_id, 'fields': {"Responsible": None}})
            continue

        user_id = get_user_id_from_cache(proposal.proposal_owner)
        if user_id:
            update_data.append({'id': record_id, 'fields': {"Responsible": {"id": user_id}}})

    for _ in range(settings.MAX_RETRIES):
        try:
            tasks_handler.update_batch(table_name=settings.PROPOSALS_PRIVATE_TABLE_NAME, records=update_data)
            logger.info('Updated Responsible')
            break
        except Exception as ex:
            logger.error(f"ERROR while updating private proposals into airtable. {ex}")
            time.sleep(.3)
    else:
        body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
        body['message'] = ':exclamation: Update data error'
        body['details'] = ['Error while updating private proposals into airtable.']
        body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
        SlackDriver().error_notification(body)


@app.task
def private_proposals_to_airtable():
    at_driver = AirTableDriver()
    records = at_driver.get_records(table_name=settings.PROPOSALS_PRIVATE_TABLE_NAME, max_retries=settings.MAX_RETRIES)

    at_saved_urls = [record["fields"]["URL"] for record in records if record.get('fields', {}).get('URL')]
    private_proposals = Proposals.objects.filter(job_private=True).exclude(url__in=at_saved_urls)

    if not private_proposals:
        logger.info('Not found private proposals for saving on Airtable!')
        return

    airtable_records = []

    for proposal in private_proposals:
        data = {"URL": proposal.url}
        user_id = get_user_id_from_cache(proposal.proposal_owner)
        if user_id:
            data['Responsible'] = {"id": user_id}
        airtable_records.append(data)

    for _ in range(settings.MAX_RETRIES):
        try:
            tasks_handler.create_many(table_name=settings.PROPOSALS_PRIVATE_TABLE_NAME, records=airtable_records)
            logger.info('Updated ')
            break
        except Exception as ex:
            logger.error(f"ERROR while saving new private proposals into airtable. {ex}")
            time.sleep(.3)
    else:
        body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
        body['message'] = ':exclamation: Saving data error'
        body['details'] = ['Error while saving new private proposals into airtable.']
        body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
        SlackDriver().error_notification(body)


@app.task
def update_private_proposals_from_at():
    table_name = settings.PROPOSALS_PRIVATE_TABLE_NAME
    at_driver = AirTableDriver()
    records = at_driver.get_records(table_name=table_name, max_retries=settings.MAX_RETRIES)

    if not records:
        logger.info('Empty records from table %s' % settings.PROPOSALS_PRIVATE_TABLE_NAME)
        return

    slack_driver = SlackDriver()
    notification_cache = caches[settings.PROPOSALS_NOTIFICATION_CACHE]

    private_urls = Proposals.objects.filter(job_private=True).values_list('url', flat=True)
    all_proposals_data = {proposals.url: proposals for proposals in Proposals.objects.all()}

    fields_map = copy.deepcopy(settings.AIRTABLE_PRIVATE_PROPOSALS_TABLE_FIELDS)
    if fields_map.get('URL') is not None:
        fields_map.pop('URL')  # removing match field, because we don't have to update this field

    future_proposals, to_update_proposals = [], []
    update_fields, handled_urls = set(), set()

    for record in records:
        record_data = record.get('fields')
        match record_data:
            case {"Responsible": dict() as proposal_owner}:
                name, user_id = proposal_owner.get('name'), proposal_owner.get('id')
                if name and user_id:
                    add_user_id_to_cache(name, user_id)

        match record_data:
            case {"URL": str() as url, **other_fields} if url in handled_urls:
                # slack_driver.save_notification_to_cache(
                #     notification_cache=notification_cache,
                #     level='info',
                #     msg_header='Found duplicate URL\'s in %s' % table_name,
                #     message=f'Record ID: {record["id"]} <{url}|link>'
                # )
                logger.warning('Found duplicate in %s URL %s Record ID %s' % (table_name, url, record['id']))
                continue

            case {"URL": str() as url, **other_fields} if url not in all_proposals_data.keys():
                new_proposals = Proposals(url=url, job_private=True, invalid_url=True)
                update_object_attrs(obj=new_proposals, update_data=other_fields, fields=fields_map)

                if new_proposals.job_removed is True:
                    new_proposals.job_removed_date = timezone.now().date()

                future_proposals.append(new_proposals)
                handled_urls.add(url)

            case {"URL": str() as url, **other_fields}:
                proposals = all_proposals_data[url]
                updated = False

                if url not in private_urls:
                    proposals.job_private = True
                    update_fields.add('job_private')
                    updated = True

                if other_fields.get(settings.PRIVATE_JOB_REMOVED_FIELD) is True and proposals.job_removed is False:
                    proposals.job_removed_date = timezone.now().date()
                    update_fields.add('job_removed_date')
                    updated = True

                updated_fields, _ = update_object_attrs(obj=proposals, update_data=other_fields, fields=fields_map)
                if updated_fields:
                    update_fields |= updated_fields
                    updated = True

                if updated is True:
                    to_update_proposals.append(proposals)

                handled_urls.add(url)

    if to_update_proposals and update_fields:
        Proposals.objects.bulk_update(to_update_proposals, fields=update_fields)

    if future_proposals:
        Proposals.objects.bulk_create(future_proposals)

    slack_driver.send_notification_from_cache(notification_cache)
    update_proposals_on_airtable()


@app.task
def update_proposals_on_airtable():
    at_driver = AirTableDriver()
    records = at_driver.get_records(table_name=settings.PROPOSALS_TABLE_NAME, max_retries=settings.MAX_RETRIES)
    if not records:
        logger.debug('Not found any records on Airtable %s' % settings.PROPOSALS_TABLE_NAME)
        return

    records_data = {record['id']: record['fields'] for record in records if record.get('id')}
    db_proposals = Proposals.objects.filter(air_id__in=records_data.keys()).order_by('air_id').distinct('air_id')
    if not db_proposals.exists():
        logger.debug('Not found any proposals records in DB')
        return

    update_records = [
        {
            'id': proposal.air_id,
            'fields': {air_field: getattr(proposal, db_field)
                       for air_field, db_field in settings.AIRTABLE_PROPOSALS_TABLE_FIELDS.items()
                       if db_field in settings.PROPOSALS_UPDATE_FIELDS
                       and getattr(proposal, db_field) != records_data[proposal.air_id].get(air_field)}
        }
        for proposal in db_proposals if records_data.get(proposal.air_id)
    ]

    for retry in range(settings.MAX_RETRIES):
        try:
            at_driver.update_batch(settings.PROPOSALS_TABLE_NAME, records=update_records)
            return
        except Exception as e:
            logger.error("Update Proposals on AirTable Error Retry %s: %s" % (retry + 1, e))
            time.sleep(.3)
    else:
        body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
        body['message'] = ':warning: Proposals warning'
        body['details'] = ['Something went wrong with update Proposals on AirTable!']
        body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
        SlackDriver().error_notification(body)


@app.task
def update_proposals_from_airtable():
    at_driver = AirTableDriver()
    slack_driver = SlackDriver()
    records = at_driver.get_records(table_name=settings.PROPOSALS_TABLE_NAME, max_retries=settings.MAX_RETRIES)

    proposals_query = Proposals.objects.all()
    saved_proposals_data = {
        proposals.air_id: (proposals.url, proposals.scraped, proposals.invalid_url) for proposals in proposals_query
    }
    proposals_urls = proposals_query.values_list('url', flat=True)

    delete_proposals_urls, future_proposals, proposals_update = [], [], []
    scraping_tasks_ids = []
    handled_urls = set()
    notification_cache = caches[settings.PROPOSALS_NOTIFICATION_CACHE]

    for record in records:
        record_id = record['id']
        saved_proposals_info = saved_proposals_data.get(record_id)
        record_data = record.get('fields')
        match record_data:
            case {
                "Proposal Owner": dict() as proposal_owner,
                **other_fields
            }:
                name, user_id = proposal_owner.get('name'), proposal_owner.get('id')
                if name and user_id:
                    add_user_id_to_cache(name, user_id)

        match record_data:
            case {
                'URL': str() as url,
                **other_air_table_fields
            } if url in handled_urls:
                continue
            case {
                'URL': str() as url,
                **other_air_table_fields
            } if saved_proposals_info and saved_proposals_info[0] != url:
                proposals = Proposals.objects.filter(air_id=record_id)
                for proposal in proposals:
                    proposal.air_id = None
                    proposals_update.append(proposal)

                proposals_instance = Proposals(air_id=record_id)
                other_air_table_fields['URL'] = url
                update_object_attrs(
                    obj=proposals_instance,
                    update_data=other_air_table_fields,
                    fields=settings.AIRTABLE_PROPOSALS_TABLE_FIELDS
                )
                future_proposals.append(proposals_instance)
                handled_urls.add(url)
            case {
                'URL': str() as url,
                **other_air_table_fields
            } if saved_proposals_info and saved_proposals_info[0] == url and saved_proposals_info[1] is False:
                if saved_proposals_info[2] is False:
                    scraping_tasks_ids.append(scrape_job_proposals.delay(url).id)

                handled_urls.add(url)
            case {
                'URL': str() as url,
                **other_air_table_fields
            } if saved_proposals_info is None and url in proposals_urls:
                slack_driver.save_notification_to_cache(
                    notification_cache=notification_cache,
                    level='info',
                    msg_header='URL\'s have already been entered before',
                    message=url
                )
                handled_urls.add(url)

                old_record = Proposals.objects.get(url=url)
                old_record_fields = {
                    air_field: getattr(old_record, list(db_field.values())[0])
                    if isinstance(db_field, dict) else getattr(old_record, db_field)
                    for air_field, db_field in settings.AIRTABLE_PROPOSALS_TABLE_FIELDS.items()
                }
                logger.error({
                    'error_name': 'duplicate proposals',
                    'new_record': record,
                    'old_record': {'id': old_record.air_id, 'fields': old_record_fields}
                })
                # proposals = Proposals.objects.get(url=url)
                # proposals.air_id = record_id
                # proposals_update.append(proposals)
            case {
                'URL': str() as url,
                **other_air_table_fields
            } if saved_proposals_info is None and url not in proposals_urls:

                proposals_instance = Proposals(air_id=record_id)
                other_air_table_fields['URL'] = url
                update_object_attrs(
                    obj=proposals_instance,
                    update_data=other_air_table_fields,
                    fields=settings.AIRTABLE_PROPOSALS_TABLE_FIELDS
                )
                future_proposals.append(proposals_instance)
                handled_urls.add(url)

    if delete_proposals_urls:
        Proposals.objects.filter(url__in=delete_proposals_urls).delete()

    if proposals_update:
        Proposals.objects.bulk_update(proposals_update, fields={'air_id'})

    if future_proposals:
        Proposals.objects.bulk_create(future_proposals)

        for proposals in future_proposals:
            scraping_tasks_ids.append(
                scrape_job_proposals.delay(proposals.url).id
            )

    if scraping_tasks_ids:
        wait_tasks(scraping_tasks_ids)

    slack_driver.send_notification_from_cache(notification_cache)
    notification_cache.clear()

    private_proposals_to_airtable.delay()
    update_proposals_on_airtable()


@app.task
def weekly_update_proposals():
    week_ago = (timezone.now() - timezone.timedelta(days=7)).date()
    proposals_objs = Proposals.objects.filter(
        modified_at__date__lte=week_ago,
        job_removed=False,
        job_private=False,
        invalid_url=False
    )
    if not proposals_objs:
        return

    scraping_tasks_ids = []

    for proposals in proposals_objs:
        task = scrape_job_proposals.delay(proposals.url, update_fields=settings.PROPOSALS_UPDATE_FIELDS)
        scraping_tasks_ids.append(task.id)

    if scraping_tasks_ids:
        wait_tasks(scraping_tasks_ids)

        for proposals in proposals_objs:
            proposals.modified_at = timezone.now()

        Proposals.objects.bulk_update(proposals_objs, fields={'modified_at'})

    slack_driver = SlackDriver()
    notification_cache = caches[settings.PROPOSALS_NOTIFICATION_CACHE]
    slack_driver.send_notification_from_cache(notification_cache)
    notification_cache.clear()

    update_proposals_on_airtable()


@app.task
def scrap_xml_task(data: dict):
    try:
        xml_scraper = XmlScraper()
        projects_list = xml_scraper.scrap_and_parse_projects(feed_url=data['feed_url'], keyword=data['keyword'])
        if projects_list:
            cache.set(data['keyword'], json.dumps(projects_list))
            return {"status": "OK"}
    except Exception as ex:
        logger.error(f"ERROR while scraping xml. {ex}")


@app.task()
def get_feed_urls_from_airtable_task():
    data_from_filters_table = tasks_handler.get_data_from_filters_table(scrap_task=scrap_xml_task)
    wait_tasks(data_from_filters_table['task_ids_storage'])
    save_projects_task.apply_async(kwargs={"keywords_list": data_from_filters_table['keywords_list']})

    slack_driver = SlackDriver()
    notification_cache = caches[settings.PROJECTS_NOTIFICATION_CACHE]
    slack_driver.send_notification_from_cache(notification_cache)
    notification_cache.clear()


@app.task
def save_projects_task(keywords_list: list):
    try:
        for keyword in keywords_list:
            projects_list = cache.get(keyword)
            saved_projects = tasks_handler.save_projects_to_database(projects_list=json.loads(projects_list))
            names_converter = NamesConverter()
            airtable_projects = names_converter.many_from_db_to_airtable(records=saved_projects, table_name="Projects")

            for _ in range(settings.MAX_RETRIES):
                try:
                    tasks_handler.create_many(table_name=settings.PROJECTS_TABLE_NAME, records=airtable_projects)
                    break
                except Exception as ex:
                    logger.error(f"ERROR while saving new projects into airtable. {ex}")
                    time.sleep(.3)
            else:
                body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
                body['message'] = ':exclamation: Saving data error'
                body['details'] = ['Error while saving new projects into airtable.']
                body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
                SlackDriver().error_notification(body)
    except Exception as ex:
        logger.error(f"ERROR while saving new projects. {ex}")


@app.task
def synchronization_task(table_name: str):
    try:
        tasks_handler.update_all_records(table_name=table_name)
    except Exception as ex:
        logger.error(f"ERROR while syncing {table_name} table. {ex}")
        body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
        body['message'] = ':exclamation: Synchronization problem'
        body['details'] = [f'Problem with sync table - `{table_name}`.']
        body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
        SlackDriver().error_notification(body)


@app.task
def update_proposals_industry_info():
    proposals = Proposals.objects.filter(job_private=False, invalid_url=False)
    for proposals in proposals:
        scrape_job_proposals.delay(
            job_url=proposals.url,
            update_fields=['industry_size', 'company_size', 'company_category']
        )

