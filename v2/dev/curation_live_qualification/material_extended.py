"""Installed Planning v3 material and exact v1/v2 replay; no host, key or provider."""
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
    legacy, original, previous, diagnosis, direct, target = map(Path, sys.argv[1:])
    replays = []
    for version, name in [('1', 'supported'), ('1', 'missing'), ('2', 'supported'), ('2', 'missing'), ('3', 'supported'), ('diagnosis', 'supported'), ('4', 'supported')]:
        folder = {'1': legacy, '2': original, '3': previous, 'diagnosis': diagnosis, '4': direct}[version] / name
        raw = (folder / 'original-packet.json').read_bytes()
        record = json.loads(raw)['untrusted_context']['request']
        request = RequestSnapshot.from_bytes(json.dumps(record).encode(), actor_id=record['actor_id'],
            scope=Scope.model_validate_json(json.dumps(record['reference']['scope'])))
        envelope = CurationEnvelope.bind(request, raw)
        assert envelope.body == (folder / 'original-envelope.json').read_bytes()
        try:
            CurationOutput.parse((folder / 'original-output.json').read_bytes(), request)
        except ValueError:
            assert (version, name) != ('2', 'missing'), 'Accepted original became invalid'
        else:
            assert (version, name) == ('2', 'missing'), 'Failed original became valid'
        replays.append({'version': version, 'scenario': name, 'original_envelope_sha256': hashlib.sha256(envelope.body).hexdigest(),
                       'original_acceptance_unchanged': True})
    value = {'instructions': reviewed_instructions('curation', '5').decode(),
        'tokenizer': curation_tokenizer_reference('5').model_dump(mode='json'),
        'output_schema': campaign_curation_draft_schema().model_dump(mode='json'),
        'original_replays': replays, 'provider_calls': 0}
    from amphora_agent_planning.curation_input.structured import GenerationSchema
    value['generation_schema_sha256'] = GenerationSchema.reviewed().sha256
    value['generation_schema'] = GenerationSchema.reviewed().format()['schema']
    target.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print('Installed v5 material and all seven exact prior replays passed', flush=True)


if __name__ == '__main__':
    main()
