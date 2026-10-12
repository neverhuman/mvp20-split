"""Explicit one-shot probes with immutable reservation-before-send evidence."""
import argparse
import copy
import hashlib
import json
import os
import time
from pathlib import Path

from jsonschema import Draft202012Validator
from amphora_agent_planning.openai_provider.http import OpenAIHTTP
from amphora_agent_planning.openai_provider.diagnostics import ResponseDiagnostic
from amphora_agent_planning.openai_provider.pricing import MODEL

MAX_CALLS = 16
HOLD = 30000000
MAX_BODY = 32768 - 1024
CONSTRAINTS = {'pattern', 'minLength', 'maxLength', 'minimum', 'maximum', 'minItems', 'maxItems'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def prune(schema):
    schema = copy.deepcopy(schema)
    definitions = schema.pop('$defs', {})
    needed = set()
    def visit(value):
        if isinstance(value, dict):
            if '$ref' in value:
                name = value['$ref'].removeprefix('#/$defs/')
                if name not in needed:
                    needed.add(name)
                    visit(definitions[name])
            for child in value.values(): visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    visit(schema)
    if needed: schema['$defs'] = {name: definitions[name] for name in sorted(needed)}
    return schema


def strip(schema, keys):
    if isinstance(schema, dict):
        return {name: ({key: strip(child, keys) for key, child in value.items()}
                       if name in {'properties', '$defs'} else strip(value, keys))
                for name, value in schema.items() if name not in keys}
    if isinstance(schema, list): return [strip(value, keys) for value in schema]
    return schema


def variant(original, name):
    schema = copy.deepcopy(original)
    if name == 'tiny':
        return {'type': 'object', 'properties': {'ok': {'type': 'boolean'}},
                'required': ['ok'], 'additionalProperties': False}
    if name == 'abstain':
        schema['properties']['outcome'] = {'$ref': '#/$defs/CurationAbstention'}
        return prune(schema)
    if name == 'structure': return strip(schema, CONSTRAINTS)
    if name == 'structure-v2': return strip(schema, CONSTRAINTS)
    if name == 'no-numeric': return strip(schema, {'minimum', 'maximum'})
    if name == 'no-large-number':
        for key in ('minimum', 'maximum'):
            del schema['$defs']['NumberConstant']['properties']['value'][key]
        return schema
    if name == 'large-number-tiny':
        return {'type': 'object', 'properties': {'value': {
            'type': 'number', 'minimum': -1e100, 'maximum': 1e100}},
            'required': ['value'], 'additionalProperties': False}
    if name == 'no-patterns': return strip(schema, {'pattern'})
    if name == 'full': return schema
    raise ValueError('unknown_variant')


def body_for(schema):
    Draft202012Validator.check_schema(schema)
    prompt = ('Return the smallest JSON object allowed by the schema. For an ok field use true. '
              'For a curation schema choose outcome kind abstain, reason_code insufficient_context, '
              'rationale diagnostic only, decision_scope ' + '0' * 64 + ', unresolved []. '
              'This is a synthetic schema diagnostic, not research or campaign execution.')
    body = canonical({'model': MODEL, 'store': False, 'stream': False, 'service_tier': 'default',
        'reasoning': {'effort': 'none'}, 'max_output_tokens': 512,
        'instructions': 'Return JSON conforming to the supplied schema.',
        'input': [{'role': 'user', 'content': prompt}],
        'text': {'format': {'type': 'json_schema', 'name': 'campaign_curation_v3', 'strict': True, 'schema': schema}}})
    assert len(body) <= MAX_BODY
    assert (len(body) + 1024) * 750 + 512 * 4500 <= HOLD
    return body


def reserve(output, label, body):
    # Exclusive lock and exclusive reservation files; crashes consume their original slot.
    output.mkdir(parents=True, exist_ok=True)
    lock = output / 'reservation.lock'
    with lock.open('x'):
        try:
            prior = list(output.glob('*/reservation.json'))
            assert len(prior) < MAX_CALLS, 'isolation_allowance_exhausted'
            folder = output / label
            folder.mkdir(exist_ok=False)
            (folder / 'request.json').write_bytes(body)
            with (folder / 'reservation.json').open('x', encoding='utf-8') as stream:
                json.dump({'authorization': 'owner-directed-isolation-20261012',
                    'original_hold_units': HOLD, 'request_sha256': hashlib.sha256(body).hexdigest(),
                    'maximum_calls': MAX_CALLS, 'maximum_total_hold_units': MAX_CALLS * HOLD,
                    'unit': 'usd_nanodollars', 'campaign_acceptance': False}, stream)
        finally:
            pass
    lock.unlink()
    return folder


def credential():
    key = os.environ.get('OPENAI_API_KEY')
    if key: return key
    for line in Path('Z:/ssos/.env').read_text(encoding='utf-8-sig').splitlines():
        name, separator, value = line.partition('=')
        if separator and name.strip() == 'OPENAI_API_KEY': return value.strip().strip('\"').strip("'")
    raise ValueError('credential_missing')


def run(body, folder):
    transport = OpenAIHTTP(credential(), timeout_seconds=60, maximum_body_bytes=32768)
    started = time.monotonic()
    evidence = {'campaign_acceptance': False, 'provider_calls': 1}
    try:
        raw = transport.send(body)
        value = json.loads(raw)
        evidence['diagnostic'] = ResponseDiagnostic.capture(raw, value).document()
        evidence['usage'] = {key: value.get('usage', {}).get(key) for key in ('input_tokens', 'output_tokens')}
        parts = [block['text'] for item in value.get('output', []) if item.get('type') == 'message'
                 for block in item.get('content', []) if block.get('type') == 'output_text']
        text = ''.join(parts)
        (folder / 'output.txt').write_text(text, encoding='utf-8')
        evidence['valid_output'] = False
        if value.get('status') == 'completed' and text:
            parsed = json.loads(text)
            Draft202012Validator(json.loads(body)['text']['format']['schema']).validate(parsed)
            evidence['valid_output'] = True
    except Exception as error:
        evidence['exception_type'] = type(error).__name__
    finally:
        evidence['transport'] = transport.last_exchange
        evidence['transport_failure'] = transport.last_failure
        evidence['elapsed_seconds'] = round(time.monotonic() - started, 3)
        (folder / 'evidence.json').write_bytes(canonical(evidence))
        print(json.dumps(evidence), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--variant', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    original = json.loads(args.original.read_bytes())['text']['format']['schema']
    body = body_for(variant(original, args.variant))
    if args.live:
        run(body, reserve(args.output, args.variant, body))
    else:
        print(json.dumps({'variant': args.variant, 'request_bytes': len(body), 'provider_calls': 0}))
