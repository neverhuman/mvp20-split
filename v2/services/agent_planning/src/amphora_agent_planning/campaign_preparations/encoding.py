"""Closed, byte-bounded canonical JSON for private retained records."""

import json

from ..campaign_context.records import canonical
from ..context.policy import require
from ..context.snapshot import _constant, _object


def decode(raw, maximum):
    require(type(raw) is bytes and 0 < len(raw) <= maximum, 'campaign_preparation_size')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and canonical(value) == raw, 'campaign_preparation_canonical')
        return value
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        raise ValueError('campaign_preparation_encoding') from error


def keys(value, expected):
    require(type(value) is dict and set(value) == set(expected), 'campaign_preparation_fields')
