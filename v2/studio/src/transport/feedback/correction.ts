import type { ReceiptCorrectionView } from "../../contracts/scientific/feedback.js";
import { canonical, same, requireReply } from "../scientific/identity.js";
import { active, sha256 } from "../provenance/integrity.js";

/** Match the owner's compact, sorted, ensure_ascii Python record encoding. */
export async function verifyCorrection(view: ReceiptCorrectionView, owner: "research" | "knowledge", signal: AbortSignal) {
  const { record, reference } = view;
  const encoded = canonical(record).replace(/[\u007f-\uffff]/g, c => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"));
  const digest = await sha256(new TextEncoder().encode(encoded));
  active(signal);
  requireReply(digest === reference.record_sha256 && same(record.chain, reference.chain) && record.ordinal === reference.ordinal);
  const purpose = owner === "research" ? "research.synthetic_sufficiency" : "knowledge.synthetic_entailment";
  for (const receipt of [record.source_receipt, record.receipt]) {
    requireReply(receipt.purpose === purpose && receipt.issuer_id === record.chain.issuer_id && same(receipt.scope, record.chain.scope) && same(receipt.subject.scope, record.chain.scope) && receipt.outcome.status !== "superseded");
    if (receipt.outcome.status === "accepted") requireReply(same(receipt.outcome.output.artifact.scope, record.chain.scope));
  }
  requireReply(same(record.source_receipt.subject, record.receipt.subject) && same(record.source_receipt.outcome, record.receipt.outcome));
  if (record.ordinal === 1) requireReply(record.predecessor === null && record.notice === null);
  else {
    requireReply(record.predecessor !== null && same(record.predecessor.chain, record.chain) && record.predecessor.ordinal === record.ordinal - 1);
    requireReply(record.notice !== null && record.notice.outcome.status === "superseded");
    requireReply(record.notice.outcome.replacement_revision === record.receipt.revision && record.notice.outcome.reason_code === record.reason_code && same(record.notice.scope, record.chain.scope) && same(record.notice.subject, record.receipt.subject) && record.notice.purpose === purpose && record.notice.issuer_id === record.chain.issuer_id);
  }
}
