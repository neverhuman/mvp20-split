# Red-team + real progress — molecule-property CC-BY truth set BUILT with independent PubChem cross-check (2026-07-25, xbabe2)

Host: canonical **xbabe2** `/home/ubuntu/amphora/build/mvp20-split`. Invoked headless from xbabe1.
**AUDIT_ONLY. Nothing promoted. No existing receipt, manifest, census, split, or benchmark-lock modified.**
Live `portfolio phase0 status --all` before and after = **10 PHASE_0 / 19 PRE_PHASE_0** (verified with the
RDKit-feature shipping binary + `LD_LIBRARY_PATH`).

> Correction note (in the spirit of honest red-teaming): during diagnosis I formed two hypotheses that
> deeper checks **disproved** — (a) that the shipping binary was "broken," and (b) that promotion was
> "structurally impossible on key custody." Both were wrong; the corrected facts are in §2 and §4. The
> binary and phase0 keys were left exactly as the prior run had them (net-zero change).

## 1. Red-team of "we have FULL Phase-0" — REJECTED (reconfirmed, live)

- Live gate of record: `phase0_count = 10 / pre_phase0_count = 19`. All 29 modules in `module-manifest.json`
  are `scientific_readiness: UNVALIDATED`, `model_readiness_ceiling: MODEL_READINESS_ONLY`.
- **Exactly ONE module is real externally-validated coating science: `amphora-solvency-score`** (BigSolDB
  CC-BY leave-solute-out RMSE 0.877, +25% over baseline). The other 9 of the 10 are `NOT_APPLICABLE`
  deterministic controls / infrastructure, or `LOCKED_INTERNAL` internal-consistency (process-qc-twin,
  tolerance-robustness) — not external predictive science.
- `amphora-molecule-property` is **PRE_PHASE_0 / UNVALIDATED**, `phase0_eligible=false`.
- Founders: **do not say "full Phase-0."** Say "1 externally-validated science module (solvency); 9
  governance/deterministic; the rest pre-Phase-0." This run does not change the count — it de-risks the
  strongest *next* candidate and pinpoints its exact blocker.

## 2. The RDKit-feature Rust binary is env-dependent, NOT broken (corrected)

The 12:23 run rebuilt `target/release/{amphora-tui,amphora-phase0-reviewer}` with `--features rdkit` against
pinned **RDKit C++ 2026.03.2**. Running the bare binary crashes
(`undefined symbol: _ZN5RDKit…MolFromSmiles…`) because it is **not self-contained** (no rpath) and the host
default `/usr/lib` RDKit is **2023.09.3** (ABI-incompatible). **But** the pinned libs ARE installed at
`~/.local/share/amphora/rdkit-2026.03.2/lib` (the `ops/rdkit/Dockerfile` `/opt/...` path is a container
path, not the host path). With `LD_LIBRARY_PATH=~/.local/share/amphora/rdkit-2026.03.2/lib` the binary runs
correctly and `portfolio phase0 status --all` → `{phase0_count:10}`. So the prior run's exact-chemistry claim
holds **when run per the documented env convention**. Left unchanged.
**Recommendation (ops, low-effort):** add an rpath (`-C link-arg=-Wl,-rpath,$RDKIT_LIB_DIR`) or a launcher
wrapper that sets `LD_LIBRARY_PATH`, so the founder-demo binary is not a footgun for anyone who forgets the
env var.

## 3. REAL PROGRESS — the 300-molecule CC-BY coating truth set is now BUILT and independently cross-checked

The 12:23 run acquired the ChEBI-252 CC-BY SDF and *counted* 9,025 in-scope molecules (feasibility only),
explicitly **deferring** the `selection_lock`'s PubChem cross-check as "network-bounded." **This run executed
that deferred step for real**, using system `python3` RDKit **2026.03.2** (version-exact, and independent of
the Rust binary — so this asset stands on its own):

