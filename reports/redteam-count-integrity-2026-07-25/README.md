# Red-team memo — the "16 Phase-0 modules" headline is not defensible (9 is)

**Date:** 2026-07-25 · **Host:** all work on the canonical Linux host
(`ssh xbabe2:/home/ubuntu/amphora/build/mvp20-split`) · **Authority:** AUDIT_ONLY,
promotes nothing, modifies none of the 66 signed receipts.

This was the last cron pass before the founder report. It was asked to disprove
"we have full Phase 0" and to make real, honest progress. It does both, and — new
this run — it converts the most consequential red-team finding from prose into a
**cryptographically-anchored, two-replay-gated, signed artifact** the founder deck
can cite directly.

---

## 1. Verdict (independently re-verified on the canonical host)

**We do not have full Phase 0. The defensible count is 9, not 16, and zero of the
9 is a science capability.** `config/program/phase0-decision-report.v2.json`
reports `status = EXECUTION_INCOMPLETE`, 16 PHASE_0 / 13 PRE_PHASE_0,
`promotable = false` for all 29.

I recomputed, from scratch on this host, for every module the report calls
PHASE_0: (a) whether its signed `evaluation.v1.dsse.json` still binds to the
benchmark bytes on disk, and (b) whether that receipt carries a valid
trust-anchored `PHASE0_EVALUATOR` Ed25519 signature.

| | count | modules |
|---|---|---|
| **Defensible PHASE_0** | **9** | candidate-contract, envelope-gates, formulation-arithmetic, formulation-universe, model-card-authority, molecule-design-gate, process-qc-twin, run-provenance, tolerance-robustness |
| **Drifted — would FAIL re-verification** | **7** | cro-protocol-packager, evidence-intake-validator, known-answer-benchmarks, optimizer-orchestrator, redteam-audit, report-packager, source-ledger |

All 9 defensible modules are **infrastructure / trust-kernel / deterministic-control**.
Every scientific-capability module (solvency, barrier-corrosion, cure-potlife,
viscosity, molecule-property/novelty/generator/role-ranker, design-rule,
public-corrosion, ingredient-library) is PRE_PHASE_0.

## 2. Why the 7 are indefensible — post-signing drift, not forgery

Each module's signed receipt binds `metrics.benchmark_result_sha256` to
`evidence/phase0/benchmark/result.v1.json`. For the 7, the attested hash no longer
matches disk:

| module | attested | disk |
|---|---|---|
| cro-protocol-packager | `9028beed…` | `dc2cb1dc…` |
| evidence-intake-validator | `65fcd096…` | `00dbbe9f…` |
| known-answer-benchmarks | `abfbf104…` | `3f2f6853…` |
| optimizer-orchestrator | `cfeb75e1…` | `e1d95b6b…` |
| redteam-audit | `2bba87aa…` | `701482a2…` |
| report-packager | `15720040…` | `fc797aac…` |
| source-ledger | `cdbfda04…` | `a6a680a1…` |

The reviewer (`amphora-phase0-reviewer/src/main.rs`, `verify_recorded_benchmark`)
bails on exactly this — *"recorded benchmark is not bound to the evaluation
receipt"* — so all 7 fail a re-run today. **The receipts themselves are intact and
their trust-anchored signatures verify** (I checked all 16 signatures against the
pinned evaluator key). The corruption is the bound benchmark file: all 7
`result.v1.json` were overwritten in a 3-second batch at **2026-07-22 23:47**,
~15 h after they were signed at 08:26, and replaced with a different-schema stub
(`bundle_sha256: null`, `replay_identical: null`). This is accidental drift from a
later batch job, not a fabricated badge.

**Restoring the 7 is a governance action, not a build fix.** `phase0 evaluate`
regenerates `result.v1.json` by running the locked benchmark twice *and re-signs* —
it mints an immutable receipt. Doing that carelessly is precisely how
molecule-property and public-corrosion-benchmark became permanently unpromotable
(`EVALUATION_RESULT_MISMATCH`). So I did **not** re-run it; I flagged it.

