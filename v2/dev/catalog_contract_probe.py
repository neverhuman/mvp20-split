"""Public wire validation in an independently installed Registry contract closure."""

import hashlib
import json
import sys

from amphora_contracts_tools import LockEntry, RegistryReceipt, ReleaseDescriptor, parse_registry_command


def main():
    value = json.loads(sys.stdin.buffer.read(65536))
    if value['operation'] == 'lock':
        descriptor = ReleaseDescriptor.model_validate_json(json.dumps(value['descriptor'])).model_dump(mode='json')
        document = {'profile': 'amphora-tool-release-v1', 'descriptor': descriptor}
        digest = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
            ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        tool = descriptor['tool']
        result = LockEntry.model_validate_json(json.dumps({'tool': tool['binding'], 'descriptor_sha256': digest,
            'input_schemas': [{'port': p['name'], 'schema_ref': p['schema_ref']} for p in tool['inputs']],
            'output_schemas': [{'port': p['name'], 'schema_ref': p['schema_ref']} for p in tool['outputs']],
            'checkpoint_schema': tool['checkpoint_schema']})).model_dump(mode='json')
    else:
        assert value['operation'] == 'heartbeat'
        parse_registry_command('registry.heartbeat', json.dumps(value['command']).encode())
        RegistryReceipt.model_validate_json(json.dumps(value['receipt']))
        result = {'status': 'valid'}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
