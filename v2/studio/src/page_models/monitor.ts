import type { GraphNodeDetail, ReadQuery } from "../contracts/observations.js";
import type { ObservationSource } from "../transport/observations.js";
import { asReadFailure, ReadFailure } from "../transport/failure.js";
import { GraphWindow, contextKey, cutKey, requireContext } from "./graph_window.js";
import type { RunContext } from "./graph_window.js";
import { EventPosition } from "./event_position.js";
import { RequestLane } from "./request_lane.js";

export type RegionPhase = "idle" | "loading" | "ready" | "empty" | "stale" | "denied" | "failed";
export interface MonitorView {
  readonly phase: RegionPhase;
  readonly window: GraphWindow | null;
  readonly loadingMore: boolean;
  readonly selection: string | null;
  readonly detail: GraphNodeDetail | null;
  readonly detailPhase: RegionPhase;
  readonly error: ReadFailure | null;
  readonly detailError: ReadFailure | null;
}

/** Owns the Monitor graph, selected-detail and invalidation regions; renderers only subscribe. */
export class MonitorModel {
  private view: MonitorView = Object.freeze({ phase: "idle", window: null, loadingMore: false,
    selection: null, detail: null, detailPhase: "idle", error: null, detailError: null });
  private context: RunContext | undefined;
  private query: ReadQuery = {};
  private visible = true;
  private disposed = false;
  private events: EventPosition | undefined;
  private readonly graphLane = new RequestLane();
  private readonly detailLane = new RequestLane();
  private readonly eventLane = new RequestLane();
  private readonly listeners = new Set<() => void>();

  constructor(private readonly source: ObservationSource) {}
  get snapshot(): MonitorView { return this.view; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private patch(fields: Partial<MonitorView>) {
    if (this.disposed) return;
    this.view = Object.freeze({ ...this.view, ...fields });
    for (const listener of this.listeners) listener();
  }

  async open(context: RunContext, query: ReadQuery = {}) {
    if (this.disposed) return;
    if (!this.context || contextKey(this.context) !== contextKey(context)) {
      this.graphLane.cancel(); this.detailLane.cancel(); this.eventLane.cancel();
      this.patch({ window: null, selection: null, detail: null, detailPhase: "idle" });
    }
    this.context = { scope: { ...context.scope }, run: context.run };
    this.query = { scope_key: query.scope_key ?? null, frontier_only: query.frontier_only ?? false };
    await this.refresh();
  }

  async refresh() {
    if (!this.context || this.disposed) return;
    const context = this.context, query = this.query, ticket = this.graphLane.begin();
    this.detailLane.cancel(); this.eventLane.cancel(); this.events = undefined;
    this.patch({ phase: "loading", error: null, loadingMore: false, detail: null, detailPhase: "idle", detailError: null });
    try {
      const page = await this.source.snapshot(context.run, query, undefined, ticket.signal);
      if (!ticket.current()) return;
      const window = GraphWindow.open(context, query, page);
      this.events = new EventPosition(page.snapshot.cut.revision, page.snapshot.event_cursor);
      this.patch({ window, phase: window.snapshot.node_count === 0 ? "empty" : "ready" });
      if (this.view.selection) await this.select(this.view.selection);
    } catch (error) { if (ticket.current()) this.graphFailure(error); }
  }

  async loadMore() {
    const window = this.view.window, context = this.context;
    if (!window?.next || !context || this.view.phase !== "ready" || this.disposed) return;
    const ticket = this.graphLane.begin();
    this.patch({ loadingMore: true, error: null });
    try {
      const page = await this.source.snapshot(context.run, this.query, window.next, ticket.signal);
      if (!ticket.current()) return;
      this.patch({ window: window.append(page), loadingMore: false });
    } catch (error) { if (ticket.current()) this.graphFailure(error); }
  }

  async select(activation: string) {
    const window = this.view.window, context = this.context;
    if (!window || !context || !["ready", "empty"].includes(this.view.phase) || this.disposed) return;
    const ticket = this.detailLane.begin();
    this.patch({ selection: activation, detail: null, detailPhase: "loading", detailError: null });
    try {
      const detail = await this.source.detail(context.run, activation, window.snapshot.snapshot_token, undefined, ticket.signal);
      if (!ticket.current() || !this.view.window || cutKey(this.view.window.snapshot.cut) !== cutKey(window.snapshot.cut)) return;
      if (cutKey(detail.cut) !== cutKey(window.snapshot.cut) || detail.node.activation_id !== activation) throw new ReadFailure("invalid_response");
      this.patch({ detail, detailPhase: "ready" });
    } catch (error) {
      if (!ticket.current()) return;
      const failure = asReadFailure(error);
      if (failure.kind === "resnapshot") this.graphFailure(failure);
      else this.patch({ detail: null, detailPhase: failure.kind === "denied" ? "denied" : "failed", detailError: failure });
    }
  }

  async poll() {
    const context = this.context, position = this.events;
    if (!context || !position || !this.visible || this.disposed || this.view.phase === "loading") return;
    const ticket = this.eventLane.begin();
    try {
      const page = await this.source.events(context.run, position.cursor, ticket.signal);
      if (!ticket.current()) return;
      requireContext(context, page.scope, page.run_id);
      const next = position.accept(page);
      this.events = next;
      if (next.revision > position.revision) await this.invalidate();
    } catch (error) {
      if (!ticket.current()) return;
      const failure = asReadFailure(error);
      if (failure.kind === "resnapshot") await this.invalidate();
      else this.graphFailure(failure);
    }
  }

  async invalidate() {
    if (this.disposed) return;
    this.graphLane.cancel(); this.detailLane.cancel(); this.eventLane.cancel();
    this.patch({ phase: "stale", loadingMore: false, detail: null, detailPhase: "stale" });
    if (this.visible) await this.refresh();
  }

  async setVisible(visible: boolean) {
    this.visible = visible;
    if (!visible) this.eventLane.cancel();
    else if (this.view.phase === "stale") await this.refresh();
  }

  private graphFailure(error: unknown) {
    const failure = asReadFailure(error);
    this.graphLane.cancel(); this.detailLane.cancel(); this.eventLane.cancel();
    if (failure.kind === "denied") {
      this.events = undefined;
      this.patch({ window: null, selection: null });
    }
    this.patch({ phase: failure.kind === "resnapshot" ? "stale" : failure.kind === "denied" ? "denied" : "failed",
      error: failure, loadingMore: false, detail: null, detailPhase: "idle" });
  }

  dispose() {
    this.disposed = true;
    this.graphLane.cancel(); this.detailLane.cancel(); this.eventLane.cancel(); this.listeners.clear();
  }
}
