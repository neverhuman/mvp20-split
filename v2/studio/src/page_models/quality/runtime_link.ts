import type { ObservationSource } from "../../transport/observations.js";
import { asReadFailure, ReadFailure } from "../../transport/failure.js";
import { immutable } from "../explore/context.js";
import { requireContext } from "../graph_window.js";
import type { RunContext } from "../graph_window.js";
import { RequestLane } from "../request_lane.js";
import { QualityAttachment } from "./attachment.js";

export interface QualityOutputPins { activation_id: string; port: string; }
export interface QualityLinkState {
  readonly phase: "idle" | "loading" | "ready" | "stale" | "denied" | "failed";
  readonly attachment: QualityAttachment | null;
  readonly error: ReadFailure | null;
}
export function checkedOutputPins(value: QualityOutputPins): QualityOutputPins {
  if (!value || Object.keys(value).sort().join(",") !== "activation_id,port" ||
      typeof value.activation_id !== "string" || !/^[a-f0-9]{64}$/.test(value.activation_id) ||
      typeof value.port !== "string" || !/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(value.port)) throw new ReadFailure("invalid_response");
  return immutable(value);
}

/** Three bounded read-only requests; no inferred consumers or automatic graph refresh. */
export class QualityLinkModel {
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private context: RunContext | null = null;
  private pins: QualityOutputPins | null = null;
  private visible = false;
  private disposed = false;
  private state: QualityLinkState = Object.freeze({ phase: "idle", attachment: null, error: null });
  constructor(private readonly source: Pick<ObservationSource, "snapshot" | "detail" | "values">) {}
  get snapshot() { return this.state; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  bind(context: RunContext, pins: QualityOutputPins | null) {
    if (this.disposed) return;
    const checked = pins ? checkedOutputPins(pins) : null;
    this.lane.cancel(); this.context = immutable(context); this.pins = checked; this.publish("idle");
  }
  visibility(visible: boolean) {
    if (this.disposed || this.visible === visible) return;
    this.visible = visible; this.lane.cancel(); this.publish("stale");
  }
  async refresh() {
    if (this.disposed || !this.visible || !this.context || !this.pins) return;
    const context = this.context, pins = this.pins, request = this.lane.begin();
    this.publish("loading"); if (!request.current()) return;
    try {
      const page = await this.source.snapshot(context.run, {}, undefined, request.signal);
      if (!request.current()) return;
      requireContext(context, page.snapshot.cut.scope, page.snapshot.cut.run_id);
      const detail = await this.source.detail(context.run, pins.activation_id, page.snapshot.snapshot_token, undefined, request.signal);
      if (!request.current()) return;
      if (detail.node.activation_id !== pins.activation_id) throw new ReadFailure("invalid_response");
      const values = await this.source.values(context.run, pins.activation_id, pins.port, page.snapshot.snapshot_token, undefined, request.signal);
      if (!request.current()) return;
      this.publish("ready", new QualityAttachment(page.snapshot, detail, pins.port, [values]));
    } catch (raw) {
      if (!request.current()) return;
      const error = asReadFailure(raw);
      this.publish(error.kind === "denied" ? "denied" : error.kind === "resnapshot" || error.kind === "aborted" ? "stale" : "failed", null, error);
    }
  }
  dispose() { this.disposed = true; this.lane.cancel(); this.listeners.clear(); this.context = null; this.pins = null;
    this.state = Object.freeze({ phase: "idle", attachment: null, error: null }); }
  private publish(phase: QualityLinkState["phase"], attachment: QualityAttachment | null = null, error: ReadFailure | null = null) {
    if (this.disposed) return;
    this.state = Object.freeze({ phase, attachment, error }); for (const listener of this.listeners) listener();
  }
}
