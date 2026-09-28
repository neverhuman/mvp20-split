"""Registry wire roots are additive; fixtures remain language-neutral."""

import copy
import json

import pytest
from amphora_contracts_tools import (
    EligibilityDecision,
    EligibilityResult,
    LockEntry,
    RegisterRelease,
    ReleaseDescriptor,
    ReleaseRegistrationReceipt,
)
from export_schemas import ROOT
from jsonschema import Draft202012Validator, FormatChecker
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


def test_selection_decision_is_additive_and_requires_aware_observation_times():
    value = json.loads((ROOT / "contracts/fixtures/v1/tool_selection_decision.json").read_text())
    result = EligibilityDecision.model_validate_json(json.dumps(value))
    assert result.status == "rejected" and result.observations.capacity.status == "available"
    for mode in ("validation", "serialization"):
        Draft202012Validator(EligibilityDecision.model_json_schema(mode=mode), format_checker=FormatChecker()).validate(value)
    value["assessed_at"] = "2026-09-28T12:00:00"
    with pytest.raises(ValidationError, match="Timezone-aware"):
        EligibilityDecision.model_validate_json(json.dumps(value))
    assert list(Draft202012Validator(EligibilityDecision.model_json_schema(), format_checker=FormatChecker()).iter_errors(value))


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
