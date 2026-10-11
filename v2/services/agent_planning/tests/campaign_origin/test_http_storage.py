"""Configured read route traverses actual owned SQL, under viewer scope only."""

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from amphora_agent_planning.supervision_api import Credentials, create_app
from amphora_agent_planning.supervision_intake import SupervisionIntake
from amphora_contracts_planning import CampaignOriginV2

from .test_storage import prepared
from ..campaign_dispatch_storage.test_journal import observed

pytestmark = pytest.mark.postgres


def test_configured_origin_route_and_foreign_scope(stored):
    _, journal, lease, operation, accepted, draft, viewer = prepared(stored)
    terminal = observed(journal, stored.principal, lease, operation, accepted.receipt, accepted.readback)
    foreign = replace(viewer, scope=viewer.scope.model_copy(update={'project_id': 'unrelated-project'}))
    credentials = Credentials((('v' * 32, viewer), ('f' * 32, foreign)))
    http = TestClient(create_app(SupervisionIntake(stored.engine), credentials))
    path = f'/v1/campaign-origins/{draft.draft_id}?revision=1&content_sha256={draft.content_sha256}'
    result = http.get(path, headers={'Authorization': 'Bearer ' + 'v' * 32})
    assert result.status_code == 200
    value = CampaignOriginV2.model_validate_json(result.content)
    assert value.origin.draft == draft and value.origin.save.receipt == accepted.receipt
    assert http.get(path, headers={'Authorization': 'Bearer ' + 'f' * 32}).status_code == 404
    assert journal.read(stored.principal, lease.selection.effect_id, operation.effect.effect_id) == terminal
