"""Focused registry authority, lifecycle and immutable record projections."""

import json
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_tools import RegistryReceipt, ReleaseDescriptor, ReleaseSnapshot

from ..descriptors.identity import ReleaseDocument


class RegistryDenied(ValueError):
    """Reason-only domain rejection; no private request data."""


@dataclass(frozen=True, slots=True)
class Principal:
    actor_id: str
    scope: Scope
    actions: frozenset[str]

    def authorize(self, command):
        if command.identity.actor_id != self.actor_id or command.identity.scope != self.scope:
            raise RegistryDenied("identity_scope_denied")
        if command.identity.command_family.removeprefix("registry.") not in self.actions:
            raise RegistryDenied("action_denied")


@dataclass(frozen=True, slots=True)
class Lifecycle:
    status: str
    revision: int

    def changed(self, action, expected):
        if self.revision != expected:
            raise RegistryDenied("revision_conflict")
        transitions = {("registered", "activate"): "active", ("active", "drain"): "draining",
                       ("registered", "revoke"): "revoked", ("active", "revoke"): "revoked",
                       ("draining", "revoke"): "revoked"}
        if (self.status, action) not in transitions:
            raise RegistryDenied("lifecycle_transition_denied")
        if self.revision >= 9007199254740991:
            raise RegistryDenied("revision_exhausted")
        return Lifecycle(transitions[self.status, action], self.revision + 1)


@dataclass(frozen=True, slots=True)
class ReleaseRecord:
    descriptor: ReleaseDescriptor
    document: ReleaseDocument
    lifecycle: Lifecycle

    @classmethod
    def from_row(cls, row):
        descriptor = ReleaseDescriptor.model_validate_json(json.dumps(row["descriptor"]))
        document = ReleaseDocument.from_descriptor(descriptor)
        if document.digest != row["descriptor_sha256"] or document.canonical_bytes != bytes(row["canonical_bytes"]):
            raise RuntimeError("Stored release identity is inconsistent")
        if document.to_lock().model_dump(mode="json") != row["lock_entry"]:
            raise RuntimeError("Stored release lock is inconsistent")
        return cls(descriptor, document, Lifecycle(row["status"], row["revision"]))

    def to_wire(self, scope):
        return ReleaseSnapshot(scope=scope, descriptor=self.descriptor, lock=self.document.to_lock(),
                               revision=self.lifecycle.revision, status=self.lifecycle.status)


@dataclass(frozen=True, slots=True)
class ReceiptFactory:
    operation_id: str

    def accepted(self, reason, *, release=None, deployment=None, heartbeat=None, decision=None):
        return RegistryReceipt(operation_id=self.operation_id, status="accepted", reason_code=reason,
                               release=release, deployment=deployment, heartbeat=heartbeat, decision=decision)

    def rejected(self, reason, *, release=None, decision=None):
        return RegistryReceipt(operation_id=self.operation_id, status="rejected", reason_code=reason,
                               release=release, deployment=None, heartbeat=None, decision=decision)
