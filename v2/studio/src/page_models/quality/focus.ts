import { immutable } from "../explore/context.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";
import type { QualityPoint, QualityProjection } from "./projection.js";

export interface FocusIntent {
  readonly point: QualityPoint;
  readonly improvement: string;
  readonly expectedLearning: string;
}

/** A local human draft, never a claim that an owner adopted or scheduled work. */
export class QualityFocus {
  readonly items: readonly FocusIntent[];
  constructor(items: readonly FocusIntent[] = []) {
    if (items.length > 32 || new Set(items.map(item => item.point.key)).size !== items.length)
      throw new ScientificReadFailure("invalid_request");
    for (const item of items) {
      for (const text of [item.improvement, item.expectedLearning])
        if (typeof text !== "string" || !text.trim() || text.length > 2048) throw new ScientificReadFailure("invalid_request");
    }
    this.items = immutable(items); Object.freeze(this);
  }
  set(projection: QualityProjection, key: string, improvement: string, expectedLearning: string) {
    const point = projection.points.find(item => item.key === key);
    if (!point) throw new ScientificReadFailure("invalid_request");
    return new QualityFocus([...this.items.filter(item => item.point.key !== key), { point, improvement, expectedLearning }]);
  }
  remove(key: string) { return new QualityFocus(this.items.filter(item => item.point.key !== key)); }
  retain(projection: QualityProjection) {
    return new QualityFocus(this.items.filter(item => projection.points.some(point => point.key === item.point.key)));
  }
  document(projection: QualityProjection) {
    const selected = this.retain(projection);
    return immutable({ format: "amphora.local-quality-focus.v1", authority: "unsubmitted_human_draft",
      applies_to: "future_campaigns_only", scientific_authority: "not_established",
      question: projection.question.reference, need: projection.requirement.reference,
      assessment: projection.assessment?.request ?? null,
      execution: projection.attachment ? { cut: projection.attachment.cut,
        activation_id: projection.attachment.activationId, port: projection.attachment.port } : null,
      selected: selected.items, unresolved: projection.points.filter(point => point.category !== "supported"),
      expected_information_gain: { kind: "qualitative_human_intent", numerical_estimate: null },
    });
  }
}
