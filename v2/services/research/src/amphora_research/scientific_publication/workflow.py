"""Recoverable Artifact-only publication through the existing public Data SDK."""
import json

from amphora_tool_protocol import ArtifactClient, CommandRejected, ProtocolError, WorkerIdentity

from ..assessment.policy import AssessmentError
from ..assessment.reader import AssessmentPeerUnavailable
from .artifact import ScientificPublicationError, require


class ScientificPublicationWorkflow:
    def __init__(self, store, reader, transport, publisher):
        self.store,self.reader,self.transport,self.publisher = store,reader,transport,publisher

    def submit(self, artifact):
        initial = self.store.begin(artifact,self.publisher)
        progress = self.store.read(initial)
        if progress.stage in ("published","failed"):
            return progress
        lease = self.store.acquire(initial)
        if lease is None:
            return self.store.read(initial)
        def guard():
            self.store.renew(lease)
        client = ArtifactClient(self.transport,WorkerIdentity(self.publisher,artifact.scope))
        try:
            progress = self.store.read(initial)
            for _ in range(12):
                if progress.stage in ("published","failed"):
                    return progress
                if progress.stage == "prepared":
                    guard()
                    require(self.reader.scope == artifact.scope,"science_publication_reader_scope")
                    try:
                        for source in artifact.declaration.inputs:
                            self.reader.read(source)
                    except AssessmentPeerUnavailable:
                        raise
                    except AssessmentError as error:
                        return self.store.advance(lease,progress.position,"denied",str(error))
                    try:
                        upload = client.begin_derived(artifact.content,artifact.declaration,
                            progress.command_id("artifacts.begin_derived_upload"),guard=guard,resume=True)
                    except CommandRejected:
                        return self._rejected(lease,progress,"artifacts.begin_derived_upload",guard)
                    progress = self.store.advance(lease,progress.position,"begun",upload.model_dump(mode="json"))
                elif progress.stage == "begun":
                    progress = self.store.advance(lease,progress.position,"streaming")
                    streamed = client.stream(progress.upload.upload,artifact.body,guard=guard)
                    progress = self.store.advance(lease,progress.position,"streamed",streamed.model_dump(mode="json"))
                elif progress.stage == "streaming":
                    progress = self.store.advance(lease,progress.position,"replace_uncertain_stream")
                elif progress.stage == "streamed":
                    progress = self.store.advance(lease,progress.position,"finalizing")
                elif progress.stage == "finalizing":
                    try:
                        final = client.finalize(progress.upload.upload,progress.command_id("artifacts.finalize"),guard=guard,resume=True)
                    except CommandRejected:
                        return self._rejected(lease,progress,"artifacts.finalize",guard)
                    guard()
                    derivation = client.derivation(final.artifact)
                    return self.store.advance(lease,progress.position,"published",{
                        "finalized":final.model_dump(mode="json"),"derivation":derivation.model_dump(mode="json")})
            raise ScientificPublicationError("science_publication_progress_limit")
        finally:
            try:
                self.store.release(lease)
            except ScientificPublicationError as error:
                if str(error) != "science_publication_lease_lost":
                    raise

    def _rejected(self, lease, progress, family, guard):
        guard()
        reply = self.transport.request("GET",f"/v1/commands/{family}/{progress.command_id(family)}")
        if reply.status != 200:
            raise ProtocolError("science_publication_rejection_unavailable")
        return self.store.advance(lease,progress.position,"rejected",json.loads(reply.body))
