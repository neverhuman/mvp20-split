"""Immutable selected metadata with explicit absence and a bounded relevant read set."""

import hashlib
from dataclasses import dataclass

from ..context.policy import require
from .read_set import ResearchRead, ResearchReadSet
from .record_policy import ResearchRecordPolicy
from .records import (
    ContextFinding,
    ResearchGap,
    ResearchIdentity,
    ResearchRecord,
    canonical,
)
from .selection import ResearchSelection


@dataclass(frozen=True)
class ResearchContext:
    selection: ResearchSelection
    records: tuple[ResearchRecord, ...]
    gaps: tuple[ResearchGap, ...]
    findings: tuple[ContextFinding, ...]

    @classmethod
    def bind(cls, selection, *, questions=(), needs=(), assessments=(), unavailable=()):
        selection = ResearchSelection.from_bytes(selection.canonical, selection.request)
        requested = selection.document()
        keys = tuple(ResearchIdentity.bind(kind, reference) for kind, references in (
            ("question", requested.questions), ("need", requested.needs),
            ("assessment", tuple(item.request for item in requested.assessments))) for reference in references)
        expected = {ResearchIdentity.bind("assessment", item.request): item for item in requested.assessments}
        records, gaps, consumed = {}, {}, 0
        for kind, supplied, limit in (("question", questions, 64), ("need", needs, 64), ("assessment", assessments, 32)):
            require(type(supplied) is tuple and len(supplied) <= limit, "campaign_record_count")
            for item in supplied:
                record = ResearchRecord.bind(kind, item)
                consumed += len(record.canonical)
                require(consumed <= 4194304, "campaign_context_record_bytes")
                key = record.identity
                require(key in keys, "campaign_record_not_selected")
                require(key not in records and key not in gaps, "campaign_record_duplicate")
                if kind == "assessment" and record.document().outcome.status != "assessed":
                    gaps[key] = ResearchGap(key, record.document().outcome.status)
                    continue
                if kind == "assessment":
                    require(record.sha256 == expected[key].status_sha256, "campaign_assessment_digest")
                records[key] = record
        require(type(unavailable) is tuple and len(unavailable) <= 160, "campaign_record_gap_limit")
        for item in unavailable:
            require(isinstance(item, ResearchGap) and item.identity in keys and
                    item.identity not in records and item.identity not in gaps, "campaign_record_gap_binding")
            gaps[item.identity] = ResearchGap(item.identity, item.reason)
        for key in keys:
            if key not in records and key not in gaps:
                gaps[key] = ResearchGap(key, "not_provided")
        findings = cls._relationships(requested, records, expected)
        result = cls(selection, tuple(records[key] for key in keys if key in records),
                     tuple(gaps[key] for key in keys if key in gaps), findings)
        require(len(result.canonical) <= 4194304, "campaign_context_record_bytes")
        return result

    @staticmethod
    def _relationships(requested, records, expected):
        questions, needs, findings = {}, {}, []
        for key, record in records.items():
            if key.kind == "question":
                question = record.document()
                ResearchRecordPolicy.question(question)
                questions[question.reference] = question
            elif key.kind == "need":
                need = record.document()
                needs[need.reference] = need
        for need in needs.values():
            findings.extend(ResearchRecordPolicy.need(need, questions, requested.questions))
        for key, record in records.items():
            if key.kind == "assessment":
                findings.extend(ResearchRecordPolicy.assessment(record.document(), expected[key], questions,
                                                                 needs, requested.needs))
        return tuple(findings)

    @property
    def canonical(self):
        return canonical({"format": "planning-campaign-research-context.v1", "authority": "selected_metadata_only",
            "selection_sha256": self.selection.sha256,
            "records": [{"identity": item.identity.document(), "record": item.document().model_dump(mode="json")}
                        for item in self.records],
            "gaps": [{"identity": item.identity.document(), "reason": item.reason} for item in self.gaps],
            "findings": [{"identity": item.identity.document(), "reason": item.reason} for item in self.findings]})

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def read_set(self):
        return ResearchReadSet(tuple(ResearchRead.available(item) for item in self.records) +
                               tuple(ResearchRead.unavailable(item) for item in self.gaps))
