import json
import copy
import logging

from django.conf import settings
from django.core.cache import caches
from django.db import IntegrityError
from django.utils import timezone
from httpx import HTTPStatusError

from drivers import AirTableDriver, SlackDriver
from server.celery import app
from services.api.clients import AirTableWebHooksClient
from services.utils import import_model

from airtable_webhooks.models import AirTableWebHook
from airtable_webhooks.utils import build_model_dict


logger = logging.getLogger('airtable_webhooks')


@app.task
def create_webhooks(notification_url: str):
    client = AirTableWebHooksClient(base_id=settings.LEADGEN_DEV_BASE_ID, oauth_token=settings.LEADGEN_DEV_TOKEN)

    for table_name, table_setups in settings.AIRTABLE_WEBHOOKS_TABLES_SETTINGS.items():
        if AirTableWebHook.objects.filter(table_name=table_name).exists():
            continue

        table_id = table_setups['table_id']
        response_data = client.create_webhook(
            notification_url=notification_url,
            specification={
                "options": {
                    "filters": {
                        "fromSources": ["client"],
                        "dataTypes": ["tableData"],
                        "recordChangeScope": table_id
                    }
                }
            }
        )

        match response_data:
            case {
                'expirationTime': str(),
                'id': str() as webhook_id,
                'macSecretBase64': str() as mac_secret_base64
            }:
                AirTableWebHook.objects.create(
                    webhook_id=webhook_id,
                    base_id=settings.LEADGEN_DEV_BASE_ID,
                    table_name=table_name,
                    mac_secret=mac_secret_base64
                )


@app.task
def update_schema():
    schema = AirTableDriver().base_schema()

    tables = schema.get('tables')
    if not tables:
        message = 'Not found Airtable schema!'
        body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
        body['message'] = 'Webhook Error'
        body['details'] = [message]
        body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
        SlackDriver().error_notification(body)
        logger.critical(message)
        raise ValueError(message)

    table_names = settings.AIRTABLE_WEBHOOKS_TABLES_SETTINGS.keys()

    cache = caches[settings.AIRTABLE_WEBHOOKS_CACHE_NAME]
    for table in tables or []:
        match table:
            case {
                "id": str() as table_id,
                "name": str() as table_name,
                "primaryFieldId": str(),
                "fields": list() as fields,
                "views": list()
            } if table_name in table_names:
                collected_schema = dict(table_id=table_id, table_name=table_name)

                for field in fields:
                    match field:
                        case {
                            "id": field_id,
                            "name": field_name,
                            "type": str()
                        }:
                            collected_schema['%s_%s' % (table_name, field_id)] = field_name
                cache.set(table_name + '_schema', json.dumps(collected_schema))


@app.task
def payload_handler(table_name: str, payload: dict):
    cache = caches[settings.AIRTABLE_WEBHOOKS_CACHE_NAME]
    table_schema_json = cache.get(table_name + '_schema')

    if not table_schema_json:
        message = 'Not found schema for table %s' % table_name
        body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
        body['message'] = 'Webhook Error'
        body['details'] = [message]
        body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
        SlackDriver().error_notification(body)
        logger.error(message)
        raise ValueError(message)

    table_schema = json.loads(table_schema_json)

    model_sets = settings.AIRTABLE_WEBHOOKS_TABLES_SETTINGS[table_name]
    table_id = model_sets['table_id']
    model_fields, model_path = model_sets['fields'], model_sets['model']
    model = import_model(model_path)

    future_objs, update_objs = [], []

    changed_tables = payload.get('changedTablesById')
    if not changed_tables:
        return

    changed_tables = payload.get('changedTablesById', {})
    changes_meta = changed_tables.get(table_id)
    changes_records_meta = changes_meta.get('changedRecordsById', {})
    saved_records_ids = [] if not changes_records_meta else model.objects.all().values_list('air_id', flat=True)
    updated_fields = set()

    for record_id, update_meta in changes_records_meta.items():
        match update_meta:
            case {
                'current': dict() as new_changes,
                **other_fields
            }:
                cell_values = new_changes.get('cellValuesByFieldId')
                if not cell_values:
                    continue

                update_kwargs = build_model_dict(cell_values, table_name, table_schema, model_fields)

                if record_id in saved_records_ids and update_kwargs:
                    obj = model.objects.get(air_id=record_id)
                    updated = False

                    for field, value in update_kwargs.items():
                        if hasattr(obj, field) and getattr(obj, field) != value:
                            updated = True
                            setattr(obj, field, value)
                            updated_fields.add(field)

                    if updated:
                        update_objs.append(obj)

                elif record_id not in saved_records_ids and update_kwargs:
                    future_objs.append(model(air_id=record_id, **update_kwargs))

        break

    if future_objs:
        try:
            model.objects.bulk_create(future_objs)
        except IntegrityError as e:
            logger.error(e)

    if update_objs:
        try:
            model.objects.bulk_update(update_objs, fields=updated_fields)
        except IntegrityError as e:
            logger.error(e)


@app.task
def extract_and_process_payloads(base_id, webhook_id, cursor, table_name):
    client = AirTableWebHooksClient(base_id=base_id, oauth_token=settings.LEADGEN_DEV_TOKEN)
    try:
        # when accessing this resource, the token is updated for 7 days
        response_data = client.webhook_payloads(webhook_id=webhook_id, cursor=cursor)
    except HTTPStatusError as request_err:
        message = 'Error request for getting details of webhook %s' % webhook_id
        body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
        body['message'] = 'Webhooks Error'
        body['details'] = [
            message,
            'Status: %s' % request_err.response.status_code
        ]
        body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
        SlackDriver().error_notification(body)
        logger.error(message)
        raise request_err

    match response_data:
        case {
            "cursor": int() as new_cursor,
            "mightHaveMore": bool(),  # TODO: if True send requests again with received cursor
            "payloads": list() as payloads
        }:
            if new_cursor > cursor:
                AirTableWebHooksClient.objects.get(base_id=base_id, webhook_id=webhook_id).update_cursor(cursor)

                for payload in payloads:
                    payload_handler(table_name, payload)
            else:
                logger.error('Received old cursor %s for webhook %s' % (new_cursor, webhook_id))

        case _:
            logger.warning('Not supported AirTable response json: %s' % response_data)
