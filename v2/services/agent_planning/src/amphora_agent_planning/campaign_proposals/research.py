"""Reconstruct consumed Research meaning before trusting evidence-purpose links."""

from dataclasses import dataclass

from ..campaign_context import (
    ResearchContext,
    ResearchGap,
    ResearchIdentity,
    ResearchSelection,
)
from ..campaign_context.records import RECORD_MODELS, REFERENCE_MODELS, canonical
from ..context.policy import require
from .observations import ObservationKey


def fields(value, expected):
    require(type(value) is dict and set(value) == set(expected), 'campaign_research_context_fields')


@dataclass(frozen=True)
class ConsumedResearch:
    context: ResearchContext

    @classmethod
    def from_proposal(cls, prepared):
        rows = [row for row in prepared.inputs.preparation.packet.context()['slices'] if row['lane'] == 'research']
        if not rows:
            return None
        require(len(rows) == 1, 'campaign_research_slice_count')
        row = rows[0]
        payload = row['payload']
        require(set(payload) == {'format', 'selection', 'context'} and
                payload['format'] == 'planning-campaign-research-slice.v1', 'campaign_research_slice_profile')
        selection = ResearchSelection.from_bytes(canonical(payload['selection']), prepared.attempt.request)
        require(row['identity'] == {'selection': selection.sha256}, 'campaign_research_slice_identity')
        value = payload['context']
        fields(value, ('format', 'authority', 'selection_sha256', 'records', 'gaps', 'findings'))
        require(all(type(value[name]) is list and len(value[name]) <= limit
                    for name, limit in (('records', 160), ('gaps', 160), ('findings', 8192))),
                'campaign_research_context_count')
        groups = {'question': [], 'need': [], 'assessment': []}
        gaps = []
        for record in value['records']:
            fields(record, ('identity', 'record'))
            fields(record['identity'], ('kind', 'reference'))
            kind = record['identity']['kind']
            require(type(kind) is str and kind in RECORD_MODELS, 'campaign_record_kind')
            groups[kind].append(RECORD_MODELS[kind].model_validate_json(canonical(record['record'])))
        for gap in value['gaps']:
            fields(gap, ('identity', 'reason'))
            fields(gap['identity'], ('kind', 'reference'))
            kind = gap['identity']['kind']
            require(type(kind) is str and kind in REFERENCE_MODELS, 'campaign_record_kind')
            require(type(gap['reason']) is str, 'campaign_research_gap_reason')
            reference = REFERENCE_MODELS[kind].model_validate_json(canonical(gap['identity']['reference']))
            gaps.append(ResearchGap(ResearchIdentity.bind(kind, reference), gap['reason']))
        context = ResearchContext.bind(selection, questions=tuple(groups['question']), needs=tuple(groups['need']),
                                       assessments=tuple(groups['assessment']), unavailable=tuple(gaps))
        require(context.canonical == canonical(value), 'campaign_research_context_reconstruction')
        actual = {entry.key: entry.sha256 for entry in prepared.inputs.entries if entry.key.lane == 'research'}
        expected = {cls.key(entry.identity): entry.observation_sha256 for entry in context.read_set().entries}
        require(actual == expected, 'campaign_research_observation_reconstruction')
        return cls(context)

    @staticmethod
    def key(identity):
        return ObservationKey('research', 'record', canonical(identity.document()))

    def selected(self, kind, reference):
        identity = ResearchIdentity.bind(kind, reference)
        require(any(entry.identity == identity for entry in self.context.read_set().entries),
                'campaign_evidence_reference_unselected')
        return identity

    def record(self, identity):
        return next((entry.document() for entry in self.context.records if entry.identity == identity), None)
