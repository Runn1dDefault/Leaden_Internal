import json
from typing import Any

from django.conf import settings
from django.core.cache import caches

from upwork_auto_login.exceptions import NotFoundToken


def remove_auth_tokens_data(tokens_data: dict[str, str | int]):
    cache = caches[settings.UPWORK_TOKENS_CACHE_NAME]
    cache.delete_pattern(tokens_data['key'])


def get_rotated_auth_tokens() -> dict[str, str | int] | None:
    cache = caches[settings.UPWORK_TOKENS_CACHE_NAME]

    tokens_keys = list(cache.keys('uw_token_*'))
    if not tokens_keys:
        raise NotFoundToken('Not founded any tokens for upwork!')

    min_usage = 1_000_000
    min_token_key = min_token_data = None

    for token_key in tokens_keys:
        token_data = json.loads(cache.get(token_key))

        match token_data:
            case {'usage_qty': int() as usage_qty, **other_fields} if usage_qty < min_usage:
                min_usage = usage_qty
                min_token_key = token_key
                min_token_data = token_data

    if min_token_key and min_token_data:
        min_token_data['usage_qty'] += 1
        min_token_data['key'] = str(min_token_key)

        cache.set(
            min_token_key,
            json.dumps(min_token_data),
            timeout=cache.ttl(min_token_key)
        )
        return min_token_data


def get_dict_by_value(data: list[dict], key: Any, value: Any) -> dict:
    for some_dict in data:
        if some_dict.get(key) == value:
            return some_dict
