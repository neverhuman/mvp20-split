import type { CriterionRef } from "../../contracts/followup.js";
import type { ResearchQuestion, EvidenceNeed } from "../../contracts/scientific/provenance.js";
import type { EvidenceAssessmentStatus } from "../../contracts/scientific/feedback.js";
import { ResearchRecordClient } from "../provenance/research.js";
import { FeedbackClient } from "../feedback/client.js";
import { active, sha256 } from "../provenance/integrity.js";
import { canonical, requireReply, same } from "../scientific/identity.js";
export interface CriterionRecords { readonly criterion: CriterionRef; readonly question: ResearchQuestion; readonly need: EvidenceNeed; readonly assessment: EvidenceAssessmentStatus | null }
export interface CriterionSource { load(ref: CriterionRef, signal: AbortSignal): Promise<CriterionRecords> }
/** Exact owner revisions only: a newer assessment cannot replace a pinned digest. */
export class CriterionClient implements CriterionSource {
  private readonly research: ResearchRecordClient;
  private readonly feedback: FeedbackClient;
  constructor(fetcher: typeof fetch = fetch, timeoutMs = 15000) {
    this.research = new ResearchRecordClient(fetcher, timeoutMs); this.feedback = new FeedbackClient(fetcher, timeoutMs);
  }
  async load(input: CriterionRef, signal: AbortSignal): Promise<CriterionRecords> {
    const criterion = structuredClone(input);
    requireReply(same(criterion.question.scope, criterion.need.scope));
    const question = await this.research.question(criterion.question, signal);
    const need = await this.research.need(criterion.need, signal);
    requireReply(same(need.question, question.reference) && need.criterion_ids.includes(criterion.criterion_id) && question.criteria.some(point => point.criterion_id === criterion.criterion_id));
    let assessment: EvidenceAssessmentStatus | null = null;
    if (criterion.assessment) {
      requireReply(same(criterion.assessment.request.question, question.reference));
      assessment = await this.feedback.assessment(criterion.assessment.request, signal);
      requireReply(await sha256(new TextEncoder().encode(canonical(assessment))) === criterion.assessment.status_sha256);
      if (assessment.outcome.status === "assessed") requireReply(assessment.outcome.assessment.needs.some(point => same(point.need, need.reference) && point.criterion_id === criterion.criterion_id));
    }
    active(signal);
    return { criterion, question, need, assessment };
  }
}
