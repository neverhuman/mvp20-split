"""Scripted public records; transport/actual-owner tiers are separate."""

import hashlib
import json
from types import SimpleNamespace

import pytest
from amphora_contracts_evidence import ConversionTrace, SourceRevision
from amphora_contracts_knowledge import GraphChangeProposal
from amphora_contracts_research import EvidenceNeed, ResearchQuestion
from amphora_knowledge.authoring.canonical import digest


class ScriptedPeers:
    def __init__(self, proposal, source, trace, question, need, content):
        self.proposal, self.source_record, self.trace_record = proposal, source, trace
        self.question_record, self.need_record, self.raw = question, need, content
        self.calls = []

    def artifact(self, ref, budget):
        self.calls.append("artifact")
        return self.source_record.reference.raw

    def content(self, ref, budget):
        self.calls.append("content")
        return self.raw

    def source(self, ref, budget):
        self.calls.append("source")
        return self.source_record

    def trace(self, ref, budget):
        self.calls.append("trace")
        return self.trace_record

    def question(self, ref, budget):
        self.calls.append("question")
        return self.question_record

    def need(self, ref, budget):
        self.calls.append("need")
        return self.need_record


def records(proposal):
    content = b"Synthetic claims are not scientifically accepted."
    raw = proposal.model_dump(mode="json")
    sha = hashlib.sha256(content).hexdigest()

    def patch(value):
        if isinstance(value, dict):
            if "artifact_id" in value:
                value.update(sha256=sha, size_bytes=len(content))
            if value.get("unit") == "byte":
                value.update(end=len(content), sha256=sha)
            for child in value.values():
                patch(child)
        elif isinstance(value, list):
            for child in value:
                patch(child)

    patch(raw)
    grounding = raw["grounding"]
    span = grounding["spans"][0]
    source_ref = span["source"]
    artifact = source_ref["raw"]
    scope = raw["graph"]["scope"]
    source = SourceRevision.model_validate_json(json.dumps({"wire_version": "1", "reference": source_ref,
        "delivery": {"issuer_id": "fixture", "delivery_id": "one"},
        "method": {"connector_id": "fixture", "connector_version": "1", "configuration_sha256": "a"*64,
                   "format": "utf8_document"},
        "rights": {"scope": scope, "rights_id": "fixture", "revision": 1},
        "supersedes": None, "completeness": "complete"}))
    trace = ConversionTrace.model_validate_json(json.dumps({"wire_version": "1", "scope": scope,
        "trace_id": "conversion", "source": source_ref, "source_schema": artifact["schema_ref"],
        "target_schema": artifact["schema_ref"], "converter_id": "fixture", "converter_version": "1",
        "configuration_sha256": "a"*64,
        "transforms": [{"transform_id": "copy", "version": "1", "configuration_sha256": "a"*64, "kind": "deterministic"}],
        "output": artifact, "fields": [{"target_path": "/text", "origin": "copied", "spans": [span], "step_indices": [0]}],
        "warnings": [], "disposition": "normalized"}))
    for item in [grounding, raw["operations"][2]["assertion"]["grounding"]]:
        item["conversion_traces"][0]["sha256"] = digest(trace)
    link = raw["operations"][2]["assertion"]["research_links"][0]
    question = ResearchQuestion.model_validate_json(json.dumps({"wire_version": "1", "reference": link["question"],
        "objective": "Synthetic question", "applicability": artifact,
        "criteria": [{"criterion_id": "declared", "description": "Declared criterion"}], "supersedes": None}))
    need = EvidenceNeed.model_validate_json(json.dumps({"wire_version": "1", "reference": link["need"],
        "question": link["question"], "criterion_ids": ["declared"], "method": artifact["schema_ref"],
        "required_context": artifact, "supersedes": None}))
    return ScriptedPeers(GraphChangeProposal.model_validate_json(json.dumps(raw)), source, trace, question, need, content)


@pytest.fixture
def peers(graph_fixture):
    return records(graph_fixture.proposal)


@pytest.fixture
def persisted_peers(stored_graph):
    peer = records(stored_graph.proposal)
    return SimpleNamespace(store=stored_graph, peers=peer)
