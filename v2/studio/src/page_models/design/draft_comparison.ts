import { decodeAuthoring } from "../../contracts/authoring.js";
import type { SaveDraft } from "../../contracts/authoring.js";

type LocalDraft = Pick<SaveDraft, "title" | "definition">;
type Category = "node" | "edge" | "binding" | "context" | "definition";
export interface DraftChange {
  path: string;
  category: Category;
  kind: "added" | "removed" | "changed" | "reordered";
  before?: unknown;
  after?: unknown;
}
const object = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === "object" && !Array.isArray(value);
const pointer = (parts: string[]) => "/" + parts.map(part => part.replaceAll("~", "~0").replaceAll("/", "~1")).join("/");

/** Structural review only: never a merge, compiler, compatibility verdict or admission grant. */
export class GraphDefinitionComparison {
  private readonly changes: DraftChange[] = [];
  private total = 0;
  private ambiguousNodes = false;

  constructor(base: LocalDraft, local: LocalDraft, private readonly limit = 200) {
    if (!Number.isSafeInteger(limit) || limit < 1 || limit > 200) throw new Error("comparison_limit_invalid");
    for (const value of [base, local]) {
      decodeAuthoring("save", { ...value, draft_id: "comparison", expected_revision: 0 });
      if (new TextEncoder().encode(JSON.stringify(value)).byteLength > 262144) throw new Error("comparison_too_large");
    }
    const a = base.definition, b = local.definition;
    if (a.scope.tenant_id !== b.scope.tenant_id || a.scope.project_id !== b.scope.project_id)
      throw new Error("comparison_context_mismatch");
    this.walk(base, local, []);
  }

  get snapshot() {
    return structuredClone({ changes: this.changes, total: this.total, omitted: this.total - this.changes.length,
      scientificCompatibility: "not_assessed" as const, validationRequired: this.total > 0,
      warnings: ["Structural changes do not establish scientific applicability or execution eligibility.",
        ...(this.ambiguousNodes ? ["Duplicate node identities: affected node lists are compared by position; repair before validation."] : [])] });
  }

  private add(parts: string[], kind: DraftChange["kind"], before: unknown, after: unknown) {
    this.total++;
    if (this.changes.length >= this.limit) return;
    const category: Category = parts.includes("context") ? "context" : parts.includes("edges") ? "edge"
      : parts.some(part => ["inputs", "outputs", "captures", "state", "members", "fields", "source", "collection", "subject", "predicate", "until"].includes(part)) ? "binding"
      : parts.includes("nodes") ? "node" : "definition";
    this.changes.push(structuredClone({ path: pointer(parts), category, kind,
      ...(before === undefined ? {} : { before }), ...(after === undefined ? {} : { after }) }));
  }

  private walk(before: unknown, after: unknown, parts: string[]) {
    if (parts.length > 64) throw new Error("comparison_too_deep");
    if (Object.is(before, after)) return;
    if (Array.isArray(before) && Array.isArray(after)) {
      if (parts.at(-1) === "nodes") {
        const left = this.nodes(before), right = this.nodes(after);
        if (left && right) {
          for (const id of new Set([...left.keys(), ...right.keys()])) this.walk(left.get(id), right.get(id), [...parts, `node:${id}`]);
          const commonLeft = [...left.keys()].filter(id => right.has(id)), commonRight = [...right.keys()].filter(id => left.has(id));
          if (JSON.stringify(commonLeft) !== JSON.stringify(commonRight)) this.add(parts, "reordered", [...left.keys()], [...right.keys()]);
          return;
        }
        this.ambiguousNodes = true;
      }
      for (let index = 0; index < Math.max(before.length, after.length); index++) this.walk(before[index], after[index], [...parts, String(index)]);
    } else if (object(before) && object(after)) {
      for (const key of [...new Set([...Object.keys(before), ...Object.keys(after)])].sort())
        this.walk(before[key], after[key], [...parts, key]);
    } else this.add(parts, before === undefined ? "added" : after === undefined ? "removed" : "changed", before, after);
  }

  private nodes(values: unknown[]): Map<string, unknown> | undefined {
    const result = new Map<string, unknown>();
    for (const value of values) {
      if (!object(value) || typeof value.node_id !== "string" || result.has(value.node_id)) return undefined;
      result.set(value.node_id, value);
    }
    return result;
  }
}

/** Same-campaign editor comparison retains its original stricter identity guard. */
export class DraftComparison extends GraphDefinitionComparison {
  constructor(base:LocalDraft,local:LocalDraft,limit=200) {
    if(base.definition.campaign_id!==local.definition.campaign_id)throw Error('comparison_context_mismatch');
    super(base,local,limit);
  }
}
