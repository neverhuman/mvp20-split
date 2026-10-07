import type { ArtifactRef } from "../../contracts/observations.js";
import type { FeedbackRecords, FeedbackLineage } from "../feedback/lineage.js";
import { immutable } from "../explore/context.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";
import { same } from "../../transport/scientific/identity.js";
import type { QualityAttachment } from "./attachment.js";

export type QualityCategory = "unassessed" | "unknown" | "contradictory" | "insufficient" | "supported";
export interface QualityPoint {
  readonly key: string;
  readonly criterionId: string;
  readonly description: string;
  readonly category: QualityCategory;
  readonly reason: string;
  readonly need: FeedbackRecords["need"]["reference"];
  readonly supporting: readonly ArtifactRef[];
  readonly contradicting: readonly ArtifactRef[];
}
export interface QualityPage {
  readonly items: readonly QualityPoint[];
  readonly offset: number;
  readonly total: number;
  readonly selectedTotal: number;
  readonly nextOffset: number | null;
}

/** Presentation of owner decisions; no scientific assessment or confidence calculation. */
export class QualityProjection {
  readonly points: readonly QualityPoint[];
  readonly question: FeedbackRecords["question"];
  readonly requirement: FeedbackRecords["need"];
  readonly assessment: FeedbackRecords["assessment"];
  readonly correction: FeedbackRecords["corrections"];
  readonly attachment: QualityAttachment | null;
  readonly assessmentState: FeedbackLineage["evidenceState"];
  readonly scientificEstablishment = false;
  readonly calibratedAccuracy = null;
  readonly demonstratedError = null;
  readonly futureCampaignsOnly = true;
  readonly missingDecisions: number;
  constructor(lineage: FeedbackLineage, attachment: QualityAttachment | null = null) {
    const { question, need, assessment, corrections } = lineage.records;
    const result = assessment?.outcome.status === "assessed" ? assessment.outcome.assessment : null;
    this.question = question; this.requirement = need; this.assessment = assessment;
    this.correction = corrections; this.assessmentState = lineage.evidenceState;
    this.attachment = result && attachment?.contains(result.subject) ? attachment : null;
    let missing = 0;
    const points = need.criterion_ids.map(criterionId => {
      const criterion = question.criteria.find(value => value.criterion_id === criterionId)!;
      const decisions = result?.needs.filter(value => value.criterion_id === criterionId && same(value.need, need.reference)) ?? [];
      if (decisions.length > 1) throw new ScientificReadFailure("invalid_response");
      const decision = decisions[0];
      if (result && !decision) missing++;
      const reason = decision ? decision.gap?.reason ?? "owner_requirement_met" : result ? "criterion_not_returned" :
        assessment ? "assessment_" + assessment.outcome.status : "assessment_unselected";
      const category: QualityCategory = !decision ? "unassessed" :
        reason === "evidence_conflict" || reason === "answer_contradicted" || reason === "evidence_contradicted" ? "contradictory" :
        reason === "answer_unknown" || reason === "missing_answer" ? "unknown" :
        reason === "no_matching_evidence" ? "insufficient" : "supported";
      return { key: JSON.stringify([question.reference, need.reference, criterionId,
          assessment?.request.assessment_id ?? null, assessment?.request.profile ?? null]),
        criterionId, description: criterion.description, category, reason, need: need.reference,
        supporting: decision?.supporting ?? [], contradicting: decision?.contradicting ?? [] };
    });
    if (new Set(points.map(point => point.key)).size !== points.length) throw new ScientificReadFailure("invalid_response");
    this.points = immutable(points); this.missingDecisions = missing; Object.freeze(this);
  }
  page(category: QualityCategory | "all" = "all", offset = 0): QualityPage {
    if (!["all", "unassessed", "unknown", "contradictory", "insufficient", "supported"].includes(category) ||
        !Number.isSafeInteger(offset) || offset < 0) throw new ScientificReadFailure("invalid_request");
    const selected = category === "all" ? this.points : this.points.filter(point => point.category === category);
    if (offset > selected.length) throw new ScientificReadFailure("invalid_request");
    return immutable({ items: selected.slice(offset, offset + 20), offset, total: this.points.length,
      selectedTotal: selected.length, nextOffset: offset + 20 < selected.length ? offset + 20 : null });
  }
}
