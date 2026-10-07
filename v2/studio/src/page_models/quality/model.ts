import type { FeedbackModel, FeedbackState } from "../feedback/model.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";
import type { QualityAttachment } from "./attachment.js";
import { QualityProjection } from "./projection.js";
import type { QualityCategory, QualityPage } from "./projection.js";
import { QualityFocus } from "./focus.js";

export interface QualityState {
  readonly phase: FeedbackState["phase"];
  readonly projection: QualityProjection | null;
  readonly page: QualityPage | null;
  readonly category: QualityCategory | "all";
  readonly selected: string | null;
  readonly error: ScientificReadFailure | null;
  readonly focus: QualityFocus;
}

/** One existing FeedbackModel owns reads; this region owns filters and selection only. */
export class QualityModel {
  private readonly listeners = new Set<() => void>();
  private readonly unsubscribe: () => void;
  private disposed = false;
  private attachment: QualityAttachment | null = null;
  private context: FeedbackState["context"] = null;
  private selection: string | null = null;
  private focus = new QualityFocus();
  private state: QualityState = Object.freeze({ phase: "idle", projection: null, page: null,
    category: "all", selected: null, error: null, focus: this.focus });
  constructor(private readonly feedback: FeedbackModel) {
    this.unsubscribe = feedback.subscribe(() => this.reconcile()); this.reconcile();
  }
  get snapshot() { return this.state; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  attach(attachment: QualityAttachment | null) { if (!this.disposed) { this.attachment = attachment; this.reconcile(); } }
  filter(category: QualityState["category"]) {
    if (!this.disposed && this.state.projection) {
      const page = this.state.projection.page(category);
      this.selection = null; this.publish({ ...this.state, category, page, selected: null });
    }
  }
  page(offset: number) {
    if (!this.disposed && this.state.projection) this.publish({ ...this.state,
      page: this.state.projection.page(this.state.category, offset) });
  }
  select(key: string | null) {
    if (this.disposed || !this.state.projection) return;
    if (key !== null && !this.state.projection.points.some(point => point.key === key)) throw new ScientificReadFailure("invalid_request");
    this.selection = key; this.publish({ ...this.state, selected: key });
  }
  focusPoint(key: string, improvement: string, expectedLearning: string) {
    if (this.disposed || !this.state.projection) return;
    this.focus = this.focus.set(this.state.projection, key, improvement, expectedLearning);
    this.publish({ ...this.state, focus: this.focus });
  }
  unfocus(key: string) {
    if (this.disposed || !this.state.projection) return;
    this.focus = this.focus.remove(key); this.publish({ ...this.state, focus: this.focus });
  }
  exportFocus() {
    if (this.disposed || !this.state.projection || !this.focus.items.length) throw new ScientificReadFailure("invalid_request");
    return this.focus.document(this.state.projection);
  }
  dispose() { this.disposed = true; this.unsubscribe(); this.listeners.clear(); this.attachment = null; this.context = null; this.selection = null;
    this.focus = new QualityFocus();
    this.state = Object.freeze({ phase: "idle", projection: null, page: null, category: "all", selected: null, error: null, focus: this.focus }); }
  private reconcile() {
    if (this.disposed) return;
    const source = this.feedback.snapshot;
    if (source.context !== this.context) {
      this.context = source.context; this.selection = null; this.attachment = null; this.focus = new QualityFocus();
    }
    if (!source.visible || source.phase === "denied" || source.phase === "failed") { this.selection = null; this.focus = new QualityFocus(); }
    let projection: QualityProjection | null = null, error = source.error, phase = source.phase;
    if (source.visible && source.phase === "ready" && source.lineage) {
      try { projection = new QualityProjection(source.lineage, this.attachment); }
      catch { phase = "failed"; error = new ScientificReadFailure("invalid_response"); }
    }
    if (projection && !projection.points.some(point => point.key === this.selection)) this.selection = null;
    if (projection) this.focus = this.focus.retain(projection);
    this.publish({ phase, projection, page: projection?.page(this.state.category) ?? null,
      category: this.state.category,
      selected: projection ? this.selection : null, error, focus: projection ? this.focus : new QualityFocus() });
  }
  private publish(state: QualityState) {
    if (this.disposed) return;
    this.state = Object.freeze(state); for (const listener of this.listeners) listener();
  }
}
