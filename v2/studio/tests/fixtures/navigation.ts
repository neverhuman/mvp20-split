/** Synthetic public-wire navigation examples, never scientific evidence. */
import type { GraphScopePage, GraphTopologyPage } from "../../src/contracts/observations.js";
import { id, node, snapshot } from "./observations.js";

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
