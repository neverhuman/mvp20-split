import { decodeCapability, decodeCuration } from '../../../src/contracts/campaign_curation.js';

/** Synthetic engineering wire fixture; no real model/scientific evidence claim. */
export function fixture() {
  const scope = { tenant_id: 'synthetic', project_id: 'curation-browser' };
  const reference = { scope, curation_id: 'curation-' + 'a'.repeat(64) };
  const capabilityRef = { scope, request_id: 'capability-' + 'a'.repeat(64) + '-00' };
  const selection = { reference, actor: 'owner', predecessor: 'original-run' };
  const gap = { gap_key: 'heat', purpose: 'Measure the heated mixture', inputs: [], outputs: [{ name: 'material',
    representation: 'mixture', schema_ref: null, description: 'Heated material state', unit: null }],
    applicability: ['Synthetic process demonstration'], evidence_need: 'Retained temperature history',
    acceptance_criteria: ['Preserve original input provenance'], graph_gap: 'After mixing, before the final addition' };
  const curation = decodeCuration({ wire_version: '1', receipt: { wire_version: '1',
    identity: { schema_version: '1', scope, actor_id: 'owner', command_id: 'revise', command_family: 'planning.curate_campaign' },
    request_sha256: 'b'.repeat(64), reference, revision: 3, phase: 'proposed', reason_code: 'capabilities_requested',
    created_at: '2026-10-12T00:00:00Z', updated_at: '2026-10-12T00:01:00Z' },
    specification: { direction: 'Study the next process step', policy_id: 'synthetic', context: {
      predecessor: { run_id: selection.predecessor, revision: 1, plan_sha256: 'c'.repeat(64) },
      draft: { scope, draft_id: 'original-draft', revision: 1, content_sha256: 'd'.repeat(64) },
      knowledge: [], questions: [], needs: [], artifacts: [] } },
    provider: { attempt: { engagement: { scope, engagement_id: 'curation-call-' + 'b'.repeat(64) }, ordinal: 1,
      request_sha256: 'e'.repeat(64) }, envelope_sha256: 'f'.repeat(64), output_sha256: '1'.repeat(64),
      usage: { input_tokens: 1, output_tokens: 1, accounting_units: 1, certainty: 'reported' }, reservation_units: 250000000 },
    proposal: { schema_version: '1', profile: 'planning.campaign-curation-draft.v1', authority: 'proposal_only',
      scientific_authority: 'not_established', decision_scope: '2'.repeat(64), rationale: 'A reviewed tool is needed.',
      outcome: { kind: 'request_capabilities', gaps: [gap] }, unresolved: [] },
    capability_requests: [capabilityRef], validated_draft: null });
  const capability = decodeCapability({ wire_version: '1', reference: capabilityRef, curation: reference,
    proposal_sha256: '3'.repeat(64), gap, status: 'requested', fulfillment: null });
  return { scope, selection, curation, capability,
    detail: { reference: capabilityRef, curation: reference, actor: 'owner', gap } };
}

export function fulfilled(status: 'verified' | 'rejected' | 'pending' = 'verified') {
  const f = fixture();
  const capability = decodeCapability({ ...f.capability, status: status === 'verified' ? 'fulfilled' : 'requested',
    fulfillment: { wire_version: '1', identity: { schema_version: '1', scope: f.scope, actor_id: 'owner',
      command_family: 'planning.fulfill_capability', command_id: 'fulfill' }, request_sha256: '4'.repeat(64),
      specification: { request: f.capability.reference, release: { schema_version: '1',
        tool: { capability_id: 'heat', release: '1.0.0', image_sha256: '5'.repeat(64), contract_version: '1' },
        descriptor_sha256: '6'.repeat(64), input_schemas: [], output_schemas: [], checkpoint_schema: null },
        acceptance_evidence: [{ scope: f.scope, artifact_id: 'reviewed-report', sha256: '7'.repeat(64),
          size_bytes: 128, media_type: 'application/json', schema_ref: { schema_id: 'review', version: '1', sha256: '8'.repeat(64) } }] },
      status, reason_code: status === 'rejected' ? 'capability_acceptance_unproven' : null,
      created_at: '2026-10-12T00:02:00Z' } });
  return { ...f, capability };
}
