"""Installed Planning worker; real owner HTTP, deterministic synthetic provider."""

import copy
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
from amphora_agent_planning.knowledge_access.reader import KnowledgeReader
from amphora_agent_planning.knowledge_access.transport import (
    KnowledgeReadWindow,
    KnowledgeTransport,
)
from amphora_agent_planning.orchestration.runner import PlanningRunner
from amphora_agent_planning.owner_handoff.coordinator import HandoffCoordinator
from amphora_agent_planning.owner_handoff.journal import HandoffJournal, HandoffState
from amphora_agent_planning.owner_handoff.preparation import HandoffPreparer
from amphora_agent_planning.owner_handoff.store import HandoffStore
from amphora_agent_planning.owner_handoff.transport import (
    OwnerTransport,
    OwnerUnavailable,
)
from amphora_agent_planning.owner_handoff.workflow import OwnerHandoff
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.proposals.context import proposal_schema
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.publication.journal import PublicationJournal
from amphora_agent_planning.publication.records import encode
from amphora_agent_planning.publication.store import PublicationStore
from amphora_agent_planning.publication.transport import PublicationTransport
from amphora_agent_planning.publication.workflow import TracePublisher
from amphora_agent_planning.research_access.reader import QuestionReader
from amphora_agent_planning.research_access.transport import ResearchTransport
from amphora_agent_planning.result_publication.journal import ResultJournal
from amphora_agent_planning.result_publication.preparation import ResultPreparer
from amphora_agent_planning.result_publication.producer import DiagnosticProducer
from amphora_agent_planning.result_publication.store import ResultStore
from amphora_agent_planning.result_publication.workflow import ResultPublisher
from amphora_agent_planning.source_access import DataReader, SourceReviewer
from amphora_contracts_core import Scope
from amphora_contracts_knowledge import DomainGraphRef
from amphora_contracts_planning import ExtractionTraceRef
from amphora_tool_protocol import ArtifactClient, WorkerIdentity
from sqlalchemy import create_engine


