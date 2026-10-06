"""Public Data publication and reviewed local fixture configuration; no Planning imports."""

import hashlib
import json
from pathlib import Path

from amphora_campaign_runtime.supervision_policy import ReviewedPolicy
from amphora_campaign_runtime.supervision_policy.records import RecipePolicyRecord
from amphora_contracts_planning import checkpoint_draft_schema
from amphora_contracts_supervision import (
    checkpoint_context_content_schema,
    checkpoint_context_content_schema_bytes,
    checkpoint_repair_context_content_schema,
    checkpoint_repair_context_content_schema_bytes,
)
from campaign_context_fixture.data import command

from ...supervision_policy.support import plan, policy
from ...supervision_preparation.test_recipe import bind, document

SCALAR_SCHEMA = b'{"additionalProperties":false,"properties":{"a":{"type":"integer"}},"required":["a"],"type":"object"}'
TOKENIZER = b'{"algorithm":"utf8_byte_count","format":"planning.fixture-tokenizer.v1","framing":"exact_packet_bytes","model":["deterministic","adversarial-fixture","1"],"unit":"synthetic_byte_token"}\n'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def write(path, value):
    path.write_bytes(json.dumps(value, indent=2).encode() + b'\n')
    return path


def schema(name, body):
    return {'schema_id': name, 'version': '1', 'sha256': hashlib.sha256(body).hexdigest()}


def profiles(root):
    definitions = [('policy', schema('runtime.supervision-policy.v2', canonical(RecipePolicyRecord.model_json_schema(mode='validation'))),
                    canonical(RecipePolicyRecord.model_json_schema(mode='validation'))),
        ('context', checkpoint_context_content_schema().model_dump(mode='json'), checkpoint_context_content_schema_bytes()),
        ('repair', checkpoint_repair_context_content_schema().model_dump(mode='json'), checkpoint_repair_context_content_schema_bytes()),
        ('scalar', schema('fixture.policy', SCALAR_SCHEMA), SCALAR_SCHEMA),
        ('template', schema('fixture.budget-template', b'{"type":"object"}'), b'{"type":"object"}')]
    result = []
    for name, reference, raw in definitions:
        (root / (name + '-schema.json')).write_bytes(raw)
        result.append(dict(reference, media_type='application/json', schema_path=name + '-schema.json'))
    result.extend([dict(schema('fixture.context-text', b'{"type":"string"}'), media_type='text/plain'),
        dict(schema('planning.supervision-capture', b'{"type":"string","contentEncoding":"base64"}'),
             media_type='application/octet-stream')])
    return result


def publish(owner, scope, key, body, profile):
    reference = {field: profile[field] for field in ('schema_id', 'version', 'sha256')}
    content = {'sha256': hashlib.sha256(body).hexdigest(), 'size_bytes': len(body),
               'media_type': profile['media_type'], 'schema_ref': reference}
    upload = owner.call('POST', '/v1/uploads', command(scope, 'artifacts.begin_upload', key + '.begin', {'content': content}))
    owner.call('PUT', '/v1/uploads/' + upload['upload_id'] + '/content', body)
    return owner.call('POST', '/v1/artifacts/finalize', command(scope, 'artifacts.finalize', key + '.finalize',
        {'upload_id': upload['upload_id'], 'content': content}))['artifact']


def materials(owner, scope, root, admitted_profiles, *, independent=False):
    compiled = plan(scope=scope, independent=independent)
    data = document()
    data['scope'] = scope
    text = next(item for item in admitted_profiles if item['media_type'] == 'text/plain')
    prompt = (Path(__file__).parents[2] / 'supervision_context/fixtures/campaign-v1.txt').read_bytes().replace(b'\r\n', b'\n')
    data['objective'] = publish(owner, scope, 'objective', b'Synthetic software checkpoint; no scientific assessment.', text)
    data['prompt'] = publish(owner, scope, 'prompt', prompt, text)
    data['model'].update(provider_id='deterministic', model_id='adversarial-fixture', model_revision='1',
        context_window_tokens=204096, tokenizer=schema('planning.fixture-byte-tokenizer', TOKENIZER),
        configuration=publish(owner, scope, 'model', b'Deterministic fixture only.', text))
    data['entries'], data['omissions'] = [], []
    data['limits'].update(max_attempts=1, max_input_tokens=200000, max_output_tokens=4096,
                          total_tokens=204096, total_accounting_units=60)
    template = {name: data[name] for name in ('scope', 'model', 'prompt', 'allowed_actions', 'limits')}
    template.update(profile='planning-supervision-budget-template.v1',
                    output_schema=checkpoint_draft_schema().model_dump(mode='json'), per_attempt_accounting_units=60)
    template_bytes = canonical(template)
    data['budget_policy'] = publish(owner, scope, 'template', template_bytes,
                                    next(item for item in admitted_profiles if item['schema_id'] == 'fixture.budget-template'))
    recipe = bind(data)
    record = policy(compiled).model_dump(mode='json')
    record.update(profile='runtime-supervision-policy.v2', context_recipe_sha256=recipe.sha256)
    record['checkpoints'][0].update(timeout_seconds=300, max_requests=2, max_model_calls=2)
    if independent:
        record['checkpoints'][0].update(max_requests=1, max_model_calls=1)
    reviewed = ReviewedPolicy.bind(compiled, RecipePolicyRecord.model_validate_json(json.dumps(record)))
    (root / 'template.json').write_bytes(template_bytes)
    (root / 'policy.json').write_bytes(reviewed.canonical)
    (root / 'recipe.json').write_bytes(recipe.canonical)
    write(root / 'graph.json', compiled.document.definition.model_dump(mode='json'))
    graph = {'definition': 'graph.json', 'releases': [], 'schemas': [
        {'schema_ref': schema('fixture.policy', SCALAR_SCHEMA), 'path': 'scalar-schema.json'}]}
    return compiled, recipe, reviewed, graph
