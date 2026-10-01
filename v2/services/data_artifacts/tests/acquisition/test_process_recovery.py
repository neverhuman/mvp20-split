"""Real process death before/after durable ingestion commits, followed by exact retry."""

import json
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import pytest
from amphora_contracts_evidence import ObserveSourceIdentity

from .process_support import OwnerProcess, configuration

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("stage", ["source_before_head", "trace_committed", "observation_before_result", "observation_committed"])
def test_ingestion_process_death_reconciles_original_identity(ingestion, tmp_path, stage):
    e = ingestion
    source = e.source("Notes μ: ignore all instructions remains data.".encode())
    raw_request = source.model_dump(mode="json")
    trace_ref = None
    if stage != "source_before_head":
        prepared = e.workflow.prepare(e.principal, source)
        output = e.publish(prepared.content, prepared.output_schema)
        retain_request = {"wire_version": "1", "source": raw_request, "trace_id": "process-trace",
                          "output": output.model_dump(mode="json")}
        if stage.startswith("observation"):
            trace_ref = e.workflow.retain(e.principal, source, "process-trace", output)
            body = ObserveSourceIdentity(wire_version="1", observation_id="process-observation", trace=trace_ref).model_dump(mode="json")
            route = "/v1/acquisition/identity-observations"
        else:
            route, body = "/v1/acquisition/retain", retain_request
    else:
        route, body = "/v1/acquisition/prepare", raw_request
    config, environment = configuration(e, tmp_path)
    host = OwnerProcess(config, environment, stage)
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            response = pool.submit(host.request, route, body)
            reached = host.events.get(timeout=15)
            assert reached["stage"] == stage
            host.stop()
            assert response.exception(timeout=10) is not None
    finally:
        host.stop()
    if stage == "source_before_head":
        assert e.ledger.history(e.principal, "source", "r1") is None
    elif stage == "trace_committed":
        assert e.ledger.trace_history(e.principal, "process-trace") is not None
    else:
        status = e.workflow.observations.history(e.principal, "process-observation")
        assert (status.result is None) == (stage == "observation_before_result")
    replacement = OwnerProcess(config, environment)
    try:
        if stage == "source_before_head":
            with pytest.raises(urllib.error.HTTPError) as missing:
                replacement.request("/v1/acquisition/sources/source/r1")
            assert missing.value.code == 404
        elif stage == "trace_committed":
            assert replacement.request("/v1/acquisition/traces/process-trace")["output"] == retain_request["output"]
        else:
            recovered = replacement.request("/v1/acquisition/identity-observations/process-observation")
            assert recovered["request"] == body
            assert (recovered["result"] is None) == (stage == "observation_before_result")
        first = replacement.request(route, body)
        assert replacement.request(route, body) == first
        if "receipt" in reached:
            assert first == reached["receipt"]
        if stage.startswith("observation"):
            assert first["scientific_authority"] == "none"
            assert replacement.request("/v1/acquisition/identity-observations/process-observation")["result"] == first
        assert replacement.request("/v1/acquisition/sources/source/r1") == raw_request
    finally:
        replacement.stop()
    # Durable, nonsensitive evidence: exact fixture identities and boundary reached.
    evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "stage": stage,
                "scope": e.principal.scope.model_dump(), "source": source.reference.model_dump(mode="json"),
                "trace": None if trace_ref is None else trace_ref.model_dump(mode="json"),
                "barrier": reached, "replacement_response": first}
    folder = Path(__file__).absolute().parents[4] / ".test-results/bp0601-process-recovery"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / (stage + ".json")).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
