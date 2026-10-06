"""Explicit exact-policy admission; original graph command parsers remain closed."""

import json
from typing import Literal

from amphora_contracts_commands import CanonicalCommand, CommandEncodingError
from amphora_contracts_core import Digest, WireModel
from amphora_contracts_graph_runtime import AdmitGraphRun


class AdmitSupervisedGraph(WireModel):
    schema_version: Literal['1'] = '1'
    admission: AdmitGraphRun
    policy_sha256: Digest


def parse_supervised_admission(raw):
    command = CanonicalCommand.for_family(raw, 'graph.admit_supervised', AdmitSupervisedGraph, allow_numeric=True)
    if command.profile != 'amphora-command-v2':
        raise CommandEncodingError('invalid_encoding')
    payload = AdmitSupervisedGraph.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))
    for binding in payload.admission.inputs:
        items = binding.value.items if binding.value.kind == 'collection' else (binding.value,)
        if any(item.kind == 'artifact' and item.artifact.scope != command.identity.scope for item in items):
            raise CommandEncodingError('scope_mismatch')
    return command
