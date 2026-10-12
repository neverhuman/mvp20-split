import type { CapabilityRef, CapabilityRequestView, CurationRef, CurationView } from "../../contracts/campaign_curation.js";
import { ScientificReadFailure } from "../scientific/failure.js";

export interface CurationSelection { reference: CurationRef; actor: string; predecessor: string }
export interface CapabilitySelection { reference: CapabilityRef; curation: CurationRef; actor: string; gap: CapabilityRequestView["gap"] }
const identifier = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const curationID = /^curation-([0-9a-f]{64})$/;
export function sameScope(a: CurationRef["scope"], b: CurationRef["scope"]) {
  return a.tenant_id === b.tenant_id && a.project_id === b.project_id;
}
function check(value: boolean) { if (!value) throw new ScientificReadFailure("invalid_response"); }
export function validSelection(value: CurationSelection) {
  if (!curationID.test(value.reference.curation_id) || !identifier.test(value.actor) ||
    !identifier.test(value.predecessor) || !identifier.test(value.reference.scope.tenant_id) ||
    !identifier.test(value.reference.scope.project_id)) throw new ScientificReadFailure("invalid_request");
}
function stable(value: unknown): string {
  if (Array.isArray(value)) return '[' + value.map(stable).join(',') + ']';
  if (value !== null && typeof value === 'object') return '{' + Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)
    .map(([key, item]) => JSON.stringify(key) + ':' + stable(item)).join(',') + '}';
  return JSON.stringify(value);
}
export function bindCuration(value: CurationView, expected: CurationSelection) {
  const receipt = value.receipt, scope = expected.reference.scope;
  check(receipt.reference.curation_id === expected.reference.curation_id && sameScope(receipt.reference.scope, scope) &&
    sameScope(receipt.identity.scope, scope) && receipt.identity.actor_id === expected.actor &&
    receipt.identity.command_family === 'planning.curate_campaign' && value.specification.context.predecessor.run_id === expected.predecessor);
  check(sameScope(value.specification.context.draft.scope, scope));
  const context = value.specification.context;
  check(context.knowledge.every(head => sameScope(head.snapshot.graph.scope, scope)) &&
    [...context.questions, ...context.needs, ...context.artifacts].every(ref => sameScope(ref.scope, scope)));
  if (value.provider) check(sameScope(value.provider.attempt.engagement.scope, scope) && value.provider.attempt.ordinal === 1 &&
    value.provider.attempt.engagement.engagement_id === 'curation-call-' + receipt.request_sha256);
  if (value.proposal) check(value.provider !== null && value.provider.output_sha256 !== null);
  const gaps = value.proposal && 'gaps' in value.proposal.outcome ? value.proposal.outcome.gaps : [];
  check(gaps.length === value.capability_requests.length && new Set(gaps.map(gap => gap.gap_key)).size === gaps.length);
  const digest = curationID.exec(expected.reference.curation_id)![1];
  value.capability_requests.forEach((ref, index) => check(sameScope(ref.scope, scope) &&
    ref.request_id === 'capability-' + digest + '-' + String(index).padStart(2, '0')));
  if (receipt.phase === 'ready') check(value.validated_draft !== null && value.proposal?.outcome.kind === 'propose_campaign');
  return value;
}
export function validCapabilitySelection(value: CapabilitySelection) {
  const match = curationID.exec(value.curation.curation_id);
  if (!match || !identifier.test(value.actor) || !sameScope(value.reference.scope, value.curation.scope) ||
    !new RegExp('^capability-' + match[1] + '-(0[0-9]|1[0-5])$').test(value.reference.request_id))
    throw new ScientificReadFailure('invalid_request');
}
export function bindCapability(value: CapabilityRequestView, expected: CapabilitySelection) {
  check(value.reference.request_id === expected.reference.request_id && sameScope(value.reference.scope, expected.reference.scope) &&
    value.curation.curation_id === expected.curation.curation_id && sameScope(value.curation.scope, expected.curation.scope) &&
    sameScope(value.curation.scope, value.reference.scope) && stable(value.gap) === stable(expected.gap));
  const receipt = value.fulfillment;
  check((value.status === 'fulfilled') === (receipt?.status === 'verified'));
  if (receipt) check(receipt.identity.actor_id === expected.actor && sameScope(receipt.identity.scope, expected.reference.scope) &&
    receipt.identity.command_family === 'planning.fulfill_capability' &&
    receipt.specification.request.request_id === value.reference.request_id && sameScope(receipt.specification.request.scope, value.reference.scope) &&
    receipt.specification.acceptance_evidence.every(ref => sameScope(ref.scope, value.reference.scope)) &&
    (receipt.status !== 'verified' || receipt.reason_code === null));
  // proposal_sha256 is the owner's canonical proposal identity, not raw provider capture SHA.
  return value;
}