def run(stage, fixture_path, origin_path, output_path=None):
    assert all(importlib.util.find_spec(name) is None for name in
        ("amphora_data_artifacts", "amphora_knowledge", "amphora_research"))
    raw = json.loads(fixture_path.read_bytes())
    scope = Scope.model_validate(raw["task"]["scope"])
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    engine = create_engine(os.environ["COMBINED_PLANNING_DB"], connect_args={"options": "-c statement_timeout=5000"})
    calls, reads, owner_calls = [], [], []
    leases = {}

    class ObservedStore(HandoffStore):
        def acquire(self, principal, effect_id, seconds=30):
            lease = super().acquire(principal, effect_id, seconds=seconds)
            leases[effect_id] = lease
            return lease

    def crash(request, response=None):
        # No finally/release runs. The driver waits for the real120s lease,
        # retaining both the Planning dispatch and the independently read owner.
        state = owners["knowledge"].journal.read(principal, request.selection.effect_id)
        lease = leases[request.selection.effect_id]
        assert state.progress.state == "dispatching" and output_path is not None
        output_path.write_bytes(encode({"pid": os.getpid(), "stage": stage, "request": request.document().model_dump(mode="json"),
            "payload_sha256": state.payload.sha256, "prepared_at": state.prepared_at.isoformat(), "position": state.position,
            "state": state.progress.state, "lease_expires": lease.expires_at.isoformat(), "fence": lease.fence,
            "remote_response": None if response is None else response.model_dump(mode="json"),
            "provider_calls": calls, "processing_reads": reads, "owner_calls": owner_calls}))
        os._exit(71 if stage == "die-before" else 72)

    class Provider:
        def __init__(self, name, body):
            self.name, self.body = name, body

        def supports(self, model):
            return True

        def reply(self, binding, packet=None):
            calls.append(self.name)
            return ProviderReply((self.body,), unknown_usage())

    class Data(DataReader):
        def content(self, ref, budget):
            reads.append(ref.artifact_id)
            return super().content(ref, budget)

    class Transport(OwnerTransport):
        def read(self, request, window, *, guard=None):
            owner_calls.append([request.owner, "read"])
            return super().read(request, window, guard=guard)

        def accepted(self, request, ref, window, *, guard=None):
            owner_calls.append([request.owner, "accepted"])
            return super().accepted(request, ref, window, guard=guard)

        def submit(self, request, window, *, guard=None):
            owner_calls.append([request.owner, "submit"])
            if stage == "die-before" and request.owner == "knowledge":
                crash(request)
            reply = super().submit(request, window, guard=guard)
            if stage == "die-after" and request.owner == "knowledge":
                crash(request, reply)
            if stage == "uncertain" and request.owner == "knowledge":
                raise OwnerUnavailable("synthetic_lost_reply_after_actual_commit")
            return reply

    data = Data(os.environ["COMBINED_DATA_ENDPOINT"], os.environ["COMBINED_DATA_TOKEN"])
    knowledge = KnowledgeReader(KnowledgeTransport(os.environ["COMBINED_KNOWLEDGE_ENDPOINT"], os.environ["COMBINED_KNOWLEDGE_TOKEN"]))
    questions = QuestionReader(ResearchTransport(os.environ["COMBINED_RESEARCH_ENDPOINT"], os.environ["COMBINED_RESEARCH_TOKEN"]))
    client = ArtifactClient(PublicationTransport(os.environ["COMBINED_DATA_ENDPOINT"], os.environ["COMBINED_DATA_TOKEN"]),
        WorkerIdentity("fixture", scope))
    traces = PublicationJournal(PublicationStore(engine, "combined-data"))
    trace_publisher = TracePublisher(traces, SourceReviewer(data), client)
    results = ResultPublisher(ResultJournal(ResultStore(engine, "combined-data", trace_publisher_id="combined-data")),
        ResultPreparer(data, knowledge=knowledge, research=questions), client)
    preparer = HandoffPreparer(data, knowledge=knowledge, research=questions)
    owners = {name: OwnerHandoff(HandoffJournal(ObservedStore(engine, "combined-" + name, trace_publisher_id="combined-data")),
        preparer, Transport("combined-" + name, name, os.environ["COMBINED_" + name.upper() + "_ENDPOINT"],
            os.environ["COMBINED_" + name.upper() + "_TOKEN"])) for name in ("research", "knowledge")}
    coordinator = HandoffCoordinator(traces, research=owners["research"], knowledge=owners["knowledge"], answers=results, questions=questions)
    result = {"pid": os.getpid(), "stage": stage, "provider_calls": calls, "processing_reads": reads, "owner_calls": owner_calls}
    try:
        if stage in {"seed", "seed-crashes"}:
            graph = DomainGraphRef.model_validate(raw["task"]["target"]["graph"])
            profile = knowledge.transport.read("/v1/graph-profiles/read", graph, KnowledgeReadWindow())
            raw["task"]["target"].update(vocabulary=profile.vocabulary_reference.model_dump(mode="json"),
                policy=profile.policy.model_dump(mode="json"), operation_schema=proposal_schema().model_dump(mode="json"))
            origins = {}
            names = ("diagnostic", "campaign", "stale") if stage == "seed" else ("crash-before", "crash-after")
            for name in names:
                candidate = copy.deepcopy(raw)
                candidate["request"]["reference"]["engagement_id"] = name
                candidate["task"].update(task_id=name, engagement=candidate["request"]["reference"])
                if name == "stale" or name.startswith("crash-"):
                    candidate["draft"].update(questions=[], answers=[], evidence_needs=[])
                if name.startswith("crash-"):
                    candidate["task"]["target"]["graph"]["graph_id"] = name
                request = RequestSnapshot.from_bytes(encode(candidate["request"]), actor_id="fixture", scope=scope)
                candidate["task"]["request_sha256"] = request.sha256
                task = ExtractionSnapshot.from_bytes(encode(candidate["task"]), request)
                context = request.document().context.model_dump(mode="json")
                policy = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
                policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=10)
                policy = BudgetPolicy.from_bytes(encode(policy))

                runner = PlanningRunner(engine, Provider(name, b"{" if name == "diagnostic" else encode(candidate["draft"])), timeout_seconds=10)
                runner.journal.register(principal, request)
                journal = ExtractionJournal(engine)
                journal.register(principal, task)
                binding = AttemptBinding(request, 1)
                runner.execute(principal, binding, policy)
                trace = journal.record(principal, task.document().task_id, binding.reference(), name).projection.reference()
                identifier = "d-" + hashlib.sha256(encode({"format": "planning-diagnostic-interpretation.v1",
                    "actor_id": principal.actor_id, "trace": trace.model_dump(mode="json")})).hexdigest()
                published = trace_publisher.publish(principal, identifier, trace)
                assert published.attempt.stage == "finalized"
                origins[name] = {"trace": trace.model_dump(mode="json"), "interpretation_id": identifier,
                    "interpretation": published.attempt.result.artifact.model_dump(mode="json"),
                    "task": task.document().model_dump(mode="json"), "task_sha256": task.sha256}
                if name == "diagnostic":
                    diagnostic = DiagnosticProducer(principal, trace_publisher, results).produce(trace)
                    assert diagnostic is not None
                    origins[name]["feedback"] = diagnostic.feedback.model_dump(mode="json")
            origin_path.write_bytes(encode(origins))
            result["origins"] = origins
        elif stage == "future-pin":
            origins = json.loads(origin_path.read_bytes())
            selected = json.loads((origin_path.parent / "future-head.json").read_bytes())
            raw["request"]["reference"]["engagement_id"] = "future-campaign"
            request = RequestSnapshot.from_bytes(encode(raw["request"]), actor_id="fixture", scope=scope)
            document = copy.deepcopy(origins["campaign"]["task"])
            document.update(task_id="future-campaign", engagement=request.document().reference.model_dump(mode="json"),
                request_sha256=request.sha256)
            document["target"]["base"] = selected
            task = ExtractionSnapshot.from_bytes(encode(document), request)
            context = knowledge.review(task)
            PlanningRunner(engine, Provider("unused", b"{}"), timeout_seconds=10).journal.register(principal, request)
            ExtractionJournal(engine).register(principal, task)
            result.update(pinned_base=task.document().target.base.model_dump(mode="json"),
                task_sha256=task.sha256, context_task_sha256=context.task_sha256)
            assert context.task_sha256 == task.sha256
        else:
            origins = json.loads(origin_path.read_bytes())
            name = "stale" if stage == "stale" else "campaign"
            if stage.endswith(("-before", "-after")):
                name = "crash-" + stage.rsplit("-", 1)[1]
            origin = origins[name]
            report = coordinator.run(principal, ExtractionTraceRef.model_validate(origin["trace"]), origin["interpretation_id"])
            effects = []
            for effect in report.effects:
                item = {"kind": effect.slot.kind, "status": effect.status, "reason": effect.reason}
                state = effect.state
                if isinstance(state, HandoffState) and state.payload is not None:
                    item.update(request=state.payload.request.document().model_dump(mode="json"), payload_sha256=state.payload.sha256,
                        prepared_at=state.prepared_at.isoformat(), position=state.position,
                        outcome=None if state.progress.outcome is None else json.loads(state.progress.outcome.canonical))
                elif state is not None and not isinstance(state, HandoffState) and state.attempt is not None:
                    item.update(artifact=None if state.attempt.result is None else state.attempt.result.artifact.model_dump(mode="json"))
                effects.append(item)
            result.update(effects=effects, task_sha256=origin["task_sha256"], pinned_base=origin["task"]["target"]["base"])
            assert not calls
        return result
    finally:
        engine.dispose()


if __name__ == "__main__":
    mode, fixture_file, origins_file, output_file = sys.argv[1:]
    Path(output_file).write_bytes(encode(run(mode, Path(fixture_file), Path(origins_file), Path(output_file))))
