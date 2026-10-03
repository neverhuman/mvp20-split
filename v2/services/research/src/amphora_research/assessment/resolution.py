"""Authenticated-publication projections into exact configured Research criteria."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_knowledge import ReasoningResult, reasoning_artifact_schema
from amphora_contracts_research import EvidenceAssessment, SyntheticEvidenceRecord, synthetic_evidence_schema

from .boundary import BoundAssessment
from .policy import AssessmentError, CandidateAnswer, EvidenceObservation
from .reader import AssessmentPeerUnavailable, _decode


def fingerprint(model):
    return hashlib.sha256(json.dumps(model.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def payload(model, content):
    try:
        return _decode(model, content)
    except AssessmentPeerUnavailable as error:
        # These bytes already passed Data identity/hash checks: invalid immutable input,
        # not an unavailable/malformed transport envelope.
        raise AssessmentError("invalid_evidence_payload") from error


def require_inputs(proof, references):
    inputs = {item.artifact_id: item for item in proof.declaration.inputs}
    if len(inputs) != len(proof.declaration.inputs) or any(inputs.get(r.artifact_id) != r for r in references):
        raise AssessmentError("evidence_lineage_mismatch")


@dataclass(frozen=True)
class ResolvedAssessment:
    assessment: EvidenceAssessment
    inputs: tuple[ArtifactRef, ...]


class AssessmentResolver:
    """One attempt; owner ledger and scoped Data reader are explicit injected adapters."""

    def __init__(self, ledger, reader):
        self.ledger, self.reader = ledger, reader

    def resolve(self, bound: BoundAssessment) -> ResolvedAssessment:
        profile = bound.configured.document
        scope = profile.question.reference.scope
        if self.reader.scope != scope:
            raise AssessmentError("assessment_scope_mismatch")
        question = profile.question.reference
        if self.ledger.read(scope, "question", question.question_id, question.revision) != profile.question:
            raise AssessmentError("question_declaration_mismatch")
        for requirement in profile.requirements:
            ref = requirement.need.reference
            if self.ledger.read(scope, "need", ref.need_id, ref.revision) != requirement.need:
                raise AssessmentError("need_declaration_mismatch")
        # Each exact owner read finishes before any network I/O; no peer access to Research SQL.
        self.reader.read(profile.subject)
        self.reader.read(profile.question.applicability)
        for requirement in profile.requirements:
            self.reader.read(requirement.need.required_context)
        answers = tuple(self._answer(bound, item) for item in bound.request.answers)
        observations = tuple(self._observation(bound, item) for item in bound.request.receipts)
        return ResolvedAssessment(bound.evaluate(answers, observations), self.reader.consumed)

    def _answer(self, bound, answer):
        profile = bound.configured.document
        reference = answer.artifact
        if reference.schema_ref != reasoning_artifact_schema() or reference.media_type != "application/json":
            raise AssessmentError("answer_schema_mismatch")
        content, proof = self.reader.published(reference, frozenset(profile.answer_publishers))
        result = payload(ReasoningResult, content)
        request = result.request
        graph = request.snapshot.graph
        if (request.subject != profile.subject or request.context != profile.question.applicability
                or request.purpose != profile.purpose or graph.scope != profile.question.reference.scope
                or request.rule_set.graph != graph):
            raise AssessmentError("answer_applicability_mismatch")
        require_inputs(proof, (request.subject, request.context))
        method = proof.declaration.transformation
        # This is a public producer-format check, not a reimplementation of its inference rules.
        method_document = {"algorithm_profile": "knowledge.signed-ground-horn.v1",
                           "rule_set": request.rule_set.model_dump(mode="json")}
        method_digest = hashlib.sha256(json.dumps(method_document, sort_keys=True, separators=(",", ":"),
                                                  ensure_ascii=False).encode()).hexdigest()
        if (method.transformation_id != "knowledge.synthetic_logical_entailment" or method.version != "1"
                or method.sha256 != method_digest):
            raise AssessmentError("answer_method_mismatch")
        targets = tuple(f.target for f in result.findings)
        if targets != request.targets or len(set(targets)) != len(targets):
            raise AssessmentError("answer_findings_mismatch")
        complete = result.outcome.status == "complete"
        literals = [*targets, *(step.fact for step in result.steps),
                    *(premise for step in result.steps for premise in step.premises)]
        assertions = [*result.excluded_context, *(a for step in result.steps for a in step.assertions)]
        if (any(literal.subject.graph != graph or literal.object.graph != graph for literal in literals)
                or any(a.graph != graph for a in assertions)):
            raise AssessmentError("answer_findings_mismatch")
        for finding in result.findings:
            expected = ("supported" if finding.positive else "contradicted") if (
                complete and finding.positive != finding.negative) else "unknown"
            if (finding.status != expected or finding.conflict != (finding.positive and finding.negative)
                    or finding.target.subject.graph != graph or finding.target.object.graph != graph
                    or any(a.graph != graph for a in (*finding.supporting_assertions, *finding.opposing_assertions))):
                raise AssessmentError("answer_findings_mismatch")
        target = next(t for t in profile.targets if t.criterion_id == answer.criterion_id)
        matched = [f for f in result.findings if fingerprint(f.target) == target.target_sha256]
        if len(matched) != 1:
            raise AssessmentError("answer_target_mismatch")
        return CandidateAnswer(answer.criterion_id, reference, matched[0].status, matched[0].conflict)

    def _observation(self, bound, reference):
        profile = bound.configured.document
        if reference.schema_ref != synthetic_evidence_schema() or reference.media_type != "application/json":
            raise AssessmentError("evidence_schema_mismatch")
        issuers = frozenset(issuer for requirement in profile.requirements for issuer in requirement.issuers)
        content, proof = self.reader.published(reference, issuers)
        record = payload(SyntheticEvidenceRecord, content)
        if record.issuer != proof.origin.actor_id:
            raise AssessmentError("evidence_issuer_mismatch")
        scope = bound.request.profile.scope
        if any(ref.scope != scope for ref in (record.need, record.subject, record.context)):
            raise AssessmentError("evidence_scope_mismatch")
        require_inputs(proof, (record.subject, record.context))
        method = proof.declaration.transformation
        if (method.transformation_id, method.version, method.sha256) != (
                record.method.schema_id, record.method.version, record.method.sha256):
            raise AssessmentError("evidence_method_mismatch")
        self.reader.read(record.subject)
        self.reader.read(record.context)
        # Method/category/context/need/purpose mismatches remain explicit policy reviews,
        # rather than becoming an accepted observation or a fabricated transport outage.
        return EvidenceObservation(reference, record.need, record.criterion_id, record.subject, record.method,
                                   record.context, record.category, record.issuer, record.purpose,
                                   record.authority, record.disposition)
