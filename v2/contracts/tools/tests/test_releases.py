"""Registry wire roots are additive; fixtures remain language-neutral."""

import copy
import json

import pytest
from amphora_contracts_tools import (
    EligibilityResult,
    LockEntry,
    RegisterRelease,
    ReleaseDescriptor,
    ReleaseRegistrationReceipt,
)
from export_schemas import ROOT
from jsonschema import Draft202012Validator
from pydantic import ValidationError

CASES = json.loads((ROOT / "contracts/fixtures/v1/tool_releases.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_release_input_output_schema_roundtrip(case):
    descriptor = ReleaseDescriptor.model_validate_json(json.dumps(case["descriptor"]))
    assert json.loads(descriptor.model_dump_json()) == case["descriptor"]
    for mode in ("validation", "serialization"):
        schema = ReleaseDescriptor.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(case["descriptor"])


@pytest.mark.parametrize("model,filename", [(LockEntry, "lock"), (RegisterRelease, "registration"),
    (ReleaseRegistrationReceipt, "receipt"), (EligibilityResult, "eligibility")])
def test_registry_transport_examples_validate_without_granting_execution(model, filename):
    examples = json.loads((ROOT / "contracts/fixtures/v1/tool_release_messages.json").read_text())
    value = examples[filename]
    parsed = model.model_validate_json(json.dumps(value))
    assert json.loads(parsed.model_dump_json()) == value
    for mode in ("validation", "serialization"):
        Draft202012Validator(model.model_json_schema(mode=mode)).validate(value)
    if filename == "eligibility":
        assert parsed.capacity.status == "available" and parsed.scientific.status == "unreviewed"


@pytest.mark.parametrize("fault", ["floating", "resource_bool", "unbounded_batch", "egress_wildcard", "authority", "version", "endpoint"])
def test_invalid_registry_declarations_fail_at_wire_boundary(fault):
    value = copy.deepcopy(CASES[0]["descriptor"])
    if fault == "floating":
        value["tool"]["binding"]["release"] = "latest"
    elif fault == "resource_bool":
        value["resources"]["cpu_millicores"] = True
    elif fault == "unbounded_batch":
        value["resources"]["max_batch_size"] = 9007199254740992
    elif fault == "egress_wildcard":
        value["egress"] = {"mode": "allowlist", "hosts": ["*"]}
    elif fault == "authority":
        value["authority_ceiling"] = "clinical_approval"
    elif fault == "version":
        value["schema_version"] = "2"
    else:
        value["replica_endpoint"] = "http://127.0.0.1:1234"
    with pytest.raises(ValidationError):
        ReleaseDescriptor.model_validate_json(json.dumps(value))
    assert list(Draft202012Validator(ReleaseDescriptor.model_json_schema()).iter_errors(value))
