# kpi-claim-currency-v1 (AUDIT_ONLY)

Independent governance-currency audit for amphora-formulation-universe.

**Claim under test:** the machine-readable Phase-0 KPI register
(`evidence/phase0/kpis/formulation-universe-cartesian-accounting-kpi.v1.json`,
metric `cartesian_canonical_duplication_fail_closed_rate`, observed 1.0,
passed=true, 4 probes: literal string duplicate, integer duplicate, null
duplicate, canonically-equal reordered objects) is a CURRENT, non-stale
characterization of the CARTESIAN_CANONICAL_DUPLICATION attack axis.

**Distinguishing note:** T-06 (2026-08-06, CLAIM_REFUTED, signed) already
red-teamed the live Rust `validate_formulation_universe` directly and found
two defects (numeric-type duplicate evasion `1` vs `1.0`; index-identity
instability across accounting-equivalent axis-value orderings). That verdict
stands and is not re-litigated here. This fire attacks a different artifact:
whether the signed KPI JSON — the thing a downstream script, not a human,
would parse — was ever corrected to reflect T-06's confirmed finding.

**Method:**
1. Provenance continuity — re-hashed `amphora-formulation-capabilities/src/lib.rs`
   and T-06's own test file
   (`tests/formulation_universe_redteam_t06_independent.rs`) and compared
   against T-06's own signed provenance: byte-for-byte unchanged since
   2026-08-06 (no fix has landed).
2. Fresh, independent, back-to-back re-execution TODAY (twice) of T-06's test
   file via `cargo test --workspace --locked -p amphora-formulation-capabilities
   --test formulation_universe_redteam_t06_independent -- --nocapture` against
   the live, unmodified runtime.
3. Supersession/retraction grep across `evidence/` for any reference to the
   KPI file path, plus an existence check for
   `evidence/phase0/kpis/RETRACTION-INDEX.md`.
4. `git log` on the KPI file itself.

**Result:**
- Both named T-06 defects are confirmed LIVE today, 9 days later:
  `axes={"dose_ratio": [1, 1.0]}` still returns `Ok(cardinality=2)` instead of
  `Err`; two accounting-equivalent universes still decode declared index 1 to
  two different physical formulations.
- `lib.rs` and T-06's test file are byte-identical to T-06's own recorded
  provenance — zero code change since the refutation.
- The KPI JSON's last git commit (2026-08-03, baseline) predates T-06
  (2026-08-06) by three days and has never been touched since.
- No `RETRACTION-INDEX.md` exists for this module; no file under `evidence/`
  references the KPI path in a supersession/retraction context.
- Two-replay: byte-identical (`diagnostic.canonical.json` ==
  `diagnostic.runB.json`, sha256 `d4427674ea37cd27...`). cargo stdout
  test-result summary is byte-identical across both runs; stderr differs only
  in non-load-bearing build-tool noise (package-cache lock waits under
  concurrent CI load), and the parsed diagnostic fields agree exactly.

**Verdict:** CLAIM_REFUTED. The standing KPI register presents
`observed=1.0, passed=true` with no caveat for an attack axis with a
confirmed, unretracted, still-live counter-example.

**Authority:** AUDIT_ONLY. Does not promote, flip `scientific_readiness`,
edit the portfolio manifest (66/11), any locked dataset, the signed Phase-0
KPI, mission.md, or the live Rust engine. Signed under the Phase-0 evaluator
seed (keyid `phase0-evaluator-3ef6b35c...`, pinned in
`config/phase0-trust-store.v1.json`), DSSE PAE + Ed25519; independently
re-verified after signing.

Files: `run_kpi_claim_currency.py` (harness), `diagnostic.canonical.json` /
`diagnostic.runB.json` (two replays), `run1.out.txt`/`run1.err.txt`,
`run2.out.txt`/`run2.err.txt` (raw captured cargo test invocations),
`sign_kpi_claim_currency.py` (signer),
`kpi-claim-currency-receipt.v1.dsse.json` (signed receipt).
