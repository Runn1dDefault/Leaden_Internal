import time

from pyairtable import Table
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save

from leadgen_management.models import Proposals


@receiver(post_save, sender=Proposals)
def update_proposals_on_airtable(sender, instance, created, update_fields, **kwargs):  # disable NOT USED!
    if created is False:
        update_data = dict()

        if not update_fields or instance.air_id is None:
            return

        table = Table(settings.AIRTABLE_TOKEN, settings.AIRTABLE_BASE_ID, settings.PROPOSALS_TABLE_NAME)

        for air_field, model_field in settings.AIRTABLE_PROPOSALS_TABLE_FIELDS.items():
            if not isinstance(model_field, str):
                continue

            if model_field not in update_fields or air_field in settings.AIRTABLE_PROPOSALS_DONT_UPDATE_FIELDS:
                continue

            if hasattr(instance, model_field):
                update_data[air_field] = getattr(instance, model_field)

        if update_data:
            time.sleep(.3)
            table.update(instance.air_id, update_data)
