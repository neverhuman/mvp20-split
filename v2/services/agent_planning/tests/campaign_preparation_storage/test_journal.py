import pytest
from amphora_agent_planning.campaign_preparations import CampaignPreparation
from amphora_agent_planning.campaign_preparations.journal import (
    CampaignPreparationJournal,
)
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.postgres


def test_registration_exact_replay_and_new_connection_readback(campaign_store):
    s = campaign_store
    reference = s.plan.request.document().reference
    with pytest.raises(ValueError, match='request_unknown'):
        s.journal.read(s.principal, reference)
    with pytest.raises(ValueError, match='request_unknown'):
        s.journal.register(s.principal, s.plan, s.packet)
    s.requests.register(s.principal, s.plan.request)
    assert s.journal.read(s.principal, reference) is None
    stored = s.journal.register(s.principal, s.plan, s.packet)
    assert stored.record == CampaignPreparation.bind(s.plan, s.packet)
    assert stored.registered_at.tzinfo is not None
    assert s.journal.register(s.principal, s.plan, s.packet) == stored
    replacement = create_engine(s.engine.url)
    try:
        assert CampaignPreparationJournal(replacement).read(s.principal, reference) == stored
    finally:
        replacement.dispose()


def test_forward_table_has_only_history_privileges(campaign_store):
    with campaign_store.engine.connect() as connection:
        assert connection.execute(text("SELECT current_user")).scalar_one() == 'planning_service'
        grants = [connection.execute(text("SELECT has_table_privilege(current_user, 'planning.campaign_preparations', :grant)"),
                                     {'grant': grant}).scalar_one() for grant in ('SELECT', 'INSERT', 'UPDATE', 'DELETE')]
        assert grants == [True, True, False, False]
