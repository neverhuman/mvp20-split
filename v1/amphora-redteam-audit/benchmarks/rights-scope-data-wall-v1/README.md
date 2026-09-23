# Red-team memo — 2026-07-25 — The rights-clean ⊗ in-scope data wall (amphora coating IP)

Run host: xbabe1 headless cron → **all** work executed on the canonical host
`ssh xbabe2:/home/ubuntu/amphora/build/mvp20-split`. **AUDIT_ONLY. Nothing promoted.
No existing signed receipt modified.** Signed with the repo `LOCAL_DEVELOPMENT_AUDIT_ONLY`
key (`local-9028773f…`), explicitly **not** a trust-anchored Phase-0 key.

Artifacts (this run):
- Harness `amphora-redteam-audit/benchmarks/rights-scope-data-wall-v1/rights_scope_data_wall_audit.py`
- Canonical diagnostic (two-replay, byte-identical) sha256 **`c43d8d9e…`**
- DSSE receipt `…/replay_receipt.v1.dsse.json` — signature **verified valid**, body sha256 `67b5cf56…`

## 1. The "FULL Phase-0" claim is FALSE — quantified, reproducibly

Live verifier (`amphora-tui portfolio phase0 status --all`) and the on-disk decision
report agree: **`phase0_count = 10`, `pre_phase0_count = 19`.** Of the 10 Phase-0 modules:

| scientific_readiness | count | what it means | modules |
|---|---|---|---|
| `NOT_APPLICABLE` | **7** | deterministic infrastructure / trust-kernel; no scientific claim | candidate-contract, envelope-gates, formulation-arithmetic, formulation-universe, model-card-authority, molecule-design-gate, run-provenance |
| `LOCKED_INTERNAL` | **3** | validated against an internal / retrospective benchmark only | solvency-score, process-qc-twin, tolerance-robustness |

**Only ONE module carries a scientific benchmark whose `scientific_outcome == PASSED`:
`amphora-solvency-score`** (BigSolDB leave-solute-out solubility, RMSE 0.877, AUDIT_ONLY).
The other two `LOCKED_INTERNAL` modules are governance/known-answer locks — e.g.
`process-qc-twin`'s own `benchmark/result.v1.json` has `scientific_outcome = FAILED`; its
Phase-0 KPI is an *authority-lock-preservation* check (1.0) on 10 self-authored synthetic
SPC universes, not a validated predictive model.

**Bottom line for founders: 10 Phase-0 = 9 governance/infra + 1 genuine (retrospective,
public, AUDIT_ONLY) science module. There is no validated *prospective, owned, in-scope
coating* science at Phase-0.** This matches the 09:14 scientific-readiness-honesty audit.

## 2. Why no NEW science module can be honestly promoted this run — a STRUCTURAL DATA WALL

New machine-checked contribution this run: a join over all **26** in-tree feedback data
objects of *(is it rights-clean?)* × *(is it an in-scope experimental coating property?)*.

- **20 / 26 are rights-clean** (`rights_class = DERIVATIVE_ALLOWED`, i.e. usable to back a
  Phase-0 KPI) — but every one is **out of coating scope**: RadonPy polyimide MD *simulation*;
  OMG / OpenPoly / PI1M *generic-polymer / computed*; UCI **SECOM semiconductor** + APROL
  process-automation + Pronto process archives; ChEBI reference structures; and BigSolDB
  solubility/density (*already* the basis of solvency).
- **The 5 directly in-scope coating polymer-physics datasets are ALL `CONTEXT_ONLY`-quarantined**
  and cannot legally back a KPI: `polyverse_melt_viscosity`, `polyverse_cohesive_energy`
  (Hansen/CED), `polyverse_thermoset_mechanics` (epoxy-amine network), `polyverse_sorption`,
  `polyverse_diffusivity` (barrier).
- **`n_rights_clean_AND_in_scope_coating_property = 0`.** The intersection is empty.

Corollary proof: the one rights-clean set that *looks* like corrosion, `corr_data_database`
(24,721 rows), is **bare-metal chemical-compatibility** corrosion (e.g. "Magnesium in
Acetaldehyde → D (Poor)"); only **37 / 24,721 rows (0.15%)** mention any coating term. It
is substrate data, not marine-coating barrier performance — so `barrier-corrosion-score`
cannot honestly claim a coating Phase-0 from it either.

**The wall is DATA RIGHTS, not science.** The physics is in hand (Arrhenius pot-life,
Van Krevelen Tg, Hansen/Fedors, EEW/AHEW stoichiometry all reproduce); the in-scope
experimental data to validate it against is either quarantined or absent.

## 3. The 19 PRE_PHASE_0 modules — blocker taxonomy (from live `failed_gates`)

| class | n | blocker | modules | unblock |
|---|---|---|---|---|
| **A** | 9 | `EVALUATION_RESULT_MISMATCH` — diagnostic bytes drifted after signing (overwrite on 2026-07-22) | cro-protocol-packager, evidence-intake-validator, known-answer-benchmarks, optimizer-orchestrator, report-packager, source-ledger, redteam-audit *(infra)*; **molecule-property, public-corrosion-benchmark** *(science)* | re-run evaluate→review ceremony (governance); **do not roll science ones forward** — their benchmarks are polyverse-contaminated / out-of-scope |
| **B** | 6 | `RIGHTS_OR_LICENSE_INCOMPLETE` | **cure-potlife-gate**, viscosity-score, ip-fto-guard, molecule-generator, molecule-role-ranker, sourceability-ehs | acquire rights-clean **in-scope** data (§2) |
| **C** | 4 | `SCIENTIFIC_BENCHMARK_NOT_EXECUTED` + `EVALUATION_SIGNATURE_ABSENT` | barrier-corrosion-score, design-rule-score, ingredient-library, molecule-novelty | execute+sign a benchmark on rights-clean in-scope data |

## 4. Highest-value science, and exactly what unblocks it (for the founder ask)

`amphora-cure-potlife-gate` is the closest science module to an honest Phase-0: its
Arrhenius pot-life KPI already reproduces bit-exact and non-circular (`Ea_fit ≈ 0.884×`
cited, MAPE 0.147, all 6 sub-gates pass in the prior signed audit). Its **only** blocker is
`rights_gate_passed = false` with **zero eligible sources** — all pot-life data in-tree is
`CONTEXT_ONLY`/`rights_status=UNRESOLVED`. **One rights-qualified, in-scope epoxy-amine
gel-time-vs-temperature dataset (CC-BY / public-domain) converts it to Phase-0.** That single
acquisition — not more modeling — is the highest-leverage next investment.

## 5. Honest caveats

- This is an AUDIT_ONLY receipt on a local key; it closes **no** gate and promotes nothing.
- The scope classification (§2) is an explicit, auditable table in the harness; reasonable
  people could re-label `polyomics_chi` (solvent χ) or BigSolDB as more/less "in scope" —
  doing so does **not** change the headline (`rights_clean_AND_in_scope = 0`), because the χ
  set is *computed/predicted* and BigSolDB is already spent on solvency.
- Solvency's Phase-0 remains defensible and is **not** reverted: rights clean, benchmark bound,
  signatures valid, honestly caveated as retrospective/public/AUDIT_ONLY.

**Net for this hour: no new module was honestly promotable, and rather than fabricate one,
this run delivers a signed, reproducible map of exactly why (the data wall) and exactly what
unblocks the highest-value module (one rights-clean pot-life dataset).**
