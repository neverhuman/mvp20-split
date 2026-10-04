"""Scripted public Data records; actual owner integration is a separate gate."""

import hashlib
import json
from importlib.resources import files
from pathlib import Path

import pytest
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.source_access import SourceReviewer
from amphora_agent_planning.source_access.review import canonical
from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_evidence import ConversionTrace, SourceRevision


class Data:
    def __init__(self, artifacts, payloads, source, trace):
        self.artifacts, self.payloads, self.revision, self.conversion = artifacts, payloads, source, trace
        self.calls = []

    def artifact(self, ref, budget):
        self.calls.append(("metadata", ref.artifact_id))
        return self.artifacts[ref.artifact_id]

    def content(self, ref, budget):
        self.calls.append(("processing-content", ref.artifact_id))
        return self.payloads[ref.artifact_id]

    def source(self, ref, budget):
        self.calls.append(("source", ref.source_id))
        return self.revision

    def trace(self, ref, budget):
        self.calls.append(("trace", ref.trace_id))
        return self.conversion


def inputs(*, trace_change=None, entries=0, scope=None):
    raw = json.loads((Path(__file__).parents[1] / "extraction/fixtures/extraction.json").read_bytes())
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {"tenant_id", "project_id"}:
                value.update(scope.model_dump())
            for item in value.values():
                rescope(item)
        elif isinstance(value, list):
            for item in value:
                rescope(item)
    if scope is not None:
        rescope(raw)
    context = raw["request"]["context"]
    payloads = {key: (key + " fixture").encode() for key in ("objective", "policy", "configuration")}
    payloads["prompt"] = files("amphora_agent_planning.extraction").joinpath("prompts/domain-decomposition-v1.txt").read_bytes()
    payloads["source-utf8"] = raw["source_text"].encode()
    payloads["converted"] = b"converted fixture"
    for index in range(entries):
        ref = dict(context["objective"], artifact_id=f"context-{index}")
        payloads[ref["artifact_id"]] = b"context fixture"
        context["entries"].append({"artifact": ref, "role": "constraint", "required": False})
    artifacts = {}
    refs = [context[key] for key in ("objective", "prompt", "policy")]
    refs += [context["model"]["configuration"], *(entry["artifact"] for entry in context["entries"])]
    for ref in refs:
        content = payloads[ref["artifact_id"]]
        ref.update(sha256=hashlib.sha256(content).hexdigest(), size_bytes=len(content))
        artifacts[ref["artifact_id"]] = ArtifactRef.model_validate_json(json.dumps(ref))
    source = raw["task"]["sources"][0]["source"]
    source["raw"] = context["entries"][0]["artifact"]
    output = dict(context["objective"], artifact_id="converted", size_bytes=len(payloads["converted"]),
                  sha256=hashlib.sha256(payloads["converted"]).hexdigest())
    artifacts["converted"] = ArtifactRef.model_validate_json(json.dumps(output))
    trace = {"wire_version": "1", "scope": raw["task"]["scope"], "trace_id": "conversion", "source": source,
             "source_schema": source["raw"]["schema_ref"], "target_schema": output["schema_ref"],
             "converter_id": "fixture", "converter_version": "1", "configuration_sha256": "a" * 64,
             "transforms": [{"transform_id": "copy", "version": "1", "configuration_sha256": "a" * 64,
                             "kind": "deterministic"}], "output": output,
             "fields": [{"target_path": "/text", "origin": "copied", "step_indices": [0],
                         "spans": [{"source": source, "unit": "byte", "start": 0,
                                    "end": source["raw"]["size_bytes"], "sha256": source["raw"]["sha256"]}]}],
             "warnings": [], "disposition": "normalized"}
    # Break shared fixture dictionaries so deliberately malformed peer cases do
    # not mutate the request oracle as a side effect.
    trace = json.loads(json.dumps(trace))
    if trace_change:
        trace_change(trace)
    trace = ConversionTrace.model_validate_json(json.dumps(trace))
    raw["task"]["sources"][0]["conversion_traces"] = [{"scope": raw["task"]["scope"],
        "trace_id": "conversion", "sha256": hashlib.sha256(canonical(trace)).hexdigest()}]
    request = RequestSnapshot.from_bytes(json.dumps(raw["request"]).encode(), actor_id="fixture",
                                         scope=Scope.model_validate(raw["task"]["scope"]))
    raw["task"]["request_sha256"] = request.sha256
    task = ExtractionSnapshot.from_bytes(json.dumps(raw["task"]).encode(), request)
    revision = SourceRevision.model_validate_json(json.dumps({"wire_version": "1", "reference": source,
        "delivery": {"issuer_id": "fixture", "delivery_id": "delivery"}, "method": {"connector_id": "fixture",
        "connector_version": "1", "configuration_sha256": "a" * 64, "format": "utf8_document"},
        "rights": {"scope": raw["task"]["scope"], "rights_id": "fixture", "revision": 1},
        "supersedes": None, "completeness": "partial"}))
    data = Data(artifacts, payloads, revision, trace)
    data.draft = raw["draft"]
    return task, data


