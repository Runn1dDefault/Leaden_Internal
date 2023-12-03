import json
import logging
import time
import uuid

from django.conf import settings
from django.utils import timezone
from slack_sdk import WebClient

from converters.time_converter import TimeConverter
from services.api.clients import AirTableClient


logger = logging.getLogger('leadgen_management')


def func_chunks_generators(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i: i + n]


class AirTableDriver(TimeConverter):
    def __init__(self):
        self.api = AirTableClient(settings.AIRTABLE_TOKEN)

    def get_records(self, table_name: str, max_retries: int = 3, **kwargs) -> list:
        retries = 0
        while retries < max_retries:
            try:
                response = self.api.all(settings.AIRTABLE_BASE_ID, table_name, **kwargs)
                return response
            except Exception as ex:
                retries += 1
                time.sleep(.5)
                logger.error(f"Error while trying fetch records from AirTable. Retry {retries}. {ex}")
        return []

    def create_many(self, table_name: str, records: list):
        return self.api.batch_create(settings.AIRTABLE_BASE_ID, table_name, records)

    def update_batch(self, table_name, **kwargs):
        return self.api.batch_update(settings.AIRTABLE_BASE_ID, table_name, **kwargs)

    def base_schema(self):
        return self.api.schema(settings.AIRTABLE_BASE_ID)


class SlackDriver:
    def __init__(self, token: str = None):
        self.client = WebClient(token=token or settings.SLACK_BOT_TOKEN)

    def post_message(self, channel: str = None, **kwargs):
        return self.client.chat_postMessage(channel=channel or settings.SLACK_CHANNEL_ID, **kwargs)

    def channel_id_by_channel_name(self, channel_name: str) -> str | None:
        conversation_id = None

        for result in self.client.conversations_list():
            if conversation_id is not None:
                break

            for channel in result["channels"]:
                if channel["name"] == channel_name:
                    conversation_id = channel["id"]
                    break

        return conversation_id

    @staticmethod
    def error_blocks(errors: list[str] = None, header: str = None, footers: list[str] = None) -> list[dict] | None:
        assert errors, 'Error message is required!'

        blocks = []

        if header:
            blocks.append({"type": "header", "text": {"type": "plain_text", "text": header}})
            blocks.append({"type": "divider"})

        if errors:
            for error in errors:
                blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": error}})

        if footers:
            footers_context = {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": footer} for footer in footers or []]
            }
            blocks.append(footers_context)

        if not blocks:
            raise ValueError('Not send notification to slack, because you send empty params!')

        return blocks

    def error_notification(self, body: dict) -> None:
        footers = ['*UTC Time: * ', body['error_time_utc']]
        details = '\n• ' + '\n• '.join(body['details']) if body.get('details') else ''

        links = body.get('links') or []
        links_count = len(links)

        if links_count == 1:
            footers.append('*<%s|Attached link>*' % links[0])
        elif links_count > 1:
            details += '\t' + '\n\t'.join(links)

        blocks = self.error_blocks(header=body['message'], errors=[details], footers=footers)
        self.post_message(blocks=blocks)

    @staticmethod
    def save_notification_to_cache(notification_cache, level: str, msg_header: str, message: str):
        assert level in settings.SLACK_LEVELS.keys()

        notification_cache.set('%s:%s' % (level, uuid.uuid4()), json.dumps({'msg_header': msg_header, 'message': message}))

    def send_notification_from_cache(self, notification_cache) -> None:
        collected_errors = {}

        for level, smile in settings.SLACK_LEVELS.items():
            for key in notification_cache.keys('%s:*' % level):
                error_data = json.loads(notification_cache.get(key))
                error_title = error_data.get('msg_header', level)
                error_header = '%s %s' % (smile, error_title)

                if error_header not in collected_errors:
                    collected_errors[error_header] = []

                if not error_data.get('message'):
                    logger.warning('You sent empty message. This message with title %s will be skip' % error_title)

                collected_errors[error_header].append(error_data['message'])

        message_blocks = []
        for header, details in collected_errors.items():
            if not details:
                continue

            details = ['\n• ' + '\n• '.join(section) for section in func_chunks_generators(details, 10)]

            error_blocks = self.error_blocks(header=header, errors=details)
            message_blocks.extend(error_blocks)

        if message_blocks:
            message_blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn",
                         "text": '*UTC Time: * ' + timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
                         }
                    ]
                }
            )
            self.post_message(blocks=message_blocks)
