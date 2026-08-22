# Red-team + real-science progress — cure-potlife external-Ea corroboration (2026-07-25)

**Author:** hourly red-team cron (xbabe1 headless → **all work on canonical host
xbabe2**, `/home/ubuntu/amphora/build/mvp20-split`).
**Authority:** AUDIT_ONLY. Promotes nothing. No existing receipt or manifest changed
(manifest still **66 receipts / 11 modules**; live `phase0_count` still **10**). Signed
with the repo `LOCAL_DEVELOPMENT_AUDIT_ONLY` key `local-9028773f…` — explicitly **NOT**
a trust-anchored Phase-0 key.

Artifacts (this run), all under
`amphora-redteam-audit/benchmarks/cure-potlife-external-ea-corroboration-v1/`:
- Harness `cure_potlife_external_ea_audit.py`
- Canonical diagnostic (two-replay, byte-identical) sha256 **`db706ae2…`**
- DSSE Ed25519 receipt `replay_receipt.v1.dsse.json` — **signature verified VALID**,
  body sha256 `b2d5a8fc…`, envelope `c63045ea…`

---

## 1. Red-team of "we have FULL Phase-0" — the skepticism is CORRECT (re-confirmed live)

Live verifier (`amphora-tui portfolio phase0 status --all`) this run:
**`phase0_count = 10`, `pre_phase0_count = 19`.** Breaking down the 10:

| scientific_readiness | count | what it is |
|---|---|---|
| `NOT_APPLICABLE` | **7** | deterministic infrastructure / trust-kernel (candidate-contract, envelope-gates, formulation-arithmetic, formulation-universe, model-card-authority, molecule-design-gate, run-provenance) |
| `LOCKED_INTERNAL` | **3** | internal/retrospective benchmark only (process-qc-twin, tolerance-robustness, **solvency-score**) |

**Exactly ONE** of the ten carries an external science benchmark with
`scientific_outcome == PASSED`: **amphora-solvency-score** (BigSolDB leave-solute-out,
RMSE 0.877, AUDIT_ONLY). "FULL Phase-0" and the stale **"16"** are both false;
**10 Phase-0 = 9 governance/infra + 1 genuine (retrospective, public) science module.**
There is still **no validated prospective, owned, in-scope coating science at Phase-0.**

The one in-scope, public-domain coating dataset in-tree (USBR ST-19168 EIS) was also
re-checked: it is BOTH an honest scientific **null** (n=10; Pearson r 0.08–0.20;
permutation p 0.58–0.82 → no EIS↔rust-creep signal) AND `rights_status =
ACQUIRED…PENDING_RIGHTS_REVIEW`. Both walls stand.

## 2. Highest-value real work this run — did the external replication the prior runs punted on

Every prior red-team run concluded "cure-potlife is science-ready but rights-blocked"
and stopped. **cure-potlife-gate** is the strongest second science candidate: its
Arrhenius pot-life KPI passes **6/6 gates** (MAPE 0.147; non-circular apparent-Ea proof),
but its `source-lock.v2` has `rights_gate_passed=false` and **`sources=[]`** — a genuine
missing rights-clean dataset, not a ceremony.

This run tested the model's **physics against genuinely independent, rights-separate
literature** — data outside the supplier-TDS lineage that parameterised it. The model
assigns each of 12 DGEBA-amine systems an apparent activation energy Ea (54–56 kJ/mol
aliphatic, 58–62 cycloaliphatic, 58–68 aromatic, 48 Mannich). Result:

| corroboration KPI | observed | note |
|---|---|---|
| union-envelope containment (Ea ∈ independent lit range 48.6–76.8) | **11/12 (0.917)** | 1 miss: Mannich 48.0, **0.64 kJ/mol** under min — reported, not tuned away |
| **CC-BY rights-clean cycloaliphatic bracket** (model ∈ 57.3–62.8) | **3/3 (1.0)** | anchor = directly-fetched **CC-BY** IPDA dataset (PMC6473346) |
| amine-family reactivity ordering (cycloaliphatic ≤ aromatic) | **holds** | consistent with amine nucleophilicity |

**Graded verdict: CORROBORATED.** The model's activation-energy physics is
independently supported by the open literature, including a genuinely **CC-BY**
DGEBA-cycloaliphatic-amine cure-kinetics dataset that this run fetched and read.
(Honest physics: peak-exotherm Kissinger Ea, e.g. TETA 76.8, exceeds the model's
apparent pot-life Ea — expected, since gel/pot-life Ea < whole-reaction Ea.)

## 3. The one finding that changes the founder narrative

The prior "wall" memo proved `rights_clean ∩ in-scope = 0` **over the 26 in-tree
datasets**. That is true — but this run shows it does **NOT** hold for the open
literature: a rights-clean **CC-BY** in-scope DGEBA-amine cure-kinetics dataset
**exists and was retrieved** (PMC6473346). So the cure-potlife blocker is a **bounded,
tractable data-acquisition + rights-review task, not an impossibility.** The concrete
unblock:
1. Acquire ≥1 **rights-clean gel-time / pot-life** dataset for DGEBA-amine systems
   (CC-BY open-access, or supplier-TDS facts cleared by counsel as non-copyrightable
   measurements). *This Ea dataset corroborates the temperature-scaling physics but is
   cure-kinetics, not the pot-life labels the KPI scores — so it is a lead, not the
   final dataset.*
2. Register it in `source-lock.v2` with an independent `rights-reviewer` overlay
   (`rights_gate_passed → true`).
3. Run the existing 6/6-passing benchmark; then the two Phase-0 signatures
   (PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER) — a human/governance step this
   AUDIT_ONLY cron holds no key for and must not forge.

## 4. Honest limitations (state to founders)
- This corroborates physical **plausibility** (Ea magnitude + family ordering), **not**
  absolute pot-life accuracy, and is **not** a Phase-0 gate.
- Only the 3 CC-BY IPDA records were directly fetched/verified this run; the other 7
  literature Ea are recorded from published abstracts and labelled SUPPORTING
  (lower-confidence).
- Nothing here promotes any module or asserts any right. The defensible Phase-0 count
  remains **10**.
