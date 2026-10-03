"""Actual Research publication process death and fresh-owner recovery through public peers."""
import os
import sys
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from amphora_contracts_core import Scope
from amphora_research.publication.store import PublicationStore

STAGES = ("prepared", "begin_returned", "stream_started", "stream_returned", "stream_verified",
          "finalizing", "data_finalized", "terminal_before_commit", "terminal_committed")


def prove(owner_factory, research, config, environment, data, request, engine):
    observations = []
    store = PublicationStore(engine)
    scope = request["profile"]["scope"]
    scope_model = Scope.model_validate(scope)
    for stage in STAGES:
        selected = request | {"assessment_id":"kill-" + stage}
        assessed = research.request("/v1/assessments", selected)
        assert assessed["outcome"]["status"] == "assessed"
        query = {"wire_version":"1", "scope":scope, "assessment_id":selected["assessment_id"]}
        dying = owner_factory("amphora_research",config,environment,"r"*32,barrier=stage)
        replacement = None
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                call = pool.submit(dying.request,"/v1/assessment-publications",query)
                assert dying.events.get(timeout=30) == {"barrier":stage}
                dying.stop()
                assert call.exception(timeout=15) is not None
            before = store.lookup(scope_model,selected["assessment_id"],"reader")
            expected = {"prepared":"prepared", "begin_returned":"prepared", "stream_started":"streaming",
                        "stream_returned":"streaming", "stream_verified":"streamed", "finalizing":"finalizing",
                        "data_finalized":"finalizing", "terminal_before_commit":"finalizing", "terminal_committed":"published"}[stage]
            assert before.stage == expected
            original_artifact = None
            if stage in {"data_finalized","terminal_before_commit","terminal_committed"}:
                receipt = data.request("/v1/commands/artifacts.finalize/" + before.command_id("artifacts.finalize"))
                assert receipt["outcome"]["status"] == "finalized"
                original_artifact = receipt["outcome"]["receipt"]["artifact"]
            replacement = owner_factory("amphora_research",config,environment,"r"*32,
                os.environ.get("AMPHORA_TEST_RESEARCH_REPLACEMENT_PYTHON",sys.executable))
            initial = replacement.request("/v1/assessment-publications/read",query)
            assert initial["outcome"]["status"] == ("published" if stage == "terminal_committed" else "pending")
            deadline = time.monotonic() + 30
            while True:
                result = replacement.request("/v1/assessment-publications",query)
                if result["outcome"]["status"] != "pending":
                    break
                assert time.monotonic() < deadline, "Publication lease failed to expire"
                time.sleep(0.1)
            assert result["outcome"]["status"] == "published"
            assert replacement.request("/v1/assessment-publications",query) == result
            after = store.lookup(scope_model,selected["assessment_id"],"reader")
            uncertain = stage in {"stream_started","stream_returned"}
            assert after.ordinal == (2 if uncertain else 1)
            for family in ("artifacts.begin_derived_upload","artifacts.finalize"):
                assert (after.command_id(family) != before.command_id(family)) is uncertain
            if uncertain:
                try:
                    data.request("/v1/commands/artifacts.finalize/" + before.command_id("artifacts.finalize"))
                except urllib.error.HTTPError as error:
                    assert error.code == 404
                else:
                    raise AssertionError("Abandoned ambiguous upload was finalized")
            if original_artifact is not None:
                assert result["outcome"]["derivation"]["artifact"] == original_artifact
            observations.append({"timestamp_local":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"barrier":stage,
                "query":query,"stage_after_kill":before.stage,"terminal_after_kill":initial["outcome"]["status"],
                "original_begin_id":before.command_id("artifacts.begin_derived_upload"),
                "original_finalize_id":before.command_id("artifacts.finalize"),"recovered_ordinal":after.ordinal,
                "abandoned_upload_not_finalized":uncertain,"result":result,
                "lease_profile":"fault host five-second DB-clock lease; replacement production sixty seconds"})
        finally:
            dying.stop()
            if replacement is not None:
                replacement.stop()
    return observations
