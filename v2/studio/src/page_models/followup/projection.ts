import type { CriterionRef, ProposalDocument } from "../../contracts/followup.js";
import { canonical, requireReply, same } from "../../transport/scientific/identity.js";
import { immutable } from "../explore/context.js";

export type ProposalRow =
  | { readonly kind: "target"; readonly criterion: CriterionRef; readonly improvement: string; readonly learning: string }
  | { readonly kind: "unresolved"; readonly criterion: CriterionRef | null; readonly description: string; readonly posture: string }
  | { readonly kind: "evidence"; readonly criterion: null; readonly description: string; readonly uncertainty: string };
export interface ProposalPage { readonly rows: readonly ProposalRow[]; readonly offset: number; readonly total: number; readonly hasNext: boolean }

/** Proposed intent is separate from execution or scientific acceptance. */
export class ProposalProjection {
  readonly document: ProposalDocument;
  readonly adoption = "Not verified";
  private readonly rows: readonly ProposalRow[];
  constructor(input: ProposalDocument, scope: CriterionRef["question"]["scope"]) {
    this.document = immutable(input);
    const document = this.document, rows: ProposalRow[] = [];
    if (document.kind === "followup") {
      const seen = new Map<string, string>();
      const check = (ref: CriterionRef) => {
        requireReply(same(ref.question.scope, scope) && same(ref.need.scope, scope));
        if (ref.assessment) requireReply(same(ref.assessment.request.question, ref.question));
        const key = canonical([ref.question, ref.need, ref.criterion_id]), full = canonical(ref);
        requireReply(!seen.has(key) || seen.get(key) === full); seen.set(key, full);
        return full;
      };
      for (const group of [document.draft.targets, document.draft.unresolved]) {
        const unique = new Set<string>();
        for (const item of group) { const key = check(item.criterion); requireReply(!unique.has(key)); unique.add(key); }
      }
      requireReply(document.draft.action !== "abstain" || document.draft.targets.length === 0);
      for (const target of document.draft.targets) {
        requireReply(Boolean(target.improvement.trim()) && Boolean(target.expected_learning.trim()));
        rows.push({ kind: "target", criterion: target.criterion, improvement: target.improvement, learning: target.expected_learning });
      }
      for (const point of document.draft.unresolved) rows.push({ kind: "unresolved", criterion: point.criterion, description: point.description, posture: point.posture });
    } else {
      for (const point of document.draft.unresolved) rows.push({ kind: "unresolved", criterion: null, description: point.description, posture: point.posture });
    }
    for (const intent of document.draft.evidence_requests) rows.push({ kind: "evidence", criterion: null, description: intent.expected_evidence, uncertainty: intent.uncertainty });
    this.rows = immutable(rows);
    Object.freeze(this);
  }
  get criterionTargetingAvailable() { return this.document.kind === "followup"; }
  page(offset = 0): ProposalPage {
    if (!Number.isSafeInteger(offset) || offset < 0 || offset % 20 !== 0 || (offset > 0 && offset >= this.rows.length)) throw new RangeError("invalid_proposal_page");
    return Object.freeze({ rows: Object.freeze(this.rows.slice(offset, offset + 20)), offset, total: this.rows.length, hasNext: offset + 20 < this.rows.length });
  }
}