## 3. Correction to the record — the signing keys are PRESENT, not lost

An earlier memory/audit claimed the Phase-0 evaluator/reviewer private keys were
absent, "gating every science module." **That is stale and wrong.** Both seeds are
on the host at `~/.local/share/amphora/phase0/keys/` and I cryptographically
re-derived their public keys — they reproduce the **exact pinned key_ids** in
`config/phase0-trust-store.v1.json`:

- `evaluator.ed25519.seed` → `phase0-evaluator-3ef6b35c…` ✓
- `internal-reviewer.ed25519.seed` → `phase0-internal-reviewer-47233af1…` ✓

**Consequence for the founder report:** the wall in front of a *real science
Phase-0* is **not** a missing key and **not** broken science. It is running the
evaluate/review ceremony — a governance/custody decision with portfolio-wide blast
radius (immutable receipts; and `operational_readiness: SHADOW` would force
`scientific_outcome: FAILED`, minting a hollow badge). That decision is above an
autonomous cron job's authority, so this run did not take it.

Caveat still standing: both role keys sit under one host user, so
evaluator/reviewer independence is **procedural, not cryptographic**.

## 4. The science itself holds (prior runs, rights-clean)

Independent replays already on this host show the physics/ML *implementations* are
sound: solvency BigSolDB leave-solute-out RMSE **0.843–0.877** (inside SOTA band,
beats the Hansen baseline, survives label permutation); Fedors molar-volume vs
measured density **2.4 % median, r = 0.94**; EEW/AHEW coating-chemistry **exact**.
The gap is not the models — it is (a) the governance ceremony above, and (b)
rights-clean data *scale* (need ≥300 molecules; ChEBI-252 CC-BY-4.0 is the named,
not-yet-acquired fix).

## 5. A concrete, fixable science-gap flagged for the deck

`amphora-barrier-corrosion-score` — the most on-thesis module (marine
anti-corrosion) — currently has **no rights-clean benchmark**: its only KPIs score
on **quarantined `polyverse_*` diffusivity** data (Georgia Tech GPUL,
`CONTEXT_ONLY`, `promotion_eligible=false`) — a rights violation, already captured
in the signed `rights-integrity-v1` receipt. Meanwhile a **rights-clean NIST
CORR-DATA** baseline exists (`corr_data_database`, 24,721 records,
`DERIVATIVE_ALLOWED`; 588 marine records fitted in public-corrosion-benchmark). The
honest next science step for barrier-corrosion is to **retract the polyverse KPIs
and re-base on the NIST/EIS rights-clean observables** — real work, not blocked by
governance.

## 6. What this run delivered (new, signed, safe)

`amphora-redteam-audit/benchmarks/phase0-count-integrity-v1/`
- `phase0_count_integrity_audit.py` — deterministic harness (on-disk/on-host facts only)
- `diagnostic.canonical.json` / `diagnostic.runB.json` — **two-replay SHA-256 gate PASS**, canonical `fa02375b…`
- `replay_receipt.v1.dsse.json` — DSSE Ed25519, key `local-9028773f…` (LOCAL_DEVELOPMENT_AUDIT_ONLY, **not** trust-anchored), **SIGNATURE_VERIFY = PASS**

Modifies none of the 66 signed receipts; manifest still 66; promotes/demotes/re-signs
nothing; emits no secret key material. xbabe1 tree untouched.

## 7. Honest one-liners for the founder report

- "**9 Phase-0 modules, all infrastructure/trust-kernel** — not 16. Seven of the
  claimed sixteen would fail re-verification today due to post-signing benchmark
  drift (fixable by re-running the ceremony)."
- "**Zero science modules are at Phase-0.** The blocker is a governance signing
  ceremony (keys are present and valid, verified this run) plus rights-clean data
  scale — **not** broken science: the solvency/EEW/molar-volume physics passes
  signed, replayable, out-of-sample validation."
- "Report the receipt headline as **58 rights-clean-scored + 8 context-only-scored**,
  not a flat 66."
