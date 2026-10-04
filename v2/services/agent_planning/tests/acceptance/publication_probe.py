"""Installed Planning worker; only own SQL credentials and public Data HTTP."""

import hashlib
import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.budget import BudgetPolicy
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.orchestration import PlanningRunner
from amphora_agent_planning.persistence.extraction import ExtractionJournal
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.publication.journal import PublicationJournal
from amphora_agent_planning.publication.store import PublicationStore
from amphora_agent_planning.publication.transport import PublicationTransport
from amphora_agent_planning.publication.workflow import TracePublisher
from amphora_agent_planning.source_access import DataReader, SourceReviewer
from amphora_contracts_core import Scope
from amphora_tool_protocol import ArtifactClient, ProtocolError, WorkerIdentity
from sqlalchemy import create_engine


def summary(state):
    return {"position": state.position, "stage": state.attempt.stage,
            "ordinal": state.attempt.identity.ordinal, "begin_id": state.attempt.identity.begin_id,
            "finalize_id": state.attempt.identity.finalize_id,
            "upload_id": None if state.attempt.upload is None else state.attempt.upload.upload.upload_id,
            "prepared_at": state.prepared_at.isoformat(), "payload_sha256": state.payload.sha256,
            "events": [{"sha256": event.sha256, "at": at.isoformat()} for event, at in state.events],
            "result": None if state.attempt.result is None else state.attempt.result.model_dump(mode="json"),
            "rejection": state.attempt.rejection}


def main():
    mode, fixture, publication, output = sys.argv[1:]
    raw = json.loads(Path(fixture).read_bytes())
    scope = Scope.model_validate(raw["task"]["scope"])
    request = RequestSnapshot.from_bytes(json.dumps(raw["request"]).encode(), actor_id="fixture", scope=scope)
    raw["task"]["request_sha256"] = request.sha256
    task = ExtractionSnapshot.from_bytes(json.dumps(raw["task"]).encode(), request)
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    engine = create_engine(os.environ["AMPHORA_TEST_PLANNING_SERVICE_URL"],
                           connect_args={"options": "-c statement_timeout=5000"})
    calls = []
    class Provider:
        def supports(self, model):
            return True
        def reply(self, binding):
            calls.append(binding.ordinal)
            return ProviderReply((json.dumps(raw["draft"]).encode(),), unknown_usage())

    try:
        runner = PlanningRunner(engine, Provider(), timeout_seconds=30)
        extractions = ExtractionJournal(engine)
        runner.journal.register(principal, request)
        extractions.register(principal, task)
        context = request.document().context.model_dump(mode="json")
        policy = {key: context[key] for key in ("model", "prompt", "policy", "output_schema", "allowed_actions", "limits")}
        policy.update(format="planning-budget-policy.v1", per_attempt_accounting_units=40)
        binding = AttemptBinding(request, 1)
        runner.execute(principal, binding, BudgetPolicy.from_bytes(json.dumps(policy).encode()))
        trace = extractions.record(principal, task.document().task_id, binding.reference(), "actual-trace")
        store = PublicationStore(engine, "actual-data-owner")
        journal = PublicationJournal(store)
        endpoint, token = os.environ["PUBLICATION_DATA_ENDPOINT"], os.environ["PUBLICATION_DATA_TOKEN"]
        client = ArtifactClient(PublicationTransport(endpoint, token), WorkerIdentity("fixture", scope))
        publisher = TracePublisher(journal, SourceReviewer(DataReader(endpoint, token)), client)

        def report(state, **extra):
            record = {"pid": os.getpid(), "model_calls": calls, "trace_sha256": trace.projection.sha256,
                      "trace_bytes": len(trace.projection.canonical), "state": summary(state), **extra}
            with Path(output).open("w", encoding="utf-8") as stream:
                stream.write(json.dumps(record, indent=2) + "\n")
                stream.flush()
                os.fsync(stream.fileno())

        if mode.startswith("crash-"):
            acquire = store.acquire
            def short_lease(*args, **kwargs):
                kwargs["seconds"] = 8
                return acquire(*args, **kwargs)
            store.acquire = short_lease
            boundary = mode.removeprefix("crash-")
            prepare, advance, finalize = journal.prepare, journal.advance, client.finalize
            def interrupt(state):
                if state.attempt.stage == boundary:
                    report(state, interrupted=boundary)
                    os._exit(73)
                return state
            journal.prepare = lambda *args, **kwargs: interrupt(prepare(*args, **kwargs))
            journal.advance = lambda *args, **kwargs: interrupt(advance(*args, **kwargs))
            if boundary == "remote-finalize":
                def finish_then_exit(*args, **kwargs):
                    receipt = finalize(*args, **kwargs)
                    report(journal.read(principal, publication), interrupted=boundary,
                           remote_artifact=receipt.artifact.model_dump(mode="json"))
                    os._exit(73)
                client.finalize = finish_then_exit
        if mode == "read":
            state = journal.read(principal, publication)
        else:
            try:
                state = publisher.publish(principal, publication, trace.projection.reference())
            except ProtocolError as error:
                if mode != "rights-denied" or str(error) != "command_request_denied":
                    raise
                state = journal.read(principal, publication)
                assert state.attempt.stage in {"prepared", "finalizing"}
                report(state, access_denial="command_request_denied")
                return
        assert state is not None
        if state.attempt.stage == "finalized" and mode != "read":
            # Explicit processing read verifies actual bytes through Data; this is
            # distinct from historical receipt readback and may be rights-denied.
            from amphora_agent_planning.source_access import ReadBudget
            body = DataReader(endpoint, token).content(state.attempt.result.artifact, ReadBudget())
            assert body == trace.projection.canonical
            assert hashlib.sha256(body).hexdigest() == state.attempt.result.artifact.sha256
        report(state)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
