"""Receipt-first Data publication with owner-journal recovery and no SQL across I/O."""

from amphora_contracts_artifacts import PublicationObservation
from amphora_tool_protocol import ArtifactClient, CommandRejected, ProtocolError, WorkerIdentity

from ..authoring.canonical import KnowledgeError
from ..reasoning.binding import GraphInputs
from ..rebuild.history import RebuildHistory
from ..validation.transport import PeerUnavailable
from .journal import PublicationJournal
from .terminal import PublicationTerminals


class PublicationWorkflow:
    def __init__(self, store, reviewer, publisher, transport):
        self.store, self.reviewer, self.publisher, self.transport = store, reviewer, publisher, transport
        self.journal = PublicationJournal(store)
        self.terminals = PublicationTerminals(self.journal)

    def _review(self, document):
        with self.store.engine.connect() as connection:
            source = self.store.source(connection, document)
        request = source.status.request
        history = RebuildHistory(self.store.engine)
        cursor = history.cursor(request.snapshot.graph).through(
            history.tail(request.snapshot.graph, 0, source.head), source.head)
        inputs = GraphInputs.from_state(cursor.state, request.context)
        if inputs.snapshot != request.snapshot:
            raise KnowledgeError("publication_snapshot_mismatch")
        included = {item.reference for item in inputs.assertions}
        assertions = tuple(item for item in cursor.state.assertions.active() if item.reference in included)
        return self.reviewer.review_reasoning(request, assertions)

    def read(self, principal, request):
        try:
            return self.terminals.read(principal, request)
        except KnowledgeError as error:
            if str(error) == "publication_intent_missing":
                return None
            raise

    def submit(self, principal, request):
        document = self.store.begin(principal, request, self.publisher)
        existing = self.terminals.read(principal, document.request)
        if existing.outcome.status != "pending":
            return existing
        lease = self.store.acquire(principal, document.request)
        if lease is None:
            return self.terminals.read(principal, document.request)

        def guard():
            self.store.renew(lease, seconds=60)

        try:
            # A terminal may have committed between the first read and acquire.
            existing = self.terminals.read(principal, document.request)
            if existing.outcome.status != "pending":
                return existing
            progress = self.journal.read(principal, document.request)
            if progress is None:
                guard()
                try:
                    observation = self._review(document)
                except PeerUnavailable:
                    raise
                except KnowledgeError as error:
                    return self.terminals.fail(lease, None, str(error))
                progress = self.journal.prepare(lease, observation)
            client = ArtifactClient(self.transport, WorkerIdentity(self.publisher.actor_id, document.request.graph.scope))
            # Every branch advances retained state or exits. A failed/uncertain
            # PUT exits this submit; its next resume explicitly abandons it.
            for _ in range(12):
                attempt, artifact = progress.attempt, progress.payload.artifact
                if attempt.stage == "prepared":
                    try:
                        upload = client.begin_derived(artifact.content, artifact.declaration,
                            attempt.identity.begin_id, guard=guard, resume=True)
                    except CommandRejected as error:
                        return self.terminals.fail(lease, progress.position, error.reason_code)
                    progress = self.journal.advance(lease, progress.position, "begun", upload)
                elif attempt.stage == "begun":
                    progress = self.journal.advance(lease, progress.position, "streaming")
                    streamed = client.stream(attempt.upload.upload, artifact.body, guard=guard)
                    progress = self.journal.advance(lease, progress.position, "streamed", streamed)
                elif attempt.stage == "streaming":
                    progress = self.journal.advance(lease, progress.position, "abandoned")
                elif attempt.stage == "abandoned":
                    if attempt.identity.ordinal == 8:
                        return self.terminals.fail(lease, progress.position, "publication_stream_attempt_limit")
                    progress = self.journal.advance(lease, progress.position, "replacement")
                elif attempt.stage == "streamed":
                    progress = self.journal.advance(lease, progress.position, "finalizing")
                elif attempt.stage == "finalizing":
                    return self._finalize(client, lease, progress, guard)
                else:
                    raise KnowledgeError("publication_storage_mismatch")
            raise KnowledgeError("publication_progress_limit")
        finally:
            try:
                self.store.release(lease)
            except KnowledgeError as error:
                if str(error) != "publication_lease_lost":
                    raise

    def _finalize(self, client, lease, progress, guard):
        attempt = progress.attempt
        try:
            receipt = client.finalize(attempt.upload.upload, attempt.identity.finalize_id, guard=guard, resume=True)
        except CommandRejected as error:
            # SDK rejection proves a bound receipt was observed; retain that
            # exact public proof before converting finalization to failure.
            guard()
            reply = self.transport.request("GET", f"/v1/commands/artifacts.finalize/{attempt.identity.finalize_id}")
            if reply.status != 200:
                raise ProtocolError("publication_rejection_unavailable") from error
            proof = PublicationObservation.model_validate_json(reply.body)
            return self.terminals.fail(lease, progress.position, error.reason_code, rejection=proof)
        guard()
        derivation = client.derivation(receipt.artifact)
        return self.terminals.finish(lease, progress.position, receipt, derivation)
