"""Strict wire shape only; Runtime tests own cross-record binding."""

import json
from pathlib import Path

import pytest
from amphora_contracts_supervision import SupervisionRequest
from pydantic import ValidationError

FIXTURE = Path(__file__).parent / 'fixtures/request.json'


def test_request_roundtrip_is_immutable_and_carries_distinct_identities():
    request = SupervisionRequest.model_validate_json(FIXTURE.read_bytes())
    assert SupervisionRequest.model_validate_json(request.model_dump_json()) == request
    assert type(request.snapshot.reads) is tuple
    assert len({request.planning_request.decision_scope, request.snapshot.footprint_sha256,
                request.snapshot.relevant_sha256}) == 3
    with pytest.raises(ValidationError):
        request.deadline_unix_ms = 0


@pytest.mark.parametrize('path,value', [
    (('schema_version',), '2'), (('deadline_unix_ms',), True), (('deadline_unix_ms',), '123'),
    (('deadline_unix_ms',), 0), (('deadline_unix_ms',), 9007199254740992),
    (('lineage', 'ordinal'), 0), (('lineage', 'ordinal'), 17), (('lineage', 'ordinal'), True),
    (('lineage', 'root_request_sha256'), 'not-a-digest'), (('snapshot', 'targets'), []),
    (('snapshot', 'reads'), []), (('snapshot', 'targets'), ['a' * 64] * 65),
    (('planning_request_sha256',), 'ABC'), (('accepted',), True),
    (('planning_request', 'context', 'model', 'endpoint'), 'https://unreviewed.invalid'),
])
def test_invalid_wire_shapes_reject(path, value):
    document = json.loads(FIXTURE.read_bytes())
    target = document
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValidationError):
        SupervisionRequest.model_validate_json(json.dumps(document))


def test_wire_does_not_claim_lineage_or_hash_verification():
    document = json.loads(FIXTURE.read_bytes())
    document['planning_request_sha256'] = 'f' * 64
    document['lineage']['ordinal'] = 2
    # Valid transport shape is intentionally not a Runtime decision grant.
    assert SupervisionRequest.model_validate_json(json.dumps(document)).lineage.ordinal == 2
