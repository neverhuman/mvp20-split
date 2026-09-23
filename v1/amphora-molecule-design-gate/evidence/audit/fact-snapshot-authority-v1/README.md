# amphora-molecule-design-gate :: fact-snapshot-authority-v1

**AUDIT_ONLY.** First live-Rust differential audit of the design gate's
*decision authority*: which input actually authors the gate verdict. Does not
modify the live Rust runtime, the fixture, any locked dataset, the portfolio
manifest (66 receipts / 11 modules), or any signed Phase-0 KPI.

## Claim under audit

The shipped Phase-0 KPI (`tests/design_gate_phase0_kpi.rs`, 42 records) asserts
gate-decision correctness, six `gate_reason` categories, and
malformed-input **fail-closed** behaviour. In every shipped record the malformed
structures carry **no** `molecule_facts_v1` snapshot, so the fail-closed lexical
ladder is only ever exercised on the facts-**absent** branch. The
STRUCTURE × SNAPSHOT decision cell is untested.

## Method

A live-Rust harness (`live_harness/`) drives the *same* `design_gate_result`
surface the shipped KPI uses, over 95 probes (`make_probes.py`). An independent
Python re-implementation of the documented decision function (`analyze.py`)
predicts each verdict from probe metadata and is compared against the live run.
Two-replay byte-stable; oracle matches the live runtime on **95/95** probes.

## Finding

On the facts-**present** branch, `design_gate_result` is a pure function of the
host-injected `MoleculeFactsV1` — `(declared_role, oxirane_ring_count>0,
reactive_amine_hydrogen_count>0)`. It consults **neither** the candidate's own
structure text **nor** the snapshot's structure-identity binding fields
(`canonical_structure_sha256`, `canonical_isomeric_smiles`).

- **G1** 8/8 structurally inert molecules (benzene, water, cyclohexane, THF,
  acetamide, pyridine, a resin re-badged as hardener) with forged
  role-appropriate facts **SCORE / pass**.
- **G2** the lexical structure ladder is **dead code** when a well-typed
  snapshot is present: a multi-fragment salt / wildcard / empty / missing-SMILES
  candidate that fails closed (`multi_fragment_structure`, …) with facts absent
  **passes** with facts present (4 paired controls); two lexically-clean but
  valence-impossible structures show even the fallback ladder cannot reject them
  (only the host normaliser can).
- **G3** DGEBA's honest facts attached to benzene still **pass** — the snapshot's
  binding fields are inert to the gate (2/2).
- **G4** the `MoleculeFactsV1` serde contract is the **sole** admission wall on
  that branch: 5 malformed snapshot classes (negative/string/float u32, unknown
  field, missing field) fall to the fail-closed branch; 1 well-typed forgery is
  accepted.
- **G5** count-insensitive above the presence threshold (`ox=1` ≡ `ox=u32::MAX`).
- **G6** the `role × (ox,nh)` decision grid is exact (16/16).
- **G0** non-regression: all 42 shipped records reproduce their shipped labels.
- **G7** every probe is two-replay byte-stable.

## Consequence

The shipped KPI's **malformed-fail-closed guarantee is conditional** on the
upstream host normaliser (`amphora-engine::normalize_molecule` →
`amphora_rdkit_ffi::molecule_facts`) never emitting a snapshot for a malformed or
structurally-inconsistent candidate. Structural binding to *this* candidate is
owned upstream, **not** by `design_gate_result`. This receipt bounds the KPI
claim to the facts-absent pathway and localises where binding actually lives.

Not a runtime vulnerability: in the real pipeline the host is the party that
emits snapshots, and only for parseable single-component structures. This is a
scope / provenance boundary finding, consistent with the gate's stated
structural-applicability-only scope.

## Reproduce

```
cd live_harness && cargo build            # links the live workspace crates
python3 make_probes.py <fixture> probes.v1.json
./target/debug/design-gate-fact-snapshot-authority-harness probes.v1.json > live-run.canonical.json
python3 analyze.py probes.v1.json live-run.canonical.json <fixture> > diagnostic.canonical.json
python3 sign_fact_snapshot_authority.py   # DSSE Ed25519, two-replay gate
```

Theory anchors: live runtime `design_gate_result` / `normalized_facts`;
`MoleculeFactsV1` serde contract (`deny_unknown_fields`, u32);
`amphora-engine::normalize_molecule`; epoxy-amine cure scope (Ellis 1993 Ch.6;
Wicks/Jones/Pappas 2007 Ch.15).
