"""Exact retained selection/record/output linkage, separate from fresh authorization."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_planning import CampaignFollowupSelection

from ..campaign_proposals.observations import ObservedInputs
from ..campaign_proposals.evidence import EvidenceLinks
from ..campaign_proposals.research import ConsumedResearch
from ..context import AttemptBinding
from ..context.policy import require
from ..persistence.records import verified_observation
from ..providers.capture import Observation
from .output import FollowupOutput
from .policy import CriterionBindings, canonical


@dataclass(frozen=True)
class FollowupPreparation:
    inputs: ObservedInputs
    criteria: CriterionBindings

    @classmethod
    def bind(cls, preparation):
        inputs = ObservedInputs.bind(preparation)
        research = ConsumedResearch.from_inputs(inputs, inputs.preparation.packet.request)
        require(research is not None, 'followup_research_missing')
        selected = research.context.selection.document()
        require(isinstance(selected, CampaignFollowupSelection), 'followup_selection_profile')
        groups = {'question': [], 'need': [], 'assessment': []}
        for row in research.context.records:
            groups[row.identity.kind].append(row.document())
        criteria = CriterionBindings.bind(selected, questions=tuple(groups['question']),
            needs=tuple(groups['need']), assessments=tuple(groups['assessment']))
        if selected.focus_artifact is not None:
            require(any(row['lane'] == 'artifact' and
                row['identity'] == selected.focus_artifact.model_dump(mode='json') and
                row['payload']['status'] == 'available'
                for row in inputs.preparation.packet.context()['slices']), 'followup_focus_not_consumed')
        return cls(inputs, criteria)

    def validate_output(self, output):
        retained = self.bind(self.inputs.preparation)
        require(retained == self, 'followup_preparation_binding')
        request = retained.inputs.preparation.packet.request
        output = FollowupOutput.parse(output.canonical, request)
        retained.criteria.validate_output(output.document())
        research = ConsumedResearch.from_inputs(retained.inputs, request)
        links = EvidenceLinks(research)
        draft = output.document()
        groups = [('/evidence_requests', draft.evidence_requests)]
        if draft.candidate is not None:
            groups.append(('/candidate/expected_evidence', draft.candidate.expected_evidence))
        for path, intents in groups:
            for index, intent in enumerate(intents):
                links.intent(intent, path + '/' + str(index))
        return output


@dataclass(frozen=True)
class PreparedFollowupProposal:
    preparation: FollowupPreparation
    attempt: AttemptBinding
    observation: Observation
    output: FollowupOutput

    @classmethod
    def bind(cls, preparation, attempt, observation):
        retained = FollowupPreparation.bind(preparation)
        request = retained.inputs.preparation.packet.request
        require(request == attempt.request, 'followup_proposal_request')
        attempt = AttemptBinding(request, attempt.ordinal)
        observed = verified_observation(attempt, observation)
        require(observed.document().status in {'proposed', 'abstained'}, 'followup_proposal_unavailable')
        output = FollowupOutput.parse(observed.capture.content, request)
        retained.validate_output(output)
        require(output.proposal() == observed.document().proposal, 'followup_proposal_output')
        return cls(retained, attempt, observed, output)

    @property
    def sha256(self):
        require(self.bind(self.preparation.inputs.preparation, self.attempt, self.observation) == self,
                'followup_proposal_binding')
        value = {'profile': 'planning-prepared-followup-proposal.v1',
            'preparation_sha256': self.preparation.inputs.preparation.sha256,
            'selection_sha256': hashlib.sha256(self.preparation.criteria.selection_bytes).hexdigest(),
            'attempt': self.attempt.reference().model_dump(mode='json'),
            'observation_sha256': hashlib.sha256(self.observation.canonical).hexdigest(),
            'capture_sha256': self.observation.capture.sha256, 'output_sha256': self.output.sha256}
        return hashlib.sha256(canonical(value)).hexdigest()
