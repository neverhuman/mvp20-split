/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ActivationId = string;
export type FrontierRevision = number;
export type PlanSha256 = string;
export type Revision = number;
export type RunId = string;
export type ProjectId = string;
export type TenantId = string;
export type ItemCount = number;
export type Index = number;
export type Value =
  (BooleanConstant | IntegerConstant | NumberValue | StringConstant | ArtifactConstant) | MissingValue;
export type Kind = "boolean";
export type Value1 = boolean;
export type Kind1 = "integer";
export type Unit = string;
export type Value2 = number;
export type Kind2 = "number";
export type Unit1 = string;
export type Value3 = string;
export type Kind3 = "string";
export type Value4 = string;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
export type Kind4 = "artifact";
export type Representation = string;
export type Unit2 = string;
export type Kind5 = "missing";
export type MemberId = string;
export type ReasonCode = string;
/**
 * @maxItems 100
 */
export type Items = GraphValueItem[];
export type NextCursor = string | null;
export type Port = string;
export type SchemaVersion = "1";

export interface GraphValuePage {
  activation_id: ActivationId;
  cut: GraphReadCut;
  item_count: ItemCount;
  items: Items;
  next_cursor: NextCursor;
  port: Port;
  schema_version?: SchemaVersion;
}
export interface GraphReadCut {
  frontier_revision: FrontierRevision;
  plan_sha256: PlanSha256;
  revision: Revision;
  run_id: RunId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface GraphValueItem {
  index: Index;
  value: Value;
}
export interface BooleanConstant {
  kind: Kind;
  value: Value1;
}
export interface IntegerConstant {
  kind: Kind1;
  unit?: Unit;
  value: Value2;
}
export interface NumberValue {
  kind: Kind2;
  unit?: Unit1;
  value: Value3;
}
export interface StringConstant {
  kind: Kind3;
  value: Value4;
}
export interface ArtifactConstant {
  artifact: ArtifactRef;
  kind: Kind4;
  representation: Representation;
  unit: Unit2;
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
export interface MissingValue {
  kind: Kind5;
  member_id: MemberId;
  reason_code: ReasonCode;
}
