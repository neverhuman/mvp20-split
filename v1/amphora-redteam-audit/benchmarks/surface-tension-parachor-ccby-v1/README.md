# surface-tension-parachor-ccby-v1 (AUDIT_ONLY)

**First rights-clean, a-priori surface-tension predictor validated for the amphora
coating portfolio**, plus a live-verified Phase-0 reconciliation red-team.

## What this is

An independent AUDIT_ONLY red-team science increment. It does **not** promote any
module and signs **no** Phase-0 evaluation/review receipt. Signed with the
`LOCAL_DEVELOPMENT_AUDIT_ONLY` key (`local-9028773f...`), not a trust-anchored
Phase-0 key.

## Science

**Theory (real, cited).** Sugden (1924) / Quayle (1953) **Parachor** additive
group-contribution method (Van Krevelen, *Properties of Polymers*, ch. 8):

    P = (M / (rho_L - rho_V)) * gamma^(1/4)   =>   gamma_pred = ( P_calc * rho / M )^4

`P_calc` is a pure **literature-constant** additive sum over atoms + unsaturation +
ring closures (RDKit-counted from Kekule SMILES). It is **not fitted** to the
validation set -> non-circular by construction. Surface tension `gamma` is the
direct input to the **Owens-Wendt-Kaelble / Young** wetting-and-adhesion equations
that govern coating adhesion to steel -- the primary marine anti-corrosion
requirement.

**Truth set.** 20 pure solvents spanning the chemistries of two-part marine
epoxy-amine thinner packages (aromatics, aliphatics, ketones, esters) + alcohols +
water. `gamma_exp` and `rho` at 20 C are tabulated physical constants
(CRC/NIST/Jasper) -- non-copyrightable facts; compilation is CC0 self-authored.

## Result

| domain | MAPE | within 10% | lift over mean-gamma null |
|---|---|---|---|
| **non-associating** (aromatic/aliphatic/ketone/ester) | **2.80%** | **100%** | **81.7%** |
| associating (alcohol/water) -- out of domain | 14.1% | -- | -- |

Per-family MAPE: aliphatic 1.1%, aromatic 1.9%, ketone 4.6%, ester 5.7%,
alcohol 14.6%, water 12.4%. Graded **VALIDATED_IN_DOMAIN**. The alcohol/water bias
is the *expected, honest* domain boundary -- the additive scheme omits H-bond
association. Reported, not hidden.

## Phase-0 reconciliation red-team (embedded, reproducible)

The harness reads every module's live `docs/mission.md` front-matter and counts
Phase-0 status deterministically:

- **17** modules labelled `PHASE_0` in live front-matter (each with signed
  evaluation + review governance receipts) -- **not 10**, correcting prior memos.
- Of these: **13** `NOT_APPLICABLE` (governance/infra) + **4** `LOCKED_INTERNAL`
  (internal known-answer only).
- **Exactly 1** (`amphora-solvency-score`) has **external-data** scientific
  validation (BigSolDB leave-solute-out) behind its Phase-0.

"FULL Phase-0" is an engineering/governance milestone, **never** a count of
validated scientific capabilities.

## Reproduce

    cd /home/ubuntu/amphora/build/mvp20-split
    python3 amphora-redteam-audit/benchmarks/surface-tension-parachor-ccby-v1/surface_tension_parachor_audit.py
    # -> diagnostic.out.json ; sha256 == 2f019f87106fc7bb8e29d021f27b99ee579a7d358a508fa27592dba3dead7a46

Two-replay SHA-256 gate = **PASS** (byte-identical across two runs). Signature
verifies against `.amphora/control/local-ed25519.pub.json`.

## What it does NOT do

- Does not promote any module to PHASE_0; adds no PHASE_0 module.
- Does not modify any of the 66 signed receipts or the manifest.
- Does not claim crosslinked-film surface energy or the polar/dispersive split
  (Phase-1 extensions requiring two-liquid contact-angle regression).
- Does not perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing.
