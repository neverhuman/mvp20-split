# Red-team memo — a-priori Hansen VECTOR for the solvency crown jewel (2026-07-26)

Run: fully-autonomous hourly cron on xbabe1; all work executed on xbabe2 at
`/home/ubuntu/amphora/build/mvp20-split/`. LAST run before the founder report.

## 1. RE-CONFIRMED: "FULL Phase-0" is governance-only, NOT validated science

Live cross-check this run (embedded, reproducibly, in the signed receipt):
- `config/program/phase0-decision-report.v2.json`: phase0_count=10, and **every**
  PHASE_0 module carries `scientific_readiness` ∈ {NOT_APPLICABLE, LOCKED_INTERNAL}.
  **ZERO modules carry `scientific_readiness = VALIDATED`.**
- Every phase0 promotion policy has `scientific_success_required = false` and ZERO
  target `scientific_readiness = VALIDATED` (ceiling is LOCKED_INTERNAL).
- Exactly ONE module (amphora-solvency-score) has any EXTERNAL-data predictive
  validation (BigSolDB leave-solute-out).

**The founder's skepticism is correct.** PHASE_0 = a reproducibility + rights +
independence GOVERNANCE lock. It is not a count of validated coating science.

## 2. Highest-value gap studied → the crown-jewel solvency module

Red-team of the module landscape:
- **viscosity-score** (PRE_PHASE_0): its Arrhenius benchmark is ALREADY executed,
  two-replay, all 7 gates pass (held-out MAPE 0.0049, lift 0.64) on a rights-clean
  CC0 truth set. But (a) it uses each solvent's own measured η_ref so it is **not a
  non-circular structural predictor**, and (b) its only blocker to PHASE_0 is
  governance signatures — which I must not forge. I tested the one honest way to add
  non-circular structure→viscosity science (Eyring E_vis ≈ c·ΔHvap, tying to the
  anchored Joback ΔHvap): **REFUTED** — E_vis vs ΔHvap298 gives R²≈0.0002, ratio CV
  22% (cyclohexane a clear outlier). No trustable new viscosity model exists to add,
  so I did not fabricate one.
- **solvency-score** (crown jewel): the ONE externally-validated module. It selects
  solvents in Hansen space via the RED number. The prior Fedors cohesive-energy audit
  validated only the SCALAR δ (0.9%) and the δd component (3.2%) — it NEVER surfaced
  δp, δh, or the operational Hansen VECTOR DISTANCE Ra the module actually consumes.
  A scalar δ cannot tell an alcohol from an ester of equal δ. **That is the real gap.**

## 3. Delivered: signed a-priori Hansen-VECTOR audit (AUDIT_ONLY)

`amphora-redteam-audit/benchmarks/hvk-hansen-vector-ccby-v1/`

- **Theory (real, cited, non-circular):** Hoftyzer–Van Krevelen partial parameters
  δd=ΣF_di/V, δp=√(ΣF_pi²)/V, δh=√(ΣE_hi/V), V=M/ρ (Van Krevelen, *Properties of
  Polymers* ch.7; Hansen Handbook 2007). Group constants are universal literature
  values, **NOT re-fit**. Ground truth: Hansen 2007 canonical (δd,δp,δh) triples.
- **Data:** 19 in-scope coating solvents (17 CORE polar/H-bonding/aliphatic + 2
  bare-aromatic/conjugated BOUNDARY). Rights-clean tabulated physical facts.
- **KPIs (CORE):** per-component RMSE δd 0.47, δp 0.35, δh 1.42 MPa^½; Hansen vector
  distance Ra median 1.19, mean 1.45, max 3.71 (o-xylene), **17/17 within Ra≤5** — far
  inside a typical epoxy/DGEBA interaction radius R0≈8–13, so a-priori placement
  preserves the solvent-selection decision; **79% lift** over a mean-vector null.
  Operational solvent-selection geometry: mean distance-rank Spearman **0.87**,
  nearest-replacement-solvent match **15/17**.
- **Verdict:** VALIDATED_IN_DOMAIN (AUDIT_ONLY). Extends the crown jewel to NOVEL
  solvents with no measured Hansen parameters — a capability BigSolDB validation did
  not cover.
- **Honest boundary:** first-order HvK has no π-cohesion group → benzene/styrene get
  δh=0 / low aromatic δd (declared BOUNDARY, reported not hidden).

## 4. Red-team side-finding (logged, NOT silently rolled forward)

The new RDKit heavy-atom (C,O,Cl) **formula guard** caught a latent bug in the shared
oxygen classifier used by the already-signed **Fedors cohesive-energy audit**: an
ester's single-bonded oxygen is double-counted as BOTH a COO_ester and an O_ether when
RDKit lists it before the carbonyl O (e.g. ethyl acetate), inflating ester δh (10.1 vs
lit 7.2). This audit CORRECTS it with a two-pass classifier (carbonyl first). Impact on
the Fedors audit was minor (its headline scalar δ is δd-dominated, ester total error
stayed ~4%). **The immutable Fedors receipt is left untouched**; the fix lives only in
this new audit and is logged here and in the receipt.

## 5. Governance honesty

- Signed AUDIT_ONLY DSSE Ed25519 (`local-9028773f49591193`, NOT a phase0 key).
- Two-replay SHA-256 gate PASS: `eeb08d4b6db3fd05b66a93f0108962a111238177429653afb9d2418c2cb519e7`.
- Promotes nothing. Manifest unchanged (**66 receipts / 11 modules**). No existing
  receipt modified. Real promotion still requires keyed supersession + human
  PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER review — deliberately NOT done autonomously.
