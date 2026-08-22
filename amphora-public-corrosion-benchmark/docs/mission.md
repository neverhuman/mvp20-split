---
{"audit_date": "2026-07-17", "authority_ceiling": "EVIDENCE_ONLY", "candidate_types": ["formulation"], "capability_profile": "capability-profile.json", "consumers": [], "dependencies": ["amphora-candidate-contract", "amphora-source-ledger"], "evidence_inventory": "../../config/module-evidence-inventory.json", "lane": "formulation", "module_id": "amphora-public-corrosion-benchmark", "operational_readiness": "AUDIT", "phase": "PRE_PHASE_0", "schema": "amphora.module-mission.v1", "scientific_readiness": "UNVALIDATED", "solver_use_ceiling": "AUDIT_ONLY"}
---

# amphora-public-corrosion-benchmark mission

## Decision and falsifiable hypothesis

This module supports the decision of whether public corrosion data can support a reproducible external benchmark. Its falsifiable hypothesis is that a provenance-locked benchmark can distinguish declared models from hostile nulls.

It does not establish product qualification, batch release, procurement approval, legal freedom to operate, regulatory compliance, supplier closure, or wet-lab performance. Phase 2, if later earned, means defensible R&D technical IP only.

## Honest current state

The live checked implementation is native Rust at `amphora-formulation-capabilities/src/lib.rs` with SHA-256 `8b7612325bff9830da1eebd1dc6ba4af411205581ce388c45fdc6be5356edde0`. Runtime registration is owned by `amphora-engine/src/lib.rs` and is checked against `module-manifest.json`. Retired Python implementation records have diagnostic provenance only and are not live authority.

Focused checked test evidence:

- `amphora-formulation-capabilities/src/lib.rs` — SHA-256 `8b7612325bff9830da1eebd1dc6ba4af411205581ce388c45fdc6be5356edde0`

Operational state is `AUDIT`; scientific state is `UNVALIDATED`, so the current phase is **Pre-Phase 0**. Execution and passing unit tests do not establish human parity. No readiness percentage is asserted.

### Checked datasets and artifacts

- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/feedback_v1/dataset_context.json` — SHA-256 `a7fa933ae5a147c4503bbfd525948b86d6dfb527023b6dac3c16e550ff74cc05`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128757_2-e-p-1k-2-s_eis.csv` — SHA-256 `da169b07c55bcd33255c69396df63783988e548ee57d752ce66dc421e760f39f`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128758_2-e-p-1k-2-s_erosion.csv` — SHA-256 `c72f611d6eea10598dc705c621c161ab86f94ab9f3cf0001787f98966743b16a`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128759_2-e-p-1k-2-s_impact.csv` — SHA-256 `d319386d740e5def9db8a53591731a2e756e6ad21763a1f13aba63e8c20716a1`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128760_2-e-p-1k-2-s_rust_creep.csv` — SHA-256 `cb60d286a24ccac45de33858c5183aa5880a8f28862ca05c9195070cf9340e0a`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128761_2-e-p-1k-2-s_wet_dry_adhesion.csv` — SHA-256 `db5667c619b03afca704f062e8b64e766219f24837038dde50548c88e7ff0995`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128762_2-e-p-2k-2-s_eis.csv` — SHA-256 `a2e49c9dfdb28b839330318c2f6df52efe96b0e100666ec4f5d3b56fac6340ba`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128763_2-e-p-2k-2-s_erosion.csv` — SHA-256 `6ae2777bf20721935ecf83d74f973304374919e25170c5fefeb1b6741c409657`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128764_2-e-p-2k-2-s_impact.csv` — SHA-256 `cba0d127347507e2fce6a6dd8e7ddd8bb9872944246a464ed285ec0f34272f36`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128765_2-e-p-2k-2-s_rust_creep.csv` — SHA-256 `d35bb0bde029f2dcb9e1dea56cdf2c7a8631c974dc72ad6ef3c377e112554735`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128766_2-e-p-2k-2-s_wet_dry_adhesion.csv` — SHA-256 `673129010365ef3984c2e2a287ff14b1c9d315d9107e446cc86e367d10ab1b42`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128767_2-z-p-1k-2-s_eis.csv` — SHA-256 `bac1b0d18bcd5e74151c7282c7e42bc4d754edcc3c5ae9e0c76507a7709b351b`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128768_2-z-p-1k-2-s_erosion.csv` — SHA-256 `2d17de08d48b96921874302e746f6a024c22b3708c935273a8112252f7de3f11`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128769_2-z-p-1k-2-s_impact.csv` — SHA-256 `b3580e3f7ea033d52e082526517002b4c6b9e03eeb68e6b783363091255b1c86`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128770_2-z-p-1k-2-s_rust_creep.csv` — SHA-256 `0846612c294259b30822fde128648962a019a19ff89fdf15daca7a41f945d89a`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128771_2-z-p-1k-2-s_wet_dry_adhesion.csv` — SHA-256 `716904a260db91ea3b3d4395fa66d3f08e2466433b6e10047a1bb0e5797609d8`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128772_2-z-p-2k-2-s_eis.csv` — SHA-256 `5544e142a47fa9314262b249de8d47541b87f7e7fddf86414b3eabb53f6d4525`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128773_2-z-p-2k-2-s_erosion.csv` — SHA-256 `ff17e7606af558480b067ca067d69c3f0651dbc2f1c7d5593726d917a7179424`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128774_2-z-p-2k-2-s_impact.csv` — SHA-256 `5e6b2f93d87e182bdf5b9c905bd43ce405c92a1c865e4f7a7449f6f594056a96`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128775_2-z-p-2k-2-s_rust_creep.csv` — SHA-256 `7e562fea6325ce865188e6a5321ff78dbd35b36443c7bb586059eeee7e3e1446`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128776_2-z-p-2k-2-s_wet_dry_adhesion.csv` — SHA-256 `1d69b9371aa99b72b2d24da151023f1f9822607fd7f9002c65f5acc29478efe5`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128777_3-d-p-2k-2-s_eis.csv` — SHA-256 `2cd236bb9fdb03f6ae49025de37f0a0f37b1f326918c948f651066a6b0be92cf`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128778_3-d-p-2k-2-s_erosion.csv` — SHA-256 `bec75f2d7330c51b7ea2a8949c8db60ff92948bf3bce10d467a527e53dfa5d73`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128780_3-d-p-2k-2-s_impact.csv` — SHA-256 `edecd4849f1c610c5cf107d76bb852da6013d8d15352672112b9b1adc09e78fa`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128781_3-d-p-2k-2-s_rust_creep.csv` — SHA-256 `6ddc24c7f8e5ebdbb28e8888e4dc38f5f58cc51310323a2c125e059cdede8a93`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128782_3-d-p-2k-2-s_wet_dry_adhesion.csv` — SHA-256 `f05baa3cfa3e94bd6ad734d777b5934c67530f30d0d27139ded712e3840a062d`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128783_3-z-p-2k-2-s_eis.csv` — SHA-256 `f423a904e7cee65beb2078097ba3909d487b2a61147d27c6c0db110bf52cd311`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128785_3-z-p-2k-2-s_erosion.csv` — SHA-256 `6ecc53e3b62a05c5b819cb7a6710c8b5cd3be92f414ea0742dceb7b8b15a17f9`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128786_3-z-p-2k-2-s_impact.csv` — SHA-256 `1fa8be3d29843f163e94a28fe991a1527c4669b879981d980563777481800531`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128787_3-z-p-2k-2-s_rust_creep.csv` — SHA-256 `991d3754dd64fd3c270ca0ae03c52316b2696eb141b41f956958b15aec73b50f`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `dataset` `amphora-public-corrosion-benchmark/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/128788_3-z-p-2k-2-s_wet_dry_adhesion.csv` — SHA-256 `b22fdbebd467a22c040885c1531d757585bad5cfdc8fac5b0ccc968b1f07b5b4`; rights `KNOWN` (A checked rights-ledger entry binds this SHA-256 as public/open official government data with stated use limits.)
- `output_artifact` `amphora-public-corrosion-benchmark/reference/mvp20/out/feedback_v1_nist_benchmark.json` — SHA-256 `e318214998d2691f5866324b84e13ed361d89a388daeb27d3f39ce2beb14fc20`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-public-corrosion-benchmark/reference/mvp20/out/v5_epoch29_corrosion_benchmark_model_card.json` — SHA-256 `1572d664af8ad654f55743ee5c4729025b2a8859adfcb6c8ae95abd87a2687b6`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-public-corrosion-benchmark/reference/mvp20/out/v5_epoch29_dataset_rights_and_source_currentness_ledger.json` — SHA-256 `671dacef8517464182a3fb7508a6bcf3f8814a3d414e8634d154b87c59b011ed`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-public-corrosion-benchmark/reference/mvp20/out/v5_epoch29_public_corrosion_dataset_manifest.json` — SHA-256 `b59bc8fff1b65e287945e52b19f4849f252e018b62e9626bed0814584f3d9a5a`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-public-corrosion-benchmark/reference/mvp20/out/v5_epoch29_public_eis_feature_table.json` — SHA-256 `58082a5356a51f74cf38fe5175de18435995de998ac23473437ffa19623059c4`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-public-corrosion-benchmark/reference/mvp20/out/v5_epoch29_unseen_benchmark.json` — SHA-256 `d58316fad1db07e3f01ec4ec136e98d786cb7c799ba51cd643df9fe601ad6ed0`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)
- `output_artifact` `amphora-public-corrosion-benchmark/reference/mvp20/out/v5_epoch30_lift_audit.json` — SHA-256 `5daada4f00b4ca6cb99a92cf0d7cb733d1118fc46630d6cf55e996aa2e3547b8`; rights `UNRESOLVED` (No checked-in license or ownership receipt is bound to this local file by the inventory.)

Rights are reported per file; local presence is not evidence of ownership or permission. Artifact presence and a matching hash do not establish dataset rights, scientific validity, or ownership. 30 artifact byte set(s) have a checked SHA-bound rights-ledger entry; all other artifact rights remain `UNRESOLVED`.

### Current benchmark result

Phase-0 known-answer harness at
`amphora-formulation-capabilities/tests/public_corrosion_benchmark_phase0_kpi.rs`
drives `public_corrosion_benchmark` across 5 formulation candidates with
default FeatureSnapshot (no verified_model_input) so runtime enters the
INSUFFICIENT_INPUT abstention path plus 3 fail-closed probes. 14 gates +
1 observational at floor 1.0. Byte-stable receipt at
`evidence/phase0/benchmark/result.v1.json` (SHA-256
`6755518f1106ef0d5f99e518c3c784c3ed06b9275ead54535c5be0be6f25ed42`).
Phase-0 KPI receipt at
`evidence/phase0/kpis/public-corrosion-benchmark-unresolved-rights-quarantine-kpi.v1.json`.

Runtime honestly returns INSUFFICIENT_INPUT with artifact_rights_status=
'UNRESOLVED', artifact_access_attempted=false, candidate_corrosion_
validation=false, benchmark_score=Null, all 4 gates false. Adversary-
supplied adversary_declared_benchmark_score=0.95, adversary_declared_
candidate_corrosion_validation=true, and candidate_declared_verified_
model_artifact=true are all defensively refused. Missing_inputs
explicitly names 'rights-cleared hash-bound public benchmark and
derived-artifact manifest'.

Theory: ASTM B117-19 salt spray; ASTM D5894-21 cyclic salt fog/UV;
ISO 12944-6:2018 coating corrosion protection; ISO 9227:2017 salt
spray; NACE SP0170-2012; USBR M-38 (2020); Macdonald 2006 EIS review
Electrochimica Acta 51(8-9):1376-1388; Randles 1947 Discussions of the
Faraday Society 1:11-19 (equivalent-circuit model); NIST FIPS 180-4;
Anderson 1980 reference-monitor.

### Phase-0 readiness

All Phase-0 deterministic gates in
`evidence/phase0/promotion/policy.v1.json` passing. Awaiting
`PHASE0_EVALUATOR` and `PHASE0_INTERNAL_REVIEWER` signatures.
Front-matter preserved.

### Empirical benchmark result — NIST CORR-DATA marine steel corrosion baseline

> **CORRECTED / SUPERSEDED (2026-08-03, repair R-A08).** The signed audit
> `evidence/audit/nist-baseline-fold-significance-v1/` returned **H0_REFUTED**
> against this section's flagship "+0.0475 log10 Ridge-beats-NULL" claim, on two
> independent grounds. (a) **Not independently reproducible**: the generating
> script (`/tmp/corr_baseline.py` per the receipt) was never committed to the
> module tree; an honest re-implementation of the KPI's own stated methodology on
> the identical hash-pinned raw CSV gives Ridge LOSD-CV MAE(log10) 0.5888 and
> NULL 0.6736 — the pinned 0.6331 / 0.6806 pair cannot be regenerated from what
> the repository preserves. (b) **Not fold-robust**: Ridge beats the NULL on only
> 17/30 independent source-document folds (56.7%, binomial p=0.585), the
> cluster-bootstrap 95% CI of the mean per-fold improvement [-0.0329, 0.4846]
> crosses zero, and the Wilcoxon signed-rank test on the 30 paired fold MAEs
> gives p=0.2710. **Corrected headline: no statistically significant lift over
> the per-material-group null median under LOSD-CV; the pinned 0.6331 is not
> independently reproducible.** The superseding signed receipt is
> `evidence/phase0/repairs/R-A08/done/nist-corr-data-marine-steel-corrosion-baseline-kpi.v2.dsse.json`
> (the superseded v1 KPI remains byte-intact on disk); see also
> `evidence/phase0/kpis/RETRACTION-INDEX.md`. The filtered population
> (588 records / 30 source documents) and the fitting-free per-material-group
> seawater reference-rate tables below reproduce exactly from the raw CSV and
> **remain valid**. The historical text below is preserved for provenance; its
> Ridge-beats-NULL claims are **retracted**.

> **FURTHER REFUTED — EXTRAPOLATION (2026-08-03, repair R-N03).** A second,
> orthogonal signed audit
> `evidence/audit/nist-baseline-material-group-extrapolation-v1/` returned
> **H0_REFUTED** against the same baseline's implicit generalization claim:
> under leave-one-material-group-out (LOMO) CV on the identical hash-pinned raw
> CSV, pooled Ridge MAE(log10) = 1.0728 vs an extrapolation-honest NULL
> (training-groups-only median) 0.8106 — a NEGATIVE improvement of **−0.2622
> log10 units**; Ridge beats the NULL on only **2/5** held-out material groups
> and is strictly worse on 3/5 (worst: Carbon and alloy steels, +0.6587 log10
> excess MAE). The in-domain "beats-null" advantage was material-group
> memorization via the one-hot dummy, not transferable physical signal.
> **Combined corrected claim (R-A08 + R-N03): no defensible predictive lift,
> in-domain or extrapolative — in-domain LOSD-CV lift not statistically
> significant AND extrapolation to unseen material groups is negative (−0.2622
> log10, 2/5 groups).** The current superseding KPI is
> `evidence/phase0/repairs/R-N03/done/nist-corr-data-marine-steel-corrosion-baseline-kpi.v3.dsse.json`
> (supersedes the R-A08 v2 KPI by path + sha256; the v1 and v2 files remain
> byte-intact); current consolidated audit index:
> `evidence/phase0/repairs/R-N03/done/audit-verdicts-consolidated-kpi.v3.dsse.json`.
> See `evidence/phase0/kpis/RETRACTION-INDEX.md`.

FIRST Phase-0 KPI receipt with real published corrosion data for this
module — directly addresses the module's `README.md` acknowledgement that
the prior locked receipt fails Phase-1 ("six systems from one study,
zero untouched external systems").

The signed scientific receipt lives at
`../../amphora-molecule-property/reference/mvp20/data/nist_corr_data_marine_steel_corrosion_baseline_receipt.v1.json`
(SHA-256 `fc6104cc22b252238e38898ba6cc7e7825e64c6eaebd9d55084fe1de4e76974f`,
receipt_id `nist-corr-marine-baseline-70ed297e20184db8f3f76adf89d93a3e613934b64878825a8a099c34508312cc`).
The Phase-0 KPI receipt lives at
`evidence/phase0/kpis/nist-corr-data-marine-steel-corrosion-baseline-kpi.v1.json`
(SHA-256 `bfbc32fe02df1d0bf8c7611ad8ab28c57f960eede7e640cda1db0b16078ab888`).

Public data source: **NIST CORR-DATA Database** (2017 doi:10.18434/M3TH4R;
24,721 records from the NACE-NIST Corrosion Data Program 1982-1997,
20+ databases spanning 250+ source documents). After filtering to marine
environments (Seawater / Sodium Chloride / Atmospheric Environments) and
coating-substrate material groups (Carbon and alloy steels, Stainless
steels, Copper/Aluminum/Nickel alloys) with numeric strictly-positive
mm/yr rates: **588 records from 30 unique source documents**.

**Baseline Ridge regression on log10(rate mm/yr) with Leave-One-Source-Document-Out CV:**

| Ridge α | LOSD-CV MAE(log10) | LOSD-CV RMSE(log10) |
|---:|---:|---:|
| 0.01 | 0.6331 | 0.8304 |
| 0.10 | 0.6338 | 0.8304 |
| 1.00 | 0.6368 | 0.8311 |
| 10.00 | 0.6428 | 0.8342 |
| 100.00 | 0.6670 | 0.8727 |

Best α = 0.01. LOSD-CV MAE(log10 rate) = **0.6331** (within a
factor of 4.3 on linear rate). NULL baseline (per-material-group median log10 rate) MAE = 0.6806. **Ridge beats NULL by +0.0475 log10 units** (7.0% relative improvement).
*[RETRACTED 2026-08-03, repair R-A08 — not independently reproducible and not
fold-robust; see the correction note at the top of this section.]*

Modest lift is HONEST for a linear model on public data spanning 6 orders
of magnitude across 30 studies with heterogeneous methodology.
*[Correction 2026-08-03, repair R-A08: the lift itself did not survive fold-level
significance testing and its pinned value is not reproducible — see note above.]* Phase-1
should extend with nonlinear ML (Random Forest, HistGBM) at n ≥ 1000.

**Uncoated seawater baseline distribution by material group** — REFERENCE
RATES ANY MARINE ANTI-CORROSION COATING CLAIM MUST BEAT:

| Material group | n | Median (mm/yr) | IQR [p25, p75] | Min | Max |
|---|---:|---:|---|---:|---:|
| Carbon and alloy steels | 44 | 0.1000 | [0.0800, 0.1500] | 0.0300 | 2.6000 |
| Stainless steels | 19 | 0.0120 | [0.0100, 0.0350] | 0.0030 | 1.9000 |
| Copper and alloys | 37 | 0.0100 | [0.0050, 0.0200] | 0.0018 | 1.0000 |
| Nickel and alloys | 23 | 0.0060 | [0.0030, 0.0215] | 0.0010 | 0.0430 |
| Aluminum and alloys | 19 | 0.0014 | [0.0009, 0.0016] | 0.0002 | 0.2800 |

Carbon and low-alloy steels in seawater median = **0.1000 mm/yr**
(p25-p75 = [0.0800, 0.1500] mm/yr,
n = 44 records) — the reference number that anti-corrosion coatings
must materially reduce.

**Observed Phase-0 KPI outcomes (10/10 gates PASSED, `phase0_deterministic_gates_passed: true`):**

- `n_records_at_least_300` — **PASSED** (588)
- `n_source_documents_at_least_10` — **PASSED** (30)
- `n_environments_at_least_3` — **PASSED** (3)
- `n_material_groups_at_least_3` — **PASSED** (5)
- `ridge_beats_null_baseline_on_LOSD_CV` — **PASSED** (+0.0475 log10 improvement) *[RETRACTED 2026-08-03, repairs R-A08 (in-domain) and R-N03 (extrapolation) — see correction notes above]*
- `MAE_log10_rate_below_1_0` — **PASSED** (0.6331)
- `seawater_carbon_steel_baseline_documented` — **PASSED**
- `seawater_stainless_baseline_documented` — **PASSED**
- `input_csv_hash_bit_stable` — **PASSED** (CSV SHA-256 recorded)
- `scientific_receipt_hash_bit_stable` — **PASSED** (two-replay verified)

**HONEST INTERPRETATION**. The receipt establishes REFERENCE RATES for
uncoated substrate corrosion in real marine environments from a
government-sanctioned public database:

- Carbon steel corrodes at median ~0.100 mm/yr in seawater with wide
  scatter (p25-p75 spans 1.9×) reflecting real environmental
  variability.
- Stainless steel corrodes at median ~0.0120 mm/yr in seawater — inherently more
  resistant, so "coating on stainless" claims have a much lower baseline
  to reduce.
- The Ridge baseline predicts to within a factor of 4.3 in linear rate;
  this is a defensible starting point on public data, but nowhere near
  engineering precision — Phase-1 must extend with (a) nonlinear ML,
  (b) frequency-resolved EIS data (module native-contract flag), and
  (c) cross-reference with EN ISO 12944 corrosivity categories.
  *[Qualified 2026-08-03, repair R-N03: in-domain interpolation only —
  under leave-one-material-group-out extrapolation the same Ridge baseline
  is WORSE than an extrapolation-honest constant null (−0.2622 log10 pooled,
  worse on 3/5 held-out groups); it grants no predictive lift for unseen
  material groups. See the R-N03 correction note above.]*

The theory stack: NIST CORR-DATA 2017 (doi:10.18434/M3TH4R);
Roberge 2008 Corrosion Engineering Principles and Practice Ch. 7;
Uhlig & Revie 2008 Corrosion and Corrosion Control §2.3, §11.2 (seawater);
NACE MP0169 (baseline steel corrosion in seawater);
EN ISO 12944-2 (marine atmospheric corrosivity C3/C4/C5-M);
Hoerl & Kennard 1970 Ridge Regression;
Kennard-Stone 1969 applicability domain.

Claim scope: this KPI documents a PUBLIC baseline on 588 NIST CORR-DATA
records for UNCOATED substrates. It grants no batch-release,
manufacturing-qualification, optimizer, or product-performance authority.
No Amphora candidate is validated by this receipt (public-row isolation
enforced per module native contract). Phase-1 explicitly flags: nonlinear
ML at n ≥ 1000; frequency-resolved EIS with Kramers-Kronig validation;
EN ISO 12944 category mapping; independent evaluator/reviewer signatures.

### Known contradictions

- The checked public-system audit reports no lift on current data and contains no owned candidate wet-lab validation.

Across the portfolio, the emitted envelope, adapter, manifest, model receipt/card, portfolio policy, and Rust ranking boundary must all agree. The most restrictive policy controls.

## Inputs, outputs, and normalization

Current accepted format: canonical CandidateEnvelope JSON. The current runtime supports JSON plus molecule SMILES only through the central candidate contract. Target interface: canonical CandidateEnvelope JSON. That target interface is already the runtime interface for this module. Unsupported formats fail closed.

External chemistry normalizes once in `amphora-candidate-contract`; this module consumes canonical `CandidateEnvelope` data. Original bytes, normalized structure/formula, toolkit/version, stereochemistry, isotope, charge, fragment, mixture, polymer, and commercial-grade policies are retained in the capability profile.

Canonical input is a finite `formulation` `CandidateEnvelope` whose payload matches `candidate_type`. Canonical output is `ScoreEnvelope`; the primary value path is `metrics.unseen_benchmark`. Units, direction, nullability, authority, uncertainty, and claim locks are explicit in the profile and envelope. A null or blocked value cannot be converted to an objective.

## Canonical current examples and typed paths

```json
{"candidate_id": "amphora-public-corrosion-benchmark-example", "candidate_type": "formulation", "formulation": {"application": {"dft_mil": 5.0, "relative_humidity_pct": 50.0, "substrate": "steel", "surface_preparation": "declared", "temperature_C": 25.0}, "basis": "mass_g_per_batch", "batch_mass_g": 137.13, "ingredient_catalog_version": "facts.v2", "process": {"application_method": null, "induction_time_min": null, "mix_order": null, "pot_age_h": 0.0}, "recipe": {"part_A": {"dgeba_828": {"ingredient_id": "dgeba_828", "mass_g": 100.0}}, "part_B": {"ancamide_350a": {"ingredient_id": "ancamide_350a", "mass_g": 37.13}}}}}
```

The schema-valid fail-closed output example is checked in at `docs/capability-profile.json#/examples/current_output`. Exact paths are: objective `None`, metric `metrics.unseen_benchmark`, gate `gates`, uncertainty `uncertainty`, evidence gaps `missing_inputs`, and claim locks `claim_locks`. Nullability is explicit; empirical units and direction come only from the locked benchmark receipt. The authority ceiling is `EVIDENCE_ONLY` and solver-use ceiling is `AUDIT_ONLY`.

