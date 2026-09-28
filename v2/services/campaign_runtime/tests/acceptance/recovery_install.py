"""Fresh wheel-only replacement processes preserve accepted state and public contracts."""

import json
import os
import subprocess
from pathlib import Path


def verify_install(python, module, peer):
    probe = (f"import {module} as owner; import importlib.util; import sys; from pathlib import Path; "
             "assert Path(owner.__file__).is_relative_to(Path(sys.prefix)); "
             f"assert importlib.util.find_spec('{peer}') is None; "
             "assert importlib.util.find_spec('torch') is None; assert importlib.util.find_spec('rdkit') is None")
    result = subprocess.run([python, "-I", "-c", probe], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, "Replacement is not isolated wheel-only installation"


def exercise(lab, recording):
    with recording(lab, "REC-09") as record:
        replacements = {"RUNTIME": os.environ["AMPHORA_REPLACEMENT_RUNTIME_PYTHON"],
                        "ARTIFACT": os.environ["AMPHORA_REPLACEMENT_ARTIFACT_PYTHON"]}
        assert Path(replacements["RUNTIME"]) != Path(lab.runtime.python)
        assert Path(replacements["ARTIFACT"]) != Path(lab.artifact.python)
        verify_install(replacements["RUNTIME"], "amphora_campaign_runtime", "amphora_data_artifacts")
        verify_install(replacements["ARTIFACT"], "amphora_data_artifacts", "amphora_campaign_runtime")
        run, command = lab.start()
        receipt = lab.worker("/v1/invocations/complete", command)
        assert receipt["outcome"]["status"] == "accepted"
        report_id = receipt["outcome"]["committed"]["object_id"]
        before = lab.rt(f"/v1/runs/{run}/completions/{report_id}")
        snapshot = lab.rt("/v1/runs/" + run)
        audit = lab.rt(f"/v1/runs/{run}/audit?limit=2")
        assert audit["next_cursor"] is not None
        continuation = f"/v1/runs/{run}/audit?limit=2&cursor=" + audit["next_cursor"]
        page = lab.rt(continuation)
        reservations = before["retention_reservation_ids"]
        assert len(reservations) == 2
        record.identify(run=run, command=command["identity"]["command_id"], intent=report_id,
                        attempt=command["payload"]["completion"]["attempt_id"], artifact=lab.output_ref["artifact_id"])
        for reservation in reservations:
            record.identify(reservation=reservation)
            assert lab.art("/v1/reservations/" + reservation, actor="runtime")["outcome"]["status"] == "reserved"
        record.event("barrier", "accepted result and pending retention exist before fresh install cutover")
        for owner, process in (("runtime", lab.runtime), ("artifact", lab.artifact)):
            record.event("kill", {"owner": owner, "pid": process.child.pid})
            process.kill()
        # Explicit owner migration bootstrap, isolated from ordinary service credentials/startup.
        for label, module in (("RUNTIME", "amphora_campaign_runtime"), ("ARTIFACT", "amphora_data_artifacts")):
            key = "AMPHORA_" + label + "_MIGRATION_URL"
            environment = dict(lab.support.isolated_env(), **{key: os.environ[key]})
            for _ in range(2):
                result = subprocess.run([replacements[label], "-I", "-m", module + ".persistence.migrate"],
                    env=environment, capture_output=True, text=True, timeout=15)
                assert result.returncode == 0, "Explicit replacement owner migration failed"
        lab.artifact.python = replacements["ARTIFACT"]
        lab.runtime.python = replacements["RUNTIME"]
        lab.artifact.start()
        lab.artifact.ready(lab.tokens["worker"])
        lab.runtime.start()
        lab.runtime.ready(lab.tokens["admin"])
        record.event("restart", "two fresh independently installed wheel environments; same database/storage/config; owner migrations idempotently reapplied")
        assert lab.worker("/v1/invocations/complete", command) == receipt
        assert lab.rt("/v1/runs/" + run) == snapshot
        assert lab.rt(f"/v1/runs/{run}/completions/{report_id}") == before
        assert lab.rt(continuation) == page
        assert lab.rt("/v1/commands/runtime.complete/" + command["identity"]["command_id"] + "?actor_id=worker") == receipt
        assert lab.support.request(lab.artifact.endpoint, "/v1/artifacts/" + lab.output_ref["artifact_id"] + "/content",
                                   lab.tokens["worker"]) == (200, json.dumps({"value": 2}).encode())
        for reservation in reservations:
            assert lab.art("/v1/reservations/" + reservation, actor="runtime")["outcome"]["status"] == "reserved"
        assert lab.deliver()["acknowledged"] >= 2
        for reservation in reservations:
            assert lab.art("/v1/reservations/" + reservation, actor="runtime")["outcome"]["status"] == "confirmed"
        assert lab.rt("/v1/runs/" + run) == snapshot
        record.event("observation", "exact historical receipt/report/cursor/state and accepted bytes preserved; replacement delivery confirms once; no reset or source imports")
