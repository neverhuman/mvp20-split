# network-tg-feasibility-v3 (AUDIT_ONLY)

**Backbone-path topological rigidity descriptor for DGEBA + amine network Tg —
the descriptor v2 said was missing, built and tested honestly.**

## What this is
An AUDIT_ONLY red-team science increment on the **highest-value UNVALIDATED gap**
in the portfolio: the glass-transition temperature of marine-coating DGEBA + amine
networks (target: `amphora-molecule-property` glass-transition capability). It
**promotes nothing**, signs **no** Phase-0 receipt, and does **not** touch the 66
signed receipts, the manifest, or the signed v1/v2 audits. Signed with the
`LOCAL_DEVELOPMENT_AUDIT_ONLY` key (`local-9028773f...`).

## Why v2 failed and what v3 changes
v2 **refuted** whole-molecule structure-only descriptors (best LOO 40.5 °C, worse
than a mean-Tg NULL) and diagnosed the cause from the data: whole-molecule
aromatic/ring fraction **cannot tell backbone-rigid from pendant-rigid**:

| system | whole-molecule aromatic fraction | Tg (°C) |
|---|---|---|
| **DDS** — aromatic rings *in* the N-to-N crosslink path | 0.71 | **208** |
| **m-XDA** — aromatic ring flanked by rotatable –CH₂– hinges | 0.60 | **100** |

Nearly equal composition, 108 °C apart. v2 said: needs a **topological** rigidity
descriptor. v3 builds exactly that.

## The descriptor (a-priori, parameter-free, non-circular)
For every pair of reactive amine N (crosslink junctions), take the shortest
topological bond path (RDKit `GetShortestPath`). A backbone bond is **rigid** if
aromatic / in-ring / multiple-order, **flexible** otherwise (the standard
rotatable-bond dichotomy restricted to the junction-to-junction backbone).
`B = mean over N–N pairs of (rigid backbone bonds / total)`. DGEBA is common to
every system → a constant offset → the amine backbone is the discriminator.
Measured Tg is **never** used as a feature.

## Result (page-verified rights-clean n=9 / 7 unique systems — NO new data)
| model (structure-only, LOO on 7 consensus systems) | LOO MAE | Pearson r |
|---|---|---|
| whole-molecule aromatic fraction (v2) | 44.9 | 0.50 |
| ring-atom fraction (v2 best) | 40.5 | 0.46 |
| **backbone rigidity (binary) — v3** | **35.7** | **0.69** |
| incumbent polyuniverse ML (signed receipt) | 39.1 | 0.08 |
| raw Van Krevelen (signed receipt) | 109.1 | — |
| LOO-NULL (mean Tg) | 37.0 | — |
| in-sample NULL (mean Tg) | 31.8 | — |

Backbone rigidity is the **first structure-only model to beat the incumbent ML and
the LOO-NULL**, improves the best LOO MAE 40.5 → 35.7 °C, cuts leave-one-**source**-out
error 42.2 → 33.2 °C, and **correctly ranks the two highest-Tg systems** (DDS 208,
IPDA 158) — the ones that matter for high-performance marine coatings.

**Cross-check:** the harness reproduces v2's `ring_only` LOO MAE (40.505739 °C)
**exactly**, an independent-implementation check of the LOO pipeline.

## Honest verdict: ADVANCED_NOT_VALIDATED
It still **fails** the KPI gate. Phase-0 gate status:
- **G1** (rights-clean cited n ≥ 12, 4 classes): **UNMET** — 7 unique / 9 meas.,
  unchanged. Web-search-summary Tg values (e.g. DGEBA/MDA ≈170 °C) were
  **rejected**: not read from an actual source page and cross-protocol → would
  violate the v2 "every value from the source page" standard and inject noise.
- **G2** (LOO MAE ≤ 25 °C): **UNMET** — 35.7 °C (improved from 40.5). Inter-lab
  floor ≈ 8.6 °C (DGEBA/DDS 200/204/220).
- **G3** (beat incumbent ML 39.1 + VK 109 + NULL): **partially met for the first
  time** — beats ML and LOO-NULL; not the in-sample NULL.
- **G4** (non-circular structure-only): **met**. **G5** (signed two-replay): **met**.

**Why it plateaus:** connectivity alone cannot encode **IPDA's gem-dimethyl steric
rigidity** (low B, high Tg) nor the crosslink-functionality boost lifting aliphatic
TETA/DETA above the ring amines. A physics-weighted variant raises in-sample r to
0.72 but **worsens** LOO — classic small-N overfitting; the simpler binary
descriptor is reported as primary. **The two remaining constraints are now precisely
identified: (a) protocol-consistent data quantity (n ≥ 12), (b) a steric/side-group
descriptor beyond backbone connectivity.**

## Phase-0 reconciliation (live, this run)
`module-manifest.json`: **0 of 29 modules are `scientific_readiness=VALIDATED`**;
every module is `MODEL_READINESS_ONLY`. "FULL Phase-0" is a governance/engineering
milestone, **not** a count of externally-validated science. Founder skepticism is
correct. The one module with real external-data science behind it remains
`amphora-solvency-score` (BigSolDB leave-solute-out).

## Reproduce
    cd /home/ubuntu/amphora/build/mvp20-split
    python3 amphora-redteam-audit/benchmarks/network-tg-feasibility-v3/network_tg_v3_audit.py > /tmp/d.json
    sha256sum /tmp/d.json   # == daee7708cb5d02a54237c16deac90f88c08bbc9159aaf89e5d5539d976bc812b

Two-replay SHA-256 gate = **PASS**. Signature verifies against
`.amphora/control/local-ed25519.pub.json`.

## What it does NOT do
- Does not promote any module to PHASE_0; adds no PHASE_0 module (G1, G2 unmet).
- Does not modify any of the 66 signed receipts, the manifest, or the v1/v2 audits.
- Does not fabricate, web-summarize, or "mid-range" any Tg value.
- Does not perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing.
