# Red-team memo — "full Phase 0" is false; new rights-clean *multi-system* cure-kinetics benchmark signed

**Date:** 2026-07-25 (final cron pass before founder report) · **Host:** canonical `xbabe2:/home/ubuntu/amphora/build/mvp20-split`
**Authority:** AUDIT_ONLY. The 66 signed receipts and the manifest are unchanged (still 66). xbabe1 tree untouched. Promotes nothing; flips no rights gate; signs no trust-anchored phase0 receipt.

---

## 1. Verdict on "do we have full Phase 0" — NO (independently re-confirmed)

`config/program/phase0-decision-report.v2.json` → `status = EXECUTION_INCOMPLETE`, `promotable = false` for all modules. The defensible Phase-0 count is **9–10, all infrastructure / trust-kernel + solvency** — **zero** *other* science capabilities are at Phase-0. The stale "16" headline fails re-verification (7 of those badges drifted post-signing; see `redteam-count-integrity-2026-07-25`). Every other science module — barrier-corrosion, cure-potlife, viscosity, molecule-property/novelty/generator/role-ranker, design-rule, public-corrosion, ingredient-library — is **PRE_PHASE_0 / UNVALIDATED**.

**Honest headline for the deck:** *the blocker to a real science Phase-0 is (a) a dual-identity governance signing ceremony above an autonomous cron's authority, and (b) rights-clean data scale — NOT broken science.* This run adds real, signed, replayable evidence on (b).

## 2. What is new this run — cross-source Kissinger cure-kinetics benchmark

`amphora-redteam-audit/benchmarks/cure-kinetics-kissinger-multisystem-ccby-v1/`

The prior run delivered a **single-dataset** rights-clean anchor (DGEBA + IPDA). A one-formulation result cannot show the estimator generalizes. This run promotes that anchor into a **3-system, 3-DOI, cross-lab benchmark** — the same first-principles Kissinger estimator, run **non-circularly** against three independent **CC-BY-4.0 (commercial + derivative-use)** epoxy-amine DSC datasets.

| system | chemistry | scope | n(β) | reported Kissinger Ea | **recovered** | abs err | R² |
|---|---|---|---|---|---|---|---|
| DGEBA + IPDA (Polymers 2019, `10.3390/polym11030391`) | cycloaliphatic | **CORE** | 4 | 57.3 | 57.261 | **0.039** | 0.994 |
| DGEBA/BDGE + IPDA prepreg (Materials 2021, `10.3390/ma14164673`) | cycloaliphatic | **CORE** | 3 | 69.95 | 68.553 | **1.397** | 0.987 |
| multifunctional epoxy + DDS (Molecules 2026, `10.3390/molecules31040640`) | aromatic | GENERALIZATION (non-DGEBA) | 5 | 64.694 | 63.657 | **1.037** | 0.9997 |

- **Theory:** Kissinger (1957), `ln(β/Tp²) = −Ea/(R·Tp) + ln(A·R/Ea)`, `Ea = −R·slope`. Estimator consumes ONLY raw `(β, Tp)`; each paper's Ea is a validation target, never an input.
- **Aggregate KPI:** CORE max abs recovery error **1.40 kJ/mol**, CORE median **0.72**, CORE min R² **0.987**, **2 independent DGEBA sources**. **8/8 pre-registered gates PASS.**
- **Two-replay SHA-256 gate = PASS** (canonical == runB = `105bdc9e…`); DSSE Ed25519 signed with the repo **LOCAL_DEVELOPMENT_AUDIT_ONLY** key `local-9028773f…` (explicitly **not** trust-anchored), **SIGNATURE_VERIFY = PASS**.

## 3. Rights discipline actually exercised (this is the point)

The wall in front of cure-potlife is **data rights**, and this run shows the discipline is real, not decorative. Four otherwise-usable DGEBA-amine cure-kinetics papers with clean tabulated `(β, Tp)` + reported Kissinger Ea were **rejected on rights** after license verification (Crossref / publisher):

- `10.1039/c8ra04525a` (DGEBA + DETDA, RSC Advances 2018) — **CC BY-NC 3.0** (non-commercial) → rejected.
- `10.1021/acsomega.4c00795` (DGEBA + amine adduct, ACS Omega) — **CC BY-NC-ND 4.0** (no commercial, no derivatives) → rejected.
- `10.1021/acsomega.0c03085` (AG-80 + DDM, ACS Omega) — non-DGEBA resin + ACS AuthorChoice non-commercial → rejected.
- `10.3390/ma12233939` (DGEBA + TETA, Materials 2019) — CC BY 4.0 but **no tabulated raw peaks** (only a single ASTM-E698 Ea) → not usable non-circularly.

Only genuine **CC-BY-4.0 with published raw peaks** were admitted. This is why the CORE is 2 DGEBA systems (both IPDA, different labs) plus 1 clearly-labeled non-DGEBA generalization point — an honest count, not an inflated one.

## 4. Honest limits (do not oversell to founders)

- Both CORE systems use the **same amine class (cycloaliphatic IPDA)** — this is a strong *cross-lab reproducibility* result but NOT yet cross-amine-chemistry breadth for DGEBA. Aromatic-amine breadth is currently only the non-DGEBA generalization point.
- The prepreg system's peaks are published only to **integer Kelvin** with **n=3** heating rates → its leave-one-out spread is large (36 kJ/mol, endpoint leverage) and R² (0.987) is the lowest; reported honestly, not hidden.
- Kissinger recovers the **reaction** apparent Ea, which is higher than the **gel/pot-life** apparent Ea the cure-potlife KPI ultimately needs. This benchmark validates the *estimator/method*, not the pot-life target variable itself.

## 5. What it deliberately does NOT do (authority ceilings sacred)

Does not promote cure-potlife; does not flip `rights_gate_passed` (needs each source ingested through `amphora-source-ledger` under a signed rights receipt); does not sign a trust-anchored phase0 receipt (dual-identity ceremony is above a cron's authority); does not touch the 66 receipts / manifest; does not use any non-CC-BY source.

## 6. Honest next steps to a real SECOND science Phase-0 (cure-potlife)

1. **Ledger these 3 CC-BY sources** through `amphora-source-ledger` with signed rights receipts → begins flipping `rights_gate_passed` toward true on real provenance (currently `false`, zero eligible rows — all in-tree cure sources are QUARANTINED vendor TDS).
2. **Acquire cross-amine breadth**: ≥1 rights-clean DGEBA + *aromatic* (DDM/DDS) and ≥1 DGEBA + *aliphatic* (DETA/TETA) CC-BY DSC series with tabulated peaks, so the CORE spans the marine-relevant amine classes.
3. **Add the pot-life target**: acquire rights-clean multi-temperature **gel-time / pot-life** series (rheology or ASTM D2471) so the KPI rests on the actual target variable, not reaction Ea.
4. **Run the dual-identity evaluate/review ceremony** (keys present & verified this portfolio) — a governance decision, not a science or key gap.

## 7. Files

- `dataset.multi.ccby.json` — the three rights-clean datasets (provenance, license, raw peaks, reported Ea).
- `cure_kinetics_multisystem_audit.py` — deterministic Kissinger harness (byte-stable).
- `diagnostic.canonical.json` / `diagnostic.runB.json` — two-replay SHA-256 gate PASS.
- `replay_receipt.v1.dsse.json` — DSSE Ed25519 receipt, local audit key, SIGNATURE_VERIFY PASS.
- `sign_multi.py` — signing + self-verification.
