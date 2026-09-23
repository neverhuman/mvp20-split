# RETRACTION INDEX -- amphora-molecule-generator

Append-only record of published claims that were refuted by a signed falsification
receipt and subsequently superseded by a signed corrected receipt. Superseded
artifacts are NEVER deleted or modified; they remain byte-intact on disk and are
listed here with the receipt that refutes them and the receipt that replaces them.

## R-A06 -- 2026-08-03 (repair_mode: interactive-2026-08-03)

Superseding receipt (all three rows):
`amphora-molecule-generator/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json`

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `molgen-deterministic-grammar-yield-v1`: feasible_fraction bootstrap 95% CI = [1.0000, 1.0000] at k=n=38. **Corrected to exact Clopper-Pearson [0.9075, 1.0000]** (percentile bootstrap is degenerate at the all-success boundary; 0.0925 lower-bound gap exceeds the a-priori 0.02 admissibility threshold). | `amphora-molecule-generator/evidence/audit/molgen-grammar-yield-bootstrap-ci-inadmissibility-v1/molgen-grammar-yield-ci-inadmissibility-receipt.v1.dsse.json` | `amphora-molecule-generator/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json` | 2026-08-03 |
| `molgen-deterministic-grammar-yield-v1`: "38 valid-unique-difunctional-feasible hardener proposals" (yield 38/38). **Corrected to 29/38** -- 9 proposals flagged `difunctional_hardener=true` carry 3-9 amine sites (homopiperazine-N,N' 3, piperazine-bis(aminoethyl)/AEP 3, DETA 3, TETA 4, TEPA 5, PEHA 6, ethyleneamine-k6 7, -k7 8, -k8 9); the gate did not implement its own stated definition `amine_sites==2`. Structures unchanged. | `amphora-molecule-generator/evidence/audit/molgen-hardener-functionality-mislabel-v1/molgen-hardener-functionality-mislabel-receipt.v1.dsse.json` | `amphora-molecule-generator/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json` | 2026-08-03 |
| `molgen-scaffold-diversity-v1`: hypothesis_evaluation verdict CORROBORATED_IN_AUDIT_INSTRUMENT on aggregate IntDiv_1 = 0.7681 ("not trivially inflated variants of a single scaffold"). **Corrected to family-resolved: cross-family diversity is real (homolog-bloc vs ring mean Tanimoto 0.1054), but within-family homolog series are near-degenerate** -- F1_polyethyleneamine IntDiv_1 = 0.1851 and F2_alpha_omega_diamine IntDiv_1 = 0.0870 over 47.4% of the accepted set, with 12/16 chain-adjacent pairs saturated at Tanimoto >= 0.99. | `amphora-molecule-generator/evidence/audit/molgen-scaffold-diversity-homolog-fingerprint-saturation-v1/molgen-scaffold-diversity-homolog-fingerprint-saturation-receipt.v1.dsse.json` | `amphora-molecule-generator/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json` | 2026-08-03 |

Superseded originals (verified byte-intact, NOT deleted or modified):

- `amphora-molecule-generator/evidence/audit/molgen-deterministic-grammar-yield-v1/molgen-deterministic-grammar-yield-receipt.v1.dsse.json`
  sha256 `a7bedf57ece42bee60fabb4a1b7069a205b1297735356f21cc4e71dc64c98b0a`
- `amphora-molecule-generator/evidence/audit/molgen-scaffold-diversity-v1/molgen-scaffold-diversity-receipt.v1.dsse.json`
  sha256 `f74b5bcc37eb4306109984178e305d3aa84b4d4f24527d5a984f32125cff9fb7`

Scope: AUDIT_ONLY. No authority promoted, no scientific_readiness flipped, no manifest,
ledger, mission front-matter, or locked dataset touched. The 38 accepted structures
themselves are unchanged -- these are interval, label, and resolution corrections.

## R-A06v2 -- 2026-08-04 (repair_mode: interactive-2026-08-04)

Superseding receipt:
`amphora-molecule-generator/evidence/phase0/repairs/R-A06v2/done/molgen-r-a06v2-functionality-convention-repair-receipt.v1.dsse.json`
sha256 `985d4aeb3effd6f9c8ffbc04b647b4ff8e283b785346e355e59741739a306f2f`

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `R-A06`: "29/38 valid-unique-**DIFUNCTIONAL**-feasible hardener proposals", where the gate used was `amine_sites == 2` (a count of nitrogen ATOMS). **Corrected: 0 of 38 are difunctional under the active-hydrogen functionality convention (`active_NH == 2`), and 29 of 38 have exactly 2 amine CENTRES (they are primary,primary diamines) with `active_NH == 4`, i.e. TETRAfunctional.** The arithmetic R-A06 published is not disputed -- the independent verify reproduced it exactly -- only the word "difunctional". Structures unchanged. | `amphora-molecule-generator/evidence/phase0/repairs/V-A06/done/v-a06-molecule-generator-repair-verify-receipt.v1.dsse.json` (verdict CLAIM_REFUTED; measured `n_amine_sites2_but_active_nh_ne_2` = 29 of 29 and `n_true_difunctional_active_h_eq_2_among_all_38` = 0) | `amphora-molecule-generator/evidence/phase0/repairs/R-A06v2/done/molgen-r-a06v2-functionality-convention-repair-receipt.v1.dsse.json` | 2026-08-04 |

Portfolio convention fixed by this repair: the word **"difunctional"** means `active_NH == 2`
(active-hydrogen count), never `amine_sites == 2` (nitrogen-atom count). The active-hydrogen
count is what AHEW is defined as (`AHEW = M / n_activeH`, Lee & Neville 1967), what the mix
ratio is computed from (`phr = 100 * AHEW / EEW`) and what Flory-Stockmayer takes as the
network functionality `f`; the nitrogen-atom count enters only the ASTM D2074 amine value and
sets no stoichiometry. For a primary,primary diamine the two differ by exactly 2x, so
confusing them doubles the hardener mix ratio. The 2-amine-centre subset should be called
**"diamines"**, never "difunctional".

Instrument validated before any count was asserted, against this module's own in-tree ground
truth `amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json`
(sha256 `b1a08e856cab233c69c09673ed0d96a40c38346753afae4ad415b5948edaa9a8`, cites Lee & Neville
1967): 8/8 `known_answer_amines` reproduced on BOTH conventions (`expected_active_nh` and
`expected_basic_n`), 6/6 `fail_closed_decoys` reproduced. Two mutually-independent RDKit
implementations (explicit per-atom rule loop; SMARTS query) agree on all 38 proposals and on
the whole ground-truth set.

Not superseded, carried forward re-derived: R-A06's exact Clopper-Pearson feasible-fraction
interval [0.9075, 1.0000] and its family-resolved IntDiv_1 diversity table -- V-A06
reproduced both exactly and R-A06v2 reproduces them again.

Superseded original (verified byte-intact, NOT deleted or modified):

- `amphora-molecule-generator/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json`
  sha256 `89fc28d21f7224743a6e0a1d2a0750055058e6167e038eee7a65b90145ea4b52`

Scope: AUDIT_ONLY, ceiling EVIDENCE_ONLY. No authority promoted, no scientific_readiness
flipped, no manifest, ledger, mission front-matter, or locked dataset touched. The 38 accepted
structures are unchanged -- this is a label/convention correction. All 38 remain valid, unique,
SA-feasible and network-forming (`active_NH >= 3`).

