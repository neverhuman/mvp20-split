import type { Checkpoint, CheckpointRequest, SupervisionWire } from "../../contracts/supervision.js";
import { decodeFollowup, decodeProposal, proposalProfile } from "../../contracts/followup.js";
import type { ProposalDocument, SupervisionResponse } from "../../contracts/followup.js";
import { ScientificHTTP } from "../scientific/http.js";
import { ScientificReadFailure } from "../scientific/failure.js";
import { canonical, requireReply, same } from "../scientific/identity.js";
import { DataProvenanceClient } from "../provenance/data.js";
import { active, sha256 } from "../provenance/integrity.js";

export interface FollowupSelection {
  readonly checkpoint: Checkpoint["reference"];
  readonly request: CheckpointRequest;
  readonly response: SupervisionWire["responses"]["items"][number];
}
export interface RetainedProposal {
  readonly selection: FollowupSelection;
  readonly record: SupervisionResponse;
  readonly document: ProposalDocument | null;
}
export interface FollowupSource { load(selection: FollowupSelection, signal: AbortSignal): Promise<RetainedProposal> }

/** Raw output may omit DTO defaults; every authored value must match interpretation. */
function authoredMatches(raw: unknown, interpreted: unknown): boolean {
  if (Array.isArray(raw)) return Array.isArray(interpreted) && raw.length === interpreted.length && raw.every((v, i) => authoredMatches(v, interpreted[i]));
  if (raw !== null && typeof raw === "object") return interpreted !== null && typeof interpreted === "object" && !Array.isArray(interpreted) &&
    Object.entries(raw).every(([key, value]) => Object.hasOwn(interpreted, key) && authoredMatches(value, (interpreted as Record<string, unknown>)[key]));
  return raw === interpreted;
}

export class FollowupClient implements FollowupSource {
  private readonly http: ScientificHTTP;
  private readonly data: DataProvenanceClient;
  constructor(fetcher: typeof fetch = fetch, timeoutMs = 15000) {
    this.http = new ScientificHTTP(fetcher, timeoutMs); this.data = new DataProvenanceClient(fetcher, timeoutMs);
  }
  async load(input: FollowupSelection, signal: AbortSignal): Promise<RetainedProposal> {
    const selection = structuredClone(input), item = selection.response;
    const id = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
    if (![selection.checkpoint.run_id, selection.checkpoint.decision_id, item.response_id].every(value => id.test(value)) ||
        !same(selection.request.engagement.scope, selection.checkpoint.scope)) throw new ScientificReadFailure("invalid_request");
    const record = await this.http.get("/api/runtime/v1/supervision/responses/" + encodeURIComponent(item.response_id),
      value => decodeFollowup("response", value), signal);
    const bytes = new TextEncoder().encode(canonical(record)), observation = record.observation;
    requireReply(bytes.byteLength <= 262144 && await sha256(bytes) === item.response_sha256);
    active(signal);
    requireReply(record.response_id === item.response_id && same(record.reference, selection.checkpoint) &&
      record.request_sha256 === selection.request.request_sha256 &&
      same(observation.attempt.engagement, selection.request.engagement) &&
      observation.attempt.request_sha256 === selection.request.planning_request_sha256 &&
      observation.attempt.ordinal === item.attempt_ordinal && observation.status === item.status && observation.reason_code === item.reason_code &&
      observation.output_complete === item.output_complete && observation.captured_bytes === item.captured_bytes &&
      observation.output_sha256 === item.output_sha256 && same(record.capture, item.capture));
    if (!record.capture || !observation.output_complete || !["proposed", "abstained"].includes(observation.status) || !observation.proposal)
      throw new ScientificReadFailure("unavailable");
    const capture = record.capture;
    requireReply(same(capture.scope, selection.checkpoint.scope) && capture.size_bytes > 0 && capture.size_bytes <= 65536 &&
      capture.size_bytes === observation.captured_bytes && capture.sha256 === observation.output_sha256);
    await this.data.artifact(capture, signal);
    const content = await this.http.content("/api/data/v1/artifacts/" + encodeURIComponent(capture.artifact_id) + "/content",
      capture.size_bytes, capture.media_type, signal);
    requireReply(await sha256(content) === capture.sha256);
    active(signal);
    const proposal = observation.proposal;
    requireReply(await sha256(new TextEncoder().encode(proposal.payload_json)) === proposal.payload_sha256);
    active(signal);
    const kind = proposalProfile(proposal.output_schema);
    if (!kind) return { selection, record, document: null };
    let interpreted: ProposalDocument;
    try {
      const raw = decodeProposal(kind, JSON.parse(new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(content)));
      interpreted = decodeProposal(kind, JSON.parse(proposal.payload_json));
      requireReply(authoredMatches(raw.draft, interpreted.draft));
    } catch { throw new ScientificReadFailure("invalid_response"); }
    requireReply(interpreted.draft.action === proposal.action && interpreted.draft.rationale === proposal.rationale);
    active(signal);
    return { selection, record, document: interpreted };
  }
}
