"""Explicit v2 checkpoint wire profile; original request parsers remain closed."""

import json
from typing import Annotated, Literal

from amphora_contracts_commands import CanonicalCommand, CommandEncodingError
from amphora_contracts_core import Digest, Identifier, WireModel
from amphora_contracts_graph_runtime import GraphReadCut
from pydantic import Field

from .requests import SupervisionNodeRead, SupervisionRequest


class InvokeCheckpoint(WireModel):
    kind: Literal['invoke']
    activation_id: Digest
    fields: tuple[()] = ()


class MaterializationCheckpoint(WireModel):
    kind: Literal['artifact_materialize']
    activation_id: Digest
    fields: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=64)]


class CheckpointSnapshot(WireModel):
    schema_version: Literal['2'] = '2'
    cut: GraphReadCut
    checkpoints: Annotated[tuple[Annotated[InvokeCheckpoint | MaterializationCheckpoint,
        Field(discriminator='kind')], ...], Field(min_length=1, max_length=64)]
    reads: Annotated[tuple[SupervisionNodeRead, ...], Field(min_length=1, max_length=256)]
    footprint_sha256: Digest
    relevant_sha256: Digest


class CheckpointRequest(SupervisionRequest):
    schema_version: Literal['2'] = '2'
    snapshot: CheckpointSnapshot


def parse_checkpoint_command(raw):
    command = CanonicalCommand.for_family(raw, 'planning.supervision.request.v2',
                                          CheckpointRequest, allow_numeric=True)
    if command.profile != 'amphora-command-v2':
        raise CommandEncodingError('invalid_encoding')
    payload = json.loads(command.canonical_bytes)['payload']
    if payload['reference']['scope'] != command.identity.scope.model_dump(mode='json'):
        raise CommandEncodingError('scope_mismatch')
    if payload['planning_request']['actor_id'] != command.identity.actor_id:
        raise CommandEncodingError('actor_mismatch')
    return command
