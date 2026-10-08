import { decodeProvenance, decodeSourceRevisionRef } from "../../contracts/scientific/provenance.js";
import type { ArtifactRef, SourceRevision, SourceSpan, ConversionTraceRef } from "../../contracts/scientific/provenance.js";
import { ScientificHTTP } from "../scientific/http.js";
import { ScientificReadFailure } from "../scientific/failure.js";
import { canonical, normalized, requireReply, same } from "../scientific/identity.js";
import { active, sha256, verifyText } from "./integrity.js";

const base = "/api/data/v1/";

export class DataProvenanceClient {
  private readonly http: ScientificHTTP;
  constructor(fetcher: typeof fetch = fetch, timeoutMs = 15_000) { this.http = new ScientificHTTP(fetcher, timeoutMs); }

  async jsonArtifact(reference: ArtifactRef, signal: AbortSignal): Promise<unknown> {
    const expected = normalized(reference, {}, value => decodeProvenance("artifact", value));
    if (expected.media_type !== 'application/json' || expected.size_bytes > 262144) throw new ScientificReadFailure('limit');
    await this.artifact(expected, signal);
    const bytes = await this.http.content(base + 'artifacts/' + encodeURIComponent(expected.artifact_id) + '/content', expected.size_bytes, expected.media_type, signal);
    requireReply(bytes.byteLength === expected.size_bytes && await sha256(bytes) === expected.sha256);
    active(signal);
    try { return JSON.parse(new TextDecoder('utf-8', { fatal:true }).decode(bytes)); }
    catch { throw new ScientificReadFailure('invalid_response'); }
  }

  async artifact(reference: ArtifactRef, signal: AbortSignal) {
    const expected = normalized(reference, {}, value => decodeProvenance("artifact", value));
    const result = await this.http.get(base + "artifacts/" + encodeURIComponent(expected.artifact_id), value => decodeProvenance("artifact", value), signal);
    requireReply(same(result, expected));
    return result;
  }

  async source(reference: SourceRevision["reference"], signal: AbortSignal) {
    const expected = normalized(reference, {}, decodeSourceRevisionRef);
    if (!same(expected.scope, expected.raw.scope)) throw new ScientificReadFailure("invalid_request");
    const result = await this.http.get(base + "acquisition/sources/" + encodeURIComponent(expected.source_id) + "/" + encodeURIComponent(expected.revision_id), value => decodeProvenance("source", value), signal);
    requireReply(same(result.reference, expected) && same(result.rights.scope, expected.scope));
    requireReply(result.supersedes === null || same(result.supersedes.scope, expected.scope));
    return result;
  }

  async trace(reference: ConversionTraceRef, signal: AbortSignal) {
    const expected = normalized(reference, {}, value => decodeProvenance("trace_ref", value));
    const result = await this.http.get(base + "acquisition/traces/" + encodeURIComponent(expected.trace_id), value => decodeProvenance("trace", value), signal);
    requireReply(result.trace_id === expected.trace_id && same(result.scope, expected.scope));
    requireReply(same(result.source.scope, expected.scope) && same(result.source.raw.scope, expected.scope) && same(result.output.scope, expected.scope));
    const bytes = new TextEncoder().encode(canonical(result));
    requireReply(bytes.byteLength <= 262144 && await sha256(bytes) === expected.sha256);
    active(signal);
    return result;
  }

  async derivation(reference: ArtifactRef, signal: AbortSignal) {
    const expected = normalized(reference, {}, value => decodeProvenance("artifact", value));
    const result = await this.http.get(base + "artifacts/" + encodeURIComponent(expected.artifact_id) + "/derivation", value => decodeProvenance("derivation", value), signal);
    requireReply(same(result.artifact, expected) && same(result.origin.scope, expected.scope));
    requireReply(result.declaration.inputs.every(input => same(input.scope, expected.scope)));
    return result;
  }

  async span(selection: SourceSpan, signal: AbortSignal) {
    const expected = normalized(selection, {}, value => decodeProvenance("span", value));
    const raw = expected.source.raw;
    if (expected.start > expected.end || expected.end > raw.size_bytes || !same(expected.source.scope, raw.scope)) throw new ScientificReadFailure("invalid_request");
    if (raw.size_bytes > 4194304 || expected.end - expected.start > 65536) throw new ScientificReadFailure("limit");
    if (!["text/plain", "application/json"].includes(raw.media_type.toLowerCase())) throw new ScientificReadFailure("unavailable");
    await this.source(expected.source, signal);
    await this.artifact(raw, signal);
    // Data separately checks current rights for content; historical metadata is not a grant.
    const bytes = await this.http.content(base + "artifacts/" + encodeURIComponent(raw.artifact_id) + "/content", raw.size_bytes, raw.media_type, signal);
    return verifyText(expected, bytes, signal);
  }
}
