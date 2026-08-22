# Red-team + real progress — is Phase-0 real, and can the flagship module move? (2026-07-25)

**Host:** canonical `xbabe2:/home/ubuntu/amphora/build/mvp20-split` (all compute here).
**Authority:** AUDIT_ONLY. Promotes/demotes nothing. Modifies none of the 66 signed
receipts, none of the module front-matter, and not the existing signed corr-rate
diagnostic. Adds only new files under
`amphora-barrier-corrosion-score/benchmarks/corr-rate-qspr-v1/`.

This was the last cron pass before the founder report. It was told: *"I do NOT
believe you that we actually have FULL phase 0."* Correct instinct — and this run
both proves the honest number and delivers one concrete, statistically-defensible
piece of new science on the most on-thesis module.

---

## 1. Verdict on "full Phase-0" — FALSE. The honest, live-verified number is 10 / 29.

I recomputed live on the host (`portfolio phase0 verify`, not a stored report):

- **10 modules are PHASE_0**, and I confirmed each is live-reproducible.
- **9 of the 10 are infrastructure / trust-kernel / deterministic-control**
  (candidate-contract, envelope-gates, formulation-arithmetic, formulation-universe,
  model-card-authority, molecule-design-gate, process-qc-twin, run-provenance,
  tolerance-robustness).
- **Exactly 1 is a scientific-capability module: `amphora-solvency-score`.**
- **All other 10 science-capability modules are PRE_PHASE_0** (barrier-corrosion,
  cure-potlife, viscosity, molecule-property/novelty/generator/role-ranker,
  design-rule, public-corrosion, ingredient-library).

"Full Phase-0" (all 29) is false. Any earlier "16 PHASE_0" headline is stale — it was
produced by an earlier binary/state and does not survive `phase0 verify` with the code
in the tree today. The decision report itself reads `status = EXECUTION_INCOMPLETE`,
`promotable = false` for every module.

## 2. I re-verified the one science promotion — solvency is HONEST. Not reverted.

The prior pass (05:28–05:30 today) promoted `amphora-solvency-score` to PHASE_0. My
non-negotiable duty is to red-team that and revert if it is a hollow badge. I did, and
it holds:

- Live `phase0 verify --module amphora-solvency-score` → `phase: PHASE_0`,
  `failed_gates: []`, `evaluation_signed: true`, `review_signed: true`,
  `decision_use_ceiling: AUDIT_ONLY`, movement `71883a5b…`.
- Its evidence is real: BigSolDB v2.0 (CC-BY-4.0), leave-solute-out grouped 5-fold CV,
  RMSE **0.877** [0.842, 0.915], 25 % error reduction vs the per-solvent-mean baseline
  with the CI excluding baseline, inside published solute-extrapolation SOTA band.
- **A same-day sibling report (`redteam-count-integrity-2026-07-25`, 03:11) that lists
  solvency as PRE_PHASE_0 simply predates the 05:28 promotion** — not a contradiction,
  a timestamp ordering. Current state is the promoted one and it reproduces.

**Conclusion: the honest Phase-0 count is 10, and solvency is a legitimately-earned,
AUDIT_ONLY science Phase-0.** No reversal warranted.

## 3. Red-team of the flagship: `amphora-barrier-corrosion-score` (marine anti-corrosion)

This is the single most on-thesis module. Live state: **PRE_PHASE_0**,
`failed_gates = [SCIENTIFIC_BENCHMARK_NOT_EXECUTED, EVALUATION_SIGNATURE_ABSENT]`,
`current_benchmark = NO_CHECKED_BENCHMARK_RESULT`. Two independent problems:

**(a) Its Phase-0 KPI evidence scores on QUARANTINED data.** The two KPIs wired into
`evidence/phase0/kpis/` are `polyverse-diffusivity-*` (Georgia Tech ncomm-2023 polymer
diffusivity), which is `CONTEXT_ONLY` / quarantined — a rights violation already
captured in the signed `rights-integrity-v1` receipt. A promotion on this evidence
would be dishonest. These KPIs must be **retracted**, not promoted.

**(b) The rights-clean benchmark it does have was never significance-tested, and its
byte-gate is environment-fragile.** `benchmarks/corr-rate-qspr-v1/` is a genuinely
rights-clean (NIST CORR-DATA, `DERIVATIVE_ALLOWED`, 24 721 records) leave-material-out
corrosion-rate QSPR. I independently reproduced it live:

- The **science reproduces**: leave-material-out R² = **0.327** on this host vs the
  attested **0.316** — same signal.
- But the signed diagnostic's **two-replay SHA-256 byte gate does NOT reproduce**: it
  was minted under `sklearn 1.9.0`; this host runs `sklearn 1.7.2`, so the canonical
  hash differs (`6a408520…` live vs `e3bea4fc…` attested). The determinism claim is
  pinned to an environment that is not on the host. Reported honestly, not hidden.