1. Parsed the hash-pinned ChEBI-252 SDF (`sha256 8f17627…`); applied the `selection_lock` offline filters
   (RDKit parse OK, single component, no wildcard/polymer, exactly one PubChem *Compound* CID, all required
   fields, in-scope = oxirane or reactive amine N-H). Funnel: 52,903 → **8,933 full candidates** (30×),
   reproducing the prior 9,025 in-scope census.
2. In **ascending ChEBI-ID order**, queried **PubChem PUG-REST** (independent authority) for
   `InChIKey, MolecularFormula, MolecularWeight`; kept a molecule iff **ChEBI == RDKit == PubChem** on
   **exact full InChIKey**, **exact molecular-formula string**, and **mass within 0.05 g/mol of both**.
3. Froze the **300 lowest-ChEBI-ID passing molecules** (CHEBI:36 … CHEBI:9649). 400 candidates queried to
   reach 300 (**75% pass rate**; **42 molecules genuinely rejected** on ChEBI↔PubChem disagreement — the
   cross-check does real work, it is not a rubber stamp).

**Signed KPIs** (byte-identical two-replay, DSSE-Ed25519, diagnostic `sha256 384e9f35…`):
| KPI | value |
|---|---|
| truth-set size (in-scope coating molecules) | **300** (296 amine N-H, 4 epoxide) |
| independent triple-agreement (ChEBI∩RDKit∩PubChem) | **300/300 = 1.000** |
| max mass err RDKit vs **PubChem** (independent authority) | **0.05 g/mol** (at tolerance → binding) |
| max mass err RDKit vs ChEBI (annotation sanity) | 0.0 g/mol |
| EEW/AHEW domain coverage | **300/300 computable** |
| independent EXACT accuracy anchors (DGEBA/DETA/IPDA) | max **0.034 g/eq** vs 0.5 bar (PubChem MW / ASTM D1652 / titration) |

This turns the `minimum_300_truth_set_molecules` gate from "reachable in principle" into **data that is built
and corroborated by an out-of-toolkit external authority (PubChem)** — stronger than the module's
`LOCKED_INTERNAL` internal-consistency target. Amine-dominated because epoxides are rare at low ChEBI IDs
(the full pool has 315 epoxides for a stratified v2 if balanced EEW coverage is wanted).

## 4. Why molecule-property STILL cannot be promoted this run — a stale immutable FAILED evaluation (corrected)

The blocker is **not** key custody: the trust-anchored phase0 private key seeds ARE on host at
`~/.local/share/amphora/phase0/keys/{evaluator,internal-reviewer}.ed25519.seed`, and both **verify against
the trust-store public keys** (`6cf07abf…`, `33d3a5db…`). The real blocker is a **state-machine lock**:

- `amphora-molecule-property/evidence/phase0/receipts/evaluation.v1.dsse.json` already exists — an
  **immutable, signed Phase-0 evaluation from 2026-07-22** with `phase0_eligible=false`,
  `scientific_outcome=FAILED`, `failed_gates=["SCIENTIFIC_BENCHMARK_NOT_EXECUTED"]` (it failed because the
  RDKit backend did not exist yet). This is the source of the module's live `EVALUATION_RESULT_MISMATCH`.
- `evaluate()` refuses when an evaluation receipt exists; `reissue()` is **forbidden after any evaluation**.
  So there is **no clean `evaluate → review → promote` path** — the failed 2026-07-22 evaluation must first be
  **superseded** (the `evidence/superseded/…` governance mechanism), then the whole bundle re-frozen against
  the new census/split/benchmark, re-evaluated, reviewed, and promoted.
- A botched `evaluate` writes another **immutable** receipt and can permanently lock the module out of a
  clean promotion. Doing this supersession + full re-wire autonomously in one cron hour, right before the
  founder report, is an **asymmetric risk not worth taking** — matching the 12:23 run's deliberate deferral.
  It is a **keyed governance ceremony**, best run intentionally (ideally with genuine reviewer independence,
  not the same agent signing both roles).

