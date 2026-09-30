import type { ReadCut } from "../contracts/observations.js";
import { captureInspection, type InspectionPin, type InspectionSelection } from "./history_pin.js";

export interface InspectionHistoryState {
  readonly pins: readonly InspectionPin[];
  readonly selected: string | null;
  readonly error: string | null;
}
const scopeKey = (scope: ReadCut["scope"]) => JSON.stringify([scope.tenant_id, scope.project_id]);

/** Ephemeral, scope-bound history of at most eight 2-MiB captures; no network or browser persistence. */
export class InspectionHistory {
  private owner: string | null = null;
  private sequence = 0;
  private readonly listeners = new Set<() => void>();
  private state: InspectionHistoryState = Object.freeze({ pins: [], selected: null, error: null });
  constructor(private readonly maximum = 8, private readonly now: () => string = () => new Date().toISOString()) {
    if (!Number.isSafeInteger(maximum) || maximum < 1 || maximum > 8) throw new Error("invalid_pin_limit");
  }
  get snapshot() { return this.state; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private patch(fields: Partial<InspectionHistoryState>) {
    this.state = Object.freeze({ ...this.state, ...fields }); for (const listener of this.listeners) listener();
  }
  compatible(scope: ReadCut["scope"]) { return this.owner === scopeKey(scope); }
  setScope(scope: ReadCut["scope"]) {
    if (this.compatible(scope)) return;
    this.owner = scopeKey(scope); this.patch({ pins: [], selected: null, error: null });
  }
  deny() { this.owner = null; this.patch({ pins: [], selected: null, error: null }); }
  capture(selection: InspectionSelection) {
    try {
      if (!selection.monitor.window || !this.compatible(selection.monitor.window.snapshot.cut.scope)) throw new Error("scope_mismatch");
      if (this.state.pins.length >= this.maximum) {
        this.patch({ error: `All ${this.maximum} local pin slots are occupied. Remove a pin first.` }); return;
      }
      const pin = captureInspection(`local-${++this.sequence}`, this.now(), selection);
      this.patch({ pins: Object.freeze([...this.state.pins, pin]), selected: pin.id, error: null });
    } catch { this.patch({ error: "This inspection could not be pinned. Refresh the selected records or narrow the view." }); }
  }
  select(id: string | null) {
    if (id !== null && !this.state.pins.some(pin => pin.id === id)) throw new Error("unknown_inspection_pin");
    this.patch({ selected: id, error: null });
  }
  remove(id: string) {
    this.patch({ pins: Object.freeze(this.state.pins.filter(pin => pin.id !== id)), selected: this.state.selected === id ? null : this.state.selected, error: null });
  }
}
