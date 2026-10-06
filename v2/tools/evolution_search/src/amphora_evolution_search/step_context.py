"""Bind an inline checkpoint to its canonical source Artifact without performing I/O."""

from dataclasses import dataclass
from hashlib import sha256

from amphora_contracts_core import ArtifactRef
from amphora_contracts_search import search_checkpoint_schema
from amphora_contracts_search_steps import EvaluationRequestBatch, SearchStepContext

from .attempts import evaluation_request
from .checkpoint import CheckpointSnapshot
from .ranking import require
from .specification import OriginalSearch


@dataclass(frozen=True)
class BoundCheckpoint:
    snapshot: CheckpointSnapshot
    reference: ArtifactRef

    def __post_init__(self):
        checked = ArtifactRef.model_validate_json(self.reference.model_dump_json())
        object.__setattr__(self, "reference", checked)
        require(checked.scope == self.snapshot.original.record.scope, "checkpoint_artifact_scope")
        require(checked.schema_ref == search_checkpoint_schema() and checked.media_type == "application/json", "checkpoint_artifact_schema")
        raw = self.snapshot.encode()
        require(checked.sha256 == sha256(raw).hexdigest() and checked.size_bytes == len(raw), "checkpoint_artifact_bytes")

    @classmethod
    def from_context(cls, context: SearchStepContext):
        checked = SearchStepContext.model_validate_json(context.model_dump_json())
        original = OriginalSearch(checked.original_specification)
        return cls(CheckpointSnapshot(original, checked.checkpoint), checked.checkpoint_artifact)

    def request_batch(self) -> EvaluationRequestBatch:
        state = self.snapshot.record
        require(state.phase in {"awaiting_evaluations", "stopped"}, "request_expansion_phase")
        attempts = {a.candidate_id: a for a in state.attempts}
        requests = tuple(evaluation_request(self.snapshot.original, attempts[p.candidate_id]) for p in state.pending)
        return EvaluationRequestBatch(schema_version="1", scope=self.reference.scope,
                                      specification_sha256=self.snapshot.original.digest,
                                      checkpoint_artifact=self.reference, requests=requests)
