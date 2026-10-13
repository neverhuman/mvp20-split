"""Installed Planning replay of one retained proposal; no provider or credentials."""
import json
import hashlib
import sys
from pathlib import Path
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.curation_input import CurationEnvelope
from amphora_agent_planning.curation_output import CurationOutput
from amphora_contracts_core import Scope
folder, output = map(Path, sys.argv[1:])
raw = (folder / 'original-packet.json').read_bytes()
record = json.loads(raw)['untrusted_context']['request']
request = RequestSnapshot.from_bytes(json.dumps(record).encode(), actor_id=record['actor_id'], scope=Scope.model_validate_json(json.dumps(record['reference']['scope'])))
envelope = CurationEnvelope.bind(request, raw)
assert envelope.body == (folder / 'original-envelope.json').read_bytes()
CurationOutput.parse((folder / 'original-output.json').read_bytes(), request)
output.write_text(json.dumps({'status': 'passed', 'provider_calls': 0, 'envelope_sha256': hashlib.sha256(envelope.body).hexdigest(), 'output_sha256': hashlib.sha256((folder / 'original-output.json').read_bytes()).hexdigest()})+'\n')
