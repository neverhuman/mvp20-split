"""Mandatory-first bounded batches with one fresh shared processing-read budget."""

from dataclasses import dataclass

from ..campaign_data_access import ArtifactSelection, CampaignArtifactReader
from ..campaign_data_access.reader import STOP_CODES
from ..context.policy import require
from ..source_access import ReadBudget
from .plan import ArtifactContextPlan
from .projection import ArtifactContextItem, ArtifactContextProjection


@dataclass(frozen=True)
class ArtifactContextRead:
    projection: ArtifactContextProjection
    calls: int
    bytes: int


class CampaignArtifactContextReader:
    def __init__(self, data):
        self.reader = CampaignArtifactReader(data)

    def read(self, request, budget=None):
        plan = ArtifactContextPlan.bind(request)
        budget = ReadBudget() if budget is None else budget
        require(isinstance(budget, ReadBudget), 'campaign_artifact_context_budget')
        calls, consumed = budget.calls, budget.consumed
        outcomes, stopped = {}, None
        eligible = []
        for item in plan.items:
            if item.reference.size_bytes > 4194304:
                outcomes[item.reference.artifact_id] = ArtifactContextItem.unavailable(item, 'source_artifact_size')
            else:
                eligible.append(item)
        for start in range(0, len(eligible), 128):
            batch = eligible[start:start + 128]
            if stopped is not None:
                for item in batch:
                    outcomes[item.reference.artifact_id] = ArtifactContextItem.unavailable(item, stopped)
                continue
            selection = ArtifactSelection.bind(plan.request, tuple(item.reference for item in batch))
            result = self.reader.read(selection, budget)
            bodies = {row.reference.artifact_id: row.body for row in result.records}
            failures = {row.reference.artifact_id: row.code for row in result.failures}
            for item in batch:
                key = item.reference.artifact_id
                if key in bodies:
                    outcomes[key] = ArtifactContextItem.available(item, bodies[key])
                else:
                    reason = failures[key]
                    outcomes[key] = ArtifactContextItem.unavailable(item, reason)
                    if reason in STOP_CODES:
                        stopped = reason
        projection = ArtifactContextProjection.bind(plan, tuple(outcomes[item.reference.artifact_id] for item in plan.items))
        return ArtifactContextRead(projection, budget.calls - calls, budget.consumed - consumed)
