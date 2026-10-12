"""Exact claimed evidence purposes; uncertainty remains distinct from eligibility."""

from dataclasses import dataclass

from ..context.policy import require
from .observations import RelevantReadSet
from .prepared import PreparedCampaignProposal
from .research import ConsumedResearch


@dataclass(frozen=True)
class EvidenceFinding:
    path: str
    code: str


class EvidenceLinks:
    def __init__(self, research):
        self.research = research
        self.keys = set()
        self.findings = []

    def reference(self, kind, reference, path):
        require(self.research is not None, 'campaign_evidence_context_missing')
        identity = self.research.selected(kind, reference)
        self.keys.add(self.research.key(identity))
        record = self.research.record(identity)
        if record is None:
            self.findings.append(EvidenceFinding(path, kind + '_unavailable'))
        return record

    def need(self, reference, question, path):
        need = self.reference('need', reference, path)
        if need is not None and question is not None:
            require(need.question == question, 'campaign_evidence_need_question')

    def intent(self, intent, path):
        self.reference('question', intent.question, path + '/question')
        require(len(set(intent.needs)) == len(intent.needs), 'campaign_evidence_duplicate_need')
        for index, need in enumerate(intent.needs):
            self.need(need, intent.question, path + '/needs/' + str(index))
        seen = set()
        for index, assessment in enumerate(intent.assessments):
            identity = self.research.selected('assessment', assessment.request)
            require(identity not in seen, 'campaign_evidence_duplicate_assessment')
            seen.add(identity)
            require(assessment in self.research.context.selection.document().assessments,
                    'campaign_evidence_assessment_pin')
            require(assessment.request.question == intent.question, 'campaign_evidence_assessment_question')
            self.reference('assessment', assessment.request, path + '/assessments/' + str(index))
        if intent.producer is not None:
            # Authored/current Runtime address resolution is the composition unit.
            self.findings.append(EvidenceFinding(path + '/producer', 'producer_resolution_required'))


@dataclass(frozen=True)
class EvidencePurposeReview:
    proposal: PreparedCampaignProposal
    research: ConsumedResearch | None
    read_set: RelevantReadSet
    findings: tuple[EvidenceFinding, ...]

    @classmethod
    def bind(cls, prepared):
        verified = PreparedCampaignProposal.bind(prepared.inputs.preparation, prepared.attempt, prepared.observation)
        require(verified == prepared, 'campaign_proposal_binding')
        research = ConsumedResearch.from_proposal(verified)
        links = EvidenceLinks(research)
        draft = verified.review_document()
        groups = [('/evidence_requests', draft.evidence_requests)]
        if draft.candidate is not None:
            groups.append(('/candidate/expected_evidence', draft.candidate.expected_evidence))
        for path, intents in groups:
            for index, intent in enumerate(intents):
                links.intent(intent, path + '/' + str(index))
        for index, point in enumerate(draft.unresolved):
            path = '/unresolved/' + str(index)
            if point.question is not None:
                links.reference('question', point.question, path + '/question')
            if point.need is not None:
                links.need(point.need, point.question, path + '/need')
        return cls(verified, research, verified.inputs.select(links.keys), tuple(links.findings))
