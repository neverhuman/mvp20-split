# doe-fixture-citation-fidelity-v1 (AUDIT_ONLY)

Independent falsification attack against `amphora-formulation-universe`
(ROTATION fire, no campaign item; fire_id
`20260817T050001-3280050-bf83a9be45cd`).

**Claim under test:** `docs/mission.md`'s standing benchmark-fidelity claim
that "the runtime reproduces every one of the 10 published DoE examples'
cardinality counts at u64 bit precision" against the self-authored
known-answer fixture
`amphora-formulation-universe/reference/phase0-formulation-universe-known-answer.v1.json`
(SHA-256 `cb3cdb8bd40ebfeadd929ab42fed7df4596375aa1d00b24242755479676029b3`,
matches the hash cited in mission.md), which underlies the signed
`cartesian_product_arithmetic_correctness_rate` and
`cartesian_identity_correctness_rate` KPI metrics.

**Distinguishing note:** T-06 (2026-08-06, CLAIM_REFUTED, signed) and
kpi-claim-currency-v1 (2026-08-15, CLAIM_REFUTED, signed) both attacked the
`validate_formulation_universe` primitive itself (duplicate-factor-collapse,
index-identity instability, and staleness of the signed KPI register after
that finding). Neither examined whether the *fixture's own citations* to
Montgomery 2017 and Wicks/Jones/Pappas 2007 are faithful reproductions of
the named designs, or whether the runtime can even represent the design
taxonomy the fixture claims to cover. This fire attacks that different,
previously-unexamined target.

## Method

1. Re-derived, from generic (textbook-independent) Design-of-Experiments
   notation, that a genuine `2^(k-p)` fractional factorial design has
   exactly `2^(k-p)` runs by construction (a half-fraction, p=1, of a
   5-factor 2-level design has `2^(5-1) = 16` runs, not 32 — this is the
   definition of the notation, not a fact requiring access to the specific
   cited page).
2. Wrote an independent Rust test file
   (`amphora-formulation-capabilities/tests/formulation_universe_doe_citation_fidelity_v1.rs`,
   SHA-256 `147db9a4955239b72a2deb1309e7a1078d48ef8f6102ebcfa43ce60408014c0e`)
   that (a) parses every fixture entry's `universe_id`/`nominal_source` for a
   literal `2^(k-p)` pattern, (b) for any entry whose `design_type` contains
   `"fractional"`, computes the genuine fractional total `2^(k-p)` and
   compares it against the fixture's own `expected_cartesian_total`, and (c)
   calls the live, unmodified `validate_formulation_universe` with exactly
   that universe's `axes` to confirm what the runtime actually returns.
3. A second test (`doe_fixture_design_type_field_is_never_consumed_by_runtime`)
   feeds the same 5-binary-axis universe under two contradictory
   `design_type` labels (`"2^(5-1)_fractional_factorial"` vs
   `"2^k_full_factorial"`) and confirms the accounting output is
   byte-identical either way, because `validate_formulation_universe` never
   reads `/context/formulation_universe/design_type` at all (confirmed by
   inspection of `amphora-formulation-capabilities/src/lib.rs`, function
   `validate_formulation_universe`, which only reads `/axes`,
   `/infeasible_indices`, and `/claims`).
4. A parser positive control
   (`doe_fixture_positive_control_parser_reads_well_formed_labels`) verifies
   the `2^(k-p)` extraction fires on a literal numeric pattern and does NOT
   fire on the non-numeric template string `"2^(k-p)_fractional_factorial"`
   itself, so the citation-fidelity check cannot be dismissed as a detector
   that fires indiscriminately.
5. Ran the full test file twice, independently, via
   `cargo test --workspace --locked -p amphora-formulation-capabilities --test formulation_universe_doe_citation_fidelity_v1 -- --nocapture`
   and parsed both raw captures into a deterministic diagnostic JSON with
   `run_doe_citation_fidelity.py`, asserting the two parsed diagnostics are
   byte-identical (they are; only wall-clock timing in the raw `.out.txt`
   files, never load-bearing, differs across the two captures).

## Result

**Mismatch found.** Fixture entry `2^(5-1)-half-fraction-screening`:

- `design_type`: `"2^(k-p)_fractional_factorial"`
- `nominal_source`: `"Montgomery 2017 8th ed. §8.2 (2^(5-1) half-fraction)"`
- claimed `(k, p)` = `(5, 1)` → genuine fractional total = `2^(5-1) = 16`
- fixture's own `expected_cartesian_total` = **32** (= the FULL `2^5`
  un-fractionated space, not the fraction)
- live runtime, given exactly this universe's `axes`, also returns
  `cartesian_total = 32`
- the entry's own `industrial_context` field says outright: "Enumerating the
  full 2^5 space; downstream design selects half-fraction" — i.e. this
  "known answer" was never a half-fraction to begin with, contrary to its
  `universe_id` and `nominal_source`.

**Root cause, confirmed by direct inspection and by test 3:**
`validate_formulation_universe` has no generator / defining-relation /
aliasing logic anywhere in its implementation — it computes only the plain
Cartesian product `Π axis_cardinalities` of whatever per-axis value arrays
are declared, and it never reads a `design_type` field at all (that field is
present in the fixture purely as human-facing prose metadata the runtime is
architecturally blind to). So no fixture entry — not just this one — could
ever encode a genuine fractional-factorial design distinct from a
full-factorial one; the runtime cannot compute anything other than the full
per-axis product regardless of what the citation claims.

**Consequence for the standing claim:** `docs/mission.md` states "The
runtime reproduces every one of the 10 published DoE examples' cardinality
counts at u64 bit precision" and separately claims the fixture spans
"Design-of-Experiments universes from Montgomery 2017 8th ed. Ch. 5-8 ...
with cartesian totals 8-32," implicitly including a genuine fractional
design. 1 of the 10 entries' cited design (a `2^(5-1)` half-fraction, 16
runs) was never actually tested — the fixture substitutes the full `2^5`
space (32) under that citation, and the runtime could not have validated a
true fractional design's cardinality even if the fixture had encoded one
correctly, because the architecture has no fraction-selection concept. The
"every one of the 10 published DoE examples" claim is false for this entry.

The other 9 entries' citations were independently re-checked by the same
harness and are internally consistent (full-factorial and mixed-level
labels correctly match `Π axis_cardinalities`; no further mismatches were
found).

**Verdict:** CLAIM_REFUTED.

## Authority

AUDIT_ONLY. Does not promote, flip `scientific_readiness`, edit the
portfolio manifest (66/11), any locked dataset, the signed Phase-0 KPI, the
fixture, or `mission.md`. Adds one new test file (does not modify
`amphora-formulation-capabilities/src/lib.rs`). Signed under the Phase-0
evaluator seed (keyid `phase0-evaluator-<sha256(pubkey)>`, pinned in
`config/phase0-trust-store.v1.json`), DSSE PAE + Ed25519; independently
re-verified after signing.

Files: `formulation_universe_doe_citation_fidelity_v1.rs` (new Rust test,
lives under `amphora-formulation-capabilities/tests/`, referenced by
SHA-256 here, not duplicated into this directory),
`run_doe_citation_fidelity.py` (harness that parses the two raw cargo test
captures into deterministic diagnostics), `run1.out.txt`/`run1.err.txt`,
`run2.out.txt`/`run2.err.txt` (raw captured cargo test invocations),
`diagnostic.canonical.json`/`diagnostic.runB.json` (two-replay diagnostics,
byte-identical), `sign_doe_citation_fidelity.py` (signer),
`doe-citation-fidelity-receipt.v1.dsse.json` (signed receipt).
