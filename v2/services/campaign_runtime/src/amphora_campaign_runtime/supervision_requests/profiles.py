"""Explicit owner dispatch; neither historical public parser is widened."""

from amphora_contracts_supervision import (
    CheckpointRequest,
    SupervisionRequest,
    parse_checkpoint_command,
    parse_supervision_command,
)

from ..supervision_scope.observations import require
from .binding import CheckpointRequestBinding, SupervisionRequestBinding


def request_type(version):
    require(version in {'1', '2'}, 'supervision_request_profile')
    return SupervisionRequest if version == '1' else CheckpointRequest


def request_command(family, raw):
    require(family in {'planning.supervision.request', 'planning.supervision.request.v2'},
            'supervision_request_family')
    return (parse_checkpoint_command(raw) if family.endswith('.v2')
            else parse_supervision_command(family, raw))


def request_binding(request):
    request_type(request.schema_version)
    return SupervisionRequestBinding if request.schema_version == '1' else CheckpointRequestBinding
