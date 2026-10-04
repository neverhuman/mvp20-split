/* Generated from the published Python-owned serialization schema. Do not edit. */

export type AssertionTotal = number;
export type IsLatest = boolean;
export type EntityId = string;
export type GraphId = string;
export type ProjectId = string;
export type TenantId = string;
export type Revision = number;
export type Polarity = "affirmed" | "negated";
export type Posture = "reported" | "hypothesis" | "unresolved";
export type Predicate = string;
export type AssertionId = string;
export type Revision1 = number;
export type Retracted = boolean;
/**
 * @maxItems 128
 */
export type Assertions = GraphAssertionSummary[];
export type EntityType = string;
export type IsLatest1 = boolean;
export type Label = string;
/**
 * @maxItems 64
 */
export type Entities = GraphEntitySummary[];
export type EntityTotal = number;
export type AssertionOffset = number;
export type EntityOffset = number;
export type QuerySha256 = string;
export type QuerySha2561 = string;
export type AssertionLimit = number;
export type EntityLimit = number;
export type History = "current" | "retained";
export type Radius = number;
export type Revision2 = number;
export type Sha256 = string;
export type WireVersion = "1";
/**
 * @maxItems 320
 */
export type UnresolvedEntities = EntityRevisionRef[];
export type WireVersion1 = "1";

export interface GraphNeighborhoodPage {
  assertion_total: AssertionTotal;
  assertions: Assertions;
  entities: Entities;
  entity_total: EntityTotal;
  next_position: GraphViewPosition | null;
  query_sha256: QuerySha2561;
  request: GraphNeighborhoodRequest;
  unresolved_entities: UnresolvedEntities;
  wire_version: WireVersion1;
}
export interface GraphAssertionSummary {
  is_latest: IsLatest;
  object: EntityRevisionRef;
  polarity: Polarity;
  posture: Posture;
  predicate: Predicate;
  reference: AssertionRevisionRef;
  retracted: Retracted;
  subject: EntityRevisionRef;
}
export interface EntityRevisionRef {
  entity_id: EntityId;
  graph: DomainGraphRef;
  revision: Revision;
}
export interface DomainGraphRef {
  graph_id: GraphId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface AssertionRevisionRef {
  assertion_id: AssertionId;
  graph: DomainGraphRef;
  revision: Revision1;
}
export interface GraphEntitySummary {
  alias_target: EntityRevisionRef | null;
  entity_type: EntityType;
  is_latest: IsLatest1;
  label: Label;
  reference: EntityRevisionRef;
}
export interface GraphViewPosition {
  assertion_offset: AssertionOffset;
  entity_offset: EntityOffset;
  query_sha256: QuerySha256;
}
export interface GraphNeighborhoodRequest {
  assertion_limit?: AssertionLimit;
  entity_limit?: EntityLimit;
  focus: EntityRevisionRef;
  history?: History;
  position?: GraphViewPosition | null;
  radius?: Radius;
  revision: DomainRevisionRef;
  wire_version: WireVersion;
}
export interface DomainRevisionRef {
  graph: DomainGraphRef;
  revision: Revision2;
  sha256: Sha256;
}
