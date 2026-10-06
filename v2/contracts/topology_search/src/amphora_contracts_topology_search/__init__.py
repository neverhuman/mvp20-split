"""Additive bounded topology proposal DTOs; no compiler or admission authority."""
from typing import Annotated, Literal
from pydantic import Field
from amphora_contracts_core import Digest, Identifier, SafePositiveInt, SchemaRef, Scope, WireModel
from amphora_contracts_tools import LockEntry, ToolBinding
from amphora_contracts_campaigns import ExecutableCampaignV4, ValueSource
from amphora_contracts_graph_runtime import CarriedBinding, PredecessorCut


class TopologyParent(WireModel):
    scope: Scope
    plan_sha256: Digest
    definition_sha256: Digest


class NodeAddress(WireModel):
    scope_path: Annotated[tuple[Identifier, ...], Field(max_length=16)]
    node_id: Identifier


class EvaluatorSwap(WireModel):
    kind: Literal['evaluator_swap']
    edit_id: Identifier
    target: NodeAddress
    expected_tool: ToolBinding
    replacement: LockEntry


class TransformInsertion(WireModel):
    kind: Literal['transform_insertion']
    edit_id: Identifier
    target: NodeAddress
    target_input: Identifier
    expected_source: ValueSource
    node_id: Identifier
    transform: LockEntry
    transform_input: Identifier
    transform_output: Identifier
    timeout_seconds: Annotated[int, Field(ge=1, le=86400)]


TopologyEdit = Annotated[EvaluatorSwap | TransformInsertion, Field(discriminator='kind')]


class TopologyPolicy(WireModel):
    wire_version: Literal['1'] = '1'
    authority: Literal['synthetic_proposal_policy'] = 'synthetic_proposal_policy'
    parent: TopologyParent
    allowed_edits: Annotated[tuple[TopologyEdit, ...], Field(min_length=1, max_length=64)]
    evaluator_call_limit: Annotated[int, Field(ge=1, le=1000000)]


class TopologyRequest(WireModel):
    wire_version: Literal['1'] = '1'
    scope: Scope
    proposal_id: Identifier
    policy: SchemaRef
    predecessor: PredecessorCut
    edit_id: Identifier
    successor_revision: SafePositiveInt
    carried: Annotated[tuple[CarriedBinding, ...], Field(max_length=64)]


class TopologyRef(WireModel):
    scope: Scope
    proposal_id: Identifier
    sha256: Digest


class TopologyProjection(WireModel):
    wire_version: Literal['1'] = '1'
    authority: Literal['proposal_only'] = 'proposal_only'
    scientific_authority: Literal['not_established'] = 'not_established'
    reference: TopologyRef
    request: TopologyRequest
    policy: TopologyPolicy
    status: Literal['proposed', 'rejected']
    reasons: Annotated[tuple[Identifier, ...], Field(max_length=64)]
    definition: ExecutableCampaignV4 | None


__all__ = ['TopologyParent', 'NodeAddress', 'EvaluatorSwap', 'TransformInsertion', 'TopologyEdit',
           'TopologyPolicy', 'TopologyRequest', 'TopologyRef', 'TopologyProjection']
