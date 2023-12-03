from django.contrib import admin

from airtable_webhooks.models import AirTableWebHook


@admin.register(AirTableWebHook)
class AirTableWebHookAdmin(admin.ModelAdmin):
    readonly_fields = ('mac_secret',)
    list_display = ('base_id', 'webhook_id', 'table_name', 'cursor')
    list_filter = ('base_id',)
    search_fields = ('table_name', 'webhook_id')
