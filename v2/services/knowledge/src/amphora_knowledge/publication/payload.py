"""Exact owner result/input binding before any Data publication side effect."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_artifacts import ContentDescriptor, DerivationDeclaration, TransformationDescriptor
from amphora_contracts_knowledge import (
    ReasoningPublicationRequest,
    ReasoningResult,
    ReasoningStatus,
    ReferenceValidation,
    reasoning_artifact_schema,
)

from ..authoring.canonical import KnowledgeError, canonical
from ..persistence.records import graph_key
from ..reasoning.profile import raw


@dataclass(frozen=True)
class PublicationRequestDocument:
    request: ReasoningPublicationRequest
    actor_id: str
    body: bytes
    sha256: str

    @classmethod
    def authorized(cls, principal, request):
        request = ReasoningPublicationRequest.model_validate(raw(request))
        principal.require("publish_reasoning", request.graph.scope)
        body = canonical(request)
        return cls(request, principal.actor_id, body, hashlib.sha256(body).hexdigest())

    @property
    def key(self):
        return graph_key(self.request.graph) | {"publication": self.request.publication_id}

    def result(self, status):
        status = ReasoningStatus.model_validate(raw(status))
        if (status.actor_id != self.actor_id or status.request.snapshot.graph != self.request.graph
            or status.request.request_id != self.request.reasoning_request_id):
            raise KnowledgeError("publication_reasoning_mismatch")
        if status.decision is None:
            raise KnowledgeError("publication_reasoning_pending")
        if status.decision.outcome != "evaluated":
            raise KnowledgeError("publication_reasoning_failed")
        if status.decision.result.request != status.request:
            raise KnowledgeError("publication_reasoning_mismatch")
        return status.decision.result


@dataclass(frozen=True)
class ReasoningArtifact:
    result: ReasoningResult
    observation: ReferenceValidation
    body: bytes
    content: ContentDescriptor
    declaration: DerivationDeclaration

    @classmethod
    def reviewed(cls, document, status, observation):
        result = document.result(status)
        # Only the owner workflow supplies this fresh review; never an HTTP payload.
        observation = ReferenceValidation.model_validate(raw(observation))
        inputs = {ref.artifact_id: ref for ref in observation.artifacts}
        if len(inputs) != len(observation.artifacts):
            raise KnowledgeError("publication_duplicate_input")
        if not inputs or any(ref.scope != document.request.graph.scope for ref in inputs.values()):
            raise KnowledgeError("publication_input_scope_mismatch")
        required = (result.request.context, result.request.subject, *(ref.raw for ref in observation.sources))
        if any(inputs.get(ref.artifact_id) != ref for ref in required):
            raise KnowledgeError("publication_required_input_missing")
        body = canonical(result)
        if len(body) > 16 * 1024 * 1024:
            raise KnowledgeError("publication_result_size_limit")
        content = ContentDescriptor(sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body),
                                    media_type="application/json", schema_ref=reasoning_artifact_schema())
        method = json.dumps({"algorithm_profile": "knowledge.signed-ground-horn.v1",
                             "rule_set": result.request.rule_set.model_dump(mode="json")},
                            sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        declaration = DerivationDeclaration(transformation=TransformationDescriptor(
            transformation_id="knowledge.synthetic_logical_entailment", version="1", sha256=hashlib.sha256(method).hexdigest()),
            inputs=tuple(inputs[key] for key in sorted(inputs)))
        return cls(result, observation, body, content, declaration)
