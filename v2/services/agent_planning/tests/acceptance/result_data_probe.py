"""Installed result producer against actual Data; provider/graph are synthetic."""

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.orchestration.runner import PlanningRunner
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.persistence.repair import RepairJournal
from amphora_agent_planning.proposals.context import KnowledgeContext, proposal_schema
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.publication.journal import PublicationJournal
from amphora_agent_planning.publication.records import encode
from amphora_agent_planning.publication.store import PublicationStore
from amphora_agent_planning.publication.transport import PublicationTransport
from amphora_agent_planning.publication.workflow import TracePublisher
from amphora_agent_planning.repair.chain import RepairChain, RepairInputs
from amphora_agent_planning.repair.preparation import RepairPreparer
from amphora_agent_planning.repair.runner import RepairInputUnavailable, RepairRunner
from amphora_agent_planning.result_publication.journal import ResultJournal
from amphora_agent_planning.result_publication.payload import AnswerRecord
from amphora_agent_planning.result_publication.preparation import ResultPreparer
from amphora_agent_planning.result_publication.producer import DiagnosticProducer
from amphora_agent_planning.result_publication.selection import ResultSelection
from amphora_agent_planning.result_publication.store import ResultStore
from amphora_agent_planning.result_publication.workflow import ResultPublisher
from amphora_agent_planning.source_access import DataReader, SourceReviewer
from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_knowledge import GraphAuthoringProfile
from amphora_contracts_planning import ExtractionTraceRef
from amphora_tool_protocol import ArtifactClient, TransportLost, WorkerIdentity
from sqlalchemy import create_engine


