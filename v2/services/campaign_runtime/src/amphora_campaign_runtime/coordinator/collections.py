"""Ordered all-member aggregation and immutable scatter membership identities."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_graph_runtime import CollectionValue, GraphBinding, MissingValue

from ..compiler.catalog import canonical
from .values import BoundValues, ensure


@dataclass(frozen=True)
class AllMembers:
    policy: object

    def collect(self, members):
        ensure(self.policy.kind == "all", "graph_collection_policy_unsupported")
        values = []
        for key, status, required, value in members:
            if status == "skipped" and self.policy.skipped == "exclude":
                continue
            if status != "succeeded":
                ensure(not required, "graph_required_member_unavailable")
                value = MissingValue(kind="missing", reason_code="member_" + status, member_id=key)
            ensure(value is not None and value.kind != "collection", "graph_collection_member_type")
            values.append(value)
        return CollectionValue(kind="collection", items=tuple(values))

    def join(self, node, scope):
        members = []
        for member in node.members:
            status = "succeeded"
            if member.source.kind == "output":
                status = scope.nodes[member.source.node_id]["status"]
            value = scope.environment.source(member.source) if status == "succeeded" else None
            members.append((member.member_id, status, member.required, value))
        return BoundValues((GraphBinding(port=node.output.name, value=self.collect(members)),))


@dataclass(frozen=True)
class FrozenMembership:
    collection: CollectionValue

    @property
    def sha256(self):
        return hashlib.sha256(canonical({"profile": "amphora-scatter-membership-v1",
                                        "collection": self.collection.model_dump(mode="json")})).hexdigest()

    def record(self):
        return {"membership_sha256": self.sha256, "collection": self.collection.model_dump(mode="json"), "next_index": 0}
