"""Test evidence identities/equivalence; never checkpoint or execution authority."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_search import SearchCheckpoint, search_checkpoint_schema


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


class RecoveryMismatch(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise RecoveryMismatch(reason)


@dataclass(frozen=True)
class CheckpointEvidence:
    artifact: ArtifactRef
    checkpoint: SearchCheckpoint

    @classmethod
    def from_bytes(cls, artifact, payload):
        try:
            ref = ArtifactRef.model_validate_json(canonical(artifact))
        except ValueError:
            raise RecoveryMismatch("checkpoint_artifact_shape") from None
        require(ref.schema_ref == search_checkpoint_schema(), "checkpoint_schema")
        require(ref.sha256 == hashlib.sha256(payload).hexdigest() and ref.size_bytes == len(payload), "checkpoint_content")
        try:
            raw = json.loads(payload)
        except (ValueError, UnicodeDecodeError):
            raise RecoveryMismatch("checkpoint_json") from None
        require(isinstance(raw, dict) and raw.get("schema_version") == "1", "checkpoint_profile")
        try:
            record = SearchCheckpoint.model_validate_json(payload)
        except ValueError:
            raise RecoveryMismatch("checkpoint_shape") from None
        require(canonical(record.model_dump(mode="json")) == payload, "checkpoint_canonical_bytes")
        require(record.specification.scope == ref.scope, "checkpoint_scope")
        require(hashlib.sha256(canonical(record.specification.model_dump(mode="json"))).hexdigest() == record.specification_sha256, "checkpoint_specification_digest")
        return cls(ref, record)

    def projection(self):
        value = self.checkpoint.model_dump(mode="json")
        del value["previous"]
        return value

    def identity(self):
        return {"artifact": self.artifact.model_dump(mode="json"), "specification_sha256": self.checkpoint.specification_sha256,
                "generation": self.checkpoint.generation, "phase": self.checkpoint.phase, "rng": self.checkpoint.rng.model_dump(mode="json")}


class CheckpointTrace:
    def __init__(self, snapshots):
        self.snapshots = tuple(snapshots)
        require(bool(self.snapshots), "checkpoint_trace_empty")
        first = self.snapshots[0].checkpoint
        require(first.previous is None and first.generation == 0, "checkpoint_trace_origin")
        for previous, current in zip(self.snapshots, self.snapshots[1:]):
            old, new = previous.checkpoint, current.checkpoint
            require(new.previous == previous.artifact, "checkpoint_chain")
            require(new.specification_sha256 == first.specification_sha256, "checkpoint_revision_mixed")
            require(new.generation >= old.generation and new.rng.counter >= old.rng.counter, "checkpoint_progress_reversed")

    def equivalent(self, other):
        require(len(self.snapshots) == len(other.snapshots), "checkpoint_trace_length")
        for index, (left, right) in enumerate(zip(self.snapshots, other.snapshots)):
            require(left.projection() == right.projection(), "checkpoint_replay_changed:" + str(index))
        return {"profile": "search-recovery-evidence-v1", "equivalent": True,
                "comparison": "all_canonical_checkpoint_fields_except_run_specific_previous_artifact",
                "baseline": [item.identity() for item in self.snapshots], "resumed": [item.identity() for item in other.snapshots],
                "authority": "synthetic_engineering_evidence_only"}
