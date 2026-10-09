"""Strict transport records; launch transitions and authorization belong to Deployment."""
from typing import Annotated, Literal

from amphora_contracts_commands import CommandIdentity
from amphora_contracts_core import Digest, Identifier, Scope, WireModel
from amphora_contracts_graph_runtime import AdmitDraft
from amphora_contracts_runtime import CommandReceipt
from amphora_contracts_tools import ToolBinding
from pydantic import AwareDatetime, Field


class LaunchProfileRef(WireModel):
    profile_id: Identifier
    version: Literal['1']
    sha256: Digest


class LegacyAdmission(WireModel):
    identity: CommandIdentity
    payload: AdmitDraft


class NumericAdmission(LegacyAdmission):
    encoding: Literal['amphora-command-v2']


class LaunchSpecification(WireModel):
    profile: LaunchProfileRef
    admission: NumericAdmission | LegacyAdmission


class LaunchRequest(WireModel):
    encoding: Literal['amphora-command-v2']
    identity: CommandIdentity
    payload: LaunchSpecification


LaunchPhase = Literal['preparing', 'admission_unresolved', 'rejected',
    'admitted_not_engaged', 'engaging', 'engaged', 'draining', 'released', 'recovery_required']


class WorkerReadiness(WireModel):
    expected: Annotated[int, Field(ge=0, le=64)]
    ready: Annotated[int, Field(ge=0, le=64)]


class LaunchReceipt(WireModel):
    wire_version: Literal['1'] = '1'
    identity: CommandIdentity
    request_sha256: Digest
    profile: LaunchProfileRef
    revision: Annotated[int, Field(ge=0, le=9007199254740991)]
    phase: LaunchPhase
    reason_code: Identifier | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    admission: CommandReceipt | None
    run_id: Identifier | None
    workers: WorkerReadiness


class LaunchProfileView(WireModel):
    reference: LaunchProfileRef
    scope: Scope
    title: Annotated[str, Field(min_length=1, max_length=160)]
    tools: Annotated[tuple[ToolBinding, ...], Field(min_length=1, max_length=64)]
    maximum_invocations: Annotated[int, Field(ge=1, le=100000)]
    maximum_deadline_seconds: Annotated[int, Field(ge=1, le=86400)]


class LaunchProfileCatalog(WireModel):
    wire_version: Literal['1'] = '1'
    scope: Scope
    profiles: Annotated[tuple[LaunchProfileView, ...], Field(max_length=32)]
