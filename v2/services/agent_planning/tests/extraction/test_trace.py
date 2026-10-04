import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot, TraceProjection
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.capture import CapturedOutput, Observation, unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_core import Scope
from amphora_contracts_planning import ExtractionTrace


class Response:
    def __init__(self, raw):
        self.raw = raw

    def supports(self, model):
        return True

    def reply(self, binding):
        return ProviderReply((self.raw,), unknown_usage())


def facts(ordinal=1, draft_change=None):
    fixture = json.loads((Path(__file__).parent / "fixtures/extraction.json").read_bytes())
    raw = fixture["request"]
    request = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id="fixture",
                                        scope=Scope.model_validate(raw["reference"]["scope"]))
    fixture["task"]["request_sha256"] = request.sha256
    task = ExtractionSnapshot.from_bytes(json.dumps(fixture["task"]).encode(), request)
    if draft_change:
        draft_change(fixture["draft"])
    binding = AttemptBinding(request, ordinal)
    return task, binding, observe(binding, Response(json.dumps(fixture["draft"]).encode()))


def test_provenance_is_derived_and_source_claim_is_not_truth():
    task, binding, observed = facts()
    projection = TraceProjection.derive("trace1", task, observed)
    trace = projection.document()
    assert trace.authority == "interpretation_only" and trace.validation == "profile_only"
    assert trace.task_sha256 == task.sha256 and trace.attempt == binding.reference()
    assert trace.sources == task.document().sources and trace.target == task.document().target
    assert trace.prompt == task.request.document().context.prompt
    assert trace.model == task.request.document().context.model
    assert trace.outcome.observation_sha256 == hashlib.sha256(observed.canonical).hexdigest()
    assert trace.outcome.candidate_sha256 == observed.document().proposal.payload_sha256
    assert trace.fields[0].origin == "model_claimed_source"
    assert all(step.kind == "deterministic" for step in trace.transforms)
    assert TraceProjection.derive("trace1", task, observed) == projection
    assert projection.reference().sha256 == projection.sha256


def test_inferred_high_confidence_and_missing_context_remain_explicit():
    def change(draft):
        draft["entities"][0]["attribution"].update(origin="inferred", confidence="high")
        draft["assertions"] = [{"local_id": "claim", "subject": "a", "predicate": "correlates_with",
                                 "object": "b", "statement": "Synthetic correlation", "polarity": "affirmed",
                                 "posture": "unresolved", "applicability": None,
                                 "attribution": draft["entities"][0]["attribution"]}]
        draft["diagnostics"] = [{"code": "missing_species", "target_path": "/species",
                                 "kind": "missing", "description": "Species was not provided."}] * 2
    task, _, observed = facts(draft_change=change)
    trace = TraceProjection.derive("trace", task, observed).document()
    assert trace.fields[0].origin == "model_inferred" and trace.fields[0].confidence == "high"
    missing = [field for field in trace.fields if field.origin == "missing"]
    assert any(field.target_path == "/assertions/0/applicability" for field in missing)
    assert len([field for field in missing if field.target_path == "/species"]) == 1
    assert all(field.confidence == "unknown" and not field.spans for field in missing)
    assert len(trace.diagnostics) == 2  # Preserve the actual model report, even duplicates.


@pytest.mark.parametrize("status", ["invalid", "unavailable", "unknown", "policy_rejected"])
def test_failed_attempts_keep_exact_capture_and_no_fabricated_candidates(status):
    task, binding, _ = facts()
    observed = Observation.record(binding, CapturedOutput(b"partial", False), status, "fixture", unknown_usage())
    trace = TraceProjection.derive("failed", task, observed).document()
    assert trace.outcome.status == status and trace.outcome.candidate_sha256 is None
    assert trace.outcome.captured_bytes == 7 and not trace.outcome.capture_complete
    assert not trace.fields and not trace.diagnostics


def test_failed_and_repaired_attempts_remain_separate_and_linked():
    task, binding, _ = facts()
    failed = observe(binding, Response(b"{"))
    first = TraceProjection.derive("failed", task, failed)
    _, _, repaired = facts(2)
    second = TraceProjection.derive("repaired", task, repaired, first)
    assert first.document().outcome.status == "invalid"
    assert second.document().outcome.status == "proposed"
    assert second.document().prior == first.reference() and second.document().repair_depth == 1
    assert first.document().repair_depth == 0 and first.document().prior is None
    with pytest.raises(ValueError, match="extraction_repair_identity"):
        TraceProjection.derive("failed", task, repaired, first)
    with pytest.raises(ValueError, match="extraction_repair_identity"):
        TraceProjection.derive("other", task, failed, first)


def test_pending_corrupt_capture_and_wrong_attempt_cannot_become_traces():
    task, _, observed = facts()
    with pytest.raises(ValueError, match="extraction_attempt_pending"):
        TraceProjection.derive("trace", task, None)
    with pytest.raises(ValueError, match="capture_digest_mismatch"):
        TraceProjection.derive("trace", task, replace(observed, capture=CapturedOutput(b"forged", True)))
    wire = observed.document().model_dump(mode="json")
    wire["attempt"]["request_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="attempt_binding_mismatch"):
        TraceProjection.derive("trace", task, replace(observed, canonical=json.dumps(wire).encode()))


@pytest.mark.parametrize("change,code", [("depth", "extraction_repair_depth"), ("source", "extraction_repair_binding"),
                                       ("target", "extraction_repair_binding")])
def test_parent_binding_and_depth_guards(change, code):
    task, _, observed = facts()
    parent = TraceProjection.derive("parent", task, observed)
    raw = parent.document().model_dump(mode="json")
    if change == "depth":
        raw["repair_depth"] = 16
    elif change == "source":
        raw["sources"][0]["source"]["revision_id"] = "changed"
    else:
        raw["target"]["graph"]["graph_id"] = "changed"
    parent = TraceProjection(ExtractionTrace.model_validate_json(json.dumps(raw)).model_dump_json().encode())
    _, _, second = facts(2)
    with pytest.raises(ValueError, match=code):
        TraceProjection.derive("next", task, second, parent)


def test_trace_contract_rejects_claimed_acceptance_and_foreign_fields():
    task, _, observed = facts()
    raw = TraceProjection.derive("trace", task, observed).document().model_dump(mode="json")
    for key, value in (("authority", "scientific_acceptance"), ("validation", "verified_truth"),
                       ("repair_depth", 17), ("accepted", True)):
        with pytest.raises(ValueError):
            ExtractionTrace.model_validate_json(json.dumps({**raw, key: value}))