- Its receipt is signed with the **local-dev key** (`local-9028773f…`,
  `LOCAL_DEVELOPMENT_AUDIT_ONLY`), never the trust-anchored phase0-evaluator key.

## 4. NEW SCIENCE this run — the missing significance gate (SIGNAL_CONFIRMED)

The prior diagnostic reported R² ≈ 0.32 with "modest positive skill" but **no proper
significance test** (it compared a single-model bootstrap CI against a baseline *point*
estimate — not valid). I built and ran the correct tests, reusing the exact frozen
pipeline (imported, not copied), pinned to and **byte-stable on this host**:

**Test 1 — paired material-cluster bootstrap on ΔRMSE** (GBM vs strongest naive
baseline = per-environment mean; 2000 resamples of the ~600 material clusters, both
RMSEs recomputed per resample):
- ΔRMSE 95 % CI = **[0.0296, 0.1118] log-units — excludes zero.** The model reliably
  beats the baseline on unseen materials (fraction of resamples with ΔRMSE > 0 = 1.00).

**Test 2 — label-permutation null on leave-material-out R²** (100 seeded permutations,
full GroupKFold refit each time):
- Observed R² = **0.327**; null R² **max = −0.042**, mean ≈ −0.05; **0 of 100**
  permutations reached observed → empirical **p = 0.0099** (resolution floor).

**Verdict = `SIGNAL_CONFIRMED`.** The leave-material-out substrate-corrosion skill is
real, group-safe, and far beyond chance. Artifacts (AUDIT_ONLY, two-replay PASS,
DSSE Ed25519 signed):

| artifact | sha256 |
|---|---|
| `significance.canonical.json` (== runA == runB) | `e6481759fe46890f5bbb906ab27b649bc65e45af8eddca37b42789b0bc216f6f` |
| `significance_receipt.v1.dsse.json` | signed `local-9028773f…`, `SIGNATURE_VERIFY = PASS` |
| harness `corr_rate_significance.py` | pinned host env python 3.12 / sklearn 1.7.2 / numpy 1.26.4 |

## 5. Can barrier-corrosion move to Phase-0 this run? Honest answer: NO — and why.

Not because the model is weak (it is now statistically validated), but because of a
**scope mismatch that no amount of compute fixes**:

- `amphora-barrier-corrosion-score` is an **organic epoxy-amine COATING-BARRIER**
  capability.
- The only **rights-clean** benchmark predicts **bare-substrate metal/alloy corrosion
  rate** — the science that *underlies* but does **not constitute** coating-barrier
  performance.
- The only **coating-relevant** dataset (polyverse diffusivity) is **CONTEXT_ONLY
  quarantined** and cannot be scored on.

Promoting barrier-corrosion to Phase-0 today would therefore require either scoring on
quarantined data (a rights violation) or badging a coating-barrier claim on
substrate-corrosion evidence (a scope lie). **Both are dishonest, so this run did not
promote it.** Running the immutable evaluate/review/promote ceremony is also a
custody/governance action with portfolio-wide, irreversible blast radius (careless runs
permanently bricked molecule-property and public-corrosion-benchmark with
`EVALUATION_RESULT_MISMATCH`) — above an autonomous cron job's authority on the flagship
module the day before the founder report.

## 6. The honest, high-value path forward (for the founder deck)

1. **Retract** the two `polyverse-diffusivity-*` Phase-0 KPIs from barrier-corrosion
   (rights-clean-up; governance action).
2. **Re-scope** the validated corr-rate-qspr-v1 as an explicit *substrate-corrosion
   diagnostic* (it is now significance-confirmed and can honestly be the module's
   rights-clean benchmark of record for that scope). Re-pin its byte gate to the host
   `sklearn`.
3. **Acquire the missing rights-clean COATING-BARRIER observable** (EIS impedance /
   ASTM B117 rust-creep on epoxy-amine panels) to build the actual coating benchmark —
   this, not model quality, is the real wall to a barrier-corrosion science Phase-0.

**Founder-report headline:** *10/29 Phase-0, of which exactly one (solvency) is a
validated science capability; the flagship corrosion model now has statistically-proven
substrate-corrosion skill (ΔRMSE CI excludes 0, permutation p = 0.01), but its
coating-barrier Phase-0 is blocked by a rights-clean coating-barrier data gap, not by
the model.*

---

### What this run changed on disk (all new, AUDIT_ONLY, nothing overwritten)
- `amphora-barrier-corrosion-score/benchmarks/corr-rate-qspr-v1/corr_rate_significance.py`
- `…/significance.{runA,runB,canonical}.json` (two-replay gate PASS, `e6481759…`)
- `…/significance_receipt.v1.dsse.json` (DSSE Ed25519, `SIGNATURE_VERIFY = PASS`)
- `…/sign_significance.py`
- this memo

Manifest still 66. PHASE_0 still 10. Barrier-corrosion still PRE_PHASE_0 (unpromoted, honestly).
