import { decodeAuthoring } from "../../contracts/authoring.js";
import type { DefinitionUniverse, ReleaseSnapshot } from "../../contracts/authoring.js";

type Lock = DefinitionUniverse["reviewed_tools"][number];
type Reference = DefinitionUniverse["schemas"][number];
export type ToolChoiceReason = "not_reviewed" | "release_inactive" | "metadata_mismatch" | "schema_unavailable";
export interface ToolChoice {
  release: ReleaseSnapshot;
  authoringAvailable: boolean;
  reasons: ToolChoiceReason[];
  executionEligibility: "not_checked";
}

const referenceKey = (value: Reference) => JSON.stringify([value.schema_id, value.version, value.sha256]);
const bindingKey = (value: Lock["tool"]) => JSON.stringify([value.capability_id, value.release, value.contract_version, value.image_sha256]);
const portsKey = (value: Lock["input_schemas"]) => JSON.stringify(value.map(port => [port.port, referenceKey(port.schema_ref)]).sort());
function sameLock(left: Lock, right: Lock) {
  return bindingKey(left.tool) === bindingKey(right.tool) && left.descriptor_sha256 === right.descriptor_sha256 &&
    portsKey(left.input_schemas) === portsKey(right.input_schemas) && portsKey(left.output_schemas) === portsKey(right.output_schemas) &&
    (left.checkpoint_schema ? referenceKey(left.checkpoint_schema) : null) === (right.checkpoint_schema ? referenceKey(right.checkpoint_schema) : null);
}
function descriptorMatches(release: ReleaseSnapshot) {
  const { tool } = release.descriptor, { lock } = release;
  const ports = (items: typeof tool.inputs) => items.map(item => ({ port: item.name, schema_ref: item.schema_ref }));
  return bindingKey(tool.binding) === bindingKey(lock.tool) &&
    new Set(tool.inputs.map(port => port.name)).size === tool.inputs.length &&
    new Set(tool.outputs.map(port => port.name)).size === tool.outputs.length &&
    portsKey(ports(tool.inputs)) === portsKey(lock.input_schemas) && portsKey(ports(tool.outputs)) === portsKey(lock.output_schemas) &&
    (tool.checkpoint_schema ? referenceKey(tool.checkpoint_schema) : null) === (lock.checkpoint_schema ? referenceKey(lock.checkpoint_schema) : null);
}

/** A bounded current discovery page joined to compiler review, never a cached admission grant. */
export class ToolChoices {
  private readonly universe: DefinitionUniverse;
  private readonly choices: ToolChoice[];

  constructor(universe: DefinitionUniverse, releases: readonly ReleaseSnapshot[]) {
    decodeAuthoring("universe", universe);
    if (releases.length > 100) throw new Error("tool_page_too_large");
    const reviewed = new Map(universe.reviewed_tools.map(lock => [bindingKey(lock.tool), lock]));
    const schemas = new Set(universe.schemas.map(referenceKey));
    if (reviewed.size !== universe.reviewed_tools.length || schemas.size !== universe.schemas.length) throw new Error("duplicate_reviewed_identity");
    const seen = new Set<string>();
    this.choices = releases.map(raw => {
      const release = decodeAuthoring("release", raw);
      if (release.scope.tenant_id !== universe.scope.tenant_id || release.scope.project_id !== universe.scope.project_id) throw new Error("release_scope_mismatch");
      if (seen.has(release.lock.descriptor_sha256)) throw new Error("duplicate_release_identity");
      seen.add(release.lock.descriptor_sha256);
      const reasons: ToolChoiceReason[] = [], lock = reviewed.get(bindingKey(release.lock.tool));
      if (!lock) reasons.push("not_reviewed");
      if (!descriptorMatches(release) || (lock && !sameLock(lock, release.lock))) reasons.push("metadata_mismatch");
      const references = [...release.lock.input_schemas, ...release.lock.output_schemas].map(port => port.schema_ref);
      if (release.lock.checkpoint_schema) references.push(release.lock.checkpoint_schema);
      if (references.some(reference => !schemas.has(referenceKey(reference)))) reasons.push("schema_unavailable");
      if (release.status !== "active") reasons.push("release_inactive");
      return { release: structuredClone(release), authoringAvailable: reasons.length === 0, reasons, executionEligibility: "not_checked" };
    });
    this.universe = structuredClone(universe);
  }

  get snapshot(): ToolChoice[] { return structuredClone(this.choices); }
  get universeDigest() { return this.universe.universe_sha256; }
  select(descriptor: string): ReleaseSnapshot {
    const choice = this.choices.find(item => item.release.lock.descriptor_sha256 === descriptor);
    if (!choice?.authoringAvailable) throw new Error("tool_unavailable_for_authoring");
    return structuredClone(choice.release);
  }
}
