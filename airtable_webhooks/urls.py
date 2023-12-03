from django.urls import path

from airtable_webhooks.views import webhook_ping


urlpatterns = [
    path('airtable_ping/', webhook_ping, name='webhooks')
]
