import schemas from "../generated/feedback/schemas.json" with { type: "json" };
import type { EvidenceAssessmentRequest } from "../generated/feedback/assessment_request.js";
import type { EvidenceAssessmentStatus } from "../generated/feedback/assessment.js";
import type { AssessmentPublicationRequest } from "../generated/feedback/publication_request.js";
import type { AssessmentPublicationStatus } from "../generated/feedback/publication.js";
import type { SelectAssessmentReceipt } from "../generated/feedback/assessment_selection.js";
import type { SelectReasoningReceipt } from "../generated/feedback/reasoning_selection.js";
import type { ReceiptCorrectionView } from "../generated/feedback/correction.js";
import type { GraphProposalStatus } from "../generated/feedback/proposal.js";
import type { AcceptedGraphChange } from "../generated/feedback/change.js";
import { decoder, referenceDecoder } from "./validation.js";

export type { EvidenceAssessmentRequest, EvidenceAssessmentStatus, AssessmentPublicationRequest, AssessmentPublicationStatus, SelectAssessmentReceipt, SelectReasoningReceipt, ReceiptCorrectionView, GraphProposalStatus, AcceptedGraphChange };
export interface FeedbackWire {
  assessment_request: EvidenceAssessmentRequest;
  assessment: EvidenceAssessmentStatus;
  publication_request: AssessmentPublicationRequest;
  publication: AssessmentPublicationStatus;
  assessment_selection: SelectAssessmentReceipt;
  reasoning_selection: SelectReasoningReceipt;
  correction: ReceiptCorrectionView;
  proposal: GraphProposalStatus;
  change: AcceptedGraphChange;
}
export const decodeFeedback = decoder<FeedbackWire>(schemas);
export const decodeAcceptedChangeRef = referenceDecoder<AcceptedGraphChange["reference"]>(schemas.change, "AcceptedChangeRef");
export const decodeFeedbackGraph = referenceDecoder<GraphProposalStatus["proposal"]["graph"]>(schemas.proposal, "DomainGraphRef");
