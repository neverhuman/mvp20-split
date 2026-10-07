"""Reviewed seed selection cannot widen the original request or replace readback."""

import pytest
import json
from dataclasses import replace
from types import SimpleNamespace
from amphora_agent_planning.campaign_context import ResearchContext
from amphora_agent_planning.campaign_context.records import RECORD_MODELS
from amphora_agent_planning.campaign_followup.source import FollowupResearch, FollowupSeed

from .test_prepared import prepared_inputs


def seed_source():
    plan, preparation, _ = prepared_inputs()
    from amphora_agent_planning.campaign_followup.prepared import FollowupPreparation
    selected = FollowupPreparation.bind(preparation).criteria.document()
    seed = FollowupSeed(budget_template=plan.request.document().context.policy,
        criteria=selected.criteria, focus_artifact=selected.focus_artifact)
    return plan, seed


def test_duplicate_seeds_and_non_tuple_configuration_reject_before_reads():
    _, seed = seed_source()
    with pytest.raises(ValueError, match='followup_seed_duplicate'):
        FollowupResearch.bind(None, (seed, seed))
    with pytest.raises(ValueError, match='followup_seed_count'):
        FollowupResearch.bind(None, [seed])


def test_seed_uses_exact_template_identity_not_shared_label():
    plan, seed = seed_source()
    source = FollowupResearch.bind(None, (seed,))
    wrong = seed.budget_template.model_copy(update={'sha256': 'f' * 64})
    with pytest.raises(ValueError, match='budget_template_unavailable'):
        source.extend(plan, wrong)


def test_copied_criteria_cannot_bypass_original_selection_policy():
    plan, seed = seed_source()
    bad = seed.model_copy(update={'criteria': (*seed.criteria, *seed.criteria)})
    source = FollowupResearch.bind(None, (bad,))
    with pytest.raises(ValueError, match='followup_duplicate_criterion'):
        source.extend(plan, seed.budget_template)


def test_assessed_seed_reconstructs_exact_public_records_without_losing_the_assessment():
    plan, seed = seed_source()
    payload = json.loads(next(row for row in plan.slices if row.lane == 'research').payload)
    groups = {'question': [], 'need': [], 'assessment': []}
    for row in payload['context']['records']:
        kind = row['identity']['kind']
        groups[kind].append(RECORD_MODELS[kind].model_validate_json(json.dumps(row['record'])))
    class Reader:
        def review(self, selection):
            context = ResearchContext.bind(selection, questions=tuple(groups['question']),
                needs=tuple(groups['need']), assessments=tuple(groups['assessment']))
            return SimpleNamespace(context=context, failures=())
    base = replace(plan, slices=tuple(row for row in plan.slices if row.lane != 'research'),
        families=tuple(name for name in plan.families if name != 'research'))
    result = FollowupResearch.bind(Reader(), (seed,)).extend(base, seed.budget_template)
    assert result == plan
    assert seed.criteria[0].assessment is not None
