# axis-adequacy-subsumption-v1

Independent non-runtime CPython oracle for **amphora-redteam-audit**, auditing the module's
own headline KPI `attack_axis_coverage_complete_rate` (shipped: observed 1.0, floor 1.0,
MAXIMIZE, sample_size 24, passed=true) — the field whose *name* asserts that adversarial
attack-axis coverage of the locked corpus is COMPLETE.

Non-overlapping with both prior amphora-redteam-audit oracles:
`meta-integrity-oracle-parity-v1` covered OUTPUT digest parity + a result-tamper corpus,
and its G3 asserted only the **checked → declared** direction (24/24 KPI axes are present
in the benchmark-lock). `dispatch-boundary-fail-closed-v1` covered the INPUT module-id
allowlist. Neither tested the **converse** direction — declared → checked — which is where
the adequacy gap turns out to live.

Falsifiable hypothesis, stated as a test-adequacy criterion (Zhu–Hall–May 1997):
`C_declared` = "every attack axis declared in the benchmark-lock is cross-checked by the
coverage KPI". If the shipped KPI satisfies `C_declared`, observed(`C_declared`) = 1.0.

## Verdict: HYPOTHESIS_PARTIALLY_REFUTED (7/7 gates executed and passed)

**Corroborated as arithmetic** — under its own criterion (`C_self`: every cross-checked
axis is declared), the KPI reproduces exactly 24/24 = 1.0, replay-identical across both
shipped replays. No arithmetic defect.

**Refuted as a completeness claim** — the lock declares **46 unique** axes; the KPI
cross-checks **24**. Under `C_declared` the same evidence yields **12/23 = 0.521739**,
below the KPI's own 1.0 floor. **22 axes are declared-and-never-cross-checked.**

## Gates

- **G1 lock multiset structure + digest parity** — benchmark_lock_sha256 recomputed from
  raw bytes matches the shipped anchor byte-exact. `attacks` has length **47** but only
  **46 unique** members: `AUTHORITY_ESCALATION` appears twice (indices 14 and 46), so the
  lock is a multiset, not a set.
- **G2 shipped-KPI reproduction under its own criterion** — independent recomputation of
  `C_self` gives 1.0 at n=24, equal to shipped observed/sample_size/passed;
  first_replay KPI == second_replay KPI. `arithmetic_defect_found: false`.
- **G3 adequacy-subsumption falsification** — checked ⊊ declared, so `C_declared` strictly
  subsumes `C_self` on this instance (Rapps–Weyuker 1985 subsumption ordering). 22 axes
  uncovered, named in full in the receipt: STALE_PARENT, SAME_SIGNER_REVIEW,
  WRONG_ROLE_SIGNATURE, FORGED_SIGNATURE, REPOSITORY_LOCAL_PRIVATE_KEY, FORGED_RIGHTS,
  MISSING_LICENSE, STRIPPED_CLAIM_LOCK, CANDIDATE_SUPPLIED_EVIDENCE,
  CROSS_MODULE_PATH_SUBSTITUTION, REPLAY_DRIFT, ALTERED_BENCHMARK_OUTPUT,
  FALSE_HUMAN_REVIEW_CLAIM, FALSE_MOVEMENT_CLAIM, NEGATIVE_RESULT_AUTHORITY_ESCALATION,
  LEGACY_AMPHORA_RECEIPT_LAUNDERING, STRIPPED_MISSION_LOCKS,
  FAILING_DETERMINISTIC_DIAGNOSTIC, FALSE_BENCHMARK_EXECUTION_COMPLETE,
  INCOMPLETE_REVIEW_POLICY, UNKNOWN_REVIEWER_MODULE, SUPERSESSION_ARCHIVE_SUBSTITUTION.
  ⇒ "complete" in the KPI name is **scope-relative, not corpus-relative**.
