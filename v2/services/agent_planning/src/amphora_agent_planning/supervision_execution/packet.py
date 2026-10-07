"""Original checkpoint packet binding and fresh included-Artifact permission."""

import base64
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_planning import checkpoint_followup_draft_schema

from ..campaign_data_access import ArtifactSelection, CampaignArtifactReader
from ..campaign_preparations.record import CampaignPreparation
from ..campaign_followup.prepared import FollowupPreparation
from ..campaign_followup.output import FollowupOutput
from ..context.policy import require
from ..source_access import ReadBudget
from .context import CheckpointContextBinding


@dataclass(frozen=True)
class CheckpointPacket:
    preparation: CampaignPreparation
    context: CheckpointContextBinding

    @classmethod
    def bind(cls, intake, principal, stored):
        record = CampaignPreparation.from_bytes(intake.planning, stored.canonical, stored.packet.canonical)
        slices = record.packet.context()['slices']
        followup = intake.planning.document().context.output_schema == checkpoint_followup_draft_schema()
        lanes = {'artifact', 'research'} if followup else {'artifact'}
        require(all(row['lane'] in lanes for row in slices), 'execution_packet_lanes')
        if followup:
            FollowupPreparation.bind(record)
        declaration = [row for row in slices if row['lane'] == 'artifact' and
            row['identity']['sha256'] == intake.planning.document().decision_scope]
        require(len(declaration) == 1, 'execution_packet_context')
        row = declaration[0]
        ref = ArtifactRef.model_validate(row['identity'])
        bound = CheckpointContextBinding.bind(intake, principal, ref,
            base64.b64decode(row['payload']['body_base64'], validate=True))
        return cls(record, bound)

    def authorize(self, data):
        """Historical omissions remain omissions; every included body needs fresh rights."""
        refs = tuple(ArtifactRef.model_validate(row['identity']) for row in
            self.preparation.packet.context()['slices'] if row['lane'] == 'artifact' and row['payload']['status'] == 'available')
        reader, budget = CampaignArtifactReader(data), ReadBudget()
        for start in range(0, len(refs), 128):
            selected = ArtifactSelection.bind(self.preparation.packet.request, refs[start:start + 128])
            result = reader.read(selected, budget)
            require(not result.failures, 'execution_processing_unavailable')


class CheckpointProvider:
    """Configured adapter receives exact bytes and the immutable absolute deadline."""

    def __init__(self, provider, packet, guard):
        self.provider, self.packet, self.guard = provider, packet, guard

    def supports(self, model):
        return self.provider.supports(model)

    def validate_output(self, raw):
        request = self.packet.preparation.packet.request
        if request.document().context.output_schema == checkpoint_followup_draft_schema():
            FollowupPreparation.bind(self.packet.preparation).validate_output(FollowupOutput.parse(raw, request))

    def reply(self, binding):
        require(binding.request.canonical == self.packet.preparation.packet.request.canonical,
                'execution_provider_request')
        deadline = self.guard(binding)
        return self.provider.reply(binding, self.packet.preparation.packet.canonical,
            deadline_unix_ms=deadline)
