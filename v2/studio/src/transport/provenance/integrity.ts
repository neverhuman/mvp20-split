import type { SourceSpan } from "../../contracts/scientific/provenance.js";
import { ScientificReadFailure } from "../scientific/failure.js";
import { requireReply } from "../scientific/identity.js";

export function active(signal: AbortSignal) { if (signal.aborted) throw new ScientificReadFailure("aborted"); }

export async function sha256(bytes: Uint8Array): Promise<string> {
  try {
    const result = await crypto.subtle.digest("SHA-256", new Uint8Array(bytes));
    return Array.from(new Uint8Array(result), b => b.toString(16).padStart(2, "0")).join("");
  } catch { throw new ScientificReadFailure("invalid_response"); }
}

export interface VerifiedSourceText {
  readonly span: SourceSpan;
  readonly text: string;
  readonly artifact_sha256: string;
  readonly span_sha256: string;
}

export async function verifyText(span: SourceSpan, bytes: Uint8Array, signal: AbortSignal): Promise<VerifiedSourceText> {
  active(signal);
  requireReply(bytes.byteLength === span.source.raw.size_bytes && bytes.byteLength <= 4194304);
  requireReply(span.start >= 0 && span.start <= span.end && span.end <= bytes.byteLength && span.end - span.start <= 65536);
  const artifactDigest = await sha256(bytes);
  active(signal); requireReply(artifactDigest === span.source.raw.sha256);
  const selected = bytes.slice(span.start, span.end);
  const spanDigest = await sha256(selected);
  active(signal); requireReply(spanDigest === span.sha256);
  let text: string;
  try { text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(selected); }
  catch { throw new ScientificReadFailure("invalid_response"); }
  return Object.freeze({ span: structuredClone(span), text, artifact_sha256: artifactDigest, span_sha256: spanDigest });
}