- **G4 block-partition diagnosis** — the cross-checked set is *exactly* the ordered
  contiguous suffix `attacks[23:47]`. The lock is two concatenated corpora: an OUTER
  portfolio-governance block (23 axes, delegated to sibling modules) and an INNER
  meta-audit block (24 axes, self-checked), intersecting in exactly one axis,
  `AUTHORITY_ESCALATION` — which is therefore both the sole delegated-and-self-checked
  axis and the source of the duplicate. A random 24-subset of 46 landing on a contiguous
  ordered suffix has probability 1.27e-13, so the omission is a **scoping seam, not a
  random or adversarial omission**.
- **G5 compensating-control search** — 29 shipped module benchmark-locks scanned. Each of
  the 22 uncovered axes is declared in **27–28 of 28 sibling locks**, yet
  `attack_axis_coverage_complete_rate` exists in exactly **1 of 29** shipped module
  results (amphora-redteam-audit itself). No sibling ships a KPI cross-checking its own
  declared axes ⇒ the outer 22 are **DECLARED_ONLY portfolio-wide**; 0 compensating
  KPI-level attestations found.
- **G6 duplicate-axis counterfactual** — the duplicate is **KPI-inert** (both `C_self` and
  `C_declared` are unchanged when removed) but **digest-load-bearing**: JCS de-duplication
  changes the canonical digest (3a81a6e4… → bb23e5f6…), so any well-intentioned downstream
  normalization that set-izes `attacks` breaks benchmark-lock continuity. Recorded as an
  operational hazard, not a security defect.
- **G7 anchors + replay determinism** — shipped result.v1.json, benchmark-lock and KPI
  document hashes anchored; benchmark_execution_complete true; replay-1 KPI == replay-2.

## Theory

Zhu, Hall & May (1997) *Software Unit Test Coverage and Adequacy*, ACM Comput. Surv.
29(4):366–427, doi:10.1145/267580.267590 — an adequacy criterion is a predicate over a
**declared** requirement set. Rapps & Weyuker (1985), IEEE TSE SE-11(4):367–375,
doi:10.1109/TSE.1985.232226 — subsumption ordering of adequacy criteria. DeMillo, Lipton
& Sayward (1978), IEEE Computer 11(4):34–41, doi:10.1109/C-M.1978.218136 — an unexercised
fault class cannot be killed by the suite. Anderson (1972) ESD-TR-73-51 reference monitor;
Saltzer & Schroeder (1975) Proc. IEEE 63(9):1278–1308, doi:10.1109/PROC.1975.9939 —
complete mediation is only as wide as the enumerated surface. NIST SP 800-53 Rev.5
CA-8/RA-5 — assessment coverage is stated against a defined scope. RFC 8785 JCS;
FIPS 180-4 SHA-256; RFC 8032 Ed25519.

## Run

```
python3 oracle_axis_adequacy.py      # stdout byte-stable; == result.v1.json
                                     # sha256 547dd17ab014f076d94e572bf0eb39efc55b11d287cd9ca49b44a5d942c1b1f5
python3 sign_axis_adequacy.py
```

Signed AUDIT_ONLY receipt:
`../../evidence/phase0/independent/axis-adequacy-subsumption-v1.dsse.json`
(phase0-evaluator key `3ef6b35c…`, DSSE PAE + Ed25519, two-replay SHA-256 gate PASS).

## Ceiling

Offline oracle over shipped evidence bytes. It measures **which axes the shipped KPI
cross-checks**, not whether the Rust runtime defends the uncovered 22 — sibling runtimes
may implement those defenses without a coverage KPI. Live Rust re-execution of the
per-axis adversarial corpus plus error-taxonomy parity remain the Phase-1 axis.

The receipt carries a non-authoritative remediation note (rename the KPI to
`meta_audit_axis_coverage_complete_rate` and add an outer-block KPI, **or** require each
sibling to ship its own axis-coverage KPI). This oracle changes nothing: AUDIT_ONLY, no
promotion, no authority, manifest (66 receipts / 11 modules), benchmark-lock, locked
dataset and signed Phase-0 KPI all untouched.
