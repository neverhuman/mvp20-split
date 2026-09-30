import type { GraphSnapshotPage, ReadCut, ReadQuery, GraphNode } from "../contracts/observations.js";
import { ReadFailure } from "../transport/failure.js";

export interface RunContext { readonly scope: ReadCut["scope"]; readonly run: string; }
export const queryKey = (query: ReadQuery) => JSON.stringify([query.scope_key ?? null, query.frontier_only ?? false]);
export const contextKey = (context: RunContext) => JSON.stringify([context.scope.tenant_id, context.scope.project_id, context.run]);
export const cutKey = (cut: ReadCut) => JSON.stringify([cut.scope.tenant_id, cut.scope.project_id, cut.run_id, cut.plan_sha256, cut.revision, cut.frontier_revision]);

export function requireContext(context: RunContext, scope: ReadCut["scope"], run: string) {
  if (contextKey(context) !== contextKey({ scope, run })) throw new ReadFailure("invalid_response");
}

export class GraphWindow {
  private constructor(readonly snapshot: GraphSnapshotPage["snapshot"], readonly nodes: readonly GraphNode[], readonly next: string | null) {}

  static open(context: RunContext, query: ReadQuery, page: GraphSnapshotPage) {
    requireContext(context, page.snapshot.cut.scope, page.snapshot.cut.run_id);
    if (queryKey(query) !== queryKey(page.snapshot.query)) throw new ReadFailure("invalid_response");
    return GraphWindow.checked(page.snapshot, page.nodes, page.next_cursor);
  }

  private static checked(snapshot: GraphSnapshotPage["snapshot"], nodes: readonly GraphNode[], next: string | null) {
    if (nodes.length > snapshot.node_count || new Set(nodes.map((node) => node.activation_id)).size !== nodes.length ||
        next === null && nodes.length !== snapshot.node_count || next !== null && (nodes.length === 0 || nodes.length >= snapshot.node_count))
      throw new ReadFailure("invalid_response");
    return new GraphWindow(snapshot, Object.freeze([...nodes]), next);
  }

  append(page: GraphSnapshotPage) {
    if (cutKey(page.snapshot.cut) !== cutKey(this.snapshot.cut)) throw new ReadFailure("resnapshot");
    if (queryKey(page.snapshot.query) !== queryKey(this.snapshot.query) || page.snapshot.node_count !== this.snapshot.node_count ||
        page.snapshot.snapshot_token !== this.snapshot.snapshot_token || page.snapshot.event_cursor !== this.snapshot.event_cursor ||
        page.snapshot.status !== this.snapshot.status || page.snapshot.budget.limit !== this.snapshot.budget.limit ||
        page.snapshot.budget.reserved !== this.snapshot.budget.reserved || page.snapshot.budget.spent !== this.snapshot.budget.spent ||
        !this.next || page.next_cursor === this.next)
      throw new ReadFailure("invalid_response");
    return GraphWindow.checked(this.snapshot, [...this.nodes, ...page.nodes], page.next_cursor);
  }

  get omitted() { return this.snapshot.node_count - this.nodes.length; }
}
