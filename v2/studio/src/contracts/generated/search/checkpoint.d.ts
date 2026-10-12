/* Generated from the published Python-owned serialization schema. Do not edit. */

export type CandidateId = string;
export type Disposition = "proposed" | "rejected" | "duplicate";
export type End = number;
export type Start = number;
export type DuplicateOf = string | null;
export type Generation = number;
/**
 * @minItems 1
 * @maxItems 32
 */
export type Genes = number[];
export type Operator = "seed" | "variation";
export type Ordinal = number;
/**
 * @maxItems 2
 */
export type Parents = string[];
export type ReasonCode = string | null;
/**
 * @minItems 1
 * @maxItems 256
 */
export type Attempts = CandidateAttempt[];
export type Generation1 = number;
export type CandidateId1 = string;
export type EvaluationId = string;
export type Outcome = EvaluatedFitness | UnavailableFitness;
export type ConstraintViolation = number;
export type ConstraintsSha256 = string;
export type CapabilityId = string;
export type ContractVersion = "1";
export type ImageSha256 = string;
export type Release = string;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
/**
 * @minItems 1
 * @maxItems 32
 */
export type Evidence = ArtifactRef[];
export type ObjectiveId = string;
export type Unit = string;
export type Value = number;
/**
 * @minItems 1
 * @maxItems 16
 */
export type Objectives = ObjectiveValue[];
export type Quality = "synthetic" | "predicted" | "measured";
export type Status = "evaluated";
/**
 * @maxItems 32
 */
export type Evidence1 = ArtifactRef[];
export type ReasonCode1 = string;
export type Status1 = "unknown" | "failed" | "inapplicable";
export type RequestSha256 = string;
export type SchemaVersion = "1";
/**
 * @maxItems 256
 */
export type Observations = EvaluationObservation[];
export type CandidateId2 = string;
export type EvaluationId1 = string;
export type RequestSha2561 = string;
/**
 * @maxItems 256
 */
export type Pending = PendingEvaluation[];
export type Phase = "awaiting_evaluations" | "ready_to_select" | "selected" | "stopped";
/**
 * @maxItems 128
 */
export type Population = string[];
export type EvaluationsIssued = number;
export type EvaluationsTerminal = number;
export type GenerationsCompleted = number;
export type UnchangedFrontGenerations = number;
export type Algorithm = "sha256-counter-u53-v1";
export type Counter = number;
export type Seed = string;
export type SchemaVersion1 = "1";
export type Disposition1 =
  "selected" | "zero_requested" | "no_feasible_candidates" | "insufficient_feasible_candidates";
export type MembershipSha256 = string;
export type Policy = "constrained-pareto-feasible-v1";
export type Boundary = boolean;
export type CandidateId3 = string;
export type Distance = number;
export type Feasible = boolean;
export type Front = number;
/**
 * @maxItems 256
 */
export type Ranks = SelectionRank[];
export type Requested = number;
/**
 * @maxItems 128
 */
export type Selected = string[];
export type MaxEvaluations = number;
export type MaxGenerations = number;
export type PopulationSize = number;
export type UnchangedFrontLimit = number | null;
export type Completion = "all_frozen_members_terminal";
/**
 * @maxItems 32
 */
export type Context = ArtifactRef[];
export type Name = string;
export type Sha2562 = string;
export type Version1 = string;
/**
 * @minItems 1
 * @maxItems 32
 */
export type Implementations = ImplementationPin[];
export type Direction = "minimize" | "maximize";
export type ObjectiveId1 = string;
export type Unit1 = string;
/**
 * @minItems 1
 * @maxItems 16
 */
export type Objectives1 = NumericObjective[];
export type CrossoverProbability = number;
export type MutationFraction = number;
export type MutationProbability = number;
export type Rng = "sha256-counter-u53-v1";
export type Selection = "constrained-pareto-feasible-v1";
export type Variation = "box-convex-uniform-v1";
export type SchemaVersion2 = "1";
export type SearchId = string;
export type Seed1 = string;
export type Lower = number;
export type Unit2 = string;
export type Upper = number;
export type VariableId = string;
/**
 * @minItems 1
 * @maxItems 32
 */
export type Variables = NumericVariable[];
export type SpecificationSha256 = string;
export type StopReason =
  | ("generation_budget" | "evaluation_budget" | "unchanged_front" | "no_feasible_candidates" | "unavailable_fitness")
  | null;

