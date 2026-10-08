import type { GraphScopePage, GraphSnapshotPage, TopologyQuery } from "../contracts/observations.js";
import type { NavigationSource } from "../transport/observations.js";
import { asReadFailure, ReadFailure } from "../transport/failure.js";
import { cutKey } from "./graph_window.js";
import { RequestLane } from "./request_lane.js";
import { TopologyWindow } from "./topology_window.js";
import type { RegionPhase } from "./monitor.js";
import { checkedViewport, type Viewport } from "./scene.js";
import { InlineScopes } from './inline_scopes/model.js';

type Anchor = GraphSnapshotPage["snapshot"];
export interface NavigationView {
  readonly phase: RegionPhase;
  readonly scopes: GraphScopePage | null;
  readonly topology: TopologyWindow | null;
  readonly topologyPhase: RegionPhase;
  readonly loadingMore: boolean;
  readonly error: ReadFailure | null;
  readonly viewport: Viewport;
  readonly offset: number;
}

/** Owns navigation requests under the Monitor's snapshot; never fetches a competing snapshot. */
export class NavigationModel {
  private anchor: Anchor | null = null;
  private disposed = false;
  private loadedScopes = 0;
  private identity: string | null = null;
  private observationEpoch = 0;
  private interactionEpoch = 0;
  private readonly viewports = new Map<string, Viewport>();
  private bookmark: { parent: string | undefined; scope: string | undefined; query: TopologyQuery } = { parent: undefined, scope: undefined, query: {} };
  private readonly scopeLane = new RequestLane();
  private readonly topologyLane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private view: NavigationView = Object.freeze({ phase: "idle", scopes: null, topology: null,
    topologyPhase: "idle", loadingMore: false, error: null, viewport: { x: 24, y: 24, zoom: 0.85 }, offset: 0 });

  readonly inline: InlineScopes;
  constructor(private readonly source: NavigationSource) { this.inline=new InlineScopes(source,error=>this.fail(error,true)); }
  get snapshot() { return this.view; }
  viewportFor(scope: string) { return this.viewports.get(scope); }
  setViewport(viewport: Viewport, viewKey?:string) {
    const value = checkedViewport(viewport);
    const scope = viewKey ?? this.view.topology?.page.graph_scope.scope_key;
    if (scope) this.viewports.set(scope, value);
    this.patch({ viewport: value });
  }
  setOffset(offset: number) {
    if (!Number.isSafeInteger(offset) || offset < 0 || offset % 200 !== 0 || offset > 0 && offset >= (this.view.topology?.page.nodes.length ?? 0))
      throw new ReadFailure("invalid_response");
    this.patch({ offset });
  }
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
    this.inline.bind(this.anchor);
    this.loadedScopes = 0;
    this.patch({ phase: "idle", scopes: null, topology: null, topologyPhase: "idle", loadingMore: false, error: null });
  }
  /** Root presentation policy calls this even when the navigation pane is hidden. */
  async observe(anchor: Anchor | null, visible: boolean, denied = false, autoRoot = false) {
    if (this.disposed) return;
    const epoch = ++this.observationEpoch;
    if (denied) {
      this.inline.reset();
      this.viewports.clear();
      this.identity = null; this.bookmark = { parent: undefined, scope: undefined, query: {} };
      this.fail(new ReadFailure("denied"), false); return;
    }
    if (anchor) {
      const identity = JSON.stringify([anchor.cut.scope.tenant_id, anchor.cut.scope.project_id, anchor.cut.run_id, anchor.cut.plan_sha256]);
      if (this.identity !== identity) { this.bookmark = { parent: undefined, scope: undefined, query: {} }; this.viewports.clear(); }
      this.identity = identity;
    }
    if (!anchor || !visible) {
      this.bind(null);
      if (this.identity) this.patch({ phase: "stale" });
      return;
    }
    if (this.anchor && cutKey(this.anchor.cut) === cutKey(anchor.cut) && this.anchor.snapshot_token === anchor.snapshot_token && this.view.phase === "ready") return;
    const saved = structuredClone(this.bookmark), interaction = this.interactionEpoch;
    this.bind(anchor);
    await this.loadScopes(saved.parent);
    if (epoch !== this.observationEpoch || interaction !== this.interactionEpoch || this.view.phase !== "ready") return;
    if (saved.scope) await this.loadTopology(saved.scope, saved.query);
    else if (autoRoot && !saved.parent) {
      const root = this.view.scopes?.scopes.find(scope => scope.occurrences.length === 0);
      if (root) await this.open(root.scope_key);
    }
  }
  private fail(raw: unknown, topology: boolean) {
    const error = asReadFailure(raw);
    if (error.kind === "aborted") return;
    if (error.kind === "denied" || error.kind === "resnapshot") {
      this.scopeLane.cancel(); this.topologyLane.cancel(); this.anchor = null;
      this.inline.bind(null);
      if (error.kind === "denied") this.bookmark = { parent: undefined, scope: undefined, query: {} };
      this.patch({ phase: error.kind === "denied" ? "denied" : "stale", scopes: null, topology: null,
        topologyPhase: "idle", loadingMore: false, error });
    } else this.patch(topology ? { topologyPhase: "failed", loadingMore: false, error } : { phase: "failed", error });
  }

  async scopes(parent?: string, next = false) {
    this.interactionEpoch++;
    this.patch({ offset: 0 });
    this.bookmark = { parent, scope: undefined, query: {} };
    await this.loadScopes(parent, next);
  }
  async root() {
    const interaction = this.interactionEpoch + 1;
    await this.scopes();
    if (this.interactionEpoch !== interaction || this.view.phase !== 'ready') return;
    const scope = this.view.scopes?.scopes.find(item => item.occurrences.length === 0);
    if (scope && !this.bookmark.parent) await this.open(scope.scope_key);
  }
  private async loadScopes(parent?: string, next = false) {
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
    this.interactionEpoch++;
    this.patch({ offset: 0 });
    this.bookmark = { ...this.bookmark, scope, query: structuredClone(query) };
    await this.loadTopology(scope, query);
  }
  private async loadTopology(scope: string, query: TopologyQuery = {}) {
    if (!this.anchor || this.disposed) return;
    const anchor = this.anchor, ticket = this.topologyLane.begin();
    this.patch({ topology: null, topologyPhase: "loading", loadingMore: false, error: null });
    try {
      const page = await this.source.topology(anchor.cut.run_id, scope, anchor.snapshot_token, query, undefined, ticket.signal);
      if (!ticket.current()) return;
      const topology = TopologyWindow.open(anchor.cut, scope, query, page);
      this.patch({ topology, topologyPhase: topology.page.node_count ? "ready" : "empty",
        offset: this.view.offset < page.nodes.length ? this.view.offset : 0 });
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
    this.inline.dispose();
    this.observationEpoch++;
    this.scopeLane.cancel(); this.topologyLane.cancel(); this.listeners.clear(); this.anchor = null; this.disposed = true;
  }
}
