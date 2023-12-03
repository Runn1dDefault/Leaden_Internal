import time
from typing import Any

from celery.result import AsyncResult
from django.conf import settings
from django.core.cache import caches

from leadgen_management.models import BaseModel


def add_user_id_to_cache(name: str, user_id: str) -> bool:
    assert name and user_id
    users_cache = caches[settings.AIRTABLE_USER_IDS_CACHE]
    key = 'proposals_owner_%s' % name
    if key not in users_cache.keys('proposals_owner_*'):
        users_cache.set(key, user_id, timeout=None)
        return True
    return False


def get_user_id_from_cache(name: str) -> str | None:
    users_cache = caches[settings.AIRTABLE_USER_IDS_CACHE]
    return users_cache.get('proposals_owner_%s' % name)


def wait_tasks(tasks_ids: list[str]):
    tasks = [AsyncResult(task_id) for task_id in tasks_ids or []]

    while tasks:
        for task in tasks:
            if task.ready():
                tasks.remove(task)

        time.sleep(1)


def model_verbose_fields(model, fields):
    return [model._meta.get_field(field).verbose_name.upper() for field in fields]


def update_object_attrs(obj, update_data: dict[str, Any],
                        fields: dict[str, str | dict[str, str]] = None) -> tuple[set[str], bool]:
    updated = False
    updated_fields = set()

    if fields is not None:
        for field, model_field_name in fields.items():
            value = update_data.get(field)

            if isinstance(model_field_name, dict) and isinstance(value, dict):
                updated_relation_fields, updated = update_object_attrs(obj, value, model_field_name)
                updated_fields |= updated_relation_fields
                continue
            elif isinstance(model_field_name, dict) and not isinstance(value, dict):
                continue

            if not hasattr(obj, model_field_name):
                continue

            if value is None and isinstance(obj, BaseModel):
                model_field = obj.__class__._meta.get_field(model_field_name)
                value = model_field.get_default()

            if getattr(obj, model_field_name) != value is not None:
                setattr(obj, model_field_name, value)
                updated_fields.add(model_field_name)
                updated = True

    else:
        for field, value in update_data.items():
            if hasattr(obj, field) and getattr(obj, field) != value:
                setattr(obj, field, value)
                updated_fields.add(field)
                updated = True

    return updated_fields, updated
