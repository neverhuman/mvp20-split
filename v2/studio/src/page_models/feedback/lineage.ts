import type { ResearchQuestion, EvidenceNeed } from "../../contracts/scientific/provenance.js";
import type { EvidenceAssessmentStatus, AssessmentPublicationStatus, GraphProposalStatus, AcceptedGraphChange, ReceiptCorrectionView } from "../../contracts/scientific/feedback.js";
import { requireReply, same } from "../../transport/scientific/identity.js";
import { immutable } from "../explore/context.js";
import type { FeedbackContext } from "./context.js";

export interface FeedbackRecords {
  question: ResearchQuestion;
  need: EvidenceNeed;
  assessment: EvidenceAssessmentStatus | null;
  publication: AssessmentPublicationStatus | null;
  proposal: GraphProposalStatus | null;
  change: AcceptedGraphChange | null;
  corrections: { previous: ReceiptCorrectionView; next: ReceiptCorrectionView } | null;
}

/** Relates explicit owner identities, never labels or inferred scientific compatibility. */
export class FeedbackLineage {
  readonly records: FeedbackRecords;
  readonly evidenceState: "unassessed" | "pending" | "failed" | "sufficient" | "gap";
  readonly proposalState: "unselected" | "pending" | "accepted" | "rejected" | "conflict";
  readonly futureOnly = true;
  constructor(context: FeedbackContext, input: FeedbackRecords) {
    const { question, need, assessment, publication, proposal, change, corrections } = input;
    requireReply(same(question.reference, context.pins.question) && same(need.reference, context.pins.need) && same(need.question, question.reference));
    requireReply(need.criterion_ids.every(id => question.criteria.some(c => c.criterion_id === id)));
    requireReply(same(question.applicability.scope, question.reference.scope) && same(need.required_context.scope, question.reference.scope));
    requireReply((assessment === null) === (context.pins.assessment === null));
    this.evidenceState = "unassessed";
    if (assessment) {
      requireReply(same(assessment.request, context.pins.assessment));
      if (assessment.outcome.status === "assessed") {
        const result = assessment.outcome.assessment;
        requireReply(same(result.request, assessment.request) && result.actor_id === assessment.actor_id);
        const decisions = result.needs.filter(n => same(n.need, need.reference));
        requireReply(decisions.length > 0 && decisions.every(d => need.criterion_ids.includes(d.criterion_id)));
        for (const d of decisions) {
          requireReply(d.gap === null || same(d.gap.need, need.reference) && d.gap.criterion_id === d.criterion_id);
          for (const receipt of [...d.supporting, ...d.contradicting]) requireReply(assessment.request.receipts.some(a => same(a, receipt)));
        }
        this.evidenceState = result.sufficient ? "sufficient" : "gap";
      } else this.evidenceState = assessment.outcome.status;
    }
    requireReply((publication === null) === (context.pins.publication === null));
    if (publication) {
      requireReply(same(publication.request, context.pins.publication));
      requireReply(assessment !== null && publication.request.assessment_id === assessment.request.assessment_id && same(publication.request.scope, question.reference.scope));
      if (publication.outcome.status === "published") {
        requireReply(assessment.outcome.status === "assessed");
        requireReply(same(publication.outcome.receipt.subject, assessment.outcome.assessment.subject));
        requireReply(publication.outcome.receipt.outcome.status !== "accepted" || assessment.outcome.assessment.sufficient);
      }
    }
    requireReply((proposal === null) === (context.pins.proposal === null));
    this.proposalState = "unselected";
    if (proposal) {
      requireReply(same(proposal.proposal.graph, context.pins.proposal!.graph) && proposal.proposal.change_id === context.pins.proposal!.change_id);
      this.proposalState = proposal.decision?.decision.outcome ?? "pending";
      // A selected proposal must actually name this question/need, not merely share a scope.
      requireReply(proposal.proposal.operations.some(op => op.operation === "add_assertion" && op.assertion.research_links.some(link => same(link.question, question.reference) && same(link.need, need.reference))));
    }
    if (change) {
      requireReply(proposal?.decision?.decision.outcome === "accepted");
      requireReply(same(change.reference, proposal.decision.decision.head.change) && same(change.content.proposal, proposal.proposal));
    }
    requireReply((corrections === null) === (context.pins.corrections === null));
    if (corrections) {
      const { previous, next } = corrections;
      requireReply(same(previous.reference, context.pins.corrections!.previous.revision) && same(next.reference, context.pins.corrections!.next.revision));
      requireReply(same(next.record.predecessor, previous.reference));
      requireReply(next.record.notice !== null && next.record.notice.revision === previous.record.receipt.revision && same(next.record.notice.subject, previous.record.receipt.subject));
      requireReply(publication?.outcome.status === "published" && same(next.record.source_receipt, publication.outcome.receipt));
    }
    this.records = immutable(input);
    Object.freeze(this);
  }
}
