"""Immutable scatter membership identities; collection policy belongs to aggregation."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_graph_runtime import CollectionValue

from ..compiler.catalog import canonical


@dataclass(frozen=True)
class FrozenMembership:
    collection: CollectionValue

    @property
    def sha256(self):
        return hashlib.sha256(canonical({"profile": "amphora-scatter-membership-v1",
                                        "collection": self.collection.model_dump(mode="json")})).hexdigest()

    def record(self):
        return {"membership_sha256": self.sha256, "collection": self.collection.model_dump(mode="json"), "next_index": 0}
