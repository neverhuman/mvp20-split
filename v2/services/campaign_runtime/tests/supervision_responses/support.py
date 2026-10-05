"""Original public fixtures; no private Planning implementation in Runtime tests."""

import hashlib
import json
from pathlib import Path

from amphora_campaign_runtime.supervision_requests import SupervisionRequestBinding
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_scope import (
    DecisionFootprint,
    NodeObservation,
)
from amphora_contracts_supervision import SupervisionRequest, SupervisionResponse

FIXTURES = Path(__file__).absolute().parents[4] / 'contracts/supervision/tests/fixtures'


def origin():
    record = SupervisionRequest.model_validate_json((FIXTURES / 'request.json').read_bytes())
    reads = tuple(NodeObservation.capture(record.snapshot.cut.plan_sha256, read.node, state=None, outputs=None)
                  for read in record.snapshot.reads)
    footprint = DecisionFootprint(record.snapshot.cut, record.snapshot.targets, reads)
    return SupervisionRequestBinding.bind(record, footprint, actor_id=record.planning_request.actor_id), footprint


def response(name='abstain'):
    record = SupervisionResponse.model_validate_json((FIXTURES / f'response-{name}.json').read_bytes())
    raw = None if name == 'unknown' else (FIXTURES / f'capture-{name}.json').read_bytes()
    return record, raw


def replace_capture(record, raw, *, align_proposal=False):
    document = record.model_dump(mode='json')
    digest = hashlib.sha256(raw).hexdigest()
    document['capture'].update(sha256=digest, size_bytes=len(raw))
    document['observation'].update(output_sha256=digest, captured_bytes=len(raw))
    if align_proposal:
        from amphora_contracts_planning import CampaignDraft
        draft = CampaignDraft.model_validate_json(raw)
        payload = encoded(draft)
        document['observation']['proposal'].update(payload_json=payload.decode(),
            payload_sha256=hashlib.sha256(payload).hexdigest(), action=draft.action, rationale=draft.rationale)
    return SupervisionResponse.model_validate_json(json.dumps(document))
