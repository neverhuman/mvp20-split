"""Actual socket protocol with exact v2 command recovery and no silent fallback."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_campaign_runtime.supervision_client import (
    CheckpointPlanningClient,
    ExchangeUnavailable,
    ExchangeWindow,
)
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_supervision import (
    CheckpointRequest,
    SupervisionCommandReceipt,
    parse_checkpoint_command,
)

from ..supervision_outcomes.test_reported import report
from .test_client import TOKEN, peer

__all__ = ['peer']

FIXTURES = Path(__file__).absolute().parents[4] / 'contracts/supervision/tests/fixtures'


def checkpoint(peer):
    peer.command = parse_checkpoint_command((FIXTURES / 'checkpoint-command.json').read_bytes())
    raw = (FIXTURES / 'checkpoint-request.json').read_bytes()
    peer.payload = CheckpointRequest.model_validate_json(raw)
    peer.receipt = SupervisionCommandReceipt.model_validate({'outcome': {'status': 'recorded', 'binding': {
        'identity': peer.command.identity, 'request_sha256': peer.command.sha256, 'operation_id': 'fixture-record'},
        'committed': {'kind': 'request', 'object_id': peer.payload.planning_request.reference.engagement_id,
                      'revision': 1, 'content_sha256': hashlib.sha256(raw).hexdigest()}}})
    return CheckpointPlanningClient(peer.command.identity.actor_id, peer.command.identity.scope, peer.endpoint, TOKEN)


def test_exact_v2_routes_and_old_client_rejection(peer):
    client = checkpoint(peer)
    window = ExchangeWindow()
    guarded = []
    saved = client.submit(peer.command, window, guard=lambda: guarded.append(True))
    observed = client.receipt(peer.command, window, previous=saved)
    assert client.readback(peer.command, observed, window).status == 'recorded'
    assert guarded == [True, True]
    assert [item[1] for item in peer.records] == ['/v2/supervision/requests', '/v2/supervision/receipts/query',
        '/v2/supervision/requests/' + peer.payload.planning_request.reference.engagement_id]
    assert peer.records[0][2] == peer.records[1][2] == peer.command.canonical_bytes
    with pytest.raises(CommandEncodingError):
        peer.client.submit(peer.command, ExchangeWindow(), guard=lambda: None)
    assert len(peer.records) == 3


def test_lost_v2_reply_recovers_without_reposting_or_switching_family(peer):
    client = checkpoint(peer)
    peer.drop = True
    with pytest.raises(ExchangeUnavailable, match='write_uncertain'):
        client.submit(peer.command, ExchangeWindow(), guard=lambda: None)
    peer.drop = False
    receipt = client.receipt(peer.command, ExchangeWindow())
    assert client.readback(peer.command, receipt, ExchangeWindow()).status == 'recorded'
    assert sum(item[1] == '/v2/supervision/requests' for item in peer.records) == 1
    assert len(peer.records) == 3


def test_execution_report_is_exact_read_only_owner_evidence(peer):
    client = checkpoint(peer)
    data = report(peer.payload)
    peer.override = json.dumps(data).encode()
    result = client.execution(peer.command, ExchangeWindow())
    assert result.document().stop_reason == 'provider_unconfigured'
    assert peer.records[0][:3] == ('GET', '/v2/supervision/execution/' +
        peer.payload.planning_request.reference.engagement_id, None)
    data['request_sha256'] = 'f' * 64
    peer.override = json.dumps(data).encode()
    with pytest.raises(ValueError, match='execution_report_request'):
        client.execution(peer.command, ExchangeWindow())
    assert all(item[0] == 'GET' for item in peer.records)