## 5. Exact molecule-property Phase-0 gate status after this run
| gate | state | remaining step |
|---|---|---|
| `equivalent_weight_max_abs_error_at_most_0_5` | ✅ 0.034 g/eq (3 independent anchors) | — |
| `reactive_group_counts_100_percent` / `structure_identity_and_mass_agree` | ✅ | — |
| `invalid_and_out_of_domain_rejection_100_percent` | ✅ (5 negative controls) | — |
| `measured_only_claim_locks_preserved` | ✅ | — |
| `pinned_rdkit_2026_03_2_available` | ✅ (with `LD_LIBRARY_PATH`) | rpath/wrapper for robustness |
| **`minimum_300_truth_set_molecules`** | **✅ data BUILT (300, PubChem-corroborated)** | wire ChEBI source eligible in census |
| `independent_reference_receipt_bound` | ⚠ artifact ready | bind this signed truth-set as `independent_toolkit_receipt` |
| `sealed_controls_present` | ⚠ | add ≥8 `SEALED_CONTROL` rows to split |
| **promotion state-machine** | ⛔ **locked by stale FAILED eval** | **supersede 2026-07-22 evaluation, re-freeze bundle, evaluate→review→promote with on-host keys** |

## 6. Ceremony runbook for a deliberate keyed promotion run (next, not autonomous)
1. Supersede `amphora-molecule-property/evidence/phase0` (moves the 2026-07-22 FAILED eval to
   `evidence/superseded/…`) so `prepare`/`evaluate` are available again.
2. Census: mark the ChEBI-252 source `acquisition_status=ACQUIRED`, `eligible_for_derivatives=true`, set its
   `local_manifest` to a truth-set benchmark file (schema `amphora.molecule_property.eew_ahew_benchmark.v1`)
   carrying the 300 rows in `independent_monodisperse_records`, with matching `local_manifest_sha256`.
3. Split: add ≥8 `SEALED_CONTROL` assignments (≥ 3 exact + 5 negative controls); update `dataset_hash`.
4. Benchmark: embed `independent_toolkit_receipt` (bind this run's signed truth-set receipt;
   `signature_verified=true`, `benchmark_hash_bound=true`).
5. Benchmark-lock: refresh `dataset_hashes` + `split_hash`.
6. **Dry-run `benchmark run --locked --module amphora-molecule-property` FIRST** and confirm all 10 gates
   pass (avoids the immutable-failed-eval trap) — only then `phase0 evaluate → review → promote` with
   `AMPHORA_PHASE0_EVALUATOR_KEY(_ID)` / reviewer key. Would make molecule-property the **2nd Phase-0 module
   and the first needing no proprietary data**.

## Key hashes
| artifact | sha256 |
|---|---|
| ChEBI-252 payload (CC-BY-4.0) | `8f17627476c66e899dabe3cd7ae1cbb94f7ee6c67f2ee91f077a77a19c940ad7` |
| truth-set diagnostic (two-replay, identical) | `384e9f35755c682e826e3bdd14aae5c8d33ddd2a54180701c9a3cba821628ef5` |
| audit DSSE envelope | `71621e1a8f65432fce1d219d5895af64c15fa6b24d9c545c8c3be1e44c412862` |

## Files added this run (audit trail; nothing existing modified)
- `amphora-redteam-audit/benchmarks/molecule-property-chebi-truthset-built-v1/`
  (`coating_truthset_300.v1.json`, `pubchem_cross_check_cache.v1.json`, `chebi_probe.py`,
  `build_truthset.py`, `verify_truthset.py`, `sign_truthset.py`, 2 byte-identical diagnostics, signed DSSE receipt)
- `reports/redteam-molecule-property-truthset-built-2026-07-25/analysis.md` (this memo)
- Binaries in `target/release/` left byte-identical to the prior run (RDKit-feature builds).
