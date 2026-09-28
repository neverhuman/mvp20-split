import copy
import json

import pytest
from amphora_campaign_runtime.graph import Graph
from amphora_contracts_campaigns import CampaignDefinition
from export_schemas import ROOT

CASES = json.loads(
    (ROOT / "contracts/fixtures/v1/wire_cases.json").read_text()
)


def fixture(name):
    return copy.deepcopy(next(c["payload"] for c in CASES if c["name"] == name))


def issues(payload):
    dto = CampaignDefinition.model_validate_json(json.dumps(payload))
    return {i.code for i in Graph.from_contract(dto.body).issues()}


def test_valid_graph_and_explicit_loop_body():
    graph = fixture("valid-campaign")
    assert issues(graph) == set()
    body = copy.deepcopy(graph["body"])
    graph["body"]["nodes"][0] = {"kind": "iterate", "node_id": "calculate", "max_iterations": 3, "body": body}
    assert issues(graph) == set()


@pytest.mark.parametrize(
    "change,expected",
    [
        (
            lambda g: g["body"]["edges"].append({"source": "done", "target": "calculate"}),
            "unstructured_cycle",
        ),
        (lambda g: g["body"]["edges"].append({"source": "unknown", "target": "done"}), "unknown_endpoint"),
        (lambda g: g["body"]["nodes"].append(g["body"]["nodes"][0]), "duplicate_node"),
        (lambda g: g["body"].update(edges=[]), "unterminated_path"),
    ],
)
def test_semantic_graph_rejection(change, expected):
    graph = fixture("valid-campaign")
    change(graph)
    assert expected in issues(graph)


def test_parallel_branches_join_and_predicate_dependencies():
    graph = fixture("valid-campaign")
    binding = graph["body"]["nodes"][0]["tool"]
    graph["body"] = {
        "nodes": [
            {"kind": "invoke", "node_id": "input", "tool": binding},
            {
                "kind": "branch",
                "node_id": "choice",
                "predicate": {
                    "source_node": "input",
                    "source_port": "value",
                    "operator": "equals",
                    "value": True,
                },
            },
            {"kind": "invoke", "node_id": "a", "tool": binding},
            {"kind": "invoke", "node_id": "b", "tool": binding},
            {"kind": "join", "node_id": "join", "policy": "all_terminal"},
            {"kind": "finish", "node_id": "done"},
        ],
        "edges": [
            {"source": "input", "target": "choice"},
            {"source": "choice", "target": "a", "route": "true"},
            {"source": "choice", "target": "b", "route": "false"},
            {"source": "a", "target": "join"},
            {"source": "b", "target": "join"},
            {"source": "join", "target": "done"},
        ],
    }
    assert issues(graph) == set()
    graph["body"]["nodes"][1]["predicate"]["source_node"] = "done"
    assert "predicate_dependency" in issues(graph)
