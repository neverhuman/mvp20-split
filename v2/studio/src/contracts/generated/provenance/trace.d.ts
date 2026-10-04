/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ConfigurationSha256 = string;
export type ConverterId = string;
export type ConverterVersion = string;
export type Disposition = "normalized" | "unresolved" | "quarantined";
export type Origin = "copied" | "converted" | "inferred" | "missing";
export type End = number;
export type Sha256 = string;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha2561 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2562 = string;
export type SizeBytes = number;
export type RevisionId = string;
export type SourceId = string;
export type Start = number;
export type Unit = "byte";
/**
 * @maxItems 32
 */
export type Spans = SourceSpan[];
/**
 * @maxItems 32
 */
export type StepIndices = number[];
export type TargetPath = string;
/**
 * @minItems 1
 * @maxItems 256
 */
export type Fields = FieldOrigin[];
export type TraceId = string;
export type ConfigurationSha2561 = string;
export type Kind = "deterministic" | "inference";
export type TransformId = string;
export type Version1 = string;
/**
 * @minItems 1
 * @maxItems 32
 */
export type Transforms = TransformStep[];
export type Code = string;
export type TargetPath1 = string | null;
/**
 * @maxItems 64
 */
export type Warnings = ConversionWarning[];
export type WireVersion = "1";

export interface ConversionTrace {
  configuration_sha256: ConfigurationSha256;
  converter_id: ConverterId;
  converter_version: ConverterVersion;
  disposition: Disposition;
  fields: Fields;
  output: ArtifactRef;
  scope: Scope;
  source: SourceRevisionRef;
  source_schema: SchemaRef;
  target_schema: SchemaRef;
  trace_id: TraceId;
  transforms: Transforms;
  warnings: Warnings;
  wire_version: WireVersion;
}
/**
 * Missing values have no fabricated value; outputs live in scoped artifacts.
 */
export interface FieldOrigin {
  origin: Origin;
  spans: Spans;
  step_indices: StepIndices;
  target_path: TargetPath;
}
/**
 * Half-open byte range; owner verifies ordering, bounds and exact content.
 */
export interface SourceSpan {
  end: End;
  sha256: Sha256;
  source: SourceRevisionRef;
  start: Start;
  unit: Unit;
}
export interface SourceRevisionRef {
  raw: ArtifactRef;
  revision_id: RevisionId;
  scope: Scope;
  source_id: SourceId;
}
export interface ArtifactRef {
  artifact_id: ArtifactId;
  media_type: MediaType;
  schema_ref: SchemaRef;
  scope: Scope;
  sha256: Sha2562;
  size_bytes: SizeBytes;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha2561;
  version: Version;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface TransformStep {
  configuration_sha256: ConfigurationSha2561;
  kind: Kind;
  transform_id: TransformId;
  version: Version1;
}
export interface ConversionWarning {
  code: Code;
  target_path: TargetPath1;
}
