"""Explicit derived-closure protection; Data owns membership and transitions."""

import json
from typing import Annotated, Literal

from amphora_contracts_artifacts import ReservationReceipt, ReserveArtifact
from amphora_contracts_commands import CanonicalCommand, CommandEncodingError
from amphora_contracts_core import Digest, WireModel
from pydantic import Field


class ReserveDerivedClosure(ReserveArtifact):
    profile: Literal["derived-closure-retention-v1"]


class DerivedClosureReservationReceipt(WireModel):
    schema_version: Literal["1"] = "1"
    profile: Literal["derived-closure-retention-v1"]
    reservation: ReservationReceipt
    artifact_count: Annotated[int, Field(ge=1, le=4096)]
    members_sha256: Digest


def parse_derived_closure_command(raw):
    command = CanonicalCommand.for_family(raw, "artifacts.reserve_derived_closure", ReserveDerivedClosure)
    artifact = json.loads(command.canonical_bytes)["payload"]["artifact"]
    if artifact["scope"] != command.identity.scope.model_dump():
        raise CommandEncodingError("scope_mismatch")
    return command


__all__ = ["ReserveDerivedClosure", "DerivedClosureReservationReceipt", "parse_derived_closure_command"]
