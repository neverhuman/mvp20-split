import { checkedOutputPins } from "../quality/runtime_link.js";
import type { QualityOutputPins } from "../quality/runtime_link.js";

/** Selects an output within the session's already selected campaign, never another run. */
export class WorkspaceQualityOutputSelection {
  readonly phase: "missing" | "ready" | "invalid";
  readonly pins: QualityOutputPins | null;
  constructor(search: string) {
    let pins: QualityOutputPins | null = null, phase: WorkspaceQualityOutputSelection["phase"] = "missing";
    try {
      if (search.length > 8192) throw new Error("selection_too_large");
      const values = new URLSearchParams(search).getAll("quality_output");
      if (values.length) {
        if (values.length !== 1) throw new Error("ambiguous_selection");
        pins = checkedOutputPins(JSON.parse(values[0]!)); phase = "ready";
      }
    } catch { phase = "invalid"; }
    this.phase = phase; this.pins = pins; Object.freeze(this);
  }
}
