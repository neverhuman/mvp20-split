"""Public SDK publication; retained stages determine recovery after every ambiguous effect."""

import json

from amphora_tool_protocol import ArtifactClient, CommandRejected, ProtocolError, WorkerIdentity

from ..assessment.policy import AssessmentError
from ..assessment.reader import AssessmentPeerUnavailable
from .artifact import SyntheticReceiptPolicy


class PublicationWorkflow:
    def __init__(self, store, reader, transport, publisher, issuer):
        self.store, self.reader, self.transport = store, reader, transport
        self.publisher, self.issuer = publisher, issuer

    def submit(self, scope, assessment_id, actor_id):
        initial = self.store.begin(scope, assessment_id, actor_id, self.publisher, self.issuer)
        progress = self.store.read(initial)
        if progress.stage in {"published", "failed"}:
            return progress
        lease = self.store.acquire(initial)
        if lease is None:
            return self.store.read(initial)

        def guard():
            self.store.renew(lease)

        client = ArtifactClient(self.transport, WorkerIdentity(self.publisher, scope))
        try:
            progress = self.store.read(initial)
            for _ in range(12):
                if progress.stage in {"published", "failed"}:
                    return progress
                if progress.stage == "prepared":
                    guard()
                    if self.reader.scope != scope:
                        raise AssessmentError("publication_reader_scope_mismatch")
                    try:
                        for reference in progress.artifact.declaration.inputs:
                            self.reader.read(reference)
                    except AssessmentPeerUnavailable:
                        raise
                    except AssessmentError as error:
                        return self.store.advance(lease, progress.position, "denied", str(error))
                    try:
                        upload = client.begin_derived(progress.artifact.content, progress.artifact.declaration,
                            progress.command_id("artifacts.begin_derived_upload"), guard=guard, resume=True)
                    except CommandRejected:
                        return self._rejected(lease, progress, "artifacts.begin_derived_upload", guard)
                    progress = self.store.advance(lease, progress.position, "begun", upload.model_dump(mode="json"))
                elif progress.stage == "begun":
                    progress = self.store.advance(lease, progress.position, "streaming")
                    streamed = client.stream(progress.upload.upload, progress.artifact.body, guard=guard)
                    progress = self.store.advance(lease, progress.position, "streamed", streamed.model_dump(mode="json"))
                elif progress.stage == "streaming":
                    progress = self.store.advance(lease, progress.position, "replace_uncertain_stream")
                elif progress.stage == "streamed":
                    progress = self.store.advance(lease, progress.position, "finalizing")
                elif progress.stage == "finalizing":
                    try:
                        finalized = client.finalize(progress.upload.upload, progress.command_id("artifacts.finalize"),
                                                    guard=guard, resume=True)
                    except CommandRejected:
                        return self._rejected(lease, progress, "artifacts.finalize", guard)
                    guard()
                    derivation = client.derivation(finalized.artifact)
                    receipt = SyntheticReceiptPolicy().issue(progress.artifact, self.publisher, self.issuer, derivation)
                    return self.store.advance(lease, progress.position, "published", {
                        "finalized": finalized.model_dump(mode="json"), "derivation": derivation.model_dump(mode="json"),
                        "receipt": receipt.model_dump(mode="json")})
            raise AssessmentError("publication_progress_limit")
        finally:
            try:
                self.store.release(lease)
            except AssessmentError as error:
                if str(error) != "publication_lease_lost":
                    raise

    def _rejected(self, lease, progress, family, guard):
        guard()
        reply = self.transport.request("GET", f"/v1/commands/{family}/{progress.command_id(family)}")
        if reply.status != 200:
            raise ProtocolError("publication_rejection_unavailable")
        return self.store.advance(lease, progress.position, "rejected", json.loads(reply.body))
