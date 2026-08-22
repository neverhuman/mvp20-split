# rights-integrity-contradiction-v1 — "all gates pass" is not rights-well-founded

**AUDIT_ONLY red-team science increment. Promotes nothing. Flips no rights gate.**
Signed with the AUDIT_ONLY use of the `PHASE0_EVALUATOR` seed key (pinned in
`config/phase0-trust-store.v1.json`), NOT as a phase0 evaluation/review signature.

**Campaign item:** C5, attack (B).

## Claim under attack

`amphora-cure-potlife-gate/evidence/phase0/kpis/cure-potlife-arrhenius-kpi.v1.json`:
"the KPI's 'all gates pass' verdict is well-founded."

## Verdict: REFUTED

The physics/arithmetic is NOT in dispute — the deterministic gates (MAPE
ceilings, applicability-domain fail-closed, authority-lock preservation)
genuinely do pass on the numbers as given. What's refuted is the framing that
passing those gates makes the KPI a well-founded Phase-0 artifact overall.

## The contradiction, plainly

1. `evidence/phase0/sources/source-lock.v2.json`: `rights_gate_passed: false`,
   `eligible_sources: []` (zero).
2. `evidence/phase0/dataset/dataset-manifest.v1.json` agrees:
   `rights_gate_passed: false`, `scientific_success_asserted: false`.
3. `config/program/cure-sources.v1.json` (the module's own source census):
   **3/3** in-tree cure TDS sources are `QUARANTINED`,
   `eligible_for_derivatives: false`, with an explicit restriction: *"Do not
   train or benchmark until derivative-use eligibility is established."*
4. Yet the signed `cure-potlife-arrhenius-kpi.v1.json` declares
   `phase0_deterministic_gates_passed: true` and all 6 metrics `passed: true`
   — the module **was** benchmarked.

## The deeper finding: an ungoverned self-assertion

The KPI's `dataset_fixture_sha256` field points byte-for-byte at
`reference/phase0-cure-potlife-known-answer.v1.json` (verified: sha256
`7ba2d0d9…` matches exactly). That fixture carries its **own** in-file
`rights` block, self-declaring `license: CC0-1.0`, `eligible_for_derivatives:
true`, `status: ACCEPTED` — a bare assertion with **no signed rights
receipt**. The file appears in **neither** `source-lock.v2.json`'s
`eligible_sources` (empty) **nor** its `excluded_sources` list — it sits
entirely outside the rights-gate accounting.

Yet 10 of its 12 systems' `pot_life_source` fields cite named vendor TDS
documents directly (Dow DER 331+DEH20/24, Huntsman Araldite/Aradur, Air
Products Ancamine, Momentive Heloxy/EPI-CURE, Mitsubishi Gaskineide) — the
exact category of material (`vendor TDS`) that the module's own source
census quarantines elsewhere in the same tree, with the same explicit
"do not benchmark" restriction.

## What is true / what is false

- **True:** the deterministic physics gates pass; the arithmetic is honest
  given the input numbers.
- **False:** that "all gates pass" implies the KPI is rights-clean or
  well-founded as a whole. The rights precondition the module gates on
  elsewhere is failing, on data whose own provenance was never ledgered
  through the module's rights pipeline.

## What this does NOT do

Does not claim the physics/arithmetic in the KPI is wrong; does not flip
`rights_gate_passed` (requires each source ingested through
`amphora-source-ledger` under a signed rights receipt — a human step); does
not promote `amphora-cure-potlife-gate` to PHASE_0; does not modify
`source-lock.v2.json`, `dataset-manifest.v1.json`, `cure-sources.v1.json`,
the known-answer fixture, the signed KPI, the manifest, or any prior
receipt; opens, parses, or derives from no quarantined source's payload
content (rights metadata only).

## Files

- `run_rights_integrity_audit.py` — deterministic rights-metadata audit harness
- `diagnostic.canonical.json` == `diagnostic.runB.json` (two-replay PASS, sha `baa1a778…`)
- `rights-integrity-contradiction-receipt.v1.dsse.json` — DSSE Ed25519, AUDIT_ONLY use of `PHASE0_EVALUATOR` key, SIGNATURE_VERIFY = PASS, key_id derives the pinned trust-store entry
- `sign_rights_integrity.py` — signing + self-verification

## Reproduce

    python3 run_rights_integrity_audit.py > /tmp/out.json   # diagnostic
    python3 sign_rights_integrity.py                         # DSSE Ed25519, AUDIT_ONLY
