import type { GraphScopePage, GraphSnapshotPage, TopologyQuery } from "../contracts/observations.js";
import type { NavigationSource } from "../transport/observations.js";
import { asReadFailure, ReadFailure } from "../transport/failure.js";
import { cutKey } from "./graph_window.js";
import { RequestLane } from "./request_lane.js";
import { TopologyWindow } from "./topology_window.js";
import type { RegionPhase } from "./monitor.js";

type Anchor = GraphSnapshotPage["snapshot"];
export interface NavigationView {
  readonly phase: RegionPhase;
  readonly scopes: GraphScopePage | null;
  readonly topology: TopologyWindow | null;
  readonly topologyPhase: RegionPhase;
  readonly loadingMore: boolean;
  readonly error: ReadFailure | null;
}

/** Owns navigation requests under the Monitor's snapshot; never fetches a competing snapshot. */
export class NavigationModel {
  private anchor: Anchor | null = null;
  private disposed = false;
  private loadedScopes = 0;
  private readonly scopeLane = new RequestLane();
  private readonly topologyLane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private view: NavigationView = Object.freeze({ phase: "idle", scopes: null, topology: null,
    topologyPhase: "idle", loadingMore: false, error: null });

  constructor(private readonly source: NavigationSource) {}
  get snapshot() { return this.view; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private patch(fields: Partial<NavigationView>) {
    if (this.disposed) return;
    this.view = Object.freeze({ ...this.view, ...fields });
    for (const listener of this.listeners) listener();
  }
  bind(anchor: Anchor | null) {
    if (this.disposed) return;
    if (anchor && this.anchor && cutKey(anchor.cut) === cutKey(this.anchor.cut) && anchor.snapshot_token === this.anchor.snapshot_token) return;
    this.scopeLane.cancel(); this.topologyLane.cancel();
    this.anchor = anchor ? structuredClone(anchor) : null;
    this.loadedScopes = 0;
    this.patch({ phase: "idle", scopes: null, topology: null, topologyPhase: "idle", loadingMore: false, error: null });
  }
  private fail(raw: unknown, topology: boolean) {
    const error = asReadFailure(raw);
    if (error.kind === "aborted") return;
    if (error.kind === "denied" || error.kind === "resnapshot") {
      this.scopeLane.cancel(); this.topologyLane.cancel(); this.anchor = null;
      this.patch({ phase: error.kind === "denied" ? "denied" : "stale", scopes: null, topology: null,
        topologyPhase: "idle", loadingMore: false, error });
    } else this.patch(topology ? { topologyPhase: "failed", loadingMore: false, error } : { phase: "failed", error });
  }

  async scopes(parent?: string, next = false) {
    if (!this.anchor || this.disposed) return;
    const previous = this.view.scopes;
    if (next && (!previous?.next_cursor || previous.parent_activation_id !== (parent ?? null))) return;
    const anchor = this.anchor, ticket = this.scopeLane.begin();
    const loaded = next ? this.loadedScopes : 0;
    this.topologyLane.cancel();
    this.patch({ phase: "loading", scopes: null, topology: null, topologyPhase: "idle", loadingMore: false, error: null });
    try {
      const page = await this.source.scopes(anchor.cut.run_id, anchor.snapshot_token, parent,
        next ? previous!.next_cursor! : undefined, ticket.signal);
      if (!ticket.current()) return;
      if (cutKey(page.cut) !== cutKey(anchor.cut)) throw new ReadFailure("resnapshot");
      if (page.parent_activation_id !== (parent ?? null) || page.scopes.length > page.scope_count ||
          new Set(page.scopes.map(scope => scope.scope_key)).size !== page.scopes.length ||
          page.scopes.some(scope => scope.parent_activation_id !== (parent ?? null)) ||
          loaded + page.scopes.length > page.scope_count ||
          page.next_cursor === null && loaded + page.scopes.length !== page.scope_count ||
          page.next_cursor !== null && (page.scopes.length === 0 || loaded + page.scopes.length >= page.scope_count) ||
          next && (page.scope_count !== previous!.scope_count || page.next_cursor === previous!.next_cursor ||
            page.scopes.some(scope => previous!.scopes.some(old => old.scope_key === scope.scope_key))))
        throw new ReadFailure("invalid_response");
      this.loadedScopes = loaded + page.scopes.length;
      this.patch({ phase: page.scope_count ? "ready" : "empty", scopes: structuredClone(page) });
    } catch (error) { if (ticket.current()) this.fail(error, false); }
  }

  async open(scope: string, query: TopologyQuery = {}) {
    if (!this.anchor || this.disposed) return;
    const anchor = this.anchor, ticket = this.topologyLane.begin();
    this.patch({ topology: null, topologyPhase: "loading", loadingMore: false, error: null });
    try {
      const page = await this.source.topology(anchor.cut.run_id, scope, anchor.snapshot_token, query, undefined, ticket.signal);
      if (!ticket.current()) return;
      const topology = TopologyWindow.open(anchor.cut, scope, query, page);
      this.patch({ topology, topologyPhase: topology.page.node_count ? "ready" : "empty" });
    } catch (error) { if (ticket.current()) this.fail(error, true); }
  }

  async more() {
    const current = this.view.topology;
    if (!this.anchor || this.disposed || this.view.loadingMore || !current?.page.next_cursor || this.view.topologyPhase !== "ready") return;
    const anchor = this.anchor, ticket = this.topologyLane.begin();
    this.patch({ loadingMore: true, error: null });
    try {
      const page = await this.source.topology(anchor.cut.run_id, current.page.graph_scope.scope_key,
        anchor.snapshot_token, current.page.query, current.page.next_cursor, ticket.signal);
      if (!ticket.current()) return;
      this.patch({ topology: current.append(page), loadingMore: false });
    } catch (error) { if (ticket.current()) this.fail(error, true); }
  }

  dispose() {
    this.scopeLane.cancel(); this.topologyLane.cancel(); this.listeners.clear(); this.anchor = null; this.disposed = true;
  }
}
