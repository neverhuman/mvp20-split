"""Explicit immutable predecessor cuts and compatible carried-value proposals."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, Scope, WireModel
from pydantic import Field

from .models import AdmitGraphRun


class PredecessorCut(WireModel):
    run_id: Identifier
    plan_sha256: Digest
    revision: Annotated[int, Field(ge=0, le=9007199254740991)]


class RunOutputSource(WireModel):
    kind: Literal["run_output"] = "run_output"
    port: Identifier


class NodeOutputSource(WireModel):
    kind: Literal["node_output"] = "node_output"
    activation_id: Digest
    port: Identifier


CarrySource = Annotated[RunOutputSource | NodeOutputSource, Field(discriminator="kind")]


class CarriedBinding(WireModel):
    target_port: Identifier
    source: CarrySource
    expected_value_sha256: Digest


class SuccessorProposal(AdmitGraphRun):
    predecessor: PredecessorCut
    carried: Annotated[tuple[CarriedBinding, ...], Field(max_length=64)]


class CarrySourceView(WireModel):
    source: CarrySource
    value_sha256: Digest


class CarrySources(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    predecessor: PredecessorCut
    predecessor_ready: bool
    sources: Annotated[tuple[CarrySourceView, ...], Field(max_length=64)]


class SuccessorLineage(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    run_id: Identifier
    plan_sha256: Digest
    predecessor: PredecessorCut
    carried: Annotated[tuple[CarriedBinding, ...], Field(max_length=64)]
    transfer_sha256: Digest
