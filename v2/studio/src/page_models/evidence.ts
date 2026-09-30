import type { ArtifactRef, CompletionRecord, GraphNodeDetail, GraphSnapshotPage, GraphValuePage } from "../contracts/observations.js";
import type { EvidenceSource } from "../transport/observations.js";
import { asReadFailure, ReadFailure } from "../transport/failure.js";
import { EvidenceContext, artifactKey } from "./evidence_context.js";
import { RequestLane } from "./request_lane.js";
import type { RegionPhase } from "./monitor.js";

export interface EvidenceRegion<T> { readonly phase: RegionPhase; readonly value: T | null; readonly error: ReadFailure | null; }
export interface EvidenceView {
  readonly completion: EvidenceRegion<CompletionRecord>;
  readonly values: EvidenceRegion<GraphValuePage>;
  readonly artifact: EvidenceRegion<ArtifactRef>;
}
const idle = (): EvidenceRegion<never> => ({ phase: "idle", value: null, error: null });
const loading = (): EvidenceRegion<never> => ({ phase: "loading", value: null, error: null });
const ready = <T>(value: T): EvidenceRegion<T> => ({ phase: "ready", value, error: null });

/** Disposable evidence regions; selected context and every public owner response are identity-bound. */
export class EvidenceModel {
  private context: EvidenceContext | null = null;
  private disposed = false;
  private loadedValues = 0;
  private readonly completionLane = new RequestLane();
  private readonly valueLane = new RequestLane();
  private readonly artifactLane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private view: EvidenceView = Object.freeze({ completion: idle(), values: idle(), artifact: idle() });
  constructor(private readonly source: EvidenceSource) {}
  get snapshot() { return this.view; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private patch(fields: Partial<EvidenceView>) {
    if (this.disposed) return;
    this.view = Object.freeze({ ...this.view, ...fields }); for (const listener of this.listeners) listener();
  }
  bind(anchor: GraphSnapshotPage["snapshot"] | null, detail: GraphNodeDetail | null) {
    if (this.disposed) return;
    this.completionLane.cancel(); this.valueLane.cancel(); this.artifactLane.cancel(); this.loadedValues = 0;
    this.context = anchor && detail ? new EvidenceContext(anchor, detail) : null;
    this.patch({ completion: idle(), values: idle(), artifact: idle() });
  }
  async completion(attemptId: string) {
    const context = this.context;
    if (!context || this.disposed) return;
    const ticket = this.completionLane.begin(); this.artifactLane.cancel();
    this.patch({ completion: loading(), artifact: idle() });
    try {
      const attempt = context.attempt(attemptId);
      const record = await this.source.completion(context.anchor.cut.run_id, attempt.completion_id!, ticket.signal);
      if (ticket.current()) this.patch({ completion: ready(context.completion(attemptId, record)) });
    } catch (error) { if (ticket.current()) this.fail("completion", error); }
  }
  async values(port: string, next = false) {
    const context = this.context, previous = this.view.values.value;
    if (!context || this.disposed || next && (!previous?.next_cursor || previous.port !== port)) return;
    const ticket = this.valueLane.begin(), loaded = next ? this.loadedValues : 0;
    this.artifactLane.cancel(); this.patch({ values: loading(), artifact: idle() });
    try {
      if (!context.detail.outputs.some(output => output.port === port)) throw new ReadFailure("unavailable");
      const page = await this.source.values(context.anchor.cut.run_id, context.detail.node.activation_id, port,
        context.anchor.snapshot_token, next ? previous!.next_cursor! : undefined, ticket.signal);
      if (!ticket.current()) return;
      if (next && page.next_cursor === previous!.next_cursor) throw new ReadFailure("invalid_response");
      const accepted = context.values(port, page, loaded); this.loadedValues = loaded + page.items.length;
      this.patch({ values: ready(accepted) });
    } catch (error) { if (ticket.current()) this.fail("values", error); }
  }
  references(): readonly ArtifactRef[] {
    const refs = (this.context?.detail.outputs ?? []).flatMap(output => output.artifact ? [output.artifact] : []);
    const result = this.view.completion.value?.result.outcome;
    if (result?.status === "succeeded") {
      refs.push(...result.outputs.map(output => output.artifact));
      if (result.checkpoint) refs.push(result.checkpoint);
    }
    for (const item of this.view.values.value?.items ?? []) if (item.value.kind === "artifact") refs.push(item.value.artifact);
    return [...new Map(refs.map(ref => [artifactKey(ref), ref])).values()];
  }
  async artifact(reference: ArtifactRef) {
    const context = this.context;
    if (!context || this.disposed) return;
    const ticket = this.artifactLane.begin(); this.patch({ artifact: loading() });
    try {
      if (!this.references().some(ref => artifactKey(ref) === artifactKey(reference))) throw new ReadFailure("unavailable");
      context.scopedArtifact(reference);
      const metadata = await this.source.artifact(reference.artifact_id, ticket.signal);
      if (ticket.current()) this.patch({ artifact: ready(context.artifact(reference, metadata)) });
    } catch (error) { if (ticket.current()) this.fail("artifact", error); }
  }
  private fail(region: keyof EvidenceView, raw: unknown) {
    const error = asReadFailure(raw);
    if (error.kind === "aborted") return;
    if (error.kind === "resnapshot" || error.kind === "denied") {
      this.completionLane.cancel(); this.valueLane.cancel(); this.artifactLane.cancel(); this.context = null;
      this.patch({ completion: idle(), values: idle(), artifact: idle() });
    }
    this.patch({ [region]: { phase: error.kind === "resnapshot" ? "stale" : error.kind === "denied" ? "denied" : "failed", value: null, error } });
  }
  dispose() { this.completionLane.cancel(); this.valueLane.cancel(); this.artifactLane.cancel(); this.listeners.clear(); this.context = null; this.disposed = true; }
}
