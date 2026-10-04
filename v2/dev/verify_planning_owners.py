"""Combined actual Data/Research/Knowledge acceptance for installed Planning."""

import argparse
import copy
import json
import os
import secrets
import shutil
import subprocess
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL

from planning_knowledge_fixture import ReadOwnerHost
from planning_owner_fixture import POLICY, VOCABULARY, fixture, result_profiles
from planning_publication_fixture import PLANNING, DataHost, configure
from postgres_fixture import owned_state


def request(endpoint, token, path, body=None, *, expected=200):
    data = None if body is None else json.dumps(body).encode()
    query = urllib.request.Request(endpoint + path, data, headers={"Authorization": "Bearer " + token,
        "Content-Type": "application/json"}, method="GET" if body is None else "POST")
    try:
        with urllib.request.urlopen(query, timeout=30) as response:
            status, raw = response.status, response.read(16777217)
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read(16777217)
    assert status == expected, f"Public owner route {path}: expected {expected}, received {status}; {raw[:300]!r}"
    assert len(raw) <= 16777216
    return json.loads(raw)


def verify(output, installation, data_python, research_installation, knowledge_installation, *, extension=None):
    assert os.environ.get("AMPHORA_TEST_POSTGRES") == "1", "Explicit retained PostgreSQL opt-in required"
    output, installation, data_python = output.absolute(), installation.absolute(), data_python.absolute()
    research_installation, knowledge_installation = research_installation.absolute(), knowledge_installation.absolute()
    assert json.loads((installation / "manifest.json").read_bytes())["status"] == "passed"
    output.mkdir(parents=True, exist_ok=False)
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA"}}
    environment["PYTHONUTF8"] = "1"

    def run(python, args, env=environment, *, expected=0):
        result = subprocess.run([str(python), "-I", *map(str, args)], cwd=output, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", timeout=180)
        with (output / "workers.log").open("a", encoding="utf-8") as stream:
            stream.write(result.stdout)
        assert result.returncode == expected, "Combined owner worker failed; inspect workers.log"

    installations = {"planning": installation, "research": research_installation, "knowledge": knowledge_installation}
    versions = {"planning": ("amphora-agent-planning", "0.30.0"), "research": ("amphora-research", "0.34.0"),
        "knowledge": ("amphora-knowledge", "0.18.0")}
    for name, root in installations.items():
        package, version = versions[name]
        for label in ("initial", "replacement"):
            run(root / label / "Scripts/python.exe", ["-c", "from importlib.metadata import version; "
                f"assert version('{package}') == '{version}'"])
    run(data_python, ["-c", "from importlib.metadata import version; assert version('amphora-data-artifacts') == '0.29.0'"])
    state = owned_state()
    host, port = state["endpoint"].split(":")
    base = URL.create("postgresql+psycopg", username="planning_service", password=state["password"],
        host=host, port=int(port), database=state["database"])
    scope = {"tenant_id": "planning-combined", "project_id": uuid.uuid4().hex}
    config, admin_token, profile = configure(output, scope)
    tokens = {key: secrets.token_hex(32) for key in ("planning_data", "knowledge_data", "planning_research",
        "knowledge_research", "planning_knowledge", "knowledge_admin", "wrong_scope", "denied")}
    credentials = {"COMBINED_" + key.upper(): value for key, value in tokens.items()}
    document = json.loads(config.read_bytes())
    result_profiles(output, document)
    document["principals"].extend([
        {"token_env": "COMBINED_PLANNING_DATA", "actor_id": "fixture", "scope": scope,
         "actions": ["read", "source_history", "upload", "finalize"]},
        {"token_env": "COMBINED_KNOWLEDGE_DATA", "actor_id": "knowledge-reader", "scope": scope,
         "actions": ["read", "source_history"]}])
    config.write_text(json.dumps(document), encoding="utf-8")
    data_env = {**environment, **credentials, "PUBLICATION_DATA_TOKEN": admin_token,
        "PUBLICATION_DATA_DATABASE": base.set(username="artifact_service").render_as_string(hide_password=False)}
    research_config = output / "research.json"
    research_config.write_text(json.dumps({"database_url_env": "COMBINED_RESEARCH_DB", "declarations": True,
        "principals": [
            {"token_env": "COMBINED_PLANNING_RESEARCH", "actor_id": "fixture", "scope": scope,
             "actions": ["read_declarations", "declare_question", "declare_evidence_need"]},
            {"token_env": "COMBINED_KNOWLEDGE_RESEARCH", "actor_id": "knowledge-reader", "scope": scope,
             "actions": ["read_declarations"]}]}), encoding="utf-8")
    research_env = {**environment, **credentials,
        "COMBINED_RESEARCH_DB": base.set(username="research_service").render_as_string(hide_password=False)}
    probe = output / "combined_owner_probe.py"
    shutil.copyfile(PLANNING / "tests/acceptance/combined_owner_probe.py", probe)
    owners, records, pids = [], {}, {}
    try:
        data = DataHost(data_python, config, data_env, admin_token)
        owners.append(data)
        fixture_path, rights, source = fixture(data, output, scope, profile)
        research = ReadOwnerHost(research_installation / "initial/Scripts/python.exe", research_config, research_env, module="amphora_research")
        owners.append(research)
        knowledge_config = output / "knowledge.json"
        knowledge_config.write_text(json.dumps({"database_url_env": "COMBINED_KNOWLEDGE_DB", "vocabulary": VOCABULARY, "policy": POLICY,
            "data": {"endpoint": data.endpoint, "token_env": "COMBINED_KNOWLEDGE_DATA"},
            "research": {"endpoint": research.endpoint, "token_env": "COMBINED_KNOWLEDGE_RESEARCH"}, "principals": [
                {"token_env": "COMBINED_PLANNING_KNOWLEDGE", "actor_id": "fixture", "scope": scope,
                 "actions": ["read_graph", "propose_graph"]},
                {"token_env": "COMBINED_KNOWLEDGE_ADMIN", "actor_id": "owner-admin", "scope": scope,
                 "actions": ["read_graph", "propose_graph", "rebuild_graph"]},
                {"token_env": "COMBINED_WRONG_SCOPE", "actor_id": "other", "scope": dict(scope, project_id="other"),
                 "actions": ["read_graph", "propose_graph"]},
                {"token_env": "COMBINED_DENIED", "actor_id": "fixture", "scope": scope, "actions": ["rebuild_graph"]}]}), encoding="utf-8")
        knowledge_env = {**environment, **credentials,
            "COMBINED_KNOWLEDGE_DB": base.set(username="knowledge_service").render_as_string(hide_password=False)}
        knowledge = ReadOwnerHost(knowledge_installation / "initial/Scripts/python.exe", knowledge_config, knowledge_env)
        owners.append(knowledge)
        pids.update(data=[data.process.pid], research=[research.process.pid], knowledge=[knowledge.process.pid])

        def worker(stage, label="replacement", *, denied=False, expected=0, result_id=None, origins="origins.json"):
            result_id = stage if result_id is None else result_id
            destination = output / (result_id + ".json")
            assert not destination.exists(), "Retained worker evidence must not be overwritten"
            env = {**environment, "COMBINED_PLANNING_DB": base.render_as_string(hide_password=False),
                "COMBINED_DATA_ENDPOINT": data.endpoint, "COMBINED_DATA_TOKEN": tokens["planning_data"],
                "COMBINED_RESEARCH_ENDPOINT": research.endpoint, "COMBINED_RESEARCH_TOKEN": tokens["planning_research"],
                "COMBINED_KNOWLEDGE_ENDPOINT": knowledge.endpoint,
                "COMBINED_KNOWLEDGE_TOKEN": tokens["denied" if denied else "planning_knowledge"]}
            run(installation / label / "Scripts/python.exe", [probe, stage, fixture_path, output / origins, destination], env, expected=expected)
            records[result_id] = json.loads(destination.read_bytes())
            return records[result_id]

        def revise(uses):
            nonlocal rights
            previous = rights["reference"]
            rights = dict(rights, reference=dict(previous, revision=previous["revision"] + 1), supersedes=previous,
                status="granted" if uses else "revoked", allowed_uses=uses)
            data.call("POST", "/v1/acquisition/rights", rights)

        def k(path, body=None, *, expected=200, role="planning_knowledge"):
            return request(knowledge.endpoint, tokens[role], path, body, expected=expected)

        seed = worker("seed", "initial")
        assert seed["provider_calls"] == ["diagnostic", "campaign", "stale"]
        revise(["read"])
        blocked = worker("processing-denied")
        assert not blocked["owner_calls"] and all(item["status"] in {"unprepared", "blocked"} for item in blocked["effects"])
        assert {item["reason"] for item in blocked["effects"] if item["kind"] != "answer"} == {"source_access_denied"}
        revise(["read", "process"])
        uncertain = worker("uncertain", "initial")
        by_kind = {item["kind"]: item for item in uncertain["effects"]}
        assert [by_kind[key]["status"] for key in ("question", "need", "answer", "graph")] == ["acknowledged", "acknowledged", "finalized", "uncertain"], by_kind
        revise(["read"])
        denied = worker("owner-denied", denied=True)
        assert denied["effects"][-1]["reason"] == "owner_access_denied"
        knowledge.close()
        knowledge = ReadOwnerHost(knowledge_installation / "replacement/Scripts/python.exe", knowledge_config, knowledge_env)
        owners.append(knowledge)
        pids["knowledge"].append(knowledge.process.pid)
        recovered = worker("recover")
        assert not recovered["processing_reads"] and recovered["owner_calls"] == [["knowledge", "read"], ["knowledge", "accepted"]]
        graph_effect = recovered["effects"][-1]
        assert graph_effect["status"] == "acknowledged"
        assert all(graph_effect[field] == by_kind["graph"][field] for field in ("request", "payload_sha256", "prepared_at"))
        replay = worker("replay", denied=True)
        assert replay["effects"] == recovered["effects"] and not replay["owner_calls"] and not replay["processing_reads"]
        proposal, outcome = graph_effect["request"], graph_effect["outcome"]
        head = outcome["status"]["decision"]["decision"]["head"]
        snapshot = k("/v1/graph-snapshots/read", head["snapshot"])
        assertions = snapshot["content"]["assertions"]
        assert {row["polarity"] for row in assertions} == {"affirmed", "negated"}
        assert {row["posture"] for row in assertions} == {"hypothesis"}
        assert k("/v1/graph-changes/read", head["change"]) == outcome["accepted"]
        negative = {}
        negative["scope"] = k("/v1/graph-changes/read", head["change"], expected=403, role="wrong_scope")
        negative["altered_snapshot"] = k("/v1/graph-snapshots/read", dict(head["snapshot"], sha256="f" * 64), expected=404)
        negative["missing_change"] = k("/v1/graph-changes/read", dict(head["change"], change_id="absent"), expected=404)
        changed = copy.deepcopy(proposal)
        changed["rationale"] = "Changed immutable bytes"
        negative["altered_proposal"] = k("/v1/graph-proposals", changed, expected=409)
        no_processing = copy.deepcopy(proposal)
        no_processing.update(change_id="processing-denied", base=head)
        negative["processing"] = k("/v1/graph-proposals", no_processing)
        assert negative["processing"]["decision"]["outcome"] == "rejected"
        assert negative["processing"]["decision"]["findings"][0]["code"] == "peer_access_denied"
        revise(["read", "process"])
        stale = worker("stale")
        assert stale["effects"][-1]["status"] == "conflict" and stale["pinned_base"] is None
        correction = copy.deepcopy(proposal)
        correction.update(change_id="typed-correction", base=head,
            operations=[{"operation": "retract_assertion", "assertion": assertions[0]["reference"]}])
        corrected = k("/v1/graph-proposals", correction, role="knowledge_admin")
        assert corrected["decision"]["outcome"] == "accepted", corrected
        corrected_head = corrected["decision"]["head"]
        corrected_snapshot = k("/v1/graph-snapshots/read", corrected_head["snapshot"])
        assert corrected_snapshot["content"]["assertions"] == assertions and len(corrected_snapshot["content"]["retractions"]) == 1
        # A separate accepted-log correction remains pending while its public
        # processing peer is unavailable; recovery retains the exact intent.
        pending = copy.deepcopy(correction)
        pending.update(change_id="pending-correction", base=corrected_head,
            operations=[{"operation": "retract_assertion", "assertion": assertions[1]["reference"]}])
        unavailable_config = output / "knowledge-unavailable.json"
        unavailable = json.loads(knowledge_config.read_bytes())
        unavailable["data"]["endpoint"] = "http://127.0.0.1:1"
        unavailable_config.write_text(json.dumps(unavailable), encoding="utf-8")
        knowledge.close()
        knowledge = ReadOwnerHost(knowledge_installation / "replacement/Scripts/python.exe", unavailable_config, knowledge_env)
        owners.append(knowledge)
        pids["knowledge"].append(knowledge.process.pid)
        negative["pending"] = k("/v1/graph-proposals", pending, expected=503, role="knowledge_admin")
        pending_status = k(f"/v1/graphs/{proposal['graph']['graph_id']}/proposals/pending-correction", role="knowledge_admin")
        assert pending_status["decision"] is None and pending_status["proposal"] == pending
        knowledge.close()
        knowledge = ReadOwnerHost(knowledge_installation / "replacement/Scripts/python.exe", knowledge_config, knowledge_env)
        owners.append(knowledge)
        pids["knowledge"].append(knowledge.process.pid)
        resumed = k("/v1/graph-proposals", pending, role="knowledge_admin")
        assert resumed["decision"]["outcome"] == "accepted" and resumed["request_sha256"] == pending_status["request_sha256"]
        corrected_head = resumed["decision"]["head"]
        corrected_snapshot = k("/v1/graph-snapshots/read", corrected_head["snapshot"])
        assert corrected_snapshot["content"]["assertions"] == assertions and len(corrected_snapshot["content"]["retractions"]) == 2
        revise([])
        rebuild_request = {"wire_version": "1", "graph": proposal["graph"], "rebuild_id": "accepted-log-only"}
        rebuilt = k("/v1/graph-rebuilds", rebuild_request, role="knowledge_admin")
        assert rebuilt["result"]["outcome"] == "published" and rebuilt["result"]["head"] == corrected_head
        assert k("/v1/graph-rebuilds/read", rebuild_request, role="knowledge_admin") == rebuilt
        assert k("/v1/graph-snapshots/read", head["snapshot"]) == snapshot
        assert k("/v1/graph-snapshots/read", corrected_head["snapshot"]) == corrected_snapshot
        assert k("/v1/graph-heads/read", proposal["graph"]) == corrected_head
        (output / "future-head.json").write_text(json.dumps(corrected_head), encoding="utf-8")
        future = worker("future-pin")
        assert future["pinned_base"] == corrected_head and not future["provider_calls"] and not future["processing_reads"]
        final = worker("after-correction", denied=True)
        assert final["effects"] == recovered["effects"] and final["task_sha256"] == recovered["task_sha256"]
        assert not final["processing_reads"] and not final["owner_calls"] and final["pinned_base"] is None
        extended = None if extension is None else extension(output, worker, revise, k)
        manifest = {"status": "passed", "verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
            "versions": versions, "scope": scope, "owner_pids": pids, "stages": records, "negative_controls": negative,
            "original_head": head, "corrected_head": corrected_head, "rebuild": rebuilt,
            "extension": extended,
            "limits": ["Synthetic provider output and scientific sources; no scientific validity or live model claim",
                "Actual owner HTTP and scoped credentials; Knowledge replacement, synthetic lost reply after real commit",
                "Historical rebuild/replay under revoked processing; no new model invocation, source grant or campaign repin",
                "No cross-owner SQL, migrators or fixture reset",
                "Base stages use normal replacement; optional extension evidence owns its named abrupt exits"]}
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "passed", "planning_workers": len(records), "owner_processes": sum(map(len, pids.values()))}))
    finally:
        for owner in reversed(owners):
            owner.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("output", "installation", "data-python", "research-installation", "knowledge-installation"):
        parser.add_argument("--" + argument, type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation, args.data_python, args.research_installation, args.knowledge_installation)
