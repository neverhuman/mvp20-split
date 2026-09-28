"""Semantic completion identity and exact output-retention bindings."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_artifacts import CompletionIntentBinding, ReserveArtifact
from amphora_contracts_runtime import CompleteInvocation
from amphora_contracts_tools import Succeeded, ToolDescriptor

from ..lifecycle.model import TransitionError


@dataclass(frozen=True, slots=True)
class CompletionProposal:
    scope: object
    actor_id: str
    request: CompleteInvocation

    @classmethod
    def from_command(cls, command):
        payload = json.loads(command.canonical_bytes)["payload"]
        return cls(command.identity.scope, command.identity.actor_id,
                   CompleteInvocation.model_validate_json(json.dumps(payload)))

    @property
    def digest(self):
        # Semantic profile 1: scope/actor plus normalized payload, excluding command ID and derived receipts.
        body = {"profile": "amphora-completion-v1", "scope": self.scope.model_dump(),
                "actor_id": self.actor_id, "payload": self.request.model_dump(mode="json")}
        return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=True, allow_nan=False).encode()).hexdigest()

    def validate_outputs(self, descriptor, specification):
        if descriptor is None:
            raise TransitionError("completion_descriptor_unavailable")
        descriptor = ToolDescriptor.model_validate_json(json.dumps(descriptor))
        if descriptor.binding.model_dump(mode="json") != specification["tool"] or descriptor.side_effects != "pure":
            raise TransitionError("completion_descriptor_mismatch")
        outcome = self.request.completion.outcome
        if not isinstance(outcome, Succeeded):
            return
        ports = {p.name: p for p in descriptor.outputs}
        supplied = {p.port for p in outcome.outputs}
        if len(supplied) != len(outcome.outputs):
            raise TransitionError("duplicate_output")
        if any(p.required and p.name not in supplied for p in descriptor.outputs):
            raise TransitionError("missing_required_output")
        for output in outcome.outputs:
            if output.port not in ports:
                raise TransitionError("unknown_output")
            if output.artifact.scope != self.scope or output.artifact.schema_ref != ports[output.port].schema_ref:
                raise TransitionError("output_binding_mismatch")
        if outcome.checkpoint is not None and (outcome.checkpoint.scope != self.scope or
                                               outcome.checkpoint.schema_ref != descriptor.checkpoint_schema):
            raise TransitionError("checkpoint_binding_mismatch")

    def artifacts(self):
        outcome = self.request.completion.outcome
        if not isinstance(outcome, Succeeded):
            return ()
        values = [("output:" + o.port, o.artifact) for o in outcome.outputs]
        if outcome.checkpoint is not None:
            values.append(("checkpoint", outcome.checkpoint))
        # Hash labels keep output identities bounded even for maximum-length port names.
        return tuple((hashlib.sha256(label.encode()).hexdigest(), artifact) for label, artifact in values)


@dataclass(frozen=True, slots=True)
class PreparedIntent:
    intent_id: str
    proposal: CompletionProposal
    runtime_owner: str

    def reservations(self):
        return tuple(ReserveArtifact(artifact=artifact, intent=CompletionIntentBinding(
            runtime_owner=self.runtime_owner, intent_id=self.intent_id,
            semantic_completion_sha256=self.proposal.digest, output_binding=key))
            for key, artifact in self.proposal.artifacts())

    def stored_bindings(self):
        return [r.model_dump(mode="json") for r in self.reservations()]
