"""Read-only diagnostics of retained model bytes; never normalize them for acceptance."""
import argparse
import hashlib
import json
from pathlib import Path

from amphora_contracts_campaign_curation import CampaignCurationDraft
from pydantic import ValidationError
from local_numeric_configuration import write


def diagnose(output):
    raw = (output / 'original-output.json').read_bytes()
    duplicates = []
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                duplicates.append(key)
            result[key] = value
        return result
    # The lenient decode is ONLY for reporting additional failures after strict JSON
    # rejection. Its result is never published as a proposal or sent to the compiler.
    value = json.loads(raw, object_pairs_hook=pairs)
    errors = []
    try:
        CampaignCurationDraft.model_validate_json(json.dumps(value))
    except ValidationError as error:
        errors = [{'path': list(row['loc']), 'type': row['type'], 'message': row['msg']}
                  for row in error.errors(include_input=False, include_url=False)]
    envelope = json.loads((output / 'original-envelope.json').read_bytes())
    content = envelope['input'][0]['content'].split('\n', 1)[1]
    payload = json.loads(content)
    size = lambda item: len(json.dumps(item, separators=(',', ':'), ensure_ascii=False).encode())
    context = payload['untrusted_context']
    write(output / 'diagnosis.json', {
        'read_only': True, 'original_output_sha256': hashlib.sha256(raw).hexdigest(),
        'duplicate_keys': duplicates, 'additional_schema_errors_after_lenient_diagnostic_decode': errors,
        'envelope_bytes': size(envelope), 'schema_bytes': size(payload['output_schema']),
        'schema_definitions': len(payload['output_schema'].get('$defs', {})),
        'context_bytes': size(context),
        'slices': [{'lane': row['lane'], 'bytes': size(row)} for row in context['slices']],
        'accepted_output': False, 'provider_calls': 0})
    print(json.dumps({'duplicate_keys': duplicates, 'additional_errors': len(errors),
                      'schema_bytes': size(payload['output_schema']), 'context_bytes': size(context)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    diagnose(parser.parse_args().output)
