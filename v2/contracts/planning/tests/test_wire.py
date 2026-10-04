import json
from pathlib import Path

import pytest
from amphora_contracts_planning import EngagementRequest, ProviderUsage
from pydantic import ValidationError

FIXTURE = Path(__file__).parent / "fixtures/request.json"


def test_request_roundtrip_and_immutable_collections():
    request = EngagementRequest.model_validate_json(FIXTURE.read_bytes())
    assert EngagementRequest.model_validate_json(request.model_dump_json()) == request
    assert type(request.context.entries) is tuple
    with pytest.raises(ValidationError):
        request.actor_id = "changed"


@pytest.mark.parametrize("path,value", [
    (("schema_version",), "2"),
    (("context", "limits", "max_attempts"), True),
    (("context", "limits", "max_attempts"), "2"),
    (("context", "limits", "max_attempts"), 17),
    (("context", "limits", "total_accounting_units"), 1.5),
    (("context", "model", "endpoint"), "https://not-a-public-setting.invalid"),
    (("context", "model", "api_key"), "not-allowed"),
    (("context", "allowed_actions"), ["execute_code"]),
    (("context", "entries"), [None]),
    (("context", "omissions"), [{}]),
    (("runtime_cut",), {}),
])
def test_strict_request_boundary(path, value):
    document = json.loads(FIXTURE.read_bytes())
    item = document
    for key in path[:-1]:
        item = item[key]
    item[path[-1]] = value
    with pytest.raises(ValidationError):
        EngagementRequest.model_validate_json(json.dumps(document))


def test_unknown_usage_is_explicit_not_invented_zero():
    usage = ProviderUsage(input_tokens=None, output_tokens=None, accounting_units=None, certainty="unknown")
    assert json.loads(usage.model_dump_json())["input_tokens"] is None
    with pytest.raises(ValidationError):
        ProviderUsage(input_tokens=-1, output_tokens=0, accounting_units=0, certainty="reported")
