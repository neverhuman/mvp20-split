/* Generated from the published Python-owned serialization schema. Do not edit. */

export type FrontierRevision = number;
export type PlanSha256 = string;
export type Revision = number;
export type RunId = string;
export type ProjectId = string;
export type TenantId = string;
export type SchemaVersion = "1";
export type Kind = "digest";
export type Name = "scope_key" | "focus_activation_id";
export type Required = boolean;
export type Default = 1;
export type Kind1 = "integer";
export type Maximum = 2;
export type Minimum = 0;
export type Name1 = "radius";
export type Required1 = false;
/**
 * @maxItems 3
 */
export type Filters = (DigestViewFilter | RadiusViewFilter)[];
export type Owner = "campaign-runtime";
export type RequiredCapability = "runtime.authored-topology.v1" | "runtime.successor-lineage.v1";
export type ResultBound = number;
export type ResultSchema = "graph-runtime.topology-page" | "graph-runtime.successor-lineage";
export type ResultSchemaVersion = "1";
export type ViewId = "execution_topology" | "successor_lineage";
export type ViewVersion = "1";
/**
 * @maxItems 2
 */
export type Views = GraphViewDefinition[];

export interface GraphViewCatalog {
  cut: GraphReadCut;
  schema_version?: SchemaVersion;
  views: Views;
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
export interface GraphViewDefinition {
  filters: Filters;
  owner?: Owner;
  required_capability: RequiredCapability;
  result_bound: ResultBound;
  result_schema: ResultSchema;
  result_schema_version?: ResultSchemaVersion;
  view_id: ViewId;
  view_version?: ViewVersion;
}
export interface DigestViewFilter {
  kind?: Kind;
  name: Name;
  required: Required;
}
export interface RadiusViewFilter {
  default?: Default;
  kind?: Kind1;
  maximum?: Maximum;
  minimum?: Minimum;
  name?: Name1;
  required?: Required1;
}
