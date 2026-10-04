"""Installed Planning repair worker: own SQL, actual Data, scripted graph profile."""

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
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.persistence.budget import BudgetLedger
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.persistence.preparation import PreparationJournal
from amphora_agent_planning.persistence.repair import RepairJournal
from amphora_agent_planning.proposals.context import KnowledgeContext, proposal_schema
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.publication.journal import PublicationJournal
from amphora_agent_planning.publication.store import PublicationStore
from amphora_agent_planning.publication.transport import PublicationTransport
from amphora_agent_planning.publication.workflow import TracePublisher
from amphora_agent_planning.repair.feedback import RepairFeedback
from amphora_agent_planning.repair.history import RepairHistory
from amphora_agent_planning.repair.preparation import RepairPreparer
from amphora_agent_planning.repair.runner import RepairInputUnavailable, RepairRunner
from amphora_agent_planning.source_access import DataReader, SourceReviewer
from amphora_contracts_artifacts import DerivationDeclaration, TransformationDescriptor
from amphora_contracts_core import ArtifactRef, Finding, Scope
from amphora_contracts_knowledge import GraphAuthoringProfile
from amphora_contracts_planning import ExtractionTraceRef
from amphora_tool_protocol import ArtifactClient, WorkerIdentity
from sqlalchemy import create_engine


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main():
    mode, fixture_path, refs_path, output = sys.argv[1:]
    assert all(importlib.util.find_spec(name) is None for name in
               ("amphora_data_artifacts", "amphora_knowledge", "amphora_research"))
    raw = json.loads(Path(fixture_path).read_bytes())
    scope = Scope.model_validate(raw["task"]["scope"])
    vocabulary = {"wire_version": "1", "vocabulary_id": "fixture", "version": "1", "entity_types": ["fixture"],
        "predicates": [{"predicate_id": "correlates_with", "description": "Synthetic association",
                        "subject_types": ["fixture"], "object_types": ["fixture"]}]}
    vocabulary_ref = {"vocabulary_id": "fixture", "version": "1", "sha256": hashlib.sha256(encoded(vocabulary)).hexdigest()}
    target = raw["task"]["target"]
    target.update(base=None, vocabulary=vocabulary_ref, operation_schema=proposal_schema().model_dump(mode="json"))
    raw["task"]["existing_entities"] = []
    profile = GraphAuthoringProfile.model_validate_json(encoded({"wire_version": "1", "graph": target["graph"],
        "vocabulary": vocabulary, "vocabulary_reference": vocabulary_ref, "policy": target["policy"],
        "origin": "configured_default"}))
    request = RequestSnapshot.from_bytes(encoded(raw["request"]), actor_id="fixture", scope=scope)
    raw["task"]["request_sha256"] = request.sha256
    task = ExtractionSnapshot.from_bytes(encoded(raw["task"]), request)
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    context = request.document().context.model_dump(mode="json")
    policy = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
    policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=10)
    policy = BudgetPolicy.from_bytes(encoded(policy))
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"])
    calls, reads = [], []
    class Provider:
        def supports(self, model): return True
        def reply(self, binding, packet=None):
            calls.append(binding.request.document().reference.engagement_id)
            if packet is not None:
                payload = json.loads(packet)
                assert payload["repair_feedback"]["previous_output"]["value"] == "{"
                assert payload["repair_feedback"]["authority"] == "diagnostic_only"
            return ProviderReply((b"{",), unknown_usage())
    class Knowledge:
        def review(self, child, window):
            window.remaining()
            return KnowledgeContext.bind(child, profile, None)
    class Data(DataReader):
        def content(self, ref, budget):
            reads.append(ref.artifact_id)
            body = super().content(ref, budget)
            return body + b"tamper" if mode == "wrong-bytes" else body
    data = Data(os.environ["PUBLICATION_DATA_ENDPOINT"], os.environ["PUBLICATION_DATA_TOKEN"])
    traces, families = ExtractionJournal(engine), RepairJournal(engine)
    try:
        result = {"pid": os.getpid(), "mode": mode, "calls": calls, "processing_reads": reads}
        if mode == "publish":
            runner = PlanningRunner(engine, Provider(), timeout_seconds=10)
            runner.journal.register(principal, request)
            traces.register(principal, task)
            families.enroll_root(principal, task.document().task_id, policy)
            binding = AttemptBinding(request, 1)
            attempt = runner.execute(principal, binding, policy)
            parent = traces.record(principal, task.document().task_id, binding.reference(), "parent").projection
            client = ArtifactClient(PublicationTransport(os.environ["PUBLICATION_DATA_ENDPOINT"], os.environ["PUBLICATION_DATA_TOKEN"]), WorkerIdentity("fixture", scope))
            state = TracePublisher(PublicationJournal(PublicationStore(engine, "repair-data-owner")),
                                   SourceReviewer(data), client).publish(principal, "parent", parent.reference())
            assert state.attempt.stage == "finalized"
            interpretation = state.attempt.result.artifact
            feedback = RepairFeedback.create(task, parent, attempt.observation,
                (Finding(code="invalid_output", location="/", message="Repair syntax and preserve context"),))
            # Synthetic fixture producer using public derived upload, not a production publisher.
            declaration = DerivationDeclaration(transformation=TransformationDescriptor(
                transformation_id="fixture.repair_diagnostics", version="1", sha256=feedback.sha256),
                inputs=(interpretation,))
            upload = client.begin_derived(feedback.publication_descriptor(), declaration, "feedback-upload")
            client.stream(upload.upload, feedback.canonical)
            receipt = client.finalize(upload.upload, "feedback-finalize")
            refs = {"parent": parent.reference().model_dump(mode="json"),
                    "feedback": receipt.artifact.model_dump(mode="json"), "interpretation": interpretation.model_dump(mode="json")}
            Path(refs_path).write_bytes(encoded(refs))
            result["published"] = refs
        else:
            refs = json.loads(Path(refs_path).read_bytes())
            parent = ExtractionTraceRef.model_validate_json(encoded(refs["parent"]))
            feedback = ArtifactRef.model_validate_json(encoded(refs["feedback"]))
            interpretation = ArtifactRef.model_validate_json(encoded(refs["interpretation"]))
            if mode == "missing":
                feedback = feedback.model_copy(update={"artifact_id": "absent-feedback"})
            history = RepairHistory.read(engine, principal, task.document().engagement, parent)
            preparer = RepairPreparer(data, Knowledge())
            if mode == "prepare":
                prepared = preparer.prepare(history, feedback, interpretation)
                child = prepared.plan.task
                from amphora_agent_planning.persistence.journal import PlanningJournal
                PlanningJournal(engine).register(principal, child.request)
                traces.register(principal, child)
                families.enroll_child(principal, task.document().engagement, child.document().task_id, parent)
                stored = PreparationJournal(engine).register(principal, prepared)
                BudgetLedger(engine).reserve(principal, AttemptBinding(child.request, 1), policy)
                result.update(manifest=stored.manifest.sha256, registered_at=stored.registered_at.isoformat())
            else:
                try:
                    step = RepairRunner(engine, preparer, Provider(), timeout_seconds=10).execute(
                        principal, task.document().engagement, parent, feedback, interpretation)
                except RepairInputUnavailable as exc:
                    assert mode in {"denied", "missing", "wrong-bytes"}
                    result["reason"] = exc.reason
                else:
                    assert mode in {"run", "replay"} and step.trace is not None
                    stored = PreparationJournal(engine).read(principal, step.attempt.binding.reference().engagement)
                    result.update(trace=step.trace.sha256, manifest=stored.manifest.sha256, registered_at=stored.registered_at.isoformat())
        Path(output).write_bytes(encoded(result))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