export interface SearchCheckpoint {
  attempts: Attempts;
  generation: Generation1;
  observations: Observations;
  pending: Pending;
  phase: Phase;
  population: Population;
  previous: ArtifactRef | null;
  progress: SearchProgress;
  rng: RngState;
  schema_version: SchemaVersion1;
  selection: SelectionReceipt | null;
  specification: SearchSpec;
  specification_sha256: SpecificationSha256;
  stop_reason: StopReason;
}
export interface CandidateAttempt {
  candidate_id: CandidateId;
  disposition: Disposition;
  draws: RngInterval;
  duplicate_of: DuplicateOf;
  generation: Generation;
  genes: Genes;
  operator: Operator;
  ordinal: Ordinal;
  parents: Parents;
  reason_code: ReasonCode;
}
export interface RngInterval {
  end: End;
  start: Start;
}
export interface EvaluationObservation {
  candidate_id: CandidateId1;
  evaluation_id: EvaluationId;
  outcome: Outcome;
  request_sha256: RequestSha256;
  schema_version: SchemaVersion;
  scope: Scope;
}
export interface EvaluatedFitness {
  constraint_violation: ConstraintViolation;
  constraints_sha256: ConstraintsSha256;
  evaluator: ToolBinding;
  evidence: Evidence;
  objectives: Objectives;
  quality: Quality;
  status: Status;
}
export interface ToolBinding {
  capability_id: CapabilityId;
  contract_version: ContractVersion;
  image_sha256: ImageSha256;
  release: Release;
}
export interface ArtifactRef {
  artifact_id: ArtifactId;
  media_type: MediaType;
  schema_ref: SchemaRef;
  scope: Scope;
  sha256: Sha2561;
  size_bytes: SizeBytes;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha256;
  version: Version;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface ObjectiveValue {
  objective_id: ObjectiveId;
  unit: Unit;
  value: Value;
}
export interface UnavailableFitness {
  evidence: Evidence1;
  reason_code: ReasonCode1;
  status: Status1;
}
export interface PendingEvaluation {
  candidate_id: CandidateId2;
  evaluation_id: EvaluationId1;
  request_sha256: RequestSha2561;
}
export interface SearchProgress {
  evaluations_issued: EvaluationsIssued;
  evaluations_terminal: EvaluationsTerminal;
  generations_completed: GenerationsCompleted;
  unchanged_front_generations: UnchangedFrontGenerations;
}
export interface RngState {
  algorithm: Algorithm;
  counter: Counter;
  seed: Seed;
}
export interface SelectionReceipt {
  disposition: Disposition1;
  membership_sha256: MembershipSha256;
  policy: Policy;
  ranks: Ranks;
  requested: Requested;
  selected: Selected;
}
export interface SelectionRank {
  boundary: Boundary;
  candidate_id: CandidateId3;
  distance: Distance;
  feasible: Feasible;
  front: Front;
}
export interface SearchSpec {
  budget: SearchBudget;
  evaluator: EvaluatorPolicy;
  implementations: Implementations;
  objectives: Objectives1;
  operators: SearchOperators;
  representation: SchemaRef;
  schema_version: SchemaVersion2;
  scope: Scope;
  search_id: SearchId;
  seed: Seed1;
  variables: Variables;
}
export interface SearchBudget {
  max_evaluations: MaxEvaluations;
  max_generations: MaxGenerations;
  population_size: PopulationSize;
  unchanged_front_limit: UnchangedFrontLimit;
}
export interface EvaluatorPolicy {
  completion: Completion;
  constraints: ArtifactRef;
  context: Context;
  tool: ToolBinding;
}
export interface ImplementationPin {
  name: Name;
  sha256: Sha2562;
  version: Version1;
}
export interface NumericObjective {
  direction: Direction;
  objective_id: ObjectiveId1;
  unit: Unit1;
}
export interface SearchOperators {
  crossover_probability: CrossoverProbability;
  mutation_fraction: MutationFraction;
  mutation_probability: MutationProbability;
  rng: Rng;
  selection: Selection;
  variation: Variation;
}
export interface NumericVariable {
  lower: Lower;
  unit: Unit2;
  upper: Upper;
  variable_id: VariableId;
}
