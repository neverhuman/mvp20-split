/* Generated from the published Python-owned serialization schema. Do not edit. */

export type GraphId = string;
export type ProjectId = string;
export type TenantId = string;
export type Revision = number;
export type Sha256 = string;
export type Selection = GraphEntitySelection | GraphAssertionSelection;
export type Kind = "entity";
export type EntityId = string;
export type Revision1 = number;
export type Kind1 = "assertion";
export type AssertionId = string;
export type Revision2 = number;
export type WireVersion = "1";

export interface GraphObjectRequest {
  revision: DomainRevisionRef;
  selection: Selection;
  wire_version: WireVersion;
}
export interface DomainRevisionRef {
  graph: DomainGraphRef;
  revision: Revision;
  sha256: Sha256;
}
export interface DomainGraphRef {
  graph_id: GraphId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface GraphEntitySelection {
  kind: Kind;
  reference: EntityRevisionRef;
}
export interface EntityRevisionRef {
  entity_id: EntityId;
  graph: DomainGraphRef;
  revision: Revision1;
}
export interface GraphAssertionSelection {
  kind: Kind1;
  reference: AssertionRevisionRef;
}
export interface AssertionRevisionRef {
  assertion_id: AssertionId;
  graph: DomainGraphRef;
  revision: Revision2;
}
