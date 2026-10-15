"""Tool-owned population orchestration payloads; no new system command or route."""
from typing import Annotated, Literal
from amphora_contracts_core import ArtifactRef, Identifier, WireModel
from amphora_contracts_population import GenerationIdentity
from pydantic import Field
from amphora_contracts_graph_runtime import GraphNodeDetail
from amphora_contracts_node_inputs import NodeInputObservation
from amphora_contracts_execution_proofs import AcceptedToolExecution
from amphora_contracts_runtime import CompletionRecord
from amphora_contracts_artifacts import DerivationReceipt


class CollectPrimaryRequest(WireModel):
    schema_version: Literal["1"]
    prepared: ArtifactRef
    execution_plan: ArtifactRef
    method_plan: ArtifactRef
    method_scope_path: Annotated[tuple[Identifier, ...], Field(max_length=16)]


class CollectedPrimaryGeneration(WireModel):
    schema_version: Literal["1"]
    generation: GenerationIdentity
    prepared: ArtifactRef
    specification: ArtifactRef
    cohort: ArtifactRef
    declarations: ArtifactRef
    evaluations: ArtifactRef
    observations: ArtifactRef
    resolution: ArtifactRef


class PrimaryOwnerEvidence(WireModel):
    schema_version: Literal["1"]
    detail: GraphNodeDetail
    inputs: NodeInputObservation
    producer: AcceptedToolExecution | None
    completion: CompletionRecord | None
    derivation: DerivationReceipt | None


class PopulationReferenceGroup(WireModel):
    schema_version: Literal["1"]
    references: Annotated[tuple[ArtifactRef, ...], Field(min_length=1,max_length=120)]


class PrimarySumPolicy(WireModel):
    schema_version: Literal["1"]
    profile: Literal["primary-dimensionless-sum-v1"]


class UnconstrainedSynthetic(WireModel):
    schema_version: Literal["1"]
    profile: Literal["unconstrained-synthetic-v1"]


class FittedPrimaryGeneration(WireModel):
    schema_version: Literal["1"]
    generation: GenerationIdentity
    collected: ArtifactRef
    specification: ArtifactRef
    pool: ArtifactRef
    fitness: ArtifactRef
    resolution: ArtifactRef
