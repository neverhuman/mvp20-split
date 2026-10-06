"""Actual winner and selected-state write fences, without fabricated owner rows."""

from dataclasses import replace

import pytest
from amphora_campaign_runtime.supervision_journal.delivery import DeliveryJournal
from amphora_campaign_runtime.supervision_journal.storage import RequestJournal
from sqlalchemy import text

from ..supervision_winners.support import prepare, setup
from .test_worker import fixture

__all__ = ['fixture']


def test_selected_observation_change_prevents_new_write(fixture):
    f = fixture
    def change():
        with f.engine.begin() as conn:
            conn.execute(text('UPDATE runtime.graph_nodes SET state=state || CAST(:change AS jsonb) '
                'WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run'),
                {**f.params, 'change': '{"fixture_change":true}'})
    f.before_absent = change
    with pytest.raises(ValueError, match='selected_observation_changed'):
        f.tick()
    assert not f.saved and len(f.records) == 1


def test_committed_model_winner_fences_later_dispatch(graph_env):
    winners, actor, reference, slot = setup(graph_env)
    actor = replace(actor, actions=actor.actions | {'supervise_dispatch'})
    response_id = prepare(graph_env, actor, reference, slot)
    requests = RequestJournal(graph_env.env.engine, {
        (actor.scope.tenant_id, actor.scope.project_id, actor.actor_id): 'fixture'})
    stored = requests.series(actor, reference.run_id, reference.decision_id)[0]
    delivery = DeliveryJournal(requests)
    lease = delivery.claim(actor, reference, stored.frame.request_sha256, event_id='original-claim')
    delivery.guard(actor, lease)
    winner = winners.resolve(actor, reference, response_id=response_id)
    assert winner.document().outcome.kind == 'model_accepted'
    with pytest.raises(ValueError, match='delivery_winner_committed'):
        delivery.guard(actor, lease)