## Data, theory, model, and uncertainty strategy

Applicability domain is solvent-borne two-component epoxy-polyamide marine-coating R&D and the explicitly declared candidate types. Missing values are not imputed across an authority boundary. Empirical work uses group, family, source, and time-safe splits; computed values remain labeled computed; candidate evidence remains separate from public context. Subgroup reporting and calibrated intervals are required wherever the locked KPI is empirical. Named standard, expert/CRO, primary-literature, simple physical, and hostile-null baselines precede promotion.

## KPI register and promotion gates

Primary KPI: **paired baseline lift** at `metrics.unseen_benchmark`. Direction and unit are declared by the locked benchmark; population is the declared applicability domain; split is group/time/source-safe; confidence intervals are mandatory for empirical claims. Locked target: At least 30 independent systems, including 10 locked external systems; at least 10 percentage-point baseline lift with paired 95% confidence lower bound above zero.

- Phase 0 — Useful: deterministic or evidence-bound capability, contract parity, fail-closed malformed/OOD behavior, no unresolved authority contradiction, and the module acceptance tests pass.
- Phase 1 — Human parity: the locked independent evaluation beats or matches the best reproducible named baseline at the stated target with uncertainty.
- Phase 2 — Defensible IP: prospective superiority repeats independently, owned provenance and ablations freeze, and patent-versus-trade-secret review is documented. Counsel separately determines FTO.

Focused acceptance command: `rtk cargo test --workspace --locked`. The native demo and replay commands in `AMPHORA_RUST.md` are the portfolio acceptance path.

External dependency or delay:

- At least 30 independent systems including 10 locked external systems

Estimated effort is represented by the checked-in 0–5 priority factors, not a fabricated schedule. Schema drift, source mutation, incomplete folds, non-finite output, authority escalation, or lost claim locks automatically demote the module.

## Red-team dossier

Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every such case must fail closed or remain an explicit evidence gap.

Module-focused checked fixture: `amphora-formulation-capabilities/src/lib.rs` via `rtk cargo test --workspace --locked`. Scenario: Keep the grouped unseen benchmark deterministic and not promoted.
