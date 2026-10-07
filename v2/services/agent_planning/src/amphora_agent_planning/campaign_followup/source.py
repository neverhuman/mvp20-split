"""Reviewed selection seeds; public Research reads precede immutable preparation."""

from dataclasses import dataclass
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, WireModel
from amphora_contracts_planning import CampaignCriterionRef, CampaignFollowupSelection
from pydantic import Field

from ..campaign_context import ResearchSelection
from ..context.policy import require
from .policy import canonical


class FollowupSeed(WireModel):
    profile: Literal['planning-followup-seed.v1'] = 'planning-followup-seed.v1'
    budget_template: ArtifactRef
    criteria: Annotated[tuple[CampaignCriterionRef, ...], Field(max_length=64)]
    focus_artifact: ArtifactRef | None


@dataclass(frozen=True)
class FollowupResearch:
    reader: object
    seeds: tuple[bytes, ...]

    @classmethod
    def bind(cls, reader, seeds):
        require(type(seeds) is tuple and len(seeds) <= 64, 'followup_seed_count')
        checked = tuple(FollowupSeed.model_validate_json(item.model_dump_json()) for item in seeds)
        require(len({item.budget_template for item in checked}) == len(checked), 'followup_seed_duplicate')
        return cls(reader, tuple(canonical(item.model_dump(mode='json')) for item in checked))

    def extend(self, plan, budget_template):
        seeds = tuple(FollowupSeed.model_validate_json(raw) for raw in self.seeds)
        selected = [seed for seed in seeds if seed.budget_template == budget_template]
        require(len(selected) == 1, 'budget_template_unavailable')
        seed = selected[0]
        require(budget_template.scope == plan.request.document().reference.scope, 'followup_seed_scope')
        # Stable first occurrence order; the full selection policy rejects duplicate
        # criteria and inconsistent assessments before any public owner call.
        selection = CampaignFollowupSelection(engagement=plan.request.document().reference,
            request_sha256=plan.request.sha256,
            questions=tuple(dict.fromkeys(item.question for item in seed.criteria)),
            needs=tuple(dict.fromkeys(item.need for item in seed.criteria)),
            assessments=tuple(dict.fromkeys(item.assessment for item in seed.criteria if item.assessment is not None)),
            criteria=seed.criteria, focus_artifact=seed.focus_artifact)
        bound = ResearchSelection.bind(selection, plan.request)
        report = self.reader.review(bound)
        require(report.context.selection == bound, 'followup_reader_selection')
        require(not report.failures, 'execution_processing_unavailable')
        return plan.with_research(report.context)
