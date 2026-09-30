"""Public-owner cancellation/completion interleavings with real installed workers."""

import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def wait_file(path, future):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            return json.loads(path.read_bytes())
        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            pass
        if future.done():
            future.result()
            raise AssertionError("Browser finished before barrier")
        time.sleep(0.02)
    raise AssertionError("Browser did not reach barrier")


def cancellation_races(e, http, operations):
    for completion_first in (False, True):
        e.admit_emergency_run()
        tool = e.stages["seed"]
        e.advance()
        operations.select(e, tool)
        worker = operations.processes.Worker(e, http, tool, "worker1", lease_seconds=120)
        try:
            claim = worker.wait("claimed")
            assert claim["outcome"]["status"] == "claimed", claim
            worker.resume()
            published = worker.wait("published")
            invocation = claim["outcome"]["invocation"]
            command = e.command("runtime.complete", {"run_id": e.active_run, "completion": {
                "schema_version": "1", "invocation_id": invocation["invocation_id"],
                "attempt_id": invocation["attempt_id"], "fence": invocation["fence"],
                "outcome": {"status": "succeeded", "outputs": [{"port": tool.descriptor["outputs"][0]["name"],
                    "artifact": published["artifact"]}], "checkpoint": None}}}, "worker1")

            def complete(command=command):
                return http.decoded(e.runtime.endpoint, "/v1/invocations/complete", e.tokens["worker1"], command)

            if completion_first:
                marker, release = e.root / "stop-captured.json", e.root / "stop-release"
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(e.authoring_browser, "cancel-completion-first",
                        expected_reason="run_revision_conflict", barrier={"marker": str(marker), "release": str(release)})
                    captured = wait_file(marker, future)
                    try:
                        receipt = complete()
                        assert receipt["outcome"]["status"] == "accepted", receipt
                        assert receipt["outcome"]["committed"]["revision"] > captured["payload"]["expected_run_revision"]
                    finally:
                        release.write_text("continue", encoding="utf-8")
                    browser = future.result(timeout=90)
                completion_path = "/v1/runs/" + e.active_run + "/completions/" + receipt["outcome"]["committed"]["object_id"]
                canonical = http.decoded(e.runtime.endpoint, completion_path, e.tokens["admin"])
                assert canonical["canonical_result"] and canonical["result"]["outcome"]["outputs"][0]["artifact"] == published["artifact"]
                assert browser["observed_status"] == "running"
                # A deliberate fresh consumer observes the new revision before requesting cleanup.
                e.authoring_browser("cancel-after-completion")
                assert http.decoded(e.runtime.endpoint, completion_path, e.tokens["admin"]) == canonical
            else:
                browser = e.authoring_browser("cancel-first")
                receipt = complete()
                assert receipt["outcome"]["status"] == "rejected", receipt
                assert browser["observed_status"] == "cancelled"
            worker.resume()
            stdout, stderr = worker.child.communicate(timeout=30)
            assert worker.child.returncode == 3, stderr[-1000:] + stdout[-1000:]
            assert json.loads(stdout) == {"status": "authority_or_transport_lost"}
            final = e.graph()
            assert final["status"] == "cancelled" and final["reserved"] == 0
            assert http.decoded(e.runtime.endpoint, "/v1/invocations/complete", e.tokens["worker1"], command) == receipt
            e.record("STUDIO-COMPLETION-FIRST" if completion_first else "STUDIO-CANCELLATION-FIRST", {
                "run": e.active_run, "completion_receipt": receipt, "stop_receipt": browser["receipt"],
                "published_artifact": published["artifact"], "final_graph": final,
                "canonical_completion_preserved": completion_first, "worker_authority_lost": True,
                "limits": "Pure synthetic worker only; external effects remain explicitly uncertain in Studio."})
        finally:
            worker.close()


def pending_crash(e, http):
    old = e.runtime
    old.close()
    marker, release = e.root / "registered.json", e.root / "restarted"
    # Reuse Service readiness/owned process cleanup, with an explicit owner-test entry point.
    fault = object.__new__(http.Service)
    fault.python, fault.module, fault.config = old.python, old.module, old.config
    fault.env, fault.directory, fault.port, fault.endpoint = old.env, old.directory, old.port, old.endpoint
    fault.log = (e.root / "registration-fault.log").open("wb")
    script = Path(__file__).absolute().parents[3] / "services/campaign_runtime/tests/definitions/registration_fault_host.py"
    fault.child = subprocess.Popen([fault.python, "-I", str(script), "--config", fault.config,
        "--port", str(fault.port), "--marker", str(marker)], cwd=e.root, env=fault.env,
        stdout=subprocess.DEVNULL, stderr=fault.log)
    e.resources.append(fault)
    e.runtime = fault
    fault.ready(e.tokens["admin"])
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(e.authoring_browser, "pending-crash", barrier={"marker": str(marker), "release": str(release)})
        registered = wait_file(marker, future)
        assert registered["status"] == "pending"
        fault.close()
        e.runtime = http.Service(e.config["replacements"]["amphora_campaign_runtime"], old.module,
            old.config, old.env, e.root, old.port)
        e.resources.append(e.runtime)
        e.runtime.ready(e.tokens["admin"])
        release.write_text("ready", encoding="utf-8")
        browser = future.result(timeout=90)
    receipt = browser["receipt"]
    assert receipt["outcome"]["status"] == "accepted"
    assert receipt["outcome"]["binding"]["operation_id"] == registered["operation_id"]
    assert receipt["outcome"]["binding"]["request_sha256"] == registered["request_sha256"]
    replay = http.decoded(e.runtime.endpoint, "/v1/definition-drafts/save", e.tokens["studio_author"], browser["submission"])
    assert replay == receipt
    e.record("STUDIO-PENDING-REGISTRATION-CRASH", {"registered": registered, "receipt": receipt,
        "same_original_submission": True, "newer_local_edits_preserved": True,
        "independent_ordinary_host_replacement": True, "limits": "Process kill, not target-host power-loss durability."})
