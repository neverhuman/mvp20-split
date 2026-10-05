"""Canonical fixture envelope; owner text is data, never instruction selection."""

import json

from ..campaign_context.records import canonical


def render(plan, instructions, included):
    included = frozenset(included)
    slices, omissions, observations = [], [], []
    for index, row in enumerate(plan.slices):
        value = row.document()
        if index not in included:
            omissions.append({'lane': row.lane, 'identity': value['identity'], 'payload_sha256': row.sha256, 'reason': 'budget'})
            continue
        if row.lane == 'artifact' and value['payload']['roles'] == ['prompt']:
            # Preserve metadata/hash; exact approved body already appears once above data.
            value['payload'].pop('body_base64')
            value['payload']['body_location'] = 'trusted_instructions'
        observations.extend({'lane': row.lane, **entry} for entry in value.pop('observations'))
        slices.append(value)
    return canonical({'format': 'planning-campaign-packet.v1',
        'trusted_instructions': instructions.body.decode('utf-8'),
        'instruction_reference': instructions.reference.model_dump(mode='json'),
        'untrusted_context': {'request': json.loads(plan.request.canonical), 'slices': slices,
            'original_omissions': [row.model_dump(mode='json') for row in plan.request.document().context.omissions],
            'budget_omissions': omissions, 'consumed_observations': observations},
        'authority': 'proposal_input_only'})
