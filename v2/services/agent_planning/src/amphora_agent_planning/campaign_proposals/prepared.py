"""Bind exact output and historical inputs without asserting fresh eligibility."""

import hashlib
from dataclasses import dataclass

from ..campaign_context.records import canonical
from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from ..campaign_output import CampaignOutput
from ..curation_output import CurationOutput
from ..context import AttemptBinding
from ..context.policy import require
from ..persistence.records import verified_observation
from ..providers.capture import Observation
from .observations import ObservedInputs


@dataclass(frozen=True)
class PreparedCampaignProposal:
    inputs: ObservedInputs
    attempt: AttemptBinding
    observation: Observation
    output: CampaignOutput | CurationOutput

    @classmethod
    def bind(cls, preparation, attempt, observation):
        inputs = ObservedInputs.bind(preparation)
        request = inputs.preparation.packet.request
        require(request == attempt.request, 'campaign_proposal_request')
        attempt = AttemptBinding(request, attempt.ordinal)
        observation = verified_observation(attempt, observation)
        require(observation.document().status in {'proposed', 'abstained'}, 'campaign_proposal_not_available')
        parser = CurationOutput if request.document().context.output_schema == campaign_curation_draft_schema() else CampaignOutput
        output = parser.parse(observation.capture.content, request)
        require(output.proposal() == observation.document().proposal, 'campaign_proposal_output')
        return cls(inputs, attempt, observation, output)

    def review_document(self):
        return self.output.review_document() if isinstance(self.output, CurationOutput) else self.output.document()

    @property
    def sha256(self):
        require(self.bind(self.inputs.preparation, self.attempt, self.observation) == self,
                'campaign_proposal_binding')
        value = {'profile': 'planning-prepared-campaign-proposal.v1',
                 'preparation_sha256': self.inputs.preparation.sha256,
                 'attempt': self.attempt.reference().model_dump(mode='json'),
                 'observation_sha256': hashlib.sha256(self.observation.canonical).hexdigest(),
                 'capture_sha256': self.observation.capture.sha256, 'output_sha256': self.output.sha256}
        return hashlib.sha256(canonical(value)).hexdigest()
