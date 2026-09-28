import copy
import json

from amphora_campaign_runtime.admission import InvocationPolicy
from amphora_campaign_runtime.graph import Graph
from amphora_contracts_campaigns import CampaignDefinition
from amphora_contracts_tools import Completion, Invocation, ToolDescriptor
from export_schemas import ROOT

CASES = json.loads(
    (ROOT / "contracts/fixtures/v1/wire_cases.json").read_text()
)


def fixture(name):
    return copy.deepcopy(next(c["payload"] for c in CASES if c["name"] == name))


def issues(payload):
    dto = CampaignDefinition.model_validate_json(json.dumps(payload))
    return {i.code for i in Graph.from_contract(dto.body).issues()}


def test_scope_and_exact_tool_version_admission():
    raw = fixture("valid-invocation")
    descriptor = ToolDescriptor.model_validate_json(json.dumps(fixture("valid-descriptor")))
    assert not InvocationPolicy.issues(Invocation.model_validate_json(json.dumps(raw)), descriptor)
    raw["inputs"][0]["artifact"]["scope"]["project_id"] = "forbidden"
    raw["tool"]["release"] = "0.2.0"
    assert {
        i.code for i in InvocationPolicy.issues(Invocation.model_validate_json(json.dumps(raw)), descriptor)
    } == {"cross_scope_artifact", "tool_binding_mismatch"}


def test_stale_completion_is_rejected_against_supplied_attempt():
    raw = fixture("valid-completion")
    raw["fence"] = 2
    result = InvocationPolicy.completion_issues(
        Completion.model_validate_json(json.dumps(raw)),
        Invocation.model_validate_json(json.dumps(fixture("valid-invocation"))),
        ToolDescriptor.model_validate_json(json.dumps(fixture("valid-descriptor"))),
    )
    assert {i.code for i in result} == {"attempt_mismatch"}
