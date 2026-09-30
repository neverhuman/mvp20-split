import type { GraphTopologyPage, ReadCut, TopologyQuery } from "../contracts/observations.js";
import { cutKey } from "./graph_window.js";
import { ReadFailure } from "../transport/failure.js";

const queryKey = (query: TopologyQuery) => JSON.stringify([query.focus_activation_id ?? null, query.radius ?? 1]);
const edgeKey = (edge: GraphTopologyPage["edges"][number]) => JSON.stringify([edge.source, edge.target, edge.route]);
const invalid = () => { throw new ReadFailure("invalid_response"); };

/** A single bounded occurrence scope. Links to unloaded targets stay explicitly unresolved. */
export class TopologyWindow {
  private constructor(readonly page: GraphTopologyPage) {}

  static open(cut: ReadCut, scope: string, query: TopologyQuery, page: GraphTopologyPage) {
    if (cutKey(cut) !== cutKey(page.cut)) throw new ReadFailure("resnapshot");
    if (scope !== page.graph_scope.scope_key || queryKey(query) !== queryKey(page.query)) invalid();
    return TopologyWindow.checked(page);
  }

  private static checked(page: GraphTopologyPage) {
    const ids = new Set(page.nodes.map(node => node.activation.activation_id));
    if (ids.size !== page.nodes.length || page.nodes.length > page.node_count ||
        page.node_count > page.graph_scope.node_count || page.edges.length > page.edge_count ||
        new Set(page.edges.map(edgeKey)).size !== page.edges.length ||
        page.edges.some(edge => !ids.has(edge.source)) ||
        page.next_cursor === null && (page.nodes.length !== page.node_count || page.edges.length !== page.edge_count ||
          page.edges.some(edge => !ids.has(edge.target))) ||
        page.next_cursor !== null && (page.nodes.length === 0 || page.nodes.length >= page.node_count)) invalid();
    return new TopologyWindow(structuredClone(page));
  }

  append(page: GraphTopologyPage) {
    const previous = this.page;
    if (cutKey(previous.cut) !== cutKey(page.cut)) throw new ReadFailure("resnapshot");
    if (!previous.next_cursor || page.next_cursor === previous.next_cursor ||
        JSON.stringify(page.graph_scope) !== JSON.stringify(previous.graph_scope) ||
        queryKey(page.query) !== queryKey(previous.query) || page.node_count !== previous.node_count ||
        page.edge_count !== previous.edge_count) invalid();
    // A producer charges each edge to its source page, including later pages.
    const incoming = new Set(page.nodes.map(node => node.activation.activation_id));
    if (page.edges.some(edge => !incoming.has(edge.source))) invalid();
    return TopologyWindow.checked({ ...page, nodes: [...previous.nodes, ...page.nodes], edges: [...previous.edges, ...page.edges] });
  }

  get visibleEdges() {
    const ids = new Set(this.page.nodes.map(node => node.activation.activation_id));
    return this.page.edges.filter(edge => ids.has(edge.target));
  }
  get omittedNodes() { return this.page.node_count - this.page.nodes.length; }
  get unresolvedEdges() { return this.page.edges.length - this.visibleEdges.length; }
}
