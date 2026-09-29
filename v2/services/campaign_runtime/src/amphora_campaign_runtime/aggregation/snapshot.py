"""Freeze an exact committed member cut before an aggregation policy consumes it."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_core import Digest, Identifier, Scope
from amphora_contracts_graph_runtime import GraphBinding
from pydantic import TypeAdapter

from ..compiler.catalog import canonical
from ..lifecycle.model import TransitionError
from ..wire import raw_fields

MAX_REVISION = 9007199254740991
TERMINAL = frozenset({"succeeded", "failed", "abstained", "skipped", "cancelled", "blocked"})
IDENTIFIER = TypeAdapter(Identifier)
DIGEST = TypeAdapter(Digest)


def require(condition, reason):
    if not condition:
        raise TransitionError(reason)


@dataclass(frozen=True)
class AggregateIdentity:
    scope: Scope
    run_id: str
    activation_id: str

    def __post_init__(self):
        IDENTIFIER.validate_python(self.run_id, strict=True)
        DIGEST.validate_python(self.activation_id, strict=True)
        object.__setattr__(self, "scope", Scope.model_validate_json(self.scope.model_dump_json()))

    @property
    def key(self):
        return hashlib.sha256(canonical({"profile": "amphora-aggregate-identity-v1",
            "scope": self.scope.model_dump(mode="json"), "run_id": self.run_id,
            "activation_id": self.activation_id})).hexdigest()


@dataclass(frozen=True)
class MemberSnapshot:
    """A committed observation, not a worker's unaccepted report or a live view."""

    member_id: str
    required: bool
    status: str
    observed_revision: int
    value: object = None
    reason_code: str | None = None

    def __post_init__(self):
        require(self.status in TERMINAL | {"pending"}, "aggregate_member_status")
        require(type(self.observed_revision) is int and 0 <= self.observed_revision <= MAX_REVISION,
                "aggregate_member_revision")
        require(type(self.required) is bool, "aggregate_member_required")
        if self.status == "succeeded":
            require(self.value is not None and self.reason_code is None, "aggregate_success_evidence")
            # Revalidate even model_construct/model_copy values; don't keep mutable input references.
            value = GraphBinding.model_validate({"port": self.member_id, "value": raw_fields(self.value)}).value
            require(value.kind != "collection", "aggregate_nested_collection")
            object.__setattr__(self, "value", value)
        else:
            require(self.value is None and self.reason_code is not None, "aggregate_missing_evidence")
            # Reuse the existing missing-slot boundary to validate identifiers without new wire types.
            GraphBinding.model_validate_json(canonical({"port": self.member_id, "value": {
                "kind": "collection", "items": [{"kind": "missing", "member_id": self.member_id,
                    "reason_code": self.reason_code}]}}))

    def record(self):
        return {"member_id": self.member_id, "required": self.required, "status": self.status,
                "observed_revision": self.observed_revision, "reason_code": self.reason_code,
                "value": None if self.value is None else self.value.model_dump(mode="json")}


@dataclass(frozen=True)
class SnapshotCut:
    """Immutable membership order and revision cut; does not decide join success."""

    identity: AggregateIdentity
    observed_revision: int
    closure_revision: int
    trigger: str
    members: tuple[MemberSnapshot, ...]

    def __post_init__(self):
        require(type(self.observed_revision) is int and type(self.closure_revision) is int and
                0 <= self.observed_revision < self.closure_revision <= MAX_REVISION, "aggregate_cut_revision")
        require(self.trigger in {"all_terminal", "deadline"}, "aggregate_cut_trigger")
        members = tuple(self.members)
        require(len(members) <= 10000, "aggregate_member_bound")
        require(len({member.member_id for member in members}) == len(members), "aggregate_duplicate_member")
        require(all(member.observed_revision <= self.observed_revision for member in members),
                "aggregate_future_member")
        require(self.trigger == "deadline" or all(member.status in TERMINAL for member in members),
                "aggregate_pending_member")
        for member in members:
            if member.value is not None and member.value.kind == "artifact":
                require(member.value.artifact.scope == self.identity.scope, "aggregate_foreign_artifact")
        object.__setattr__(self, "members", members)

    def record(self):
        return {"profile": "amphora-aggregate-cut-v1", "aggregate_id": self.identity.key,
                "scope": self.identity.scope.model_dump(mode="json"), "run_id": self.identity.run_id,
                "activation_id": self.identity.activation_id, "observed_revision": self.observed_revision,
                "closure_revision": self.closure_revision, "trigger": self.trigger,
                "members": [member.record() for member in self.members]}

    @property
    def sha256(self):
        return hashlib.sha256(canonical(self.record())).hexdigest()
