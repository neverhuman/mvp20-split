"""Operator admission-policy identifiers; no client model/provider configuration."""
import json

from amphora_contracts_core import Identifier
from pydantic import TypeAdapter

from ..context.policy import require
from ..context.snapshot import _constant, _object


def policy_ids(raw):
    require(type(raw) is str and len(raw.encode('utf-8')) <= 8192, 'curation_configuration_size')
    values = json.loads(raw, object_pairs_hook=_object, parse_constant=_constant)
    require(type(values) is list and len(values) <= 32, 'curation_configuration_shape')
    checked = tuple(TypeAdapter(Identifier).validate_python(item, strict=True) for item in values)
    require(len(checked) == len(set(checked)), 'duplicate_curation_policy')
    return frozenset(checked)
