"""Actual Knowledge process death against an existing actual Data fixture."""

import json
import os
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo

from amphora_contracts_knowledge import ReasoningPublicationRequest
from amphora_knowledge.access import Principal
from amphora_knowledge.publication.journal import PublicationJournal
from amphora_knowledge.publication.store import PublicationStore

from .processes import Owner
from .publication_faults import STAGES


def prove(case, config, environment, data, publication_query, knowledge_python):
    observations = []
    for stage in STAGES:
        request = dict(publication_query, publication_id=stage)
        query = ReasoningPublicationRequest.model_validate_json(json.dumps(request))
        principal = Principal("author", query.graph.scope, frozenset({"publish_reasoning"}))
        journal = PublicationJournal(PublicationStore(case.engine))
        dying = Owner("amphora_knowledge", config, environment, "k" * 32, python=knowledge_python, barrier=stage)
        replacement = None
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                call = pool.submit(dying.request, "/v1/reasoning-publications", request)
                assert dying.events.get(timeout=30) == {"barrier": stage}
                dying.stop()
                assert call.exception(timeout=15) is not None
            before = journal.read(principal, query)
            expected_stage = {
                "reasoning_prepared": "prepared", "reasoning_begin_returned": "prepared",
                "reasoning_stream_started": "streaming", "reasoning_stream_returned": "streaming",
                "reasoning_stream_verified": "streamed", "reasoning_finalizing": "finalizing",
                "reasoning_data_finalized": "finalizing", "reasoning_terminal_before_commit": "finalizing",
                "reasoning_terminal_committed": "finalizing",
            }[stage]
            assert before.attempt.stage == expected_stage
            original_artifact = None
            if stage in {"reasoning_data_finalized", "reasoning_terminal_before_commit", "reasoning_terminal_committed"}:
                receipt = data.request(f"/v1/commands/artifacts.finalize/{before.attempt.identity.finalize_id}")
                assert receipt["outcome"]["status"] == "finalized"
                original_artifact = receipt["outcome"]["receipt"]["artifact"]
            replacement = Owner("amphora_knowledge", config, environment, "k" * 32,
                python=os.environ.get("AMPHORA_TEST_KNOWLEDGE_REPLACEMENT_PYTHON", knowledge_python))
            initial = replacement.request("/v1/reasoning-publications/read", request)
            assert initial["outcome"]["status"] == ("published" if stage == "reasoning_terminal_committed" else "pending")
            deadline = time.monotonic() + 30
            while True:
                result = replacement.request("/v1/reasoning-publications", request)
                if result["outcome"]["status"] != "pending":
                    break
                assert time.monotonic() < deadline, "database lease did not expire within recovery bound"
                time.sleep(0.1)
            assert result["outcome"]["status"] == "published"
            assert replacement.request("/v1/reasoning-publications", request) == result
            after = journal.read(principal, query)
            uncertain = stage in {"reasoning_stream_started", "reasoning_stream_returned"}
            assert after.attempt.identity.ordinal == (2 if uncertain else 1)
            if uncertain:
                assert after.attempt.identity.begin_id != before.attempt.identity.begin_id
                try:
                    data.request(f"/v1/commands/artifacts.finalize/{before.attempt.identity.finalize_id}")
                except urllib.error.HTTPError as error:
                    assert error.code == 404
                else:
                    raise AssertionError("abandoned upload was finalized")
            else:
                assert after.attempt.identity == before.attempt.identity
            if original_artifact is not None:
                assert result["outcome"]["derivation"]["artifact"] == original_artifact
            observations.append({"timestamp_local": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
                "barrier": stage, "request": request, "stage_after_kill": before.attempt.stage,
                "terminal_after_kill": initial["outcome"]["status"], "original_begin_id": before.attempt.identity.begin_id,
                "original_finalize_id": before.attempt.identity.finalize_id, "recovered_ordinal": after.attempt.identity.ordinal,
                "result": result, "abandoned_upload_not_finalized": uncertain,
                "lease_profile": "fault host five-second DB-clock expiry; replacement production sixty-second lease"})
        finally:
            dying.stop()
            if replacement is not None:
                replacement.stop()
    return observations
