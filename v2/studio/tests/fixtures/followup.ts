import { createHash } from "node:crypto";
import requests from "./supervision/requests.json" with { type: "json" };
import responses from "./supervision/responses.json" with { type: "json" };
import pins from "../../src/contracts/generated/followup/profiles.json" with { type: "json" };
import { decodeSupervision } from "../../src/contracts/supervision.js";
import { canonical } from "../../src/transport/scientific/identity.js";
import type { CheckpointFollowupDraft, SupervisionResponse } from "../../src/contracts/followup.js";
import type { FollowupSelection } from "../../src/transport/followup/client.js";
export const digest = (text: string) => createHash("sha256").update(text).digest("hex");
export const scope = requests.reference.scope;
export function draft(count = 1): CheckpointFollowupDraft {
  return { schema_version: "3", action: "abstain", authority: "proposal_only", scientific_authority: "not_established",
    decision_scope: "a".repeat(64), candidate: null, alternatives: [], evidence_requests: [], focus_artifact: null,
    rationale: "More evidence is needed", targets: [], unresolved: Array.from({ length: count }, (_, index) => ({
      criterion: { question: { scope, question_id: "question", revision: 1 }, need: { scope, need_id: "need", revision: 1 }, criterion_id: `criterion-${index}`, assessment: null },
      description: "The available evidence is incomplete", posture: "unknown",
    })) };
}
export function fixture() {
  const document = draft(), raw = JSON.stringify(document), hash = digest(raw);
  const request = decodeSupervision("requests", structuredClone(requests)).items[0]!;
  const item = decodeSupervision("responses", structuredClone(responses)).items[0]!;
  const capture = { ...item.capture!, media_type: "application/json", size_bytes: Buffer.byteLength(raw), sha256: hash };
  const record: SupervisionResponse = { schema_version: "1", response_id: item.response_id, reference: requests.reference, request_sha256: request.request_sha256, capture,
    observation: { schema_version: "2", attempt: { engagement: request.engagement, ordinal: 1, request_sha256: request.planning_request_sha256 },
      captured_bytes: capture.size_bytes, output_complete: true, output_sha256: hash, reason_code: null, status: "abstained",
      proposal: { schema_version: "1", action: document.action, rationale: document.rationale, output_schema: { ...pins.followup, version: "1" }, payload_json: raw, payload_sha256: hash },
      usage: { accounting_units: null, certainty: "unknown", input_tokens: null, output_tokens: null } } };
  const selection: FollowupSelection = { checkpoint: requests.reference, request, response: { ...item, capture, status: "abstained", captured_bytes: capture.size_bytes, output_sha256: hash, response_sha256: digest(canonical(record)) } };
  return { document, raw, record, selection };
}
