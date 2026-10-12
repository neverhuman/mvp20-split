"""Installed Planning v2 material and exact v1 replay; no host, key or provider."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from amphora_agent_planning.campaign_packet_profiles import reviewed_instructions
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.curation_input import CurationEnvelope, curation_tokenizer_reference
from amphora_agent_planning.curation_output import CurationOutput
from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from amphora_contracts_core import Scope


def main():
    assert all(importlib.util.find_spec(name) is None for name in (
        'amphora_campaign_runtime', 'amphora_data_artifacts', 'amphora_deployment',
        'amphora_research', 'amphora_knowledge', 'amphora_capability_registry'))
    original, target = map(Path, sys.argv[1:])
    replays = []
    for name in ('supported', 'missing'):
        folder = original / name
        raw = (folder / 'original-packet.json').read_bytes()
        record = json.loads(raw)['untrusted_context']['request']
        request = RequestSnapshot.from_bytes(json.dumps(record).encode(), actor_id=record['actor_id'],
            scope=Scope.model_validate_json(json.dumps(record['reference']['scope'])))
        envelope = CurationEnvelope.bind(request, raw)
        assert envelope.body == (folder / 'original-envelope.json').read_bytes()
        try:
            CurationOutput.parse((folder / 'original-output.json').read_bytes(), request)
        except ValueError:
            pass
        else:
            raise AssertionError('Original failed response was reinterpreted as valid')
        replays.append({'scenario': name, 'original_envelope_sha256': hashlib.sha256(envelope.body).hexdigest(),
                       'original_output_still_rejected': True})
    value = {'instructions': reviewed_instructions('curation', '2').decode(),
        'tokenizer': curation_tokenizer_reference('2').model_dump(mode='json'),
        'output_schema': campaign_curation_draft_schema().model_dump(mode='json'),
        'original_v1_replays': replays, 'provider_calls': 0}
    target.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print('Installed v2 material and both exact v1 replays passed', flush=True)


if __name__ == '__main__':
    main()
