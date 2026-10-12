"""Candidate coverage without retaining omitted payloads or granting source rights."""

import base64
import hashlib
from dataclasses import dataclass

from amphora_contracts_campaign_curation import campaign_curation_draft_schema

from ..campaign_artifact_context import ArtifactContextItem, ArtifactContextPlan
from ..campaign_context.records import canonical
from ..campaign_packet_profiles import reviewed_for_request
from ..context.policy import require
from .encoding import keys
from .wire import CandidateRecord


@dataclass(frozen=True)
class PreparationInputs:
    candidates: tuple[CandidateRecord, ...]

    @classmethod
    def capture(cls, plan, packet):
        return cls(tuple(CandidateRecord.model_validate_json(canonical(row)) for row in summaries(plan, packet)))

    def document(self):
        return [row.model_dump(mode='json') for row in self.candidates]

    def verify(self, request, context):
        validate(request, self.candidates, context)


def summaries(plan, packet):
    included = frozenset(packet.included)
    return [{'lane': row.lane, 'identity': row.document()['identity'], 'payload_sha256': row.sha256,
             'required': row.required, 'included': index in included,
             'observations': row.document()['observations'] if index in included else []}
            for index, row in enumerate(plan.slices)]


def validate(request, candidates, context):
    counts = {}
    for row in candidates:
        counts[row.lane] = counts.get(row.lane, 0) + 1
        if row.lane != 'artifact':
            require(row.required == (row.lane not in {'research_view', 'registry_inventory', 'retrieval'}),
                    'campaign_preparation_lane_requirement')
    limits = {'curation_knowledge': 0, 'curation': 0, 'artifact': 132, 'research': 1, 'research_view': 32, 'graph': 1, 'registry_scan': 1,
              'registry_inventory': 400, 'registry_exact': 64, 'runtime': 1, 'runtime_schema': 256, 'retrieval': 1}
    if request.document().context.output_schema == campaign_curation_draft_schema():
        limits['graph'] = 8
        limits['curation'] = 1
        limits['curation_knowledge'] = 1
    require(all(count <= limits[lane] for lane, count in counts.items()), 'campaign_preparation_lane_count')
    require(not (counts.get('registry_inventory') or counts.get('registry_exact')) or counts.get('registry_scan') == 1,
            'campaign_preparation_registry_scan')
    require(not counts.get('runtime_schema') or counts.get('runtime') == 1, 'campaign_preparation_runtime_universe')
    require(not counts.get('research_view') or counts.get('research') == 1, 'campaign_preparation_research_selection')
    identities = [(row.lane, canonical(row.identity)) for row in candidates]
    require(len(set(identities)) == len(identities), 'campaign_preparation_candidate_duplicate')
    required = [row.required for row in candidates]
    require(required == sorted(required, reverse=True), 'campaign_preparation_candidate_order')
    require(all(not row.required or row.included for row in candidates), 'campaign_preparation_required')
    included = [row for row in candidates if row.included]
    require(type(context['slices']) is list and len(context['slices']) == len(included), 'campaign_preparation_slice_coverage')
    for candidate, value in zip(included, context['slices'], strict=True):
        keys(value, ('lane', 'identity', 'required', 'payload'))
        require(value['lane'] == candidate.lane and canonical(value['identity']) == canonical(candidate.identity) and
                type(value['required']) is bool and value['required'] == candidate.required, 'campaign_preparation_slice_binding')
        require(type(value['payload']) is dict, 'campaign_preparation_payload_shape')
        payload = dict(value['payload'])
        if candidate.lane == 'curation':
            from ..curation_context import CurationIntent
            intent = CurationIntent.from_payload(request, payload)
            require(candidate.identity == intent.identity and not candidate.observations,
                    'curation_intent_candidate')
        if candidate.lane == 'artifact' and payload.get('roles') == ['prompt']:
            require(payload.pop('body_location', None) == 'trusted_instructions' and 'body_base64' not in payload,
                    'campaign_preparation_prompt_location')
            payload['body_base64'] = base64.b64encode(reviewed_for_request(request)).decode('ascii')
        require(hashlib.sha256(canonical(payload)).hexdigest() == candidate.payload_sha256, 'campaign_preparation_payload_digest')
    from ..curation_knowledge.validation import validate_knowledge
    validate_knowledge(request, context["slices"])
    omissions = [{'lane': row.lane, 'identity': row.identity, 'payload_sha256': row.payload_sha256, 'reason': 'budget'}
                 for row in candidates if not row.included]
    require(canonical(context['budget_omissions']) == canonical(omissions), 'campaign_preparation_budget_omissions')
    require(all(row.included or not row.observations for row in candidates), 'campaign_preparation_omitted_observations')
    observations = [{'lane': row.lane, **observation.model_dump(mode='json')}
                    for row in included for observation in row.observations]
    require(canonical(context['consumed_observations']) == canonical(observations), 'campaign_preparation_observations')
    validate_artifacts(request, candidates, context)


def validate_artifacts(request, candidates, context):
    expected = ArtifactContextPlan.bind(request)
    declared = [row for row in candidates if row.lane == 'artifact']
    require(len(declared) == len(expected.items), 'campaign_preparation_artifact_coverage')
    payloads = {canonical(row['identity']): row['payload'] for row in context['slices'] if row['lane'] == 'artifact'}
    for candidate, planned in zip(declared, expected.items, strict=True):
        identity = planned.reference.model_dump(mode='json')
        require(canonical(candidate.identity) == canonical(identity) and candidate.required == planned.required,
                'campaign_preparation_artifact_binding')
        if not candidate.included:
            continue
        payload = dict(payloads[canonical(identity)])
        if payload.get('body_location') == 'trusted_instructions':
            payload.pop('body_location')
            payload['body_base64'] = base64.b64encode(reviewed_for_request(request)).decode('ascii')
        body = payload.get('body_base64')
        if body is None:
            require(not planned.required, 'campaign_preparation_artifact_required')
            item = ArtifactContextItem.unavailable(planned, payload.get('reason'))
        else:
            require(type(body) is str, 'campaign_preparation_artifact_encoding')
            item = ArtifactContextItem.available(planned, base64.b64decode(body, validate=True))
        require(canonical(item.payload()) == canonical(payload), 'campaign_preparation_artifact_payload')
        require([row.model_dump(mode='json') for row in candidate.observations] ==
                [{'kind': 'artifact', 'identity': identity, 'sha256': item.observation_sha256}], 'campaign_preparation_artifact_observation')
