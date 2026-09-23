# Red-team + real-science run — 2026-07-25 (hourly cron, host xbabe1 → xbabe2)

All work executed on the canonical host `ssh xbabe2:/home/ubuntu/amphora/build/mvp20-split`.
No existing signed receipt modified. No front-matter promoted. Master manifest
untouched. xbabe1 mvp20-split tree untouched. Every number below was produced by
executing code on this tree, not by reading a document that asserts it.

## 1. Red-team of "we have FULL Phase-0" — REJECTED (re-confirmed, 4th independent pass)

- `reports/portfolio-status-2026-07-23/data/frontmatter.json`, re-read directly:
  **16 PHASE_0 / 13 PRE_PHASE_0**. Every one of the 16 PHASE_0 modules is
  infrastructure / trust-kernel / gate (candidate-contract, envelope-gates,
  run-provenance, report-packager, redteam-audit, source-ledger,
  formulation-arithmetic, known-answer-benchmarks, process-qc-twin,
  tolerance-robustness, model-card-authority, …). **Every scientific-capability
  module is PRE_PHASE_0**: solvency, barrier-corrosion, cure-potlife, viscosity,
  molecule-property / novelty / role-ranker / generator, design-rule,
  public-corrosion, ingredient-library, sourceability-ehs.
- Root blocker for every science module: **`EVALUATION_SIGNATURE_ABSENT`**. The
  `config/phase0-trust-store.v1.json` pins only the two public keys
  (`phase0-evaluator-3ef6b35c…`, `phase0-internal-reviewer-47233af1…`); the
  corresponding **private signing keys are absent on the host**. No
  science-positive Phase-0 ceremony can be minted this run. This is a
  **governance / key-custody** step, not a build step. **Do not tell founders any
  science module is Phase-0.**
- The "66 signed scientific receipts" headline is signed by
  `toolkit-reviewer-cbe8c0fd…`, a key **absent from the trust store** — those are
  self-attested, not trust-anchored. Prior passes established this; still true.

## 2. Rights red-team finding surfaced this run (important — prevents a violation)

While hunting for the highest-value unused data I found that **all Georgia-Tech
"polyverse" datasets are quarantined `CONTEXT_ONLY`, `promotion_eligible=false`**
under a custom GT Research Corporation license ("Custom license requires
counsel; physically quarantine all derivatives"):

    polyverse_cohesive_energy, polyverse_diffusivity, polyverse_melt_viscosity,
    polyverse_sorption, polyverse_thermoset_mechanics   (+ pi1m_structures)

These carry the CED, thermoset-mechanics, solvent-sorption, diffusivity and
melt-viscosity data — tempting for viscosity/barrier/solvency benchmarks. **They
must NOT be used for any scored benchmark.** The scoring-eligible
(`DERIVATIVE_ALLOWED`) in-scope datasets are BigSolDB v2.0 (CC-BY-4.0), OMG
physical properties (MIT), OpenPoly (MIT), NIST corr-data (public), polyomics
(CC-BY). This run used only the first.

## 3. Real science executed HERE this run (closes a genuine, previously-open gap)

**`amphora-solvency-score/benchmarks/molar-volume-density-v1/`** — first
experimental validation of the module's own molar-volume engine.

**The gap.** Every Hansen/Hildebrand solubility-parameter the solvency module
estimates for an *unmeasured* molecule divides by a group-contribution molar
volume V (`delta_D = sumF_d/V`, `delta_H = sqrt(sumE_h/V)`), computed by
`hsp.hvk_hsp()` using Fedors' 1974 additive volume increments. The module's only
known-answer test (`validate_hvk`) checks the HSP *components* against tabulated
HSP — it **never checked V itself against an experimental observable.** The
denominator of the whole engine was unvalidated.

**The test.** For each coating-relevant solvent, take the module's OWN engine
output V, form `rho_pred = MW / V` (MW from RDKit 2026.03.2), and compare to the
**measured** liquid density at 298.15 K from **BigSolDB v2.0** (Krasnov et al.,
*Sci. Data* 12 (2025), doi:10.1038/s41597-025-05559-8; CC-BY-4.0; in-tree,
`bigsoldb_density-02226420…`). Fedors' increments are fixed 1974 constants, not
fit to BigSolDB → **strict out-of-sample validation of prior theory, zero
train/test leakage.** Fail-closed: scored only if name→in-tree-SMILES maps, the
engine returns V (it abstains on water/formamide/inorganics), and a density at
298.15 K exists or bracket-interpolates within [283.15, 313.15] K.

**Result** (two independent replays, byte-identical diagnostic
`9847c803c11fdefc…`, **two-replay SHA-256 gate = PASS**):

| KPI | Value | Bar | Pass |
|---|---|---|---|
| Solvents scored | 67 / 69 organic | — | — |
| Coverage of organic candidates | 0.971 | ≥ 0.85 | ✅ |
| Median abs. relative error | **2.38 %** | ≤ 5.0 % | ✅ |
| Mean abs. relative error | **4.40 %** | ≤ 6.0 % | ✅ |
| Density MAE | 0.046 g/cm³ | — | — |
| Pearson r (pred vs exp) | **0.936** | ≥ 0.90 | ✅ |
| **Acceptance bar (all gates)** | **PASS** | | ✅ |

Accuracy is **sub-0.2 %** for aliphatic/aromatic hydrocarbons, esters and ethers
(the bulk of epoxy-coating solvents: heptane −0.04 %, octane −0.05 %, hexane
+0.15 %, n-pentyl acetate +0.17 %). Error rises to 15–33 % **only** for small
strongly-associated polar/halogenated liquids (formic acid +33 %, CCl₄ +26 %,
ethyl formate +20 %, DMSO −18 %, NMP −17 %) — the exact domain where additive
molar-volume group contribution is textbook-documented to be weakest. This
doubles as a **domain-of-validity finding**: callers should treat the engine's V
(hence HSP) for small associated polar species as low-confidence.

Signed DSSE Ed25519 with the repo `LOCAL_DEVELOPMENT_AUDIT_ONLY` key
`local-9028773f49591193` (**NOT** trust-anchored). Signature independently
verified against the public key; envelope byte-stable
`f3e5d38b3d2401f6…`, receipt body `f5fada644b1d4f3e…`.
Receipt: `amphora-solvency-score/benchmarks/molar-volume-density-v1/replay_receipt.v1.dsse.json`.

## 4. Honesty ledger — what this run does and does NOT do

- **Does** give solvency-score its first real experimental validation of the
  molar-volume denominator underlying its HSP engine, out-of-sample, zero
  leakage, on rights-clean CC-BY-4.0 data, with a passing acceptance bar and a
  two-replay determinism gate.
- **Does NOT** promote amphora-solvency-score to Phase-0 (audit-only signature;
  trust-anchored key absent — `EVALUATION_SIGNATURE_ABSENT` stands).
- **Does NOT** validate the polar δ_P/δ_H terms, only V.
- **Does NOT** touch the master receipts manifest. Adding an audit-only receipt
  to the "scientific receipts manifest" would risk exactly the inflation prior
  passes flagged; that consolidation is a governance action.
- **Founder-report line:** "Textbook Fedors/Van-Krevelen theory, as implemented
  in our solvency engine, predicts measured solvent densities to a 2.4 % median
  error (r = 0.94) out-of-sample on CC-BY experimental data — validating the
  physics core. This is signed, replayable evidence, but it is *audit-only*: no
  science module is at trust-anchored Phase-0 until the evaluator signing keys
  are provisioned (a governance step)."
