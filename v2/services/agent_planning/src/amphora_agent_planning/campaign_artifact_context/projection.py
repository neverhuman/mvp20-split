"""Byte-owned observed payloads and explicit failures, not continuing permission."""

import base64
import hashlib
from dataclasses import dataclass

from ..campaign_data_access.reader import CODES
from ..context.policy import require
from .plan import ArtifactContextPlan, PlannedArtifact, encode


@dataclass(frozen=True)
class ArtifactContextItem:
    planned: PlannedArtifact
    body: bytes | None
    failure: str | None

    @classmethod
    def available(cls, planned, body):
        require(type(body) is bytes and len(body) <= 4194304 and len(body) == planned.reference.size_bytes and
                hashlib.sha256(body).hexdigest() == planned.reference.sha256, 'campaign_artifact_context_bytes')
        return cls(planned, body, None)

    @classmethod
    def unavailable(cls, planned, reason):
        require(reason in CODES | {'campaign_artifact_invalid'}, 'campaign_artifact_context_reason')
        return cls(planned, None, reason)

    def metadata(self):
        return dict(self.planned.document(), status='available' if self.body is not None else 'unavailable', reason=self.failure)

    def payload(self):
        # Representation is lossless for arbitrary Artifact formats, not text conversion.
        return dict(self.metadata(), body_base64=None if self.body is None else base64.b64encode(self.body).decode('ascii'))

    @property
    def observation_sha256(self):
        return hashlib.sha256(encode(self.metadata())).hexdigest()


@dataclass(frozen=True)
class ArtifactContextProjection:
    plan: ArtifactContextPlan
    items: tuple[ArtifactContextItem, ...]

    @classmethod
    def bind(cls, plan, items):
        original = ArtifactContextPlan.bind(plan.request)
        require(original == plan, 'campaign_artifact_context_plan')
        require(type(items) is tuple and len(items) == len(plan.items) and
                tuple(item.planned for item in items) == plan.items, 'campaign_artifact_context_items')
        verified, total = [], 0
        for item in items:
            require((item.body is None) != (item.failure is None), 'campaign_artifact_context_shape')
            if item.failure is None:
                verified.append(ArtifactContextItem.available(item.planned, item.body))
                total += len(item.body)
            else:
                verified.append(ArtifactContextItem.unavailable(item.planned, item.failure))
        require(total <= 33554432, 'campaign_artifact_context_total')
        return cls(original, tuple(verified))

    @property
    def missing_required(self):
        return tuple(item for item in self.items if item.planned.required and item.failure is not None)

    @property
    def canonical(self):
        # Artifact references already bind exact body bytes; metadata hashes do not renew grants.
        return encode({'format': 'planning-campaign-artifact-context.v1', 'plan_sha256': self.plan.sha256,
            'authority': 'observed_processing_read_only', 'items': [item.metadata() for item in self.items]})

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
