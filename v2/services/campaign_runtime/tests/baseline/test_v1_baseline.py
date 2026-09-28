"""Source integrity and structural compatibility; not scientific or execution parity."""

import hashlib
import json
import re

from amphora_campaign_runtime.graph import Graph
from amphora_contracts_campaigns import CampaignDefinition
from export_schemas import ROOT

FIXTURES = ROOT / "services/campaign_runtime/tests/fixtures/v1_solver"


def test_source_graph_is_connected_and_pinned_to_frozen_code():
    graph = json.loads((FIXTURES / "behavior_graph.json").read_text())
    sources = {}
    for key, source in graph["sources"].items():
        path = ROOT.parent / source["path"]
        assert path.is_relative_to(ROOT.parent / "v1")
        assert hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest() == source["sha256"]
        sources[key] = path.read_text().splitlines()
    nodes = {n["id"] for n in graph["nodes"]}
    assert len(nodes) == len(graph["nodes"])
    for node in graph["nodes"]:
        source = node["source"]
        assert 1 <= source["start_line"] <= source["end_line"] <= len(sources[source["file"]])
    for edge in graph["edges"]:
        assert edge["source"] in nodes and edge["target"] in nodes
    reached = {graph["entry"]}
    while True:
        expanded = reached | {e["target"] for e in graph["edges"] if e["source"] in reached}
        if expanded == reached:
            break
        reached = expanded
    assert reached == nodes


def test_scoring_chains_match_native_registry_including_order():
    graph = json.loads((FIXTURES / "behavior_graph.json").read_text())
    source = (ROOT.parent / graph["sources"]["engine"]["path"]).read_text()
    for lane, constant in [("molecule", "MOLECULE_SCORE_MODULES"),
                           ("formulation", "FORMULATION_SCORE_MODULES"),
                           ("evidence", "EVIDENCE_SCORE_MODULES")]:
        block = re.search(r"const " + constant + r":[^=]+= \[(.*?)\];", source, re.S)
        assert block is not None
        assert graph["candidate_scoring"]["module_chains"][lane] == re.findall(
            r'"(amphora-[^"]+)"', block.group(1)
        )


def test_campaign_scaffold_preserves_stage_order_and_explicit_iteration():
    campaign = CampaignDefinition.model_validate_json((FIXTURES / "campaign_scaffold.json").read_bytes())
    assert Graph.from_contract(campaign.body).issues() == ()
    assert [n.node_id for n in campaign.body.nodes] == [
        "initialize", "seed_population", "score_initial", "rank_initial", "generations", "finalize", "done"
    ]
    loop = campaign.body.nodes[4]
    assert loop.max_iterations == 2
    assert [n.node_id for n in loop.body.nodes] == [
        "select_parents", "mutate", "score_generation", "retain_and_rank", "checkpoint", "done"
    ]
