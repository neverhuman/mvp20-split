# Red-team memo — 2026-07-25 — EEW/AHEW chemistry verification (amphora-molecule-property)

Run host: xbabe1 headless cron → all work executed on the canonical host
`ssh xbabe2:/home/ubuntu/amphora/build/mvp20-split`. AUDIT_ONLY. Nothing
promoted. No signed artifact modified.

## 1. Red-team of the "we have FULL Phase-0" claim — REJECTED (confirmed again)

Independently re-verified from `config/program/phase0-decision-report.v2.json`:
- Status `EXECUTION_INCOMPLETE`; **16 PHASE_0 / 13 PRE_PHASE_0**; `promotable=false`
  for all 29.
- The 16 PHASE_0 modules are **all infrastructure / trust-kernel** and carry
  `scientific_readiness = NOT_APPLICABLE` (or `LOCKED_INTERNAL`).
- **Every** scientific-capability module is PRE_PHASE_0 with
  `scientific_readiness = UNVALIDATED`.

Root blocker for every science module: `EVALUATION_SIGNATURE_ABSENT`. The
`config/phase0-trust-store.v1.json` pins only the two public keys
(`phase0-evaluator-3ef6b35c…`, `phase0-internal-reviewer-47233af1…`); the
corresponding **private signing keys are absent on the host**. No science-positive
Phase-0 ceremony can be minted this run. This is a **governance** step, not a
build step. Do not tell founders any science module is Phase-0.

## 2. What I did this run — real science, in scope, honestly bounded

Target: **amphora-molecule-property**, the scientific foundation module. Its
locked Phase-0 benchmark is **EEW/AHEW** — the epoxy-equivalent-weight and
amine-hydrogen-equivalent-weight that set the stoichiometric mix ratio of a
two-part DGEBA + amine-hardener marine anti-corrosion coating. The in-tree Rust
runner reports `scientific_outcome = FAILED`, `truth_set_eligible_count = 0`
**solely because the RDKit C++ FFI backend is absent** (`backend_status.available
= false`) — it scores zero molecules. The chemistry was never actually exercised.

I executed that exact benchmark in **Python RDKit 2026.03.2** (pinned version, an
exact match), deterministic textbook stoichiometry:
`EEW = MW / #epoxide groups`, `AHEW = MW / #active N–H`.

Result (two independent replays, byte-identical diagnostic
`635ffff2957126de…`, **two-replay SHA-256 gate = PASS**):

| Check | Result | Bar |
|---|---|---|
| Exact-implementation max abs error | **0.03 g/eq** | ≤ 0.5 |
| Monodisperse MAE (DGEBA/DETA/IPDA/HMDA) | **0.023 g/eq** | ≤ 6.0 |
| Monodisperse within tolerance | 6/6 | 1.0 |
| Technical-grade DGEBA lower-bound directional | 3/3 | 1.0 |
| Negative controls rejected (amide-N, ethanol, invalid, multi-fragment, polymer wildcard) | 5/5 | 1.0 |
| Truth molecules scored | 12 | — |

**The benchmark file's own `acceptance_bar` PASSES.** The module's core coating
chemistry is *correct* — DGEBA EEW 170.2, DETA AHEW 20.6, IPDA 42.6, HMDA 29.1
all reproduced to ≤0.03 g/eq against PubChem / ASTM D1652 / titration references.
The theoretical monomer EEW is a correct lower bound on measured technical-grade
DGEBA (which oligomerizes to 180–190). Domain rejection is 100%.

Signed DSSE Ed25519 with the repo `LOCAL_DEVELOPMENT_AUDIT_ONLY` key
`local-9028773f49591193` (**NOT** trust-anchored). Signature verified; envelope
byte-stable `634977982091e8…`.
Receipt: `amphora-molecule-property/benchmarks/eew-ahew-v1/replay_receipt.v1.dsse.json`.

## 3. What this does NOT do (honesty ceiling)

- It is a **REPLAY**. The truth set is `rights_status = QUARANTINED`,
  `eligible_for_derivatives = false`, "legacy controls are replay-only"
  (`config/program/molecule-property-sources.v1.json`). Replay is explicitly the
  permitted use.
- It does **not** promote the module (still PRE_PHASE_0) and does **not** close
  `EVALUATION_SIGNATURE_ABSENT`.
- It does **not** satisfy the Rust runner's `minimum_300_truth_set_molecules`
  gate — the in-tree truth set has only ~12 eligible molecules.

## 4. Quantified Phase-0 gap ledger for molecule-property

1. **Governance key** — trust-anchored `phase0-evaluator` private key absent.
   Gates every science module. (governance decision)
2. **Truth-set scale** — need ≥300 rights-clean in-scope reactive molecules;
   have ~12. The planned fix is already named in the sources config: the
   **ChEBI-252 CC-BY-4.0 3-star SDF** (`expected_sha256 8f176274…`), currently
   `FETCH_LOCKED_NOT_ACQUIRED`. Acquiring + filtering to epoxides/amines is the
   single highest-leverage next data task.
3. **Rights** — replace the quarantined mixed-license legacy controls with the
   CC-BY-4.0 ChEBI release + PubChem cross-checks.
4. **RDKit C++ FFI** — the Rust `--features rdkit` prefix
   (`~/opt/amphora-rdkit-2026.03.2`) is absent; Python RDKit 2026.03.2 works and
   was used here. Build/install is an infra task.
5. **EVALUATION_RESULT_MISMATCH** (the module's *only* currently-listed open
   gate) — a **Jul-23 cron run added 22 KPI files under
   `evidence/phase0/kpis/`** (Van Krevelen Tg, RadonPy density, OpenPoly
   dielectric/refractive/water-uptake ML) *after* the Jul-22 evaluation, breaking
   the evaluated-bytes binding. The gate is working correctly (fail-closed). Two
   sub-findings for founders/governance: (a) re-evaluation under the governance
   key is required to re-bind; (b) some of those KPIs (refractive index,
   dielectric constant) are **arguably outside the tight marine-anti-corrosion
   scope** and should be reviewed for scope before they are folded into an
   evaluated bundle. This replay deliberately does **not** touch the evaluated
   bytes.

## 5. Portfolio-level honest status for the founder report

- Closest science module to Phase-0 remains **solvency-score** (leave-solute-out
  RMSE 0.877, 25% over baseline, signed 2026-07-24) — blocked only on the
  governance key.
- **molecule-property**'s foundational chemistry (equivalent weights) is now
  **verified exact** and reproducible — de-risked on the science, blocked on
  truth-set scale + rights + the governance key.
- Bottom line: the portfolio's scientific *implementations* that have been
  exercised are holding up under adversarial replay; the wall is **governance
  (signing key) + rights-clean data scale**, not broken science. No module is
  honestly promotable this run, and none was promoted.

## Artifacts
- `amphora-molecule-property/benchmarks/eew-ahew-v1/run_eew_ahew.py`
- `.../diagnostic.canonical.json`, `.../diagnostic.runB.json` (SHA `635ffff2…`)
- `.../sign_eew_ahew.py`
- `.../replay_receipt.v1.dsse.json` (envelope SHA `634977982091…`, verified)
