"""Exact per-operation Artifact reads; never a retained processing-rights grant."""

import hashlib

from amphora_contracts_core import ArtifactRef

from ..context.policy import require


class ArtifactReview:
    def __init__(self, data, scope, budget):
        self.data, self.scope, self.budget = data, scope, budget
        self.identities, self.payloads = {}, {}

    def artifact(self, reference):
        reference = ArtifactRef.model_validate(reference.model_dump(mode="python", warnings=False))
        require(reference.scope == self.scope, "source_artifact_scope")
        existing = self.identities.get(reference.artifact_id)
        require(existing is None or existing == reference, "source_artifact_conflict")
        if reference.artifact_id not in self.payloads:
            require(len(self.identities) < 128, "source_input_count")
            require(reference.size_bytes <= 4194304, "source_artifact_size")
            self.identities[reference.artifact_id] = reference
            actual = self.data.artifact(reference, self.budget)
            actual = ArtifactRef.model_validate(actual.model_dump(mode="python", warnings=False))
            require(actual == reference, "source_artifact_binding")
            content = self.data.content(reference, self.budget)
            require(type(content) is bytes and len(content) == reference.size_bytes and
                    hashlib.sha256(content).hexdigest() == reference.sha256, "source_artifact_bytes")
            self.payloads[reference.artifact_id] = content
        return self.payloads[reference.artifact_id]
