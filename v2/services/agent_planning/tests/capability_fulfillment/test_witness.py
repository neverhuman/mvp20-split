from datetime import UTC, datetime
import base64
import json

import pytest

from amphora_agent_planning.campaign_context.records import canonical
from amphora_agent_planning.capability_acceptance.review import AcceptanceReview
from amphora_agent_planning.capability_fulfillment.original import OriginalFulfillment
from amphora_agent_planning.capability_fulfillment.witness import VerificationWitness
from amphora_agent_planning.curation_intake.commands import FulfillmentCommand
from ..capability_acceptance.test_review import case, evidence


def example():
    capability, release, report = case()
    spec, processed = evidence(capability, release, report)
    raw = {'encoding': 'amphora-command-v2', 'identity': {'scope': capability.curation.scope.model_dump(),
        'actor_id': 'owner', 'command_family': 'planning.fulfill_capability', 'command_id': 'fulfill'},
        'payload': spec.model_dump(mode='json')}
    original = OriginalFulfillment(FulfillmentCommand.restore(json.dumps(raw)), capability, datetime.now(UTC))
    review = AcceptanceReview.bind(capability, spec, release, processed)
    return original, review


def test_witness_replays_exact_original_report_and_json_registry_snapshot():
    original, review = example()
    witness = VerificationWitness.capture(original, review)
    witness.validate(original)
    record = json.loads(witness.canonical)
    assert base64.b64decode(record['report_base64']) == review.evidence[0].body
    assert record['processed_evidence'] == [item.reference.model_dump(mode='json') for item in review.evidence]
    assert set(record) == {'profile', 'command_sha256', 'release', 'report_base64', 'processed_evidence'}


@pytest.mark.parametrize('fault', ['command', 'missing_evidence', 'report', 'release', 'profile', 'extra'])
def test_replay_rejects_rebound_or_incomplete_retained_facts(fault):
    original, review = example()
    record = json.loads(VerificationWitness.capture(original, review).canonical)
    if fault == 'command': record['command_sha256'] = 'f' * 64
    if fault == 'missing_evidence': record['processed_evidence'] = []
    if fault == 'report': record['report_base64'] = base64.b64encode(b'{}').decode()
    if fault == 'release': record['release']['lock']['descriptor_sha256'] = 'f' * 64
    if fault == 'profile': record['profile'] = 'invented'
    if fault == 'extra': record['current_eligibility'] = True
    with pytest.raises(ValueError): VerificationWitness(canonical(record)).validate(original)
