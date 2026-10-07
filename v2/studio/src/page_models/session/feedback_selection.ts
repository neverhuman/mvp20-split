import { FeedbackContext } from "../feedback/context.js";
import type { FeedbackPins } from "../feedback/context.js";
import type { WorkspaceContext } from "../../transport/session/client.js";
import { same } from "../../transport/scientific/identity.js";

/** Explicit bounded launcher selection; the authenticated session alone grants scope. */
export class WorkspaceFeedbackSelection {
  readonly phase: "missing" | "ready" | "invalid";
  readonly pins: FeedbackPins | null;
  constructor(search: string, scope: WorkspaceContext["scope"]) {
    let pins: FeedbackPins | null = null, phase: WorkspaceFeedbackSelection["phase"] = "missing";
    try {
      if (search.length > 8192) throw new Error("selection_too_large");
      const values = new URLSearchParams(search).getAll("feedback");
      if (values.length) {
        if (values.length !== 1) throw new Error("ambiguous_selection");
        const value = JSON.parse(values[0]!);
        if (!value || Object.keys(value).sort().join(",") !== "assessment,corrections,need,proposal,publication,question") throw new Error("invalid_selection");
        const context = new FeedbackContext(value);
        if (!same(context.pins.question.scope, scope)) throw new Error("foreign_scope");
        pins = context.pins; phase = "ready";
      }
    } catch { phase = "invalid"; }
    this.phase = phase; this.pins = pins; Object.freeze(this);
  }
}
