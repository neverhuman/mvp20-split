"""Named publication/acceptance recovery against real isolated installed owners."""

import hashlib
import importlib.util
import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from http.client import HTTPException
from pathlib import Path
from urllib.error import URLError

spec = importlib.util.spec_from_file_location("recovery_evidence", Path(__file__).with_name("recovery_evidence.py"))
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


@contextmanager
def recording(lab, case):
    record = evidence.ScenarioEvidence(case, lab.scope, lab.packages, 45)
    folder = lab.evidence_dir / lab.scope["project_id"]
    folder.mkdir(parents=True, exist_ok=True)
    try:
        yield record
        record.finish()
    except BaseException as error:
        record.event("failure", type(error).__name__)
        raise
    finally:
        record.save(folder / (case + ".json"))
    print(case + " passed; manifest " + str(folder / (case + ".json")), flush=True)


def dropped(future):
    try:
        future.result(timeout=12)
    except (OSError, URLError, HTTPException, AssertionError):
        return
    raise AssertionError("Killed owner unexpectedly returned a completed response")


def fault_event(lab, pool):
    line = pool.submit(lab.artifact.child.stdout.readline).result(timeout=10)
    assert line, "Fault host exited before barrier"
    return json.loads(line)


def content(lab, value):
    body = json.dumps({"value": value}).encode()
    return body, {"sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body),
                  "media_type": "application/json", "schema_ref": lab.schema}


def begin(lab, descriptor):
    command = lab.command("artifacts.begin_upload", {"content": descriptor}, "worker")
    receipt = lab.art("/v1/uploads", command)
    return command, receipt


def assert_bytes(lab, artifact, body):
    assert lab.support.request(lab.artifact.endpoint, "/v1/artifacts/" + artifact["artifact_id"] + "/content",
                               lab.tokens["worker"]) == (200, body)


def publication(lab):
    with recording(lab, "REC-01") as record:
        lab.artifact.close()
        lab.artifact.start(lab.fault_script, "upload_synced")
        lab.artifact.ready(lab.tokens["worker"])
        body, descriptor = content(lab, 101)
        command, upload = begin(lab, descriptor)
        record.identify(command=command["identity"]["command_id"], upload=upload["upload_id"])
        path = "/v1/uploads/" + upload["upload_id"] + "/content"
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = pool.submit(lab.support.request, lab.artifact.endpoint, path, lab.tokens["worker"], body, "PUT")
            try:
                event = fault_event(lab, pool)
                assert event["barrier"] == "upload_synced" and event["upload_id"] == upload["upload_id"]
                record.identify(attempt=event["attempt_id"])
                record.event("barrier", "actual bytes synced; selected-attempt commit not entered")
            finally:
                pid = lab.artifact.child.pid
                lab.artifact.kill()
                record.event("kill", {"owner": "artifact", "pid": pid})
            dropped(pending)
        lab.artifact.start()
        lab.artifact.ready(lab.tokens["worker"])
        record.event("restart", "same artifact database and storage root; no reset")
        assert lab.art("/v1/uploads", command) == upload
        request = {"upload_id": upload["upload_id"], "content": descriptor}
        rejected = lab.command("artifacts.finalize", request, "worker")
        status, raw = lab.support.request(lab.artifact.endpoint, "/v1/artifacts/finalize", lab.tokens["worker"], rejected)
        assert status == 409 and json.loads(raw)["reason_code"] == "upload_not_ready"
        assert lab.support.request(lab.artifact.endpoint, path, lab.tokens["worker"], body, "PUT")[0] == 200
        finalized = lab.command("artifacts.finalize", request, "worker")
        result = lab.art("/v1/artifacts/finalize", finalized)
        assert lab.art("/v1/artifacts/finalize", finalized) == result
        assert lab.art("/v1/artifacts/finalize", lab.command("artifacts.finalize", request, "worker")) == result
        record.identify(artifact=result["artifact"]["artifact_id"], command=finalized["identity"]["command_id"])
        assert_bytes(lab, result["artifact"], body)
        record.event("observation", "unselected synced bytes cannot finalize; retry and duplicate finalize yield one readable artifact")

    with recording(lab, "REC-02") as record:
        lab.artifact.close()
        lab.artifact.start(lab.fault_script, "finalize_committed")
        lab.artifact.ready(lab.tokens["worker"])
        body, descriptor = content(lab, 102)
        _, upload = begin(lab, descriptor)
        path = "/v1/uploads/" + upload["upload_id"] + "/content"
        assert lab.support.request(lab.artifact.endpoint, path, lab.tokens["worker"], body, "PUT")[0] == 200
        command = lab.command("artifacts.finalize", {"upload_id": upload["upload_id"], "content": descriptor}, "worker")
        record.identify(upload=upload["upload_id"], command=command["identity"]["command_id"])
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = pool.submit(lab.art, "/v1/artifacts/finalize", command)
            try:
                event = fault_event(lab, pool)
                assert event["barrier"] == "finalize_committed"
                original = event["receipt"]
                record.identify(artifact=original["artifact"]["artifact_id"])
                record.event("barrier", "catalog and original receipt committed; response body withheld")
            finally:
                pid = lab.artifact.child.pid
                lab.artifact.kill()
                record.event("kill", {"owner": "artifact", "pid": pid})
            dropped(pending)
        lab.artifact.start()
        lab.artifact.ready(lab.tokens["worker"])
        record.event("restart", "same artifact state; production executable")
        assert lab.art("/v1/artifacts/finalize", command) == original
        assert_bytes(lab, original["artifact"], body)
        record.event("observation", "exact original receipt and hash-matching bytes survive process death")


