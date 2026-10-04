import { decodeFeedback, decodeAcceptedChangeRef, decodeFeedbackGraph } from "../../contracts/scientific/feedback.js";
import type { EvidenceAssessmentRequest, AssessmentPublicationRequest, SelectAssessmentReceipt, SelectReasoningReceipt, AcceptedGraphChange, GraphProposalStatus } from "../../contracts/scientific/feedback.js";
import { ScientificHTTP } from "../scientific/http.js";
import { ScientificReadFailure } from "../scientific/failure.js";
import { canonical, normalized, requireReply, same } from "../scientific/identity.js";
import { active, sha256 } from "../provenance/integrity.js";
import { verifyCorrection } from "./correction.js";

/** Reads committed owner records. No publish, correct, accept, or repin command. */
export class FeedbackClient {
  private readonly http: ScientificHTTP;
  constructor(fetcher: typeof fetch = fetch, timeoutMs = 15_000) { this.http = new ScientificHTTP(fetcher, timeoutMs); }

  async assessment(request: EvidenceAssessmentRequest, signal: AbortSignal) {
    const expected = normalized(request, {}, v => decodeFeedback("assessment_request", v));
    const result = await this.http.post("/api/research/v1/assessments/read", expected, v => decodeFeedback("assessment", v), signal);
    requireReply(same(result.request, expected));
    if (result.outcome.status === "assessed") {
      requireReply(same(result.outcome.assessment.request, expected) && result.outcome.assessment.actor_id === result.actor_id);
    }
    return result;
  }

  async publication(request: AssessmentPublicationRequest, signal: AbortSignal) {
    const expected = normalized(request, {}, v => decodeFeedback("publication_request", v));
    const result = await this.http.post("/api/research/v1/assessment-publications/read", expected, v => decodeFeedback("publication", v), signal);
    requireReply(same(result.request, expected));
    if (result.outcome.status === "published") {
      const receipt = result.outcome.receipt;
      requireReply(same(receipt.scope, expected.scope) && same(receipt.subject.scope, expected.scope) && receipt.purpose === "research.synthetic_sufficiency");
    }
    return result;
  }

  async correction(owner: "research" | "knowledge", request: SelectAssessmentReceipt | SelectReasoningReceipt, signal: AbortSignal) {
    if (owner !== "research" && owner !== "knowledge") throw new ScientificReadFailure("invalid_request");
    const expected = normalized(request, {}, v => decodeFeedback(owner === "research" ? "assessment_selection" : "reasoning_selection", v));
    // Exploration must choose a historical revision explicitly. Head discovery belongs to future-campaign planning.
    if (expected.revision === null || !same(expected.chain, expected.revision.chain)) throw new ScientificReadFailure("invalid_request");
    const family = owner === "research" ? "assessment" : "reasoning";
    const result = await this.http.post(`/api/${owner}/v1/${family}-receipts/select`, expected, v => decodeFeedback("correction", v), signal);
    requireReply(same(result.reference, expected.revision));
    await verifyCorrection(result, owner, signal);
    return result;
  }

  async proposal(graph: GraphProposalStatus["proposal"]["graph"], changeId: string, signal: AbortSignal) {
    const expected = normalized(graph, {}, decodeFeedbackGraph);
    if (!/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(changeId)) throw new ScientificReadFailure("invalid_request");
    const path = `/api/knowledge/v1/graphs/${encodeURIComponent(expected.graph_id)}/proposals/${encodeURIComponent(changeId)}`;
    const result = await this.http.get(path, v => decodeFeedback("proposal", v), signal);
    requireReply(same(result.proposal.graph, expected) && result.proposal.change_id === changeId);
    requireReply(await sha256(new TextEncoder().encode(canonical(result.proposal))) === result.request_sha256);
    active(signal);
    if (result.decision !== null) requireReply(same(result.decision.graph, expected) && result.decision.change_id === changeId && result.decision.request_sha256 === result.request_sha256);
    return result;
  }

  async change(reference: AcceptedGraphChange["reference"], signal: AbortSignal) {
    const expected = normalized(reference, {}, decodeAcceptedChangeRef);
    const result = await this.http.post("/api/knowledge/v1/graph-changes/read", expected, v => decodeFeedback("change", v), signal);
    requireReply(same(result.reference, expected) && same(result.content.proposal.graph, expected.graph) && result.content.proposal.change_id === expected.change_id && result.content.position === expected.position);
    requireReply(await sha256(new TextEncoder().encode(canonical(result.content))) === expected.sha256);
    active(signal);
    return result;
  }
}
