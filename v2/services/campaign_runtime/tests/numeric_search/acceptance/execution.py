"""Real standalone worker processes and owner receipt/evidence assertions."""

import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor


def worker_command(e, stage, actor, http, lease_seconds=90):
    config = {"actor_id": actor, "scope": e.scope, "run_id": e.active_run, "image_sha256": e.image(stage),
        "runtime": {"endpoint": e.runtime_relay.endpoint, "token_env": "WORKER_TOKEN"},
        "artifacts": {"endpoint": e.artifact_relay.endpoint, "token_env": "WORKER_TOKEN"}, "lease_seconds": lease_seconds}
    path = e.root / (stage + "-" + actor + "-worker.json")
    path.write_text(json.dumps(config), encoding="utf-8")
    numeric = stage != "evaluate"
    module = "amphora_evolution_search" if numeric else "amphora_synthetic_objectives"
    arguments = ["--operation", stage] if numeric else []
    command = [e.config["numeric" if numeric else "evaluator"], "-I", "-m", module,
               "worker", *arguments, "--config", str(path)]
    if numeric and e.config.get("reconstructed_adapter"):
        command = [e.config["numeric"], "-I", e.config["reconstructed_adapter"], "worker", "--operation", stage,
                   "--descriptor", str(e.root / (stage + "-descriptor.json")), "--config", str(path)]
    return command, dict(http.isolated_env(), WORKER_TOKEN=e.tokens[actor])


def run_worker(e, stage, actor, http):
    command, environment = worker_command(e, stage, actor, http)
    process = subprocess.run(command, cwd=e.root, env=environment, capture_output=True, check=False, timeout=120)
    assert process.returncode == 0, (stage, process.stderr.decode()[-1000:])
    result = json.loads(process.stdout)
    assert result["status"] in {"completion_accepted", "no_eligible_work"}, result
    if result["status"] == "completion_accepted":
        assert result["outcome"] == "succeeded", (stage, result)
    return result


def execute(e, http, *, failure=None):
    outcomes = []
    first_event = len(e.runtime_relay.events)
    interrupted = False
    for _ in range(100):
        page = e.advance()
        if page["status"] != "running":
            break
        modes = {"seed": "seed", "expand": "requests", "collect": "collect", "vary": "vary", "evaluate": "evaluate"}
        eligible = {modes[node["path"]["node_id"]] for node in page["nodes"]
                    if node["kind"] == "invoke" and node["status"] == "issued"}
        for stage in ("seed", "requests", "collect", "vary", "evaluate"):
            if stage not in eligible:
                continue
            failure_stage = getattr(failure, "stage", "vary")
            if stage == failure_stage and failure is not None and not interrupted:
                failure.interrupt(e, http, worker_command)
                interrupted = True
            actors = ("worker1", "worker2") if stage == "evaluate" else ("worker1",)
            with ThreadPoolExecutor(max_workers=len(actors)) as pool:
                outcomes.extend(pool.map(lambda actor, stage=stage: run_worker(e, stage, actor, http), actors))
            if stage == failure_stage and failure is not None and interrupted and not failure.verified:
                failure.verify_retry(e, http)
    assert page["status"] == "completed", page
    reports, seen = [], set()
    for event in e.runtime_relay.events[first_event:]:
        identity = event.get("identity")
        if not identity or identity["command_family"] != "runtime.complete":
            continue
        key = (identity["actor_id"], identity["command_id"])
        if key in seen:
            continue
        seen.add(key)
        receipt = http.decoded(e.runtime.endpoint, "/v1/commands/runtime.complete/" + key[1] + "?actor_id=" + key[0], e.tokens["admin"])
        record = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run + "/completions/" +
            receipt["outcome"]["committed"]["object_id"], e.tokens["admin"])
        assert record["canonical_result"] and len(record["retention_reservation_ids"]) == 1
        artifact = record["result"]["outcome"]["outputs"][0]["artifact"]
        reports.append({"receipt": receipt, "completion": record, "artifact": artifact, "result": json.loads(e.bytes(artifact))})
    selected = [report for report in reports if report["artifact"]["schema_ref"]["schema_id"] == "search.checkpoint"
                and report["result"]["phase"] in {"selected", "stopped"}]
    assert [report["result"]["generation"] for report in selected] == [0, 1, 2]
    final = selected[-1]
    assert final["result"]["stop_reason"] == "generation_budget" and final["result"]["rng"]["counter"] == 26
    evaluations = [report for report in reports if report["artifact"]["schema_ref"]["schema_id"] == "search.evaluation-observation"]
    assert len(evaluations) == final["result"]["progress"]["evaluations_issued"]
    assert all(report["result"]["outcome"]["evidence"] == [e.policy] for report in evaluations)
    assert page["reserved"] == 0 and page["spent"] == len(reports) + int(interrupted)
    value = {"kind": "artifact", "artifact": final["artifact"], "representation": "search.checkpoint", "unit": "1"}
    digest = hashlib.sha256(json.dumps({"profile": "amphora-carried-value-v1", "value": value}, sort_keys=True,
                                      separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
    cut = http.decoded(e.runtime.endpoint, "/v1/graph-runs/" + e.active_run + "/carry-sources", e.tokens["admin"])
    assert cut["sources"][0]["value_sha256"] == digest
    reservations = {event["response"]["outcome"]["binding"]["reservation_id"]: event["response"]
        for event in e.artifact_relay.events if event["path"] == "/v1/reservations" and event["status"] == 200}
    for _ in range(12):
        e.owner_command("deliver", "--limit", "100", "--time-budget", "10")
        retained = {key: http.decoded(e.artifact.endpoint, "/v1/reservations/" + key, e.tokens["runtime"]) for key in reservations}
        if all(receipt["outcome"]["status"] == "confirmed" for receipt in retained.values()):
            break
    assert reservations and all(receipt["outcome"]["status"] == "confirmed" for receipt in retained.values())
    assert http.decoded(e.runtime.endpoint, "/v1/graph-runs", e.tokens["admin"], e.admission_command) == e.admission
    return {"graph": page, "admission": e.admission, "reports": reports, "final": final, "cut": cut,
            "retained": retained, "workers": outcomes, "runtime_requests": e.runtime_relay.events,
            "artifact_requests": e.artifact_relay.events, "interruption": None if failure is None else failure.evidence}