def test_full_consumed_inputs_prompt_bytes_and_partial_source_are_preserved():
    task, data = inputs()
    reviewer = SourceReviewer(data)
    result = reviewer.review(task)
    assert [ref.artifact_id for ref in result.inputs()] == ["configuration", "converted", "objective", "policy",
                                                          "prompt", "source-utf8"]
    assert result.bundle.sources[0].content == data.payloads["source-utf8"]
    assert result.prompt.instructions == data.payloads["prompt"]
    assert SourceRevision.model_validate_json(result.source_documents[0]).completeness == "partial"
    assert ConversionTrace.model_validate_json(result.trace_documents[0]) == data.conversion
    assert len([call for call in data.calls if call[0] == "processing-content"]) == 6
    assert not any(key == "extra" for _, key in data.calls)  # Omitted input was not consumed.
    assert reviewer.review(task) == result
    assert len([call for call in data.calls if call[0] == "processing-content"]) == 12  # No rights cache.


@pytest.mark.parametrize("case,code", [("bytes", "source_artifact_bytes"), ("metadata", "source_artifact_binding"),
    ("revision", "source_revision_binding"), ("format", "source_input_format"), ("trace", "source_trace_binding")])
def test_forged_peer_identity_or_bytes_never_produce_a_review(case, code):
    task, data = inputs()
    if case == "bytes":
        data.payloads["objective"] = b"tampered"
    elif case == "metadata":
        data.artifacts["objective"] = data.artifacts["objective"].model_copy(update={"sha256": "f" * 64})
    elif case == "revision":
        data.revision = data.revision.model_copy(update={"reference": data.revision.reference.model_copy(
            update={"revision_id": "other"})})
    elif case == "format":
        data.revision = data.revision.model_copy(update={"method": data.revision.method.model_copy(
            update={"format": "synthetic_lab_json"})})
    else:
        data.conversion = data.conversion.model_copy(update={"converter_id": "other"})
    with pytest.raises(ValueError, match=code):
        SourceReviewer(data).review(task)


@pytest.mark.parametrize("path,value,code", [
    (("source_schema", "sha256"), "f" * 64, "source_trace_provenance"),
    (("fields", 0, "spans", 0, "source", "revision_id"), "other", "source_trace_span_source"),
    (("fields", 0, "spans", 0, "end"), 999, "source_trace_span_bounds"),
    (("fields", 0, "spans", 0, "sha256"), "f" * 64, "source_trace_span_digest"),
    (("output", "scope", "project_id"), "foreign", "source_artifact_scope"),
    (("output", "artifact_id"), "objective", "source_artifact_conflict"),
    (("output", "size_bytes"), 4194305, "source_artifact_size"),
])
def test_trace_cross_record_provenance_checks_even_when_digest_matches(path, value, code):
    def change(trace):
        target = trace
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
    task, data = inputs(trace_change=change)
    with pytest.raises(ValueError, match=code):
        SourceReviewer(data).review(task)


def test_input_bound_matches_public_derived_declaration_without_silent_omissions():
    task, data = inputs(entries=127)
    with pytest.raises(ValueError, match="source_input_count"):
        SourceReviewer(data).review(task)
    assert len([call for call in data.calls if call[0] == "metadata"]) == 128


def test_evidence_quality_is_not_a_global_scientific_gate():
    task, data = inputs(trace_change=lambda trace: trace.update(disposition="quarantined"))
    reviewed = SourceReviewer(data).review(task)
    assert ConversionTrace.model_validate_json(reviewed.trace_documents[0]).disposition == "quarantined"


def test_current_process_denial_propagates_without_using_prior_review(monkeypatch):
    task, data = inputs()
    reviewer = SourceReviewer(data)
    reviewer.review(task)
    def denied(*args):
        raise ValueError("source_access_denied")
    monkeypatch.setattr(data, "content", denied)
    with pytest.raises(ValueError, match="source_access_denied"):
        reviewer.review(task)
