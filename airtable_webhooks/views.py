from rest_framework import status, response
from rest_framework.decorators import api_view

from airtable_webhooks.utils import airtable_webhooks_listener
from airtable_webhooks.tasks import extract_and_process_payloads


@api_view(['POST'])
@airtable_webhooks_listener
def webhook_ping(request, webhook_instance, request_data):
    extract_and_process_payloads.delay(
        webhook_instance.base_id,
        webhook_instance.webhook_id,
        webhook_instance.cursor,
        webhook_instance.table_name
    )
    return response.Response(status=status.HTTP_204_NO_CONTENT)
