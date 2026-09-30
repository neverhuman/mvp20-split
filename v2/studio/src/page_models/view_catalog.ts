import type { GraphViewCatalog, ReadCut, SuccessorLineage } from "../contracts/observations.js";
import { cutKey, requireContext } from "./graph_window.js";
import { ReadFailure } from "../transport/failure.js";

const implemented = {
  execution_topology: { schema: "graph-runtime.topology-page", capability: "runtime.authored-topology.v1", bound: 256 },
  successor_lineage: { schema: "graph-runtime.successor-lineage", capability: "runtime.successor-lineage.v1", bound: 64 },
} as const;
export const scientificViews = Object.freeze([
  { id: "property_history", label: "Property history", owner: "Research" },
  { id: "material_state", label: "Material state summary", owner: "Research" },
  { id: "model_evidence", label: "Model and evidence comparison", owner: "Research / Data" },
  { id: "knowledge", label: "Domain knowledge", owner: "Knowledge" },
]);
export type RuntimeViewId = keyof typeof implemented;

/** Capability receipt, not a new source of domain truth or an arbitrary query language. */
export class ViewCatalog {
  private constructor(readonly page: GraphViewCatalog) {}
  static open(cut: ReadCut, page: GraphViewCatalog) {
    if (cutKey(cut) !== cutKey(page.cut)) throw new ReadFailure("resnapshot");
    const ids = new Set(page.views.map(view => view.view_id));
    if (ids.size !== page.views.length) throw new ReadFailure("invalid_response");
    for (const view of page.views) {
      const accepted = implemented[view.view_id];
      if (!accepted || (view.view_version ?? "1") !== "1" || (view.result_schema_version ?? "1") !== "1" ||
          (view.owner ?? "campaign-runtime") !== "campaign-runtime" || view.result_schema !== accepted.schema ||
          view.required_capability !== accepted.capability || view.result_bound !== accepted.bound)
        throw new ReadFailure("invalid_response");
      const names = view.filters.map(filter => filter.name ?? "radius").sort();
      if (JSON.stringify(names) !== JSON.stringify(view.view_id === "execution_topology" ? ["focus_activation_id", "radius", "scope_key"] : []))
        throw new ReadFailure("invalid_response");
      for (const filter of view.filters) if ((filter.required ?? false) !== (filter.name === "scope_key")) throw new ReadFailure("invalid_response");
    }
    return new ViewCatalog(structuredClone(page));
  }
  available(name: string) { return this.page.views.some(view => view.view_id === name); }
  resolve(name: string, filters: Record<string, unknown>) {
    const view = this.page.views.find(item => item.view_id === name);
    if (!view) throw new ReadFailure("unavailable");
    if (Object.keys(filters).some(name => !view.filters.some(filter => (filter.name ?? "radius") === name))) throw new ReadFailure("invalid_response");
    const values: Record<string, string | number> = {};
    for (const filter of view.filters) {
      const name = filter.name ?? "radius";
      const value = filters[name];
      if (value === undefined) {
        if (filter.required) throw new ReadFailure("invalid_response");
        if (name === "radius") values[name] = 1;
      } else if (filter.name === "scope_key" || filter.name === "focus_activation_id") {
        if (typeof value !== "string" || !/^[0-9a-f]{64}$/.test(value)) throw new ReadFailure("invalid_response");
        values[name] = value;
      } else {
        if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0 || value > 2)
          throw new ReadFailure("invalid_response");
        values[name] = value;
      }
    }
    return { definition: view, filters: values };
  }
  acceptLineage(lineage: SuccessorLineage) {
    this.resolve("successor_lineage", {});
    const cut = this.page.cut;
    requireContext({ scope: cut.scope, run: cut.run_id }, lineage.scope, lineage.run_id);
    if (lineage.plan_sha256 !== cut.plan_sha256 || lineage.carried.length > 64) throw new ReadFailure("invalid_response");
    return structuredClone(lineage);
  }
}