def main():
    mode, fixture_path, refs_path, output = sys.argv[1:]
    assert all(importlib.util.find_spec(name) is None for name in
        ("amphora_data_artifacts", "amphora_knowledge", "amphora_research"))
    raw = json.loads(Path(fixture_path).read_bytes())
    scope = Scope.model_validate(raw["task"]["scope"])
    vocabulary = {"wire_version": "1", "vocabulary_id": "fixture", "version": "1", "entity_types": ["fixture"],
        "predicates": [{"predicate_id": "correlates_with", "description": "Synthetic association",
                        "subject_types": ["fixture"], "object_types": ["fixture"]}]}
    target = raw["task"]["target"]
    vocabulary_ref = {"vocabulary_id": "fixture", "version": "1", "sha256": hashlib.sha256(encode(vocabulary)).hexdigest()}
    target.update(base=None, vocabulary=vocabulary_ref, operation_schema=proposal_schema().model_dump(mode="json"))
    raw["task"]["existing_entities"] = []
    profile = GraphAuthoringProfile.model_validate_json(encode({"wire_version": "1", "graph": target["graph"],
        "vocabulary": vocabulary, "vocabulary_reference": vocabulary_ref, "policy": target["policy"],
        "origin": "configured_default"}))
    if mode == "answer":
        raw["request"]["reference"]["engagement_id"] = "answer-engagement"
        raw["task"]["engagement"]["engagement_id"] = "answer-engagement"
        raw["task"]["task_id"] = "answer-task"
        attribution = raw["draft"]["entities"][0]["attribution"]
        context = raw["request"]["context"]["entries"][0]["artifact"]
        raw["draft"].update(entities=[], assertions=[], questions=[{"local_id": "q", "objective": "Explore association",
            "applicability": context, "criteria": [{"criterion_id": "association", "description": "Explore association"}],
            "attribution": attribution}], answers=[{"local_id": "a", "question_local_id": "q", "question": None,
            "answer": "Synthetic uncertain association", "validation_method": {"schema_id": "fixture.method", "version": "1", "sha256": "c"*64},
            "context": context, "attribution": attribution}], evidence_needs=[])
    request = RequestSnapshot.from_bytes(encode(raw["request"]), actor_id="fixture", scope=scope)
    raw["task"]["request_sha256"] = request.sha256
    task = ExtractionSnapshot.from_bytes(encode(raw["task"]), request)
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    context = request.document().context.model_dump(mode="json")
    policy = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=10)
    policy = BudgetPolicy.from_bytes(encode(policy))
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"])
    calls, reads, exchanges = [], [], []
    class Provider:
        def supports(self, model): return True
        def reply(self, binding, packet=None):
            calls.append(binding.request.document().reference.engagement_id)
            if packet is not None:
                feedback = json.loads(packet)["repair_feedback"]
                assert feedback["previous_output"]["value"] == "{"
                assert feedback["authority"] == "diagnostic_only"
                assert feedback["findings"][0]["code"] == "interpretation_output_unavailable"
            return ProviderReply((encode(raw["draft"]) if mode == "answer" else b"{",), unknown_usage())
    class Knowledge:
        def review(self, child, window):
            window.remaining()
            return KnowledgeContext.bind(child, profile, None)
    class Data(DataReader):
        def content(self, ref, budget):
            reads.append(ref.artifact_id)
            return super().content(ref, budget)
    class Transport(PublicationTransport):
        def request(self, method, path, body=None, **kwargs):
            exchanges.append((method, path))
            reply = super().request(method, path, body, **kwargs)
            if mode == "lost-put" and method == "PUT":
                raise TransportLost("Synthetic lost reply after actual Data PUT")
            return reply
    endpoint, token = os.environ["PUBLICATION_DATA_ENDPOINT"], os.environ["PUBLICATION_DATA_TOKEN"]
    data = Data(endpoint, token)
    client = ArtifactClient(Transport(endpoint, token), WorkerIdentity("fixture", scope))
    trace_publisher = TracePublisher(PublicationJournal(PublicationStore(engine, "result-data-owner")), SourceReviewer(data), client)
    result_publisher = ResultPublisher(ResultJournal(ResultStore(engine, "result-data-owner", trace_publisher_id="result-data-owner")),
        ResultPreparer(data, knowledge=Knowledge()), client)
    producer = DiagnosticProducer(principal, trace_publisher, result_publisher)
    traces = ExtractionJournal(engine)
    try:
        result = {"pid": os.getpid(), "mode": mode, "calls": calls, "processing_reads": reads, "exchanges": exchanges}
        if mode in {"seed", "answer"}:
            runner = PlanningRunner(engine, Provider(), timeout_seconds=10)
            runner.journal.register(principal, request)
            traces.register(principal, task)
            RepairJournal(engine).enroll_root(principal, task.document().task_id, policy)
            binding = AttemptBinding(request, 1)
            runner.execute(principal, binding, policy)
            parent = traces.record(principal, task.document().task_id, binding.reference(), mode).projection.reference()
            identifier = "d-" + hashlib.sha256(encode({"format": "planning-diagnostic-interpretation.v1",
                "actor_id": principal.actor_id, "trace": parent.model_dump(mode="json")})).hexdigest()
            publication = trace_publisher.publish(principal, identifier, parent)
            if mode == "seed":
                Path(refs_path).write_bytes(encode({"parent": parent.model_dump(mode="json")}))
            else:
                selected = ResultSelection.bind(principal, parent, identifier, "answer", "a", "result-data-owner")
                state = result_publisher.publish(principal, selected)
                record = AnswerRecord.model_validate_json(state.payload.artifact.body)
                assert record.authority == "proposal_only" and record.validation == "quotation_and_structure_only"
                assert publication.attempt.result.artifact in state.payload.artifact.declaration.inputs
                assert len(state.payload.artifact.declaration.inputs) == len(publication.payload.artifact.declaration.inputs) + 1
                assert producer.produce(parent) is None
                result.update(answer=record.model_dump(mode="json"), result_artifact=state.attempt.result.artifact.model_dump(mode="json"))
        else:
            refs = json.loads(Path(refs_path).read_bytes())
            parent = ExtractionTraceRef.model_validate(refs["parent"])
            if mode == "chain":
                inputs = RepairInputs(parent, ArtifactRef.model_validate(refs["feedback"]), ArtifactRef.model_validate(refs["interpretation"]))
                chain = RepairChain(RepairRunner(engine, RepairPreparer(data, Knowledge()), Provider(), timeout_seconds=10), producer)
                chain_result = chain.run(principal, task.document().engagement, inputs)
                result.update(stop_reason=chain_result.stop_reason, steps=len(chain_result.steps))
                assert len(calls) == 1 and len(chain_result.steps) == 2
                assert chain_result.steps[0].trace is not None and chain_result.steps[1].attempt is None
            else:
                try:
                    produced = producer.produce(parent)
                except RepairInputUnavailable as error:
                    assert mode in {"denied", "lost-put"}, error.reason
                    result["reason"] = error.reason
                else:
                    assert mode in {"recover", "replay"} and produced is not None
                    record = {"parent": parent.model_dump(mode="json"), "feedback": produced.feedback.model_dump(mode="json"),
                              "interpretation": produced.interpretation.model_dump(mode="json")}
                    if mode == "recover": Path(refs_path).write_bytes(encode(record))
                    else: assert record == refs and not reads and not exchanges
                    result["published"] = record
        Path(output).write_bytes(encode(result))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