def completion_record(lab, record, run, command):
    record.identify(run=run, command=command["identity"]["command_id"],
                    attempt=command["payload"]["completion"]["attempt_id"], artifact=lab.output_ref["artifact_id"])


def accepted(lab, record, run, command, receipt):
    assert receipt["outcome"]["status"] == "accepted", receipt
    assert lab.worker("/v1/invocations/complete", command) == receipt
    report_id = receipt["outcome"]["committed"]["object_id"]
    record.identify(intent=report_id)
    report = lab.rt(f"/v1/runs/{run}/completions/{report_id}")
    assert report["canonical_result"] is True and len(report["retention_reservation_ids"]) == 2
    for reservation in report["retention_reservation_ids"]:
        record.identify(reservation=reservation)
        assert lab.art("/v1/reservations/" + reservation, actor="runtime")["outcome"]["status"] == "reserved"
    assert lab.deliver()["acknowledged"] >= 2
    for reservation in report["retention_reservation_ids"]:
        assert lab.art("/v1/reservations/" + reservation, actor="runtime")["outcome"]["status"] == "confirmed"
    snapshot = lab.rt("/v1/runs/" + run)
    assert snapshot["status"] == "completed" and snapshot["budget"] == {"limit": 5, "available": 4, "reserved": 0, "spent": 1}
    assert_bytes(lab, lab.output_ref, json.dumps({"value": 2}).encode())
    record.event("observation", "one canonical acceptance and spent unit; original receipt; both bindings confirmed; accepted bytes readable")


def reservation(lab):
    with recording(lab, "REC-03") as record:
        run, command = lab.start()
        completion_record(lab, record, run, command)
        lab.proxy.arrived.clear()
        lab.proxy.release.clear()
        lab.proxy.hold_next = True
        offset = len(lab.proxy.receipts)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(lab.worker, "/v1/invocations/complete", command)
            try:
                assert lab.proxy.arrived.wait(timeout=10)
                binding = lab.proxy.receipts[offset]["outcome"]["binding"]
                record.identify(intent=binding["intent"]["intent_id"], reservation=binding["reservation_id"])
                assert lab.rt("/v1/completion-intents/outcome", binding, "artifact")["proof"]["status"] == "prepared"
                record.event("barrier", "artifact reserved; actual runtime PREPARED; reserve response withheld")
                pid = lab.runtime.child.pid
                lab.runtime.kill()
                record.event("kill", {"owner": "runtime", "pid": pid})
                reconcile = lab.command("artifacts.reconcile", {"reservation_id": binding["reservation_id"]}, "runtime")
                assert lab.support.request(lab.artifact.endpoint, "/v1/reservations/reconcile", lab.tokens["runtime"], reconcile)[0] == 503
                assert lab.art("/v1/reservations/" + binding["reservation_id"], actor="runtime")["outcome"]["status"] == "reserved"
                record.event("observation", "unreachable runtime leaves protection intact")
            finally:
                lab.proxy.release.set()
            dropped(pending)
        lab.runtime.start()
        lab.runtime.ready(lab.tokens["admin"])
        record.event("restart", "same runtime database, pins and credentials; no reset")
        assert lab.rt("/v1/completion-intents/outcome", binding, "artifact")["proof"]["status"] == "prepared"
        receipt = lab.worker("/v1/invocations/complete", command)
        accepted(lab, record, run, command, receipt)


