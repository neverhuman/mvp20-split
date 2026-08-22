# Red-team + real-science progress — network-Tg feasibility (2026-07-25)

**Author:** hourly red-team cron (xbabe1 → xbabe2, canonical tree only)
**Scope:** coating IP — two-part DGEBA + amine, marine anti-corrosion.
**Authority:** AUDIT_ONLY. Promotes nothing. No existing receipt or manifest
changed (manifest still **66 receipts / 11 modules**). Signed with the
LOCAL_DEVELOPMENT_AUDIT_ONLY key `local-9028773f…` — explicitly NOT a
trust-anchored Phase-0 key.

## 1. Red-team of "we have FULL Phase-0" — the skepticism is CORRECT

Honest, live-verifiable Phase-0 = **10 modules**, not "full", not "16":
- **9 infrastructure / trust-kernel / deterministic-control** modules, **plus**
- **amphora-solvency-score** — the FIRST and (as of this run) ONLY promoted
  SCIENCE module (Hansen/BigSolDB leave-solute-out, signed).

Supporting facts re-confirmed this run on the canonical host:
- `config/program/phase0-decision-report.v2.json` lists exactly 10 modules at
  `phase:"PHASE_0"` (candidate-contract, envelope-gates, formulation-arithmetic,
  formulation-universe, model-card-authority, molecule-design-gate,
  process-qc-twin, run-provenance, solvency-score, tolerance-robustness). Of
  these, only **solvency-score** carries real predictive science; the rest are
  `scientific_readiness: NOT_APPLICABLE` (infra) or `LOCKED_INTERNAL`.
- The stale **"16 PHASE_0"** figure remains non-reproducible (prior runs traced
  it to a 2-record succession chain that the current verifier rejects). **Do NOT
  use "16."**
- **Caveat for the founder pack:** the decision report still stamps
  `DECISION_COMPLETE_EXECUTION_INCOMPLETE` with a null reported count. Regenerate
  it so it prints the true **10** before the pack ships.
- **cure-potlife-gate** remains the strongest SECOND science candidate:
  scientifically Phase-0-ready (6/6 Arrhenius gates pass, signed two-replay), but
  blocked ONLY by the dual-signature governance ceremony (PHASE0_EVALUATOR +
  PHASE0_INTERNAL_REVIEWER). This cron holds only the AUDIT_ONLY key, so it
  cannot and did not perform that ceremony. That is a key-custody/governance
  step, not a science gap — and it must not be forged.

## 2. Where the biggest SCIENCE gap is — and real progress on it

The crown-jewel unvalidated property is **network glass-transition temperature
(Tg)** of cured DGEBA-amine coatings (governs service temperature, barrier, and
durability). This run red-teamed the in-tree Tg capability and did real science.

**Finding — the incumbent Tg approach FAILS (reproduced by citing signed receipts):**
- polyuniverse-trained ML: **MAE 39.1 °C, Pearson r ≈ 0.08** across the 5
  canonical DGEBA-amine systems → *no correlation*
  (`…external_validation_5_canonical…` sha `0aaf262d…`).
- raw Van Krevelen group contribution: **MAE 109.1 °C** (`…van_krevelen_physical…`
  sha `0e1cafe9…`). Linear-polymer group contribution is the **wrong physics**
  for a crosslinked thermoset; and it was scored on CONTEXT_ONLY polyuniverse data.

**Contribution — the CORRECT physics, prototyped, signed, reproducible:**
- Tg of a stoichiometric epoxy-amine network is set by (a) **crosslink density**
  computed **exactly and NON-CIRCULARLY from stoichiometry** (amine-hydrogen
  functionality + DGEBA EEW; ties directly to the already-verified EEW/AHEW
  core — never uses measured Tg), and (b) **backbone segmental rigidity**,
  captured by **ring-atom fraction** (which, unlike aromatic fraction, correctly
  credits IPDA/PACM *cycloaliphatic* rings) and rotatable-bond density.
- On rights-clean cited data the signal is real: **ring-fraction Pearson
  r = +0.69 (n=10)**; a minimal physical model reaches **LOO MAE ~24–29 °C
  (direction-only)** — versus the incumbent 39.1 °C ML and 109.1 °C VK.

**Honest verdict — NOT promoted, and why (no fabricated progress):**
- Rights-clean, consistently-cited experimental Tg is only **n=5, single source**
  (May 1988 Epoxy Resins Ch.6), and inter-lab Tg scatter is **±20–30 °C**
  (e.g. DGEBA/DDS spans 128–220 °C across isomer/ratio/cure). On n=5 a fitted
  model overfits (cited-5 LOO MAE 73.9 °C > constant-mean baseline). **No Tg KPI
  is claimed.** The 5-system representative extension (provenance B) is mid-range
  literature (±15–25 °C) used ONLY to show the physics direction generalizes; it
  is excluded from every gate.
- Status: **PRE_PHASE_0 — CORRECT_PHYSICS_IDENTIFIED, BLOCKED_ON_RIGHTS_CLEAN_DATA.**

## 3. The concrete, honest path to a third science Phase-0

One **rights-clean, cited Tg dataset (≥12 stoichiometric DGEBA-amine systems,
controlled cure schedule, spanning aliphatic/cycloaliphatic/araliphatic/aromatic)**
converts this prototype into a defensible Phase-0 KPI. The physics, the
non-circular descriptor pipeline (tied to verified EEW/AHEW), the incumbent
baselines to beat (39.1 °C / 109.1 °C), and the acceptance gates are all already
specified in the signed diagnostic. This is a data-acquisition task, not a
research risk.

## 4. Signed artifact (this run)

`amphora-redteam-audit/benchmarks/network-tg-feasibility-v1/`
- `network_tg_feasibility_audit.py` — independent Python+RDKit harness
- `diagnostic.canonical.json` == `diagnostic.runB.json`, sha
  `902cf6738f91589e324d49b6634e37007123f1736a4baa91ade2e576d6fc836b`
  (two-replay SHA gate **PASS**)
- `replay_receipt.v1.dsse.json` — DSSE Ed25519, key `local-9028773f…`,
  **SIGNATURE_VALID**, envelope sha
  `346a87c357e819f89e23d319e55c08589c60bd04013d60bbda185087c12d7ba8`

## 5. Recommendation to founders

Present **10 defensible Phase-0** (9 infra + solvency-score). Name **cure-potlife**
as the verified second science candidate awaiting only the dual-signature
ceremony, and **network-Tg** as the third, with the correct physics already
prototyped and signed and a concrete data-acquisition path to Phase-0. Regenerate
the decision report to print the true **10** first. Do NOT present "full Phase-0"
or "16".
