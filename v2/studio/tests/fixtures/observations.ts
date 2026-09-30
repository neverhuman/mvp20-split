/** Synthetic public-wire examples; no scientific result or live backend claim. */
import type { GraphSnapshotPage, GraphNodeDetail, GraphInvalidationPage, GraphNode } from "../../src/contracts/observations.js";

export const scope = { tenant_id: "synthetic", project_id: "studio-spike" };
export const context = { scope, run: "run-1" };
export const id = (index: number) => index.toString(16).padStart(64, "0");
export const node = (index: number): GraphNode => ({ activation_id: id(index), path: {
  schema_version: "2", node_id: `node-${index}`, occurrences: [] }, kind: "invoke", status: "issued", reason_code: null });

export function snapshot(options: { revision?: number; ids?: number[]; total?: number; next?: string | null; run?: string } = {}): GraphSnapshotPage {
  const revision = options.revision ?? 1, ids = options.ids ?? [1, 2];
  return { schema_version: "1", snapshot: { cut: { scope, run_id: options.run ?? context.run, plan_sha256: "a".repeat(64),
    revision, frontier_revision: revision }, status: "running", budget: { limit: 8, reserved: 0, spent: 0 },
    query: { scope_key: null, frontier_only: false }, node_count: options.total ?? ids.length,
    snapshot_token: `snapshot-${revision}`, event_cursor: `events-${revision}` }, nodes: ids.map(node), next_cursor: options.next ?? null };
}

export function detail(index: number, revision = 1): GraphNodeDetail {
  return { schema_version: "1", cut: snapshot({ revision }).snapshot.cut, node: node(index), scope_key: "c".repeat(64),
    parent_activation_id: null, outputs: [], attempts: [], next_cursor: null };
}

export function events(revisions: number[], observed = revisions.at(-1) ?? 1, more = false): GraphInvalidationPage {
  return { schema_version: "1", scope, run_id: context.run, observed_revision: observed,
    entries: revisions.map((revision) => ({ event_id: `event-${revision}`, revision, kind: "run_changed" })),
    next_cursor: `events-${observed}`, has_more: more };
}

export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
