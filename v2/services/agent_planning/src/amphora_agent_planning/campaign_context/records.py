"""Typed immutable Research metadata identities; pure values do not prove owner contact."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_research import (
    EvidenceAssessmentRequest,
    EvidenceAssessmentStatus,
    EvidenceNeed,
    EvidenceNeedRef,
    ResearchQuestion,
    ResearchQuestionRef,
)

from ..context.policy import require

REFERENCE_MODELS = {"question": ResearchQuestionRef, "need": EvidenceNeedRef, "assessment": EvidenceAssessmentRequest}
RECORD_MODELS = {"question": ResearchQuestion, "need": EvidenceNeed, "assessment": EvidenceAssessmentStatus}
GAP_REASONS = frozenset({"not_provided", "unavailable", "denied", "pending", "failed"})


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class ResearchIdentity:
    kind: str
    reference: bytes

    @classmethod
    def bind(cls, kind, reference):
        require(kind in REFERENCE_MODELS, "campaign_record_kind")
        value = REFERENCE_MODELS[kind].model_validate_json(reference.model_dump_json(warnings=False))
        return cls(kind, canonical(value.model_dump(mode="json")))

    def document(self):
        return {"kind": self.kind, "reference": json.loads(self.reference)}


@dataclass(frozen=True)
class ResearchRecord:
    identity: ResearchIdentity
    canonical: bytes

    @classmethod
    def bind(cls, kind, supplied):
        require(kind in RECORD_MODELS, "campaign_record_kind")
        raw = supplied.model_dump_json(warnings=False).encode("utf-8")
        require(len(raw) <= 1048576, "campaign_record_size")
        value = RECORD_MODELS[kind].model_validate_json(raw)
        reference = value.request if kind == "assessment" else value.reference
        body = canonical(value.model_dump(mode="json"))
        require(len(body) <= 1048576, "campaign_record_size")
        return cls(ResearchIdentity.bind(kind, reference), body)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def document(self):
        return RECORD_MODELS[self.identity.kind].model_validate_json(self.canonical)


@dataclass(frozen=True)
class ResearchGap:
    identity: ResearchIdentity
    reason: str

    def __post_init__(self):
        require(self.reason in GAP_REASONS, "campaign_record_gap_reason")


@dataclass(frozen=True)
class ContextFinding:
    identity: ResearchIdentity
    reason: str