def committed(lab):
    with recording(lab, "REC-04") as record:
        run, command = lab.start()
        completion_record(lab, record, run, command)
        proxy = lab.support.ReservationProxy(lab.runtime.endpoint, "/v1/invocations/complete")
        proxy.hold_next = True
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(lab.support.decoded, proxy.endpoint, "/v1/invocations/complete", lab.tokens["worker"], command)
                try:
                    assert proxy.arrived.wait(timeout=10)
                    original = proxy.receipts[0]
                    assert original["outcome"]["status"] == "accepted"
                    record.event("barrier", "atomic acceptance committed; client response and outbox delivery not observed")
                    pid = lab.runtime.child.pid
                    lab.runtime.kill()
                    record.event("kill", {"owner": "runtime", "pid": pid})
                finally:
                    proxy.release.set()
                pending.result(timeout=10)  # Deliberately discard buffered reply; recover by original command.
            lab.runtime.start()
            lab.runtime.ready(lab.tokens["admin"])
            record.event("restart", "same runtime state; delivery worker starts only after replay")
            assert lab.worker("/v1/invocations/complete", command) == original
            accepted(lab, record, run, command, original)
        finally:
            proxy.close()


def aborted(lab):
    with recording(lab, "REC-05") as record:
        run, command = lab.start()
        completion_record(lab, record, run, command)
        lab.proxy.arrived.clear()
        lab.proxy.release.clear()
        lab.proxy.hold_next = True
        offset = len(lab.proxy.receipts)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(lab.worker, "/v1/invocations/complete", command)
            try:
                assert lab.proxy.arrived.wait(timeout=10)
                binding = lab.proxy.receipts[offset]["outcome"]["binding"]
                record.identify(intent=binding["intent"]["intent_id"], reservation=binding["reservation_id"])
                record.event("barrier", "reserved binding response withheld from stale completion")
                assert lab.rt("/v1/runs/cancel", lab.command("runtime.cancel", {"run_id": run, "reason_code": "recovery"}))["outcome"]["status"] == "accepted"
                released = lab.art("/v1/reservations/reconcile", lab.command("artifacts.reconcile",
                    {"reservation_id": binding["reservation_id"]}, "runtime"), "runtime")
                assert released["outcome"]["status"] == "released"
            finally:
                lab.proxy.release.set()
            rejected = pending.result(timeout=15)
        assert rejected["outcome"]["status"] == "rejected"
        assert lab.worker("/v1/invocations/complete", command) == rejected
        lab.deliver()
        for receipt in lab.proxy.receipts[offset:]:
            reservation_id = receipt["outcome"]["binding"]["reservation_id"]
            assert lab.art("/v1/reservations/" + reservation_id, actor="runtime")["outcome"]["status"] == "released"
        snapshot = lab.rt("/v1/runs/" + run)
        assert snapshot["status"] == "cancelled" and snapshot["budget"]["spent"] == 1 and snapshot["budget"]["reserved"] == 0
        record.event("observation", "exact abort proof releases before stale response; no acceptance; terminal replay and budget stable")


def exercise(lab):
    publication(lab)
    reservation(lab)
    committed(lab)
    aborted(lab)
    worker_spec = importlib.util.spec_from_file_location("recovery_workers", Path(__file__).with_name("recovery_workers.py"))
    workers = importlib.util.module_from_spec(worker_spec)
    worker_spec.loader.exec_module(workers)
    workers.exercise(lab, recording, dropped)
