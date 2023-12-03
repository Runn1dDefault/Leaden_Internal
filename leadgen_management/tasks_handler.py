import copy
import logging

from django.conf import settings
from django.utils import timezone
from pyairtable.formulas import match

from drivers import AirTableDriver, SlackDriver
from converters.fields_names_converter import NamesConverter
from services.utils import import_model

from leadgen_management.models import Projects


logger = logging.getLogger('leadgen_management')


class TasksHandler(AirTableDriver, NamesConverter):

    def __init__(self):
        super(TasksHandler, self).__init__()

    def get_data_from_filters_table(self, scrap_task) -> dict:
        keywords_list = []
        task_ids_storage = []
        try:
            active_filters = self.get_records(
                settings.FILTERS_TABLE_NAME,
                max_retries=settings.MAX_RETRIES,
                formula=match({"Active": True}),
                view=settings.AIRTABLE_FILTERS_TABLE_VIEW
            )
            for data in active_filters:
                data_to_scrap = {
                    "keyword": data['fields']['Keyword'],
                    "feed_url": data['fields']['Feed URL']
                }
                keywords_list.append(data_to_scrap['keyword'])
                result = scrap_task.apply_async(kwargs={'data': data_to_scrap})
                task_ids_storage.append(str(result))
        except Exception as ex:
            logger.error(f"ERROR while trying to get data from Airtable Filters table. {ex}")
            body = copy.deepcopy(settings.ERROR_MSG_SNIPPED)
            body['message'] = 'Airtable data error'
            body['details'] = ['ERROR while trying to get data from Airtable Filters table']
            body['error_time_utc'] = timezone.now().utcnow().strftime('%d.%m.%Y %H:%M')
            SlackDriver().error_notification(body)

        return {"keywords_list": keywords_list, "task_ids_storage": task_ids_storage}

    @staticmethod
    def save_projects_to_database(projects_list: list) -> list:
        try:
            today = timezone.now()
            saved_urls = Projects.objects.values_list('url', flat=True)

            last_month_projects = Projects.objects.filter(created_at__date__month=today.month,
                                                          created_at__date__year=today.year)
            check_fields = ('title', 'country', 'project_type')
            checklist = set(last_month_projects.values_list(*check_fields))
            new_projects, handled_urls, duplicates_to_saving = [], set(), []

            for project in projects_list:
                try:
                    url, keyword = project['url'], project['keyword']
                except KeyError as key_err:
                    # TODO: notification INFO Not found required field: key_err
                    logger.warning('Not found some required fields in new project: %s' % key_err)
                    continue

                if url in handled_urls:
                    # TODO: notification INFO Founded duplicates!
                    logger.warning('Found duplicates in new projects list %s' % url)
                    continue

                if url not in saved_urls:
                    new_project = Projects(
                        url=url,
                        keyword=keyword,
                        title=project.get('title'),
                        shift=project.get('shift'),
                        budget=project.get('budget'),
                        hourly=project.get('hourly'),
                        country=project.get('country'),
                        category=project.get('category'),
                        description=project.get('description'),
                        project_type=project.get('project_type')
                    )
                    checking_values = tuple(project.get(key) for key in check_fields)

                    if checking_values in checklist:
                        new_project.duplicate = True
                        duplicates_to_saving.append(new_project)
                        continue

                    new_projects.append(new_project)
                    handled_urls.add(url)
                    checklist.add(checking_values)

            if duplicates_to_saving:
                Projects.objects.bulk_create(duplicates_to_saving)

            return Projects.objects.bulk_create(new_projects)
        except Exception as ex:
            logger.error(f"ERROR while saving projects to database. {ex}")

    def update_all_records(self, table_name: str):
        model_path = settings.TASKS_HANDLER_MAP[table_name]['model']
        model_fields = settings.TASKS_HANDLER_MAP[table_name]['fields']
        match_field = settings.TASKS_HANDLER_MAP[table_name]['match_field']
        model = import_model(model_path)

        records = self.get_records(table_name=table_name, max_retries=settings.MAX_RETRIES)
        converted_records = self.convert_records_to_database_format(
            table_name=table_name,
            records=records,
            db_fields=model_fields
        )
        records_to_update = []
        matches_values = set()

        for record in converted_records:
            match_field_value = record.get(match_field)

            if record.get(match_field) is None or match_field_value in matches_values:
                logger.warning('Found duplicate in %s: %s' % (table_name, record))
                continue

            matches_values.add(match_field_value)
            records_to_update.append(model(**record))

        if not records_to_update:
            logger.debug('Not found records to update for %s' % table_name)
            return

        fields_to_update = copy.copy(model_fields)
        fields_to_update.remove(match_field)
        try:
            model.objects.bulk_update_or_create(
                records_to_update,
                fields_to_update,
                match_field=match_field
            )
        except Exception as ex:
            logger.error(f"Exception while trying to bulk update. {ex}")
