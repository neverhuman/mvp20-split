"""Deterministic collection decisions over an immutable, owner-accepted cut."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_campaigns import AllCollectionPolicy, PartialCollectionPolicy
from amphora_contracts_graph_runtime import CollectionValue, MissingValue
from pydantic import TypeAdapter

from ..compiler.catalog import canonical
from ..wire import raw_fields
from .snapshot import SnapshotCut, require

POLICY = TypeAdapter(AllCollectionPolicy | PartialCollectionPolicy)


@dataclass(frozen=True)
class JoinAccumulator:
    policy: object

    def __post_init__(self):
        policy = POLICY.validate_python(raw_fields(self.policy), strict=True)
        if policy.kind == "partial":
            require((policy.close == "deadline") == (policy.deadline_seconds is not None),
                    "aggregate_deadline_policy")
        object.__setattr__(self, "policy", policy)

    def close(self, cut: SnapshotCut):
        require(cut.trigger != "deadline" or
                (self.policy.kind == "partial" and self.policy.close == "deadline"),
                "aggregate_deadline_not_declared")
        return AggregateDecision(cut, self)


@dataclass(frozen=True)
class AggregateDecision:
    """Derived decision; callers cannot inject a successful status or substitute outputs."""

    cut: SnapshotCut
    accumulator: JoinAccumulator

    def __post_init__(self):
        policy = self.accumulator.policy
        require(self.cut.trigger != "deadline" or (policy.kind == "partial" and policy.close == "deadline"),
                "aggregate_deadline_not_declared")

    @property
    def eligible(self):
        return tuple(member for member in self.cut.members if member.status == "succeeded")

    @property
    def reason_code(self):
        policy = self.accumulator.policy
        if policy.kind == "partial":
            return "aggregate_minimum_unmet" if len(self.eligible) < policy.minimum else None
        for member in self.cut.members:
            if member.status == "skipped" and policy.skipped == "exclude":
                continue
            if member.required and member.status != "succeeded":
                return "graph_required_member_unavailable"
        return None

    @property
    def status(self):
        return "succeeded" if self.reason_code is None else "blocked"

    @property
    def collection(self):
        if self.reason_code is not None:
            return None
        policy = self.accumulator.policy
        values = []
        for member in self.cut.members:
            if policy.kind == "all" and policy.skipped == "exclude" and member.status == "skipped":
                continue
            values.append(member.value if member.status == "succeeded" else
                          MissingValue(kind="missing", member_id=member.member_id, reason_code=member.reason_code))
        return CollectionValue(kind="collection", items=tuple(values))

    def record(self):
        collection = self.collection
        return {"profile": "amphora-aggregate-decision-v1", "cut_sha256": self.cut.sha256,
                "policy": self.accumulator.policy.model_dump(mode="json"), "status": self.status,
                "reason_code": self.reason_code, "eligible_members": [member.member_id for member in self.eligible],
                "collection": None if collection is None else collection.model_dump(mode="json")}

    @property
    def sha256(self):
        return hashlib.sha256(canonical(self.record())).hexdigest()
