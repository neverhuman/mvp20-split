"""Independent precision, schema and resource-budget expectations."""

import hashlib
import json
from decimal import Decimal
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.artifact_bindings.encoding import payload
from amphora_campaign_runtime.artifact_bindings.model import BindingBudget
from amphora_campaign_runtime.compiler import PinnedSchema, SchemaIdentity
from amphora_campaign_runtime.lifecycle.model import TransitionError


def test_exact_decimal_encoding_and_schema_bounds():
    assert payload({"n": Decimal("0.100000000000000000001")}) == b'{"n":0.100000000000000000001}'
    body = b'{"type":"number","minimum":0.1,"multipleOf":0.1}'
    schema = PinnedSchema(SchemaIdentity("number", "1", hashlib.sha256(body).hexdigest()), body)
    schema.validate(Decimal("0.3"))
    with pytest.raises(TransitionError, match="binding_schema_invalid"):
        schema.validate(Decimal("0.31"))


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("1e101"), Decimal("1e-325"), 0.1])
def test_encoding_rejects_unbounded_or_implicit_float_conversion(value):
    with pytest.raises(TransitionError):
        payload({"value": value})


@pytest.mark.parametrize("field,limit,reason", [("items", "max_items", "member"), ("artifacts", "max_artifacts", "artifact"), ("size", "max_bytes", "byte")])
def test_budget_limits_are_cumulative(field, limit, reason):
    limits = {"max_items": 10, "max_artifacts": 10, "max_bytes": 10}
    limits[limit] = 3
    budget = BindingBudget(SimpleNamespace(**limits))
    budget.add(**{field: 2})
    with pytest.raises(TransitionError, match="binding_" + reason + "_budget"):
        budget.add(**{field: 2})


def test_schema_format_is_checked_at_the_conversion_boundary():
    body = json.dumps({"type": "string", "format": "date-time"}).encode()
    schema = PinnedSchema(SchemaIdentity("date", "1", hashlib.sha256(body).hexdigest()), body)
    with pytest.raises(TransitionError, match="binding_schema_invalid"):
        schema.validate("not-a-date")


def test_unknown_schema_format_cannot_silently_pass_conversion():
    body = b'{"type":"string","format":"unknown-scientific-format"}'
    schema = PinnedSchema(SchemaIdentity("unknown", "1", hashlib.sha256(body).hexdigest()), body)
    with pytest.raises(TransitionError, match="binding_schema_format_unsupported"):
        schema.validate("unverified")
