"""Installed campaign Research clients, actual owner, retained restart and future revisions."""

import argparse
import copy
import hashlib
import json
import os
import secrets
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from amphora_agent_planning.context import RequestSnapshot
from amphora_contracts_core import Scope
from sqlalchemy import URL

from planning_knowledge_fixture import ROOT, ReadOwnerHost, rescope
from postgres_fixture import owned_state


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def case_file(path, template, prepared, *, missing=False, foreign=False, future=None):
    request = copy.deepcopy(template)
    scope = prepared["question"]["reference"]["scope"]
    rescope(request, scope)
    if foreign:
        scope = dict(scope, project_id="foreign")
        rescope(request, scope)
    bound = RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id="fixture", scope=Scope.model_validate_json(json.dumps(scope)))
    question = prepared["question"] if future is None else future["question"]
    selected = {"schema_version": "1", "engagement": request["reference"], "request_sha256": bound.sha256,
        "questions": [question["reference"]], "needs": [] if future else [prepared["need"]["reference"]],
        "assessments": [] if future else [{"request": prepared["completed"]["request"],
            "status_sha256": hashlib.sha256(canonical(prepared["completed"])).hexdigest()},
            {"request": prepared["pending"], "status_sha256": "0" * 64}]}
    if missing:
        selected["questions"].append(dict(question["reference"], question_id="missing"))
    observation = prepared["observation"] if future is None else future["observation"]["reference"]
    queries = {"specimens": {"wire_version": "1", "experiment": prepared["experiment"], "limit": 1},
        "properties": {"wire_version": "1", "experiment": prepared["experiment"],
                       "observations": [observation, prepared["series"]], "limit": 1},
        "observation_series": {"wire_version": "1", "observation": prepared["series"], "limit": 1}}
    value = {"request": request, "selection": selected, "queries": queries}
    if foreign:
        # Copy first: selected references came from the retained preparation result.
        value = copy.deepcopy(value)
        rescope(value, scope)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def verify(output, installation, research_python):
    assert os.environ.get("AMPHORA_TEST_POSTGRES") == "1", "Explicit retained PostgreSQL opt-in required"
    output, installation, research_python = output.absolute(), installation.absolute(), research_python.absolute()
    manifest = json.loads((installation / "manifest.json").read_bytes())
    assert manifest["status"] == "passed" and manifest["planning"] == "0.34.0"
    output.mkdir(parents=True, exist_ok=False)
    python = installation / "environment/Scripts/python.exe"
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="research_service", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "COMSPEC"}}
    environment["PYTHONUTF8"] = "1"
    scope = {"tenant_id": "campaign-research", "project_id": uuid.uuid4().hex}
    fixture = {"views": json.loads((ROOT / "contracts/research_views/tests/fixtures/views.json").read_bytes()),
        "records": json.loads((ROOT / "services/agent_planning/tests/campaign_context/fixtures/records.json").read_bytes())}
    rescope(fixture, scope)
    fixture_path = output / "synthetic-inputs.json"
    fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
    seed_env = dict(environment, CAMPAIGN_RESEARCH_DB=url.render_as_string(hide_password=False))

    def run(executable, args, env):
        process = subprocess.run([str(executable), "-I", *map(str, args)], cwd=output, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", timeout=60)
        with (output / "processes.log").open("a", encoding="utf-8") as stream:
            stream.write(process.stdout)
        assert process.returncode == 0, "Campaign Research process failed; inspect retained processes.log"
        return json.loads(process.stdout)

    seed = ROOT / "dev/planning_campaign_research_seed.py"
    prepared = run(research_python, [seed, "prepare", fixture_path], seed_env)
    token, denied = secrets.token_hex(32), secrets.token_hex(32)
    peer = {"endpoint": "http://127.0.0.1:1", "token_env": "CAMPAIGN_UNUSED_TOKEN"}
    config = {"database_url_env": "CAMPAIGN_RESEARCH_DB", "principals": [
        {"token_env": "CAMPAIGN_RESEARCH_TOKEN", "actor_id": "fixture", "scope": scope,
         "actions": ["read_declarations", "read_assessment", "read_scientific_record"]},
        {"token_env": "CAMPAIGN_RESEARCH_DENIED", "actor_id": "fixture", "scope": scope, "actions": ["resolve_identity"]}],
        "assessment": {"profiles": [prepared["profile"]], "data": peer,
            "publication": {"actor_id": "publisher", "issuer_id": "fixture", "token_env": "CAMPAIGN_UNUSED_TOKEN"}},
        "science": {"lab_profiles": [], "eligibility_profiles": [], "synthesis_profiles": [], "data": peer,
            "publication": {"actor_id": "publisher", "token_env": "CAMPAIGN_UNUSED_TOKEN"}, "consumer_publishers": []}}
    config_path = output / "research.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    host_env = dict(seed_env, CAMPAIGN_RESEARCH_TOKEN=token, CAMPAIGN_RESEARCH_DENIED=denied, CAMPAIGN_UNUSED_TOKEN=secrets.token_hex(32))
    template = json.loads((ROOT / "services/agent_planning/tests/campaign_context/fixtures/request.json").read_bytes())
    original_path = case_file(output / "original.json", template, prepared)
    probe = output / "campaign_research_probe.py"
    shutil.copyfile(ROOT / "services/agent_planning/tests/acceptance/campaign_research_probe.py", probe)
    owner = ReadOwnerHost(research_python, config_path, host_env, module="amphora_research")
    owners, results = [owner.process.pid], {}

    def read(label, path=original_path, credential=token):
        result = run(python, [probe, path], dict(environment,
            CAMPAIGN_RESEARCH_ENDPOINT=owner.endpoint, CAMPAIGN_RESEARCH_TOKEN=credential))
        results[label] = result
        return result

    def same(left, right):
        assert {k: v for k, v in left.items() if k != "pid"} == {k: v for k, v in right.items() if k != "pid"}

    try:
        original = read("original")
        assert not original["record_failures"] and len(original["record_hashes"]) == 3 and original["record_calls"] == 4
        assert [item["record"] for item in original["context"]["records"]] == [
            prepared["question"], prepared["need"], prepared["completed"]]
        assert [gap["reason"] for gap in original["context"]["gaps"]] == ["pending"]
        assessment = original["context"]["records"][2]["record"]["outcome"]["assessment"]
        assert assessment["disposition"] == "unknown" and not assessment["sufficient"] and not assessment["scientifically_established"]
        assert original["view_calls"] == 6 and original["catalog"] is not None
        assert all(item["failure"] is None for item in original["pages"].values())
        assert original["pages"]["properties"]["page"]["rows"][0]["reference"] == prepared["observation"]
        assert original["pages"]["properties"]["page"]["rows"][0]["quality"] == fixture["views"]["observation"]["quality"]
        assert original["pages"]["properties"]["page"]["rows"][0]["value"] == fixture["views"]["observation"]["value"]
        assert original["pages"]["properties"]["next"]["rows"][0]["reference"] == prepared["series"]
        series = original["pages"]["observation_series"]
        assert series["page"]["points"][0]["x"] == series["next"]["points"][0]["x"]
        partial = read("missing-question", case_file(output / "partial.json", template, prepared, missing=True))
        assert partial["record_failures"] == ["research_reference_unavailable"] and partial["record_hashes"] == original["record_hashes"]
        blocked = read("denied", credential=denied)
        assert not blocked["record_hashes"] and set(blocked["record_failures"]) == {"research_access_denied"}
        assert all(item["failure"] == "research_access_denied" for item in blocked["pages"].values())
        foreign = read("foreign-scope", case_file(output / "foreign.json", template, prepared, foreign=True))
        assert not foreign["record_hashes"] and all(item["failure"] == "research_access_denied" for item in foreign["pages"].values())
        revised = run(research_python, [seed, "advance", fixture_path], seed_env)
        same(original, read("original-after-correction"))
        future = read("future-campaign", case_file(output / "future.json", template, prepared, future=revised))
        assert future["record_hashes"] != original["record_hashes"] and not future["record_failures"]
        assert future["pages"]["properties"]["page"]["rows"][0]["value"] == {"kind": "missing", "reason": "report_corrected"}
        owner.close()
        owner = ReadOwnerHost(research_python, config_path, host_env, module="amphora_research")
        owners.append(owner.process.pid)
        same(original, read("original-after-owner-restart"))
    finally:
        owner.close()
    proof = {"status": "passed", "verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "planning": "0.34.0", "research": "0.34.0", "scope": scope, "owner_pids": owners,
        "worker_pids": [value["pid"] for value in results.values()], "stages": list(results),
        "original": original, "future": future, "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        "limits": ["Owner-local synthetic fixture setup, not public registration or scientific proof",
            "Planning has only public contracts; no Research implementation or SQL in its worker",
            "Retained PostgreSQL scope; no migrator, reset, source processing, provider or active campaign rebase",
            "Fresh workers and owner restart use existing independently verified wheels; no new replacement wheel"]}
    (output / "manifest.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "workers": len(results), "owners": len(owners)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--research-python", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation, args.research_python)
