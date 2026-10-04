"""Actual owner-handoff abrupt exits, genuine lease expiry and authority negatives."""

import argparse
import copy
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from verify_planning_owners import verify


def failures(output, worker, revise, knowledge):
    revise(["read", "process"])
    seed = worker("seed-crashes", "initial", origins="crash-origins.json")
    assert seed["provider_calls"] == ["crash-before", "crash-after"]
    evidence = {}
    for boundary, code in (("before", 71), ("after", 72)):
        revise(["read", "process"])
        crash = worker("die-" + boundary, "initial", expected=code, origins="crash-origins.json")
        assert crash["state"] == "dispatching" and crash["position"] == 2
        proposal = crash["request"]
        status_path = f"/v1/graphs/{proposal['graph']['graph_id']}/proposals/{proposal['change_id']}"
        remote = knowledge(status_path, expected=404 if boundary == "before" else 200)
        if boundary == "after":
            assert remote["decision"] == crash["remote_response"]
            assert remote["decision"]["decision"]["outcome"] == "accepted"
        else:
            assert crash["remote_response"] is None
        live = worker("live-" + boundary, origins="crash-origins.json")
        assert live["effects"] == [{"kind": "graph", "status": "blocked", "reason": "busy"}]
        assert not live["owner_calls"] and not live["processing_reads"]
        revise(["read"])
        expires = datetime.fromisoformat(crash["lease_expires"])
        remaining = (expires - datetime.now(UTC)).total_seconds()
        assert 0 < remaining <= 120, "Expected a real live production lease"
        print(json.dumps({"stage": "waiting_for_actual_lease_expiry", "boundary": boundary, "seconds": round(remaining, 1)}), flush=True)
        # No lease-table rewrite, fixture clock mutation or test-only short lease.
        deadline = time.monotonic() + remaining + 1
        while time.monotonic() < deadline:
            time.sleep(min(0.2, max(0, deadline - time.monotonic())))
        recovered = worker("recover-" + boundary, origins="crash-origins.json")
        if boundary == "before":
            assert recovered["effects"][0]["reason"] == "source_access_denied"
            assert recovered["owner_calls"] == [["knowledge", "read"]]
            knowledge(status_path, expected=404)
            revise(["read", "process"])
            recovered = worker("recover-before", result_id="recover-before-regranted", origins="crash-origins.json")
            assert recovered["owner_calls"].count(["knowledge", "submit"]) == 1
        else:
            assert not recovered["processing_reads"]
            assert recovered["owner_calls"] == [["knowledge", "read"], ["knowledge", "accepted"]]
        effect = recovered["effects"][0]
        assert effect["status"] == "acknowledged" and recovered["pinned_base"] is None
        assert all(effect[field] == crash[field] for field in ("request", "payload_sha256", "prepared_at"))
        replay = worker("replay-" + boundary, denied=True, origins="crash-origins.json")
        assert replay["effects"] == recovered["effects"] and not replay["owner_calls"] and not replay["processing_reads"]
        assert len({crash["pid"], live["pid"], recovered["pid"], replay["pid"]}) == 4
        evidence[boundary] = {"exit_code": code, "crash": crash, "live_lease": live, "recovered": recovered,
            "replay": replay, "owner_before_recovery": remote}
        with (output / ("boundary-" + boundary + ".json")).open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(evidence[boundary], indent=2) + "\n")

    revise(["read", "process"])
    original = evidence["after"]["crash"]["request"]
    fabricated = copy.deepcopy(original)

    def regraph(value):
        if isinstance(value, dict):
            if "graph_id" in value:
                value["graph_id"] = "fabricated-span"
            for item in value.values():
                regraph(item)
        elif isinstance(value, list):
            for item in value:
                regraph(item)
    regraph(fabricated)
    conflicted = copy.deepcopy(fabricated)
    conflicted["change_id"] = "conflicting-source-span"
    conflicted["grounding"]["spans"][0]["sha256"] = "f" * 64
    conflict = knowledge("/v1/graph-proposals", conflicted)
    assert conflict["decision"]["outcome"] == "rejected"
    assert conflict["decision"]["findings"][0]["code"] == "reference_identity_conflict"
    fabricated["change_id"] = "fabricated-source-span"
    target = fabricated["grounding"]["spans"][0]

    def forge_all_copies(value):
        if isinstance(value, dict):
            if value.get("unit") == "byte" and all(value.get(key) == target[key] for key in ("source", "start", "end")):
                value["sha256"] = "f" * 64
            for item in value.values():
                forge_all_copies(item)
        elif isinstance(value, list):
            for item in value:
                forge_all_copies(item)
    forge_all_copies(fabricated)
    rejected = knowledge("/v1/graph-proposals", fabricated)
    assert rejected["decision"]["outcome"] == "rejected", rejected
    assert rejected["decision"]["findings"][0]["code"] == "source_span_digest_mismatch", rejected
    knowledge("/v1/graph-heads/read", fabricated["graph"], expected=404)
    unauthorized = copy.deepcopy(original)
    unauthorized["change_id"] = "unauthorized-proposal"
    denied = knowledge("/v1/graph-proposals", unauthorized, expected=403, role="denied")
    knowledge(f"/v1/graphs/{original['graph']['graph_id']}/proposals/unauthorized-proposal", expected=404)
    head = knowledge("/v1/graph-heads/read", original["graph"])
    assert head == evidence["after"]["recovered"]["effects"][0]["outcome"]["status"]["decision"]["decision"]["head"]
    evidence["authority_negatives"] = {"conflicting_span": conflict, "fabricated_span": rejected,
        "unauthorized": denied, "original_head_unchanged": head}
    evidence["limits"] = ["Abrupt os._exit at named Planning boundaries; actual remote Knowledge HTTP and retained SQL",
        "Production120s leases expire naturally; no control reset, clock mutation or shortened lease",
        "Synthetic scientific/provider inputs; no machine/power-failure or live-model claim"]
    (output / "failure-oracles.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return {"status": "passed", "file": "failure-oracles.json", "boundaries": ["before_owner_post", "after_owner_response"],
        "unauthorized_accepted_changes": 0, "fabricated_accepted_citations": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("output", "installation", "data-python", "research-installation", "knowledge-installation"):
        parser.add_argument("--" + argument, type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation, args.data_python, args.research_installation, args.knowledge_installation, extension=failures)
