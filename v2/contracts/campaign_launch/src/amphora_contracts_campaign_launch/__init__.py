"""Published launch DTOs and canonical parsing, not lifecycle or execution authority."""
import json

from amphora_contracts_commands import CanonicalCommand, CommandEncodingError, NUMERIC_ENCODING
from amphora_contracts_graph_runtime import parse_graph_command

from .models import (LaunchPhase, LaunchProfileCatalog, LaunchProfileRef, LaunchProfileView,
    LaunchReceipt, LaunchRequest, LaunchSpecification, WorkerReadiness)


def parse_launch(raw: str | bytes) -> tuple[CanonicalCommand, CanonicalCommand]:
    request = CanonicalCommand.for_family(raw, 'campaign.launch', LaunchSpecification, allow_numeric=True)
    if request.profile != NUMERIC_ENCODING:
        raise CommandEncodingError('launch_encoding_required')
    payload = json.loads(request.canonical_bytes)['payload']
    admission = parse_graph_command('graph.admit_draft', json.dumps(payload['admission'], separators=(',', ':')))
    if admission.identity.scope != request.identity.scope or admission.identity.actor_id != request.identity.actor_id:
        raise CommandEncodingError('launch_admission_identity')
    if admission.identity.command_id != request.identity.command_id:
        raise CommandEncodingError('launch_admission_request_id')
    return request, admission


__all__ = ['LaunchPhase', 'LaunchProfileCatalog', 'LaunchProfileRef', 'LaunchProfileView',
    'LaunchReceipt', 'LaunchRequest', 'LaunchSpecification', 'WorkerReadiness', 'parse_launch']
