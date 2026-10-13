"""Offline counterexample to an unsupported-wiring claim; never provider output."""
import argparse
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from amphora_contracts_campaign_curation import CampaignCurationDraft


def verify(envelope_path, fixture_path, integrated_path, output):
    envelope = json.loads(envelope_path.read_bytes())
    original = fixture_path.read_bytes()
    # This is a prior deterministic fixture, not the new model response.
    witness = CampaignCurationDraft.model_validate_json(original).model_dump(mode='json')
    schema = envelope['text']['format']['schema']
    Draft202012Validator(schema).validate(witness)
    definition = witness['outcome']['candidate']['definition']
    body = definition['body']
    port = next(row for row in body['inputs'] if row['name'] == 'previous_result')
    exported = next(row for row in body['outputs'] if row['name'] == 'previous_result')
    assert port['value_type'] == exported['value_type']
    finish = next(row for row in body['nodes'] if row['kind'] == 'finish')
    assert next(row for row in finish['outputs'] if row['port'] == 'previous_result')['source'] == {'kind': 'input', 'name': 'previous_result'}
    integrated = json.loads(integrated_path.read_bytes())
    assert integrated['successor']['status'] == 'completed'
    assert integrated['curation']['proposal'] == witness
    value = {'status': 'passed', 'provider_calls': 0, 'new_campaigns': 0,
        'scope': 'Prior deterministic executed witness validates against exact current generation schema; not model-generated acceptance',
        'fixture_sha256': hashlib.sha256(original).hexdigest(),
        'current_envelope_sha256': hashlib.sha256(envelope_path.read_bytes()).hexdigest(),
        'generation_schema_sha256': hashlib.sha256(json.dumps(schema, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'prior_completed_successor': integrated['successor']['run_id'],
        'supported_binding': {'kind': 'input', 'name': 'previous_result'},
        'reasoning_effort': envelope['reasoning']['effort'],
        'model_effectiveness_established': False}
    output.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print('Prior executed carry wiring validates under exact v7 generation schema; no provider or new campaign', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('envelope', 'fixture', 'integrated', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    verify(args.envelope, args.fixture, args.integrated, args.output)
