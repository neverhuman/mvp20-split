# cured-network-density-apriori-refuted-v1 (AUDIT_ONLY)

**Red-team memo — "FULL Phase-0" re-refuted live, AND the obvious next cured-network
axis (a-priori network density) tested and REFUTED with evidence. Promotes nothing.
Manifest stays 66/11. Signed LOCAL_DEVELOPMENT_AUDIT_ONLY `local-9028773f…`.**

Date: 2026-07-26 (final cron before founder report) · Host: canonical `xbabe2:/home/ubuntu/amphora/build/mvp20-split`

---

## 1. Verdict on "do we have FULL Phase 0" — NO (re-verified LIVE this run)
- `module-manifest.json` → **all 29 modules `scientific_readiness = UNVALIDATED`** (0 VALIDATED).
- `config/program/phase0-decision-report.v2.json` → `status = EXECUTION_INCOMPLETE`,
  `promotable = false` for every module; `phase0_count` is a **governance** label
  (its PHASE_0 modules are `NOT_APPLICABLE` infra or `LOCKED_INTERNAL`, never VALIDATED).
- **The founder's skepticism is correct.** "FULL Phase-0" = an engineering/governance
  milestone, not validated science.

## 2. Highest-value gap studied this run
Solvent-property suite is complete; cure-kinetics (Kissinger) is validated-in-domain.
The frontier is **cured-network bulk properties**. Tg point-prediction is stuck on data
scarcity (n=7, 3 prior attempts → ADVANCED_NOT_VALIDATED). The un-attempted axis with the
most robust theory + highest barrier relevance is **cured-network mass density** (free
volume → water/O₂ permeability → the anti-corrosion barrier function).

## 3. What was built — a-priori network density predictor (non-circular)
Reuses the portfolio's **own density-validated** Fedors/Van-Krevelen molar-volume engine
(`amphora-solvency-score/.../hsp.py`, validated vs BigSolDB solvent densities) applied to
the **fully-reacted stoichiometric network unit**: epoxy + N-H → β-hydroxyamine (atoms
conserved), ρ = M_unit / V_unit. Reaction-delta bookkeeping verified **EXACT** vs direct
RDKit decomposition for both primary→secondary (333.8) and primary→tertiary (255.5).

## 4. Result — REFUTED (three independent causes)
| system | ρ_pred (naive) | ρ_measured (rights-clean CC-BY) | error |
|---|---|---|---|
| DGEBA + IPDA | 1.332 | **1.105** (10.3390/polym13081348, CC-BY-4.0) | **+20.5 %** |

1. **Additive engine over-predicts clustered H-bonded polyols/aminoalcohols** — glycerol
   **+19.3 %**, triethanolamine **+12.9 %**, diethanolamine +7.8 % — and the cured network
   IS a poly-β-hydroxyamine (worst case).
2. **Reaction-differenced additive V overshoots real cure shrinkage ~3×** (modeled 13.0 %
   vs physical 2–6 %).
3. **A motif correction calibrated NON-CIRCULARLY** on 10 independent aminoalcohol/polyol
   CRC densities (c = 2.634 cm³/motif, cal RMS 3.5 %) **FAILS to transfer** to the network
   (residual +17.6 %) — diluted in the large aromatic/ether repeat unit.

All 7 pre-registered gates PASS (they certify the refutation + its diagnostics).
Two-replay SHA-256 gate = PASS (canonical == runB = `9ff17c8b…`); DSSE Ed25519
SIGNATURE_VERIFY = PASS.

## 5. Data-rights wall — re-confirmed this run, for density specifically
Only **one** rights-clean CC-BY-4.0 measured DGEBA+amine cured density is in reach
(IPDA 1.105). The richer multi-amine experimental set (DETA 1.178 / IPDA 1.135 / MXDA
1.185, ACS Omega `10.1021/acsomega.2c03071`) is **CC-BY-NC-ND** → **REJECTED on rights**,
carried only as non-scored corroboration. Same wall the prior crons documented.

## 6. Honest forward path (founder-actionable)
- The refutation kills the **naive additive-volume** route only. Next candidate: a proper
  amorphous-network method (Van Krevelen V = V_w × 1.6, or Bicerano network correlation with
  an explicit crosslink-densification term).
- To VALIDATE any cured-network density predictor to a PHASE_0 standard needs **≥4 rights-
  clean CC-BY-4.0 DGEBA+amine cured densities** across aliphatic/cycloaliphatic/aromatic amine
  classes (only 1 in reach). Acquiring them via `amphora-source-ledger` is the blocker — a
  data-acquisition decision, not a science gap.

## 7. What this deliberately does NOT do
Promotes no module; changes no `scientific_readiness`; adds no PHASE_0 module; modifies none
of the 66 signed receipts or the manifest (66/11); scores on no rights-restricted datum;
performs no trust-anchored phase0 signing. It records a **negative result** so a future run
cannot mistake this predictor for progress.

## Files
- `cured_density_audit.py` — deterministic harness (self-contained, reuses `hsp.py`).
- `diagnostic.canonical.json` / `diagnostic.runB.json` — byte-identical (`9ff17c8b…`).
- `sign_cured_density.py` / `replay_receipt.v1.dsse.json` — DSSE Ed25519 signed receipt.
