"""Tool-owned population orchestration payloads; no new system command or route."""
from typing import Annotated, Literal
from amphora_contracts_core import ArtifactRef, Identifier, WireModel
from amphora_contracts_population import GenerationIdentity
from pydantic import Field,model_validator
from amphora_contracts_graph_runtime import GraphNodeDetail,GraphReadCut
from amphora_contracts_node_inputs import NodeInputObservation
from amphora_contracts_execution_proofs import AcceptedToolExecution
from amphora_contracts_search import RngState
from amphora_contracts_runtime import CompletionRecord
from amphora_contracts_artifacts import DerivationReceipt


class CollectPrimaryRequest(WireModel):
    schema_version: Literal["1"]
    prepared: ArtifactRef
    execution_plan: ArtifactRef
    method_plan: ArtifactRef
    method_scope_path: Annotated[tuple[Identifier, ...], Field(max_length=16)]


class CollectSuccessorSliceRequest(WireModel):
    schema_version: Literal["1"]
    sliced: ArtifactRef
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


class SelectedPrimaryGeneration(WireModel):
    schema_version: Literal["1"]
    generation: GenerationIdentity
    specification: ArtifactRef
    pool: ArtifactRef
    fitness: ArtifactRef
    resolution: ArtifactRef
    selection: ArtifactRef
    checkpoint: ArtifactRef
    source_proof: ArtifactRef
    work_cut: GraphReadCut
    stopped: bool
    stop_reason: Identifier | None


class PreparedPrimarySuccessor(WireModel):
    schema_version: Literal["1"]
    generation: GenerationIdentity
    prepared: ArtifactRef
    pool: ArtifactRef
    source_selected: ArtifactRef
    rng: RngState
    evaluations_planned: Annotated[int, Field(ge=0,le=8000)]
    logical_evaluation_capacity: Annotated[int, Field(ge=0,le=808000)]
    method_attempt_capacity: Annotated[int, Field(ge=0,le=9007199254740991)]
    disposition: Literal["evaluate","duplicate_only","evaluation_budget","attempt_budget"]


class PrimarySuccessorDecision(WireModel):
    schema_version: Literal["1"]
    checkpoint: ArtifactRef
    source_selected: ArtifactRef
    stopped: bool
    reason_code: Identifier | None
    successor: ArtifactRef | None
    work_cut: GraphReadCut

    @model_validator(mode="after")
    def consistent_decision(self):
        if self.stopped != (self.successor is None) or self.stopped != (self.reason_code is not None):
            raise ValueError("successor_decision_mismatch")
        refs=(self.checkpoint,self.source_selected,*(() if self.successor is None else (self.successor,)))
        if any(ref.scope!=self.work_cut.scope for ref in refs):
            raise ValueError("successor_decision_scope")
        return self
