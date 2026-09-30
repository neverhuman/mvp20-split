/** Synthetic public-wire navigation examples, never scientific evidence. */
import type { GraphScopePage, GraphTopologyPage } from "../../src/contracts/observations.js";
import { id, node, snapshot } from "./observations.js";
import type { GraphViewCatalog, SuccessorLineage } from "../../src/contracts/observations.js";

export function catalog(): GraphViewCatalog {
  return { schema_version: "1", cut: snapshot().snapshot.cut, views: [
    { view_id: "execution_topology", view_version: "1", owner: "campaign-runtime", result_schema: "graph-runtime.topology-page",
      result_schema_version: "1", required_capability: "runtime.authored-topology.v1", result_bound: 256,
      filters: [{ kind: "digest", name: "scope_key", required: true }, { kind: "digest", name: "focus_activation_id", required: false },
        { kind: "integer", name: "radius", required: false, minimum: 0, maximum: 2, default: 1 }] },
    { view_id: "successor_lineage", view_version: "1", owner: "campaign-runtime", result_schema: "graph-runtime.successor-lineage",
      result_schema_version: "1", required_capability: "runtime.successor-lineage.v1", result_bound: 64, filters: [] },
  ] };
}

export function lineage(): SuccessorLineage {
  const cut = snapshot().snapshot.cut;
  return { schema_version: "1", scope: cut.scope, run_id: cut.run_id, plan_sha256: cut.plan_sha256,
    predecessor: { run_id: "parent-run", plan_sha256: id(300), revision: 8 }, carried: [], transfer_sha256: id(301) };
}

export function scopes(): GraphScopePage {
  return { schema_version: "1", cut: snapshot().snapshot.cut, parent_activation_id: null,
    scope_count: 1, scopes: [{ scope_key: id(100), definition_path: [], occurrences: [],
      parent_activation_id: null, status: "active", node_count: 2 }], next_cursor: null };
}

export function topology(): GraphTopologyPage {
  return { schema_version: "1", cut: snapshot().snapshot.cut, graph_scope: scopes().scopes[0]!,
    query: { focus_activation_id: null, radius: 1 }, node_count: 2, edge_count: 1,
    nodes: [1, 2].map(index => ({ activation: node(index), child_scope_count: 0 })),
    edges: [{ source: id(1), target: id(2), route: "next" }], next_cursor: null };
}
