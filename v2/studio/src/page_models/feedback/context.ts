import { decodeEvidenceNeedRef, decodeResearchQuestionRef } from "../../contracts/scientific/provenance.js";
import type { EvidenceNeed, ResearchQuestion } from "../../contracts/scientific/provenance.js";
import { decodeFeedback, decodeFeedbackGraph } from "../../contracts/scientific/feedback.js";
import type { EvidenceAssessmentRequest, AssessmentPublicationRequest, GraphProposalStatus, SelectAssessmentReceipt } from "../../contracts/scientific/feedback.js";
import { same } from "../../transport/scientific/identity.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";
import { immutable } from "../explore/context.js";

export interface FeedbackPins {
  question: ResearchQuestion["reference"];
  need: EvidenceNeed["reference"];
  assessment: EvidenceAssessmentRequest | null;
  publication: AssessmentPublicationRequest | null;
  proposal: { graph: GraphProposalStatus["proposal"]["graph"]; change_id: string } | null;
  corrections: { owner: "research"; previous: SelectAssessmentReceipt; next: SelectAssessmentReceipt } | null;
}

export class FeedbackContext {
  readonly pins: FeedbackPins;
  constructor(input: FeedbackPins) {
    try {
      this.pins = immutable(input);
      decodeResearchQuestionRef(this.pins.question); decodeEvidenceNeedRef(this.pins.need);
      this.require(same(input.question.scope, input.need.scope));
      if (input.assessment) {
        decodeFeedback("assessment_request", input.assessment);
        this.require(same(input.assessment.question, input.question) && same(input.assessment.profile.scope, input.question.scope));
        this.require(input.assessment.answers.every(a => same(a.artifact.scope, input.question.scope)) && input.assessment.receipts.every(a => same(a.scope, input.question.scope)));
      }
      if (input.proposal) {
        decodeFeedbackGraph(input.proposal.graph);
        this.require(same(input.proposal.graph.scope, input.question.scope) && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(input.proposal.change_id));
      }
      if (input.publication) {
        decodeFeedback("publication_request", input.publication);
        this.require(input.assessment !== null && input.publication.assessment_id === input.assessment.assessment_id && same(input.publication.scope, input.question.scope));
      }
      if (input.corrections) {
        const { owner, previous, next } = input.corrections;
        this.require(owner === "research");
        this.require(input.publication !== null);
        for (const selected of [previous, next]) {
          decodeFeedback("assessment_selection", selected);
          this.require(selected.revision !== null && same(selected.chain.scope, input.question.scope) && same(selected.chain, selected.revision.chain));
        }
        this.require(same(previous.chain, next.chain) && next.revision!.ordinal === previous.revision!.ordinal + 1);
      }
    } catch { throw new ScientificReadFailure("invalid_request"); }
    Object.freeze(this);
  }
  private require(value: boolean) { if (!value) throw new Error("invalid_context"); }
}
