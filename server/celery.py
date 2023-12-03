from __future__ import absolute_import
import os

from celery import Celery
from kombu import Exchange, Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

app = Celery('server')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_exchange_type = 'default'
app.conf.task_default_routing_key = 'default'

app.conf.task_queues = (
    Queue(name='default', routing_key='default', exchange=Exchange('default')),
    Queue(name='feed_urls', routing_key='feed_urls', exchange=Exchange('feed_urls')),
    Queue(name='xml_scrapers', routing_key='xml_scrapers', exchange=Exchange('xml_scrapers')),
    Queue(name='save_projects', routing_key='save_projects', exchange=Exchange('save_projects')),
    Queue(name='synchronization', routing_key='synchronization', exchange=Exchange('synchronization')),
    Queue(name='generic', routing_key='generic', exchange=Exchange('generic')),
    Queue(name='upwork_auto_login', routing_key='upwork_auto_login', exchange=Exchange('upwork_auto_login')),
)

BASE_FEED_URLS_QUEUE_ROUTE = {'queue': 'feed_urls', 'routing_key': 'feed_urls'}
BASE_XML_SCRAPERS_QUEUE_ROUTE = {'queue': 'xml_scrapers', 'routing_key': 'xml_scrapers'}
BASE_SAVE_PROJECTS_QUEUE_ROUTE = {'queue': 'save_projects', 'routing_key': 'save_projects'}
BASE_SYNCHRONIZATION_QUEUE_ROUTE = {'queue': 'synchronization', 'routing_key': 'synchronization'}
BASE_GENERIC_QUEUE_ROUTE = {'queue': 'generic', 'routing_key': 'generic'}
BASE_UPWORK_QUEUE_ROUTE = {'queue': 'upwork_auto_login', 'routing_key': 'upwork_auto_login'}

# TODO: create a new queue or separate the scrape_job_proposals task from the update_proposals_from_airtable task,
#  because the task update_proposals_from_airtable is waiting for the completion of all tasks running in it for
#  scraping and this can lead to the employment of all the concurrency of the queue

# bind routing with queues
app.conf.task_routes = {
    'upwork_auto_login.tasks.*': BASE_UPWORK_QUEUE_ROUTE,
    'airtable_webhooks.tasks.*': BASE_GENERIC_QUEUE_ROUTE,
    'leadgen_management.tasks.scrape_job_proposals': BASE_GENERIC_QUEUE_ROUTE,
    'leadgen_management.tasks.update_proposals_from_airtable': BASE_GENERIC_QUEUE_ROUTE,
    'leadgen_management.tasks.update_proposals_on_airtable': BASE_GENERIC_QUEUE_ROUTE,
    'leadgen_management.tasks.weekly_update_proposals': BASE_GENERIC_QUEUE_ROUTE,
    'leadgen_management.tasks.private_proposals_to_airtable': BASE_GENERIC_QUEUE_ROUTE,
    'leadgen_management.tasks.update_private_proposals_from_at': BASE_GENERIC_QUEUE_ROUTE,
    'leadgen_management.tasks.update_private_proposals_responsible_on_at': BASE_GENERIC_QUEUE_ROUTE,
    'leadgen_management.tasks.get_feed_urls_from_airtable_task': BASE_FEED_URLS_QUEUE_ROUTE,
    'leadgen_management.tasks.scrap_xml_task': BASE_XML_SCRAPERS_QUEUE_ROUTE,
    'leadgen_management.tasks.save_projects_task': BASE_SAVE_PROJECTS_QUEUE_ROUTE,
    'leadgen_management.tasks.synchronization_task': BASE_SYNCHRONIZATION_QUEUE_ROUTE,
    'leadgen_management.tasks.update_proposals_industry_info': BASE_GENERIC_QUEUE_ROUTE,
}
