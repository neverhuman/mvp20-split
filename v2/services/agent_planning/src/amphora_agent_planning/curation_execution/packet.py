"""Current processing authorization never changes originally retained input."""
from amphora_contracts_core import ArtifactRef
from ..campaign_data_access import ArtifactSelection, CampaignArtifactReader
from ..context.policy import require
from ..source_access import ReadBudget


def authorize(frozen, data):
    refs = tuple(ArtifactRef.model_validate(row['identity']) for row in frozen.preparation.packet.context()['slices']
        if row['lane'] == 'artifact' and row['payload']['status'] == 'available')
    reader, budget = CampaignArtifactReader(data), ReadBudget()
    for start in range(0, len(refs), 128):
        selected = ArtifactSelection.bind(frozen.preparation.packet.request, refs[start:start + 128])
        result = reader.read(selected, budget)
        require(not result.failures, 'curation_processing_unavailable')


class CurationProvider:
    def __init__(self, provider, frozen, guard, deadline):
        self.provider, self.frozen, self.guard, self.deadline = provider, frozen, guard, deadline

    def supports(self, model):
        return self.provider.supports(model)

    def reply(self, binding):
        require(binding.ordinal == 1 and binding.request == self.frozen.preparation.packet.request,
                'curation_provider_original_input')
        self.guard()
        return self.provider.reply(binding, self.frozen.preparation.packet.canonical, deadline_unix_ms=self.deadline)
