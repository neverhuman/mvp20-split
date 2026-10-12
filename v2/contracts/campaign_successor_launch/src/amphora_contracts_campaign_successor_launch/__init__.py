"""Additive successor launch boundary; Runtime alone accepts predecessor transfer."""
import json
from typing import Annotated, Literal

from amphora_contracts_campaign_launch import LaunchPhase, LaunchProfileRef, WorkerReadiness
from amphora_contracts_commands import CanonicalCommand, CommandEncodingError, CommandIdentity, NUMERIC_ENCODING
from amphora_contracts_core import Digest, Identifier, WireModel
from amphora_contracts_draft_successor import AdmitDraftSuccessor, parse_draft_successor
from amphora_contracts_graph_runtime import PredecessorCut
from amphora_contracts_runtime import CommandReceipt
from pydantic import AwareDatetime, Field


class SuccessorAdmission(WireModel):
    encoding: Literal['amphora-command-v2']
    identity: CommandIdentity
    payload: AdmitDraftSuccessor


class SuccessorLaunchSpecification(WireModel):
    profile: LaunchProfileRef
    admission: SuccessorAdmission


class SuccessorLaunchRequest(WireModel):
    encoding: Literal['amphora-command-v2']
    identity: CommandIdentity
    payload: SuccessorLaunchSpecification


class SuccessorLaunchReceiptQuery(WireModel):
    identity: CommandIdentity
    request_sha256: Digest


class SuccessorLaunchReceipt(WireModel):
    wire_version: Literal['1'] = '1'
    profile_kind: Literal['campaign-successor-launch.v1']
    identity: CommandIdentity
    request_sha256: Digest
    profile: LaunchProfileRef
    predecessor: PredecessorCut
    revision: Annotated[int, Field(ge=0, le=9007199254740991)]
    phase: LaunchPhase
    reason_code: Identifier | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    admission: CommandReceipt | None
    run_id: Identifier | None
    workers: WorkerReadiness


def parse_successor_launch(raw: str | bytes) -> tuple[CanonicalCommand, CanonicalCommand]:
    command = CanonicalCommand.for_family(raw, 'campaign.launch_successor',
                                          SuccessorLaunchSpecification, allow_numeric=True)
    if command.profile != NUMERIC_ENCODING:
        raise CommandEncodingError('successor_launch_encoding_required')
    payload = json.loads(command.canonical_bytes)['payload']
    admission = parse_draft_successor(json.dumps(payload['admission'], separators=(',', ':')))
    if admission.identity.scope != command.identity.scope or admission.identity.actor_id != command.identity.actor_id:
        raise CommandEncodingError('successor_launch_admission_identity')
    if admission.identity.command_id != command.identity.command_id:
        raise CommandEncodingError('successor_launch_admission_request_id')
    return command, admission


__all__ = ['SuccessorAdmission', 'SuccessorLaunchSpecification', 'SuccessorLaunchRequest',
           'SuccessorLaunchReceiptQuery', 'SuccessorLaunchReceipt', 'parse_successor_launch']
