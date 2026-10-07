"""Real Runtime SQL retains future intent without changing active field bindings."""

import pytest
from sqlalchemy import text
from amphora_campaign_runtime.supervision_context.preparation import ContextPreparer
from amphora_campaign_runtime.supervision_winners import WinnerStore
from amphora_contracts_planning import checkpoint_followup_draft_schema

from ..supervision_context.test_preparation import prepared
from ..supervision_winners.support import prepare, setup
from .support import draft

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('action,kind', [('abstain', 'abstained'), ('request_evidence', 'evidence_request'),
    ('propose_campaign', 'future_campaign')])
def test_accepted_followup_is_only_a_retained_proposal_and_exact_replay(graph_env, action, kind):
    store, actor, ref, slot = setup(graph_env)
    def change(value):
        value.update(draft(actor.scope.model_dump(mode='json'), value['decision_scope'], action=action,
            definition=graph_env.entry.plan.document.definition.model_dump(mode='json')))
    response = prepare(graph_env, actor, ref, slot, mutation=change, followup=True)
    result = store.resolve(actor, ref, response_id=response)
    assert result.document().outcome.effect.kind == kind
    assert result.selection is None
    assert WinnerStore(graph_env.env.engine).read(actor, ref) == result
    assert store.resolve(actor, ref, response_id=response) == result
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.binding_intents WHERE run_id=:run'),
            {'run': ref.run_id}).scalar_one() == 0


def test_admitted_followup_recipe_generates_new_profile_and_replays_original_context(graph_env):
    actor, ref, _, artifacts, preparer = prepared(graph_env, followup=True)
    original = preparer.prepare(actor, ref)
    assert original.frame.request.planning_request.context.output_schema == checkpoint_followup_draft_schema()
    replacement = ContextPreparer(graph_env.env.engine, preparer.journal.planning_actors, artifacts)
    assert replacement.prepare(actor, ref) == original
    assert len(artifacts.calls) == 2
