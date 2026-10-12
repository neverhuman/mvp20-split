import { decodeCapability, decodeCuration, type CapabilityRequestView, type CurationView } from '../../contracts/campaign_curation.js';
import { bindCapability, bindCuration, type CapabilitySelection, type CurationSelection } from '../../transport/campaign_curation/identity.js';
import { ScientificReadFailure } from '../../transport/scientific/failure.js';
import { immutable } from '../explore/context.js';

/** Semantic comparison of validated browser values, never a canonical-byte hash. */
export function sameValue(left: unknown, right: unknown): boolean {
  function ordered(value: unknown): unknown {
    if (Array.isArray(value)) return value.map(ordered);
    if (value !== null && typeof value === 'object') return Object.fromEntries(Object.entries(value)
      .sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([key, item]) => [key, ordered(item)]));
    return value;
  }
  return JSON.stringify(ordered(left)) === JSON.stringify(ordered(right));
}
function requireOriginal(value: boolean) { if (!value) throw new ScientificReadFailure('invalid_response'); }

export class RecordedCuration {
  readonly data: CurationView;
  readonly selection: CurationSelection;
  constructor(data: CurationView, selection: CurationSelection) {
    this.selection = immutable(selection);
    this.data = immutable(bindCuration(decodeCuration(data), this.selection));
    Object.freeze(this);
  }
  get terminal() {
    return ['ready','failed','indeterminate','abstained'].includes(this.data.receipt.phase)||
      this.data.receipt.phase==='proposed'&&this.data.proposal?.outcome.kind==='request_capabilities';
  }
  get status() {
    if (this.data.receipt.phase === 'proposed' && !this.data.proposal) return 'Proposal details unavailable';
    if (this.data.receipt.phase === 'proposed' && this.data.proposal?.outcome.kind === 'request_capabilities')
      return 'Additional tools needed';
    const labels: Record<CurationView['receipt']['phase'], string> = { queued: 'Revision requested',
      assembling: 'Collecting research context', awaiting_provider: 'Awaiting model result',
      proposed: 'Proposal recorded', abstained: 'No revision proposed', compiling: 'Validating proposed graph',
      ready: 'Draft validated for a future campaign', failed: 'Revision preparation failed', indeterminate: 'Outcome unknown' };
    return labels[this.data.receipt.phase];
  }
  get requests() {
    const outcome = this.data.proposal?.outcome;
    const gaps = outcome && 'gaps' in outcome ? outcome.gaps : [];
    return Object.freeze(gaps.map((gap, index) => Object.freeze({ index, reference: this.data.capability_requests[index]!,
      purpose: gap.purpose, graphGap: gap.graph_gap })));
  }
  capability(index: number): CapabilitySelection {
    const outcome = this.data.proposal?.outcome;
    const gaps = outcome && 'gaps' in outcome ? outcome.gaps : [];
    if (!Number.isInteger(index) || index < 0 || index >= gaps.length) throw new ScientificReadFailure('invalid_request');
    return immutable({ reference: this.data.capability_requests[index]!, curation: this.data.receipt.reference,
      actor: this.selection.actor, gap: gaps[index]! });
  }
  reconcile(next: RecordedCuration) {
    const before = this.data, after = next.data;
    requireOriginal(sameValue(this.selection, next.selection) && sameValue(before.receipt.identity, after.receipt.identity) &&
      before.receipt.request_sha256 === after.receipt.request_sha256 && before.receipt.created_at === after.receipt.created_at &&
      sameValue(before.specification, after.specification) && after.receipt.revision >= before.receipt.revision &&
      Date.parse(after.receipt.updated_at) >= Date.parse(before.receipt.updated_at));
    if (before.receipt.revision === after.receipt.revision) requireOriginal(sameValue(before, after));
    if (this.terminal)
      requireOriginal(sameValue(before, after));
    if (before.provider !== null) requireOriginal(sameValue(before.provider, after.provider));
    if (before.proposal !== null) requireOriginal(sameValue(before.proposal, after.proposal));
    if (before.validated_draft !== null) requireOriginal(sameValue(before.validated_draft, after.validated_draft));
  }
}

export class RecordedCapability {
  readonly data: CapabilityRequestView;
  constructor(data: CapabilityRequestView, selection: CapabilitySelection) {
    this.data = immutable(bindCapability(decodeCapability(data), selection));
    Object.freeze(this);
  }
  get fulfillmentStatus() {
    const status = this.data.fulfillment?.status;
    if (!status) return 'Not yet supplied';
    return { pending: 'Evidence review pending', rejected: 'Evidence not accepted',
      indeterminate: 'Review outcome unknown', verified: 'Fulfillment evidence verified' }[status];
  }
  get evidence() { return this.data.fulfillment?.specification.acceptance_evidence ?? []; }
  reconcile(next: RecordedCapability) {
    const before = this.data, after = next.data;
    requireOriginal(sameValue(before.reference, after.reference) && sameValue(before.curation, after.curation) &&
      sameValue(before.gap, after.gap) && before.proposal_sha256 === after.proposal_sha256);
    const oldReceipt = before.fulfillment, receipt = after.fulfillment;
    if (oldReceipt?.status === 'verified') requireOriginal(sameValue(oldReceipt, receipt));
    if (oldReceipt && receipt && sameValue(oldReceipt.identity, receipt.identity)) {
      requireOriginal(oldReceipt.request_sha256 === receipt.request_sha256 && sameValue(oldReceipt.specification, receipt.specification));
      if (oldReceipt.status !== 'pending' || receipt.status === 'pending') requireOriginal(sameValue(oldReceipt, receipt));
      else requireOriginal(Date.parse(receipt.created_at) >= Date.parse(oldReceipt.created_at));
    }
  }
}
