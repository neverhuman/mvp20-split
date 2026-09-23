# Amphora program status — 2026-07-17

> **Snapshot, not current state.** This is the position as of 2026-07-17. Only the RDKit
> limitation below has been corrected since; nothing else was revisited for evidence filed
> after that date. Twenty-two `evidence/phase0/kpis/RETRACTION-INDEX.md`
> files and 58 `CLAIM_REFUTED` verdicts across the module trees are the authoritative record
> of what has since been withdrawn — check a module's retraction index before relying on any
> claim below. See [START_HERE.md](START_HERE.md#what-we-got-wrong).

Amphora is a functioning pre-Phase-0 research and diagnostics system. It is not
currently authorized to claim scientific superiority, product readiness,
qualification, procurement approval, FTO, or Phase 1/2 readiness.

## Assets that exist now

- Exactly 29 named mission capabilities with explicit candidate types,
  authority ceilings, claim locks, and demotion policy.
- Exact v1 canonical JSON hashing plus a strict native parser and typed
  candidate boundary.
- Deterministic formulation arithmetic and design-envelope diagnostics,
  known-answer fixtures, structural negative controls, source ledgers, CRO
  packet inputs, and replayable run state.
- Public and supplier archives retained by content identity. Rights-unresolved
  artifacts are archived but excluded from ranking and promotion evidence.
- Thirty rights-known raw public-corrosion CSV artifacts and six public coating
  systems available for benchmark work; current evaluation shows no promoted
  lift and makes no candidate-performance claim.
- Native Rust capability groups for molecule, formulation/performance,
  assurance/evidence, and the trust kernel.

## Measured limitations

- The current cure benchmark performs worse than its named median baseline.
- The reconciled control-by-control receipt records 13 `VERIFIED_PASS` controls and one
  `UNVERIFIED` historical control. The arithmetic artifact is a 6/6 subset and is never
  represented as a 14/14 known-answer result.
- Public-corrosion evaluation currently shows zero promoted lift and is not
  candidate-bound.
- Molecular role and novelty work lack the locked independent labels and fully
  rights-cleared production corpus required for ranking.
- Chemistry normalization and positive structural applicability fail closed unless the
  pinned RDKit C++ 2026.03.2 boundary is built and the non-default `rdkit` cargo feature is
  enabled; no substitute canonicalizer is ever used. (As of 2026-08-23 that boundary **is**
  built at `/home/ubuntu/.local/share/amphora/rdkit-2026.03.2/` -- on xbabe2 originally, and
    on xbabe1 since the 2026-08-24 move, verified byte-identical -- and
  `amphora-rdkit-ffi/evidence/phase0/repairs/W-FFI2/` records builds against it with
  `exact_version_match=true`. The 2026-07-17 statement that it was absent is superseded.
  Build instructions: [BUILD.md](BUILD.md).)
- External CRO, supplier, laboratory, counsel, and independent red-team work
  cannot be completed by a software build and remains an explicit evidence or
  procurement checkpoint.

## Promotion rule

A module becomes ranking-eligible only after its manifest/profile policy is
changed through review and its named locked external gate passes. Software
parity, successful compilation, green unit tests, or a generated report cannot
promote scientific authority.

Until then, Amphora can generate or ingest candidates, reject malformed inputs,
run deterministic diagnostics, package experiments, preserve evidence, and
replay hash-bound decisions without presenting diagnostic values as a
validated optimizer.
