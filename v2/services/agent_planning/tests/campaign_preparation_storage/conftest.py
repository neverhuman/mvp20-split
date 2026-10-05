import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.campaign_packet import prepare
from amphora_agent_planning.campaign_preparations.journal import (
    CampaignPreparationJournal,
)
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_contracts_core import Scope
from sqlalchemy import create_engine

from ..campaign_packet.replay_probe import source


@pytest.fixture
def campaign_store(planning_database):
    value = json.loads((Path(__file__).parents[1] / 'campaign_packet/fixtures/predecessor-v1.json').read_bytes())
    scope = Scope(tenant_id='planning-campaign-journal', project_id=uuid.uuid4().hex)

    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}:
                value.update(scope.model_dump(mode='json'))
            for item in value.values():
                rescope(item)
        elif isinstance(value, list):
            for item in value:
                rescope(item)

    rescope(value['request'])
    plan = source(value)
    packet = prepare(plan).packet
    principal = Principal(plan.request.document().actor_id, scope, frozenset({'record_requests', 'record_attempts', 'read_attempts'}))
    engine = create_engine(planning_database, connect_args={'options': '-c statement_timeout=5000'})
    yield SimpleNamespace(plan=plan, packet=packet, principal=principal, engine=engine,
        journal=CampaignPreparationJournal(engine), requests=PlanningJournal(engine), binding=AttemptBinding(plan.request, 1))
    engine.dispose()
