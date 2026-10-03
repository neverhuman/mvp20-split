"""Reference-only intake identity and historical status; source checks belong to Research."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, Scope, WireModel
from pydantic import Field

from .lab_reports import LabReportResolution


class LabProfileRef(WireModel):
    scope: Scope
    profile_id: Identifier
    version: Identifier
    sha256: Digest


class LabIntakeRequest(WireModel):
    wire_version: Literal["1"]
    intake_id: Identifier
    profile: LabProfileRef
    report: ArtifactRef


class LabIntakePending(WireModel):
    status: Literal["pending"]


class LabIntakeResolved(WireModel):
    status: Literal["resolved"]
    resolution: LabReportResolution


class LabIntakeFailed(WireModel):
    status: Literal["failed"]
    reason: Identifier


class LabIntakeStatus(WireModel):
    wire_version: Literal["1"]
    request: LabIntakeRequest
    actor_id: Identifier
    outcome: Annotated[LabIntakePending | LabIntakeResolved | LabIntakeFailed,Field(discriminator="status")]
