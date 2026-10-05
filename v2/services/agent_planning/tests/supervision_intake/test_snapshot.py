"""Independent original Planning binding; no claim to Runtime observation authority."""

import json
from dataclasses import replace

import pytest
from amphora_agent_planning.supervision_intake.commands import IncomingRequest
from amphora_agent_planning.supervision_intake.snapshot import IntakeSnapshot

from .support import FIXTURES, command, principal, request


def test_literal_request_profiles_and_exact_original_planning_bytes():
    snapshot = IntakeSnapshot.bind(request(), principal())
    assert snapshot.planning.canonical == (FIXTURES / 'planning-request.json').read_bytes()
    assert snapshot.sha256 == (FIXTURES / 'request.sha256').read_text().strip()
    assert IntakeSnapshot.from_bytes(snapshot.canonical, principal()) == snapshot
    incoming = IncomingRequest.bind(principal(), command(request()))
    assert incoming.snapshot == snapshot
    assert incoming.receipt('operation').outcome.status == 'recorded'


@pytest.mark.parametrize('path,value,reason', [
    (('planning_request', 'purpose'), 'campaign_proposal', 'supervision_purpose_mismatch'),
    (('reference', 'run_id'), 'other', 'supervision_cut_mismatch'),
    (('reference', 'scope', 'project_id'), 'other', 'supervision_scope_mismatch'),
    (('policy', 'artifact_id'), 'other', 'supervision_policy_mismatch'),
    (('snapshot', 'targets'), ['f' * 64], 'supervision_read_set_mismatch'),
    (('lineage', 'root_request_sha256'), 'f' * 64, 'supervision_root_mismatch'),
    (('lineage', 'ordinal'), 3, 'supervision_parent_missing'),
    (('planning_request', 'context', 'limits', 'total_tokens'), 1, 'insufficient_attempt_budget'),
])
def test_invalid_cross_record_claims_reject(path, value, reason):
    def change(data):
        target = data
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
    with pytest.raises(ValueError, match=reason):
        IntakeSnapshot.bind(request(change=change), principal())


def test_original_actor_digest_and_canonical_bytes_are_required():
    with pytest.raises(ValueError, match='actor_mismatch'):
        IntakeSnapshot.bind(request(), replace(principal(), actor_id='other'))
    with pytest.raises(ValueError, match='supervision_actor_mismatch'):
        IncomingRequest.bind(replace(principal(), actor_id='other'), command(request()))
    changed = request().model_copy(update={'planning_request_sha256': 'f' * 64})
    with pytest.raises(ValueError, match='planning_request_digest_mismatch'):
        IntakeSnapshot.bind(changed, principal())
    snapshot = IntakeSnapshot.bind(request(), principal())
    for raw in (snapshot.canonical + b'\n', b'{"checkpoint_id":"other",' + snapshot.canonical[1:]):
        with pytest.raises(ValueError, match='noncanonical_supervision_request'):
            IntakeSnapshot.from_bytes(raw, principal())


def test_out_of_order_wrapper_recording_does_not_prove_owned_ancestry():
    def change(data):
        data['lineage'] = {'ordinal': 2, 'root_request_sha256': 'b' * 64, 'parent_request_sha256': 'b' * 64}
    snapshot = IntakeSnapshot.bind(request(change=change), principal())
    assert snapshot.document().lineage.ordinal == 2
    data = snapshot.document().model_dump(mode='json')
    data['lineage']['parent_request_sha256'] = 'c' * 64
    with pytest.raises(ValueError, match='supervision_first_parent_mismatch'):
        IntakeSnapshot.from_bytes(json.dumps(data, sort_keys=True, separators=(',', ':')).encode(), principal())
    data['lineage']['ordinal'] = 3
    assert IntakeSnapshot.from_bytes(json.dumps(data, sort_keys=True, separators=(',', ':')).encode(), principal()).document().lineage.ordinal == 3
