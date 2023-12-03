import base64
import hashlib
import hmac
import json
from json import JSONDecodeError

from rest_framework import status
from rest_framework.response import Response

from airtable_webhooks.models import AirTableWebHook


def airtable_webhooks_listener(func):
    def wrapper(request):
        try:
            request_data = json.loads(request.body)
        except JSONDecodeError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        webhook_id = request_data.get('webhook', {}).get('id')
        base_id = request_data.get('base', {}).get('id')

        if not webhook_id or not base_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        webhook_query = AirTableWebHook.objects.filter(webhook_id=webhook_id, base_id=base_id)
        if not webhook_query.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        webhook_instance = webhook_query.first()
        signature = request.headers.get('X-Airtable-Content-MAC')

        if not signature:
            return Response(status=status.HTTP_412_PRECONDITION_FAILED)

        resp_hmac = hmac.new(base64.b64decode(webhook_instance.mac_secret), request.body, digestmod=hashlib.sha256)
        expected_signature = 'hmac-sha256=' + resp_hmac.hexdigest()

        if signature != expected_signature:
            return Response(status=status.HTTP_412_PRECONDITION_FAILED)

        return func(request, webhook_instance, request_data)
    return wrapper


def build_model_dict(airtable_data, table_name, table_schema, model_fields):
    model_data = {}

    for field_id, value in airtable_data.items():
        field_name = table_schema.get('%s_%s' % (table_name, field_id))
        model_field = model_fields.get(field_name)

        if not model_field:
            continue

        if isinstance(model_field, dict) and isinstance(value, dict):
            new_value = value.get(list(model_field.keys())[0])

            if not new_value:
                continue

            model_field = list(model_field.values())[0]
            value = new_value

        model_data[model_field] = value
    return model_data
