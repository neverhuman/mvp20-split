# RETRACTION INDEX — amphora-molecule-novelty

## R-A07 (repair_mode interactive-2026-08-03)

| Claim | Refuted-by receipt path | Superseded-by | Date |
|---|---|---|---|
| DDS cross-family novelty count at alpha=0.05 is 1/4 (maccs_166 only), computed on a 443-row calibration corpus treated as exchangeable (`evidence/audit/cross-family-concordance-v1/cross-family-concordance-receipt.v1.dsse.json`, sha256 `c2498d0590b04786955e5d2269e112862bdccc1522a6dafe3dccf3049c3ad9ab`) | `evidence/audit/corpus-duplicate-exchangeability-audit-v1/corpus-duplicate-exchangeability-receipt.v1.dsse.json` (corpus has only 350 canonically-unique structures; 129 dup rows / 36 alias groups; 5 signed family/alpha cells flip; DDS true count 0/4) | `evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json` | 2026-08-03 |
| IPDA candidate_smiles `CC1(CC(CC(C1)N)C)CN` in the Phase-0 Tanimoto-NN novelty KPI represents isophorone diamine (`evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json`, sha256 `55f8c96c957c8f5ee41aa76ad65d4ddf938a7d705ed522acffe168b512137d25`) | `evidence/audit/candidate-structure-identity-audit-v1/candidate-structure-identity-audit-receipt.v1.dsse.json` (string canonicalizes to C9H20N2, a demethylated homolog; real isophorone diamine is CAS 2855-13-2, C10H22N2) | `evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json` (corrected canonical `CC1(C)CC(N)CC(C)(CN)C1`; recomputed NN 0.16666666666666666 vs deduped corpus, still NOVEL < 0.40) | 2026-08-03 |

Both superseded artifacts remain byte-intact (supersede-never-rewrite). Top-level result under both corrections: 5/5 NOVEL stands; exchangeability precondition now satisfied on the deduplicated 350-structure corpus (dedup set sha256 `74513e30071335d097ee83315f5b21249da86ea6a5d61e98a27d07b631593dce`).

## V-A07 independent verify of R-A07 (2026-08-04)

R-A07's own `corrected_family_alpha_table_deduped_350` applies the dedup correction to all four fingerprint families, but applies the IPDA structural correction (C9H20N2 to real isophorone diamine C10H22N2) only inside a separate morgan_r2_2048-only side table (`top_level_five_over_five_corrected`). Independent reimplementation propagating the corrected IPDA structure into maccs_166, atompair_2048, and toptorsion_2048 as well surfaces one additional, undisclosed cell flip: `atompair_2048 / IPDA / alpha=0.01` goes from shipped NOVEL=False to true NOVEL=True. R-A07's claim that its shipped family/alpha table is corrected "under both corrections" is false for those three families. The top-level 5/5-NOVEL headline is unaffected. See `evidence/phase0/repairs/V-A07/done/v-a07-independent-verify-of-r-a07-receipt.v1.dsse.json` (verdict CLAIM_REFUTED). R-A07 itself is left byte-intact (supersede-never-rewrite); a follow-up repair item is needed to propagate the IPDA structural fix into all four families of the shipped table.
## R-A07v2 -- 2026-08-04 (repair_mode: interactive-2026-08-04)

Superseding receipt:
`evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json`
sha256 `45b75c2a1a534d6ec0667e55e5ad130ecaa66bdaa60bb5cd12088a1af694328e`

| Claim | Refuted-by receipt path | Superseded-by | Date |
|---|---|---|---|
| `R-A07`: `corrected_family_alpha_table_deduped_350` is "recomputed ... under both corrections". **False for three of the four fingerprint families**: the IPDA structural correction (C9H20N2 to real isophorone diamine C10H22N2) was applied only inside a separate `morgan_r2_2048`-only side table, so the `maccs_166` / `atompair_2048` / `toptorsion_2048` IPDA cells of the shipped table were still computed on the refuted structure. **Corrected: the complete four-family table is republished with the corrected structure in every family, and the one undisclosed flip it surfaces -- `atompair_2048 / IPDA / alpha=0.01`, conformal p 0.011396 to 0.008547, NOVEL false to true -- is disclosed.** | `evidence/phase0/repairs/V-A07/done/v-a07-independent-verify-of-r-a07-receipt.v1.dsse.json` (verdict CLAIM_REFUTED; 11/11 self-tests passed and R-A07's 5 declared flip cells reproduced before the defect was found) | `evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json` | 2026-08-04 |

**The top-level 5/5-NOVEL headline STANDS.** All 5 candidates remain below the 0.40
Bajusz-Racz-Heberger Morgan(r2,2048) Tanimoto cutoff on the deduplicated 350-distinct corpus
with the corrected structure (NN range 0.1579-0.3929), and the IPDA structural fix leaves the
Morgan nearest-neighbour similarity numerically unchanged at 0.16666666666666666 -- the
headline never depended on any defective cell.

Complete flip disclosure published in the v2 receipt (four difference sets, so no flip can
hide in a comparison that was never made):

- **A** dedup effect, old structure (R-A07's declared set, reproduced exactly): **5** cells --
  `maccs_166/DDS/a0.05`, `maccs_166/IPDA/a0.01`, `atompair_2048/DDS/a0.2`,
  `atompair_2048/IPDA/a0.01`, `atompair_2048/m-XDA/a0.01`.
- **B** structural effect, undisclosed by R-A07, found by V-A07: **1** cell --
  `atompair_2048/IPDA/a0.01` (NOVEL false to true).
- **C** net, originally-signed to fully-corrected: **4** cells. `atompair_2048/IPDA/a0.01`
  appears in both A and B and therefore cancels in the net view -- two independent errors
  offset -- so it is disclosed in A and B regardless.
- **D** dedup effect isolated under correct chemistry: **4** cells.

Constructive reproduction of V-A07's diagnosis: all 20 cells of R-A07's shipped four-family
table reproduce exactly when the OLD, refuted C9H20N2 string is used in every family.
Isophorone diamine was re-derived a third independent way (`NCC1(C)CC(N)CC(C)(C)C1`, written
from the exocyclic aminomethyl carbon) and pinned to the in-tree ground truth
`amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json`
(sha256 `b1a08e856cab233c69c09673ed0d96a40c38346753afae4ad415b5948edaa9a8`).

Not superseded, carried forward reproduced exactly: the 443 to 350 canonical deduplication
(36 duplicate groups / 129 duplicate rows, dedup-set sha256
`74513e30071335d097ee83315f5b21249da86ea6a5d61e98a27d07b631593dce`), R-A07's 5 declared flip
cells, its DDS cross-family count 0/4 at alpha=0.05, and its top-level 5/5-NOVEL result.

Superseded original (verified byte-intact, NOT deleted or modified):

- `evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json`
  sha256 `72496a149815075618fd22b4e6fc60cae4953d81f7100a67b394b01b59583198`

Scope: AUDIT_ONLY, ceiling EVIDENCE_ONLY. No authority promoted, no scientific_readiness
flipped, no manifest, ledger, mission front-matter, or locked dataset touched.



## W-NOV1 -- independent re-verification and campaign closure of R-A07v2 (2026-08-05)

R-A07v2 (above) was correctly computed and DSSE-signed on 2026-08-04 but the fire that
produced it never appended a falsification-ledger line and never published under a
campaign-item path, so it was orphaned relative to campaign item W-NOV1 (whose
`done_check` looks under `evidence/phase0/repairs/W-NOV1/done/`). No re-derivation was
needed -- R-A07v2 already fully discharges W-NOV1's objective (all four fingerprint
families, corrected IPDA structure, every flip disclosed, headline stands) -- so this
fire independently re-attacked it per repair-mode rule 2 (fresh RDKit reimplementation
from scratch, fresh DSSE signature verification against the pinned trust-store key,
fresh chain byte-intactness check) rather than re-deriving it.

Verdict: **CLAIM_SURVIVED**. All 20 shipped (family, candidate) cells reproduced exactly
after fixing a bug in this re-verification's OWN leave-one-out code (it initially
excluded corpus self-points by display Name rather than corpus index; the 350
canonically-distinct structures contain 6 duplicate-name groups -- chitosan, cellulose,
polyimide, starch, polylactide, poly(alpha-methylstyrene) -- each spanning two genuinely
distinct structures, so name-based exclusion wrongly dropped a valid neighbour in 2 of 20
cells before the fix; R-A07v2's own `calib_alphas` was already correctly index-based).
DSSE signature independently verified against the pinned Phase-0 evaluator key. Receipt:
`evidence/phase0/repairs/W-NOV1/done/w-nov1-done-receipt.v1.dsse.json`.

R-A07v2 remains the operative superseding artifact; nothing about it was found wrong or
re-signed. This entry documents closure of the campaign item that tracks it.

## OPEN FINDING (not yet repaired) -- citation-provenance-threshold-source-v1 (2026-08-14)

**Claim under attack:** `evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json`
and its underlying scientific receipt
`reference/mvp20/data/tanimoto_nn_novelty_of_canonical_epoxy_amines_against_openpoly_receipt.v1.json`
declare `"threshold_source": "Bajusz-Rácz-Héberger 2015 J. Cheminform."` as the published
basis for the 0.40 (novel/weakly-similar), 0.55 (moderately similar), and 0.75 (highly
similar) Tanimoto novelty-classification cutoffs. This citation is inherited unmodified
by every downstream audit and repair receipt in this module (14 files grep-match
"Bajusz": both root artifacts, RETRACTION-INDEX.md itself, and 12 audit/repair scripts).

**Attack:** fetched the actual cited paper (DOI `10.1186/s13321-015-0069-3`, Bajusz D,
Rácz A, Héberger K, *J Cheminform* 2015;7:20; identity confirmed via NCBI's ID Converter
API resolving that exact DOI to PMCID PMC4456712 / PMID 26052348) and searched its full
text for "threshold", "cutoff", "weakly similar", "moderately similar", "highly similar",
and the values 0.85/0.75/0.55/0.40. Verified the fetch was real article content (not a
bot-challenge page) via topic-anchor terms (`SRD` 79 hits, `Soergel` 18, `Dice` 15,
`Sum of ranking differences` 18). Ran the identical detector against a copy with a
synthetic threshold sentence planted, confirming the detector fires when a threshold
scheme is actually present.

**Result:** ZERO hits for "threshold", "cutoff", "weakly similar", "moderately similar",
or the values 0.85/0.75/0.55/0.40 anywhere in the cited paper. The paper is a comparative
study of similarity/distance metrics (Tanimoto vs Dice vs Cosine vs Soergel vs 4 others)
ranked by Sum-of-Ranking-Differences and ANOVA -- it does not propose or discuss any
Tanimoto similarity-value classification scheme. The `threshold_source` citation is
fabricated / unsupported attribution.

**Scope:** this does NOT contest the raw NN-Tanimoto values (0.1579-0.3929), independently
re-derived correct 6 times by prior fires (see R-A07/V-A07/R-A07v2/W-NOV1/V-A07v2 entries
above) -- only the literature provenance of the numeric boundaries that turn those values
into NOVEL/not-NOVEL verdicts.

Verdict: **CLAIM_REFUTED** (scoped to citation provenance). Receipt:
`evidence/audit/citation-provenance-threshold-source-v1/citation-provenance-threshold-source-receipt.v1.dsse.json`.

**Not yet repaired.** No corrected threshold_source or re-derived cutoff is proposed by
this entry. A follow-up R- campaign item should either (a) locate the real published
source for a 0.40/0.55/0.75-style Tanimoto novelty-classification scheme (candidates to
check: Martin et al. 2002 "neighborhood behavior" ~0.85 similar-activity threshold
literature, or Willett-Barnard-Downs 1998 already cited alongside Bajusz in this same
KPI's `theory` list) and re-cite correctly, or (b) drop the specific-paper attribution and
document the thresholds as an internal, uncited convention pending a real source. Neither
KPI, scientific receipt, nor any prior audit/repair receipt is modified by this entry
(supersede-never-rewrite; nothing here is a supersession, only a new open finding).


## OPEN FINDING (not yet repaired) -- conformal-novelty-significance-reattack-v1 (2026-08-16)

**Claim under attack:** the still-live, un-superseded KPI
`evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json`
metric `all_candidates_classified_novel_below_0_40_threshold` (`observed:5, passed:true`)
and capability text `"REAL FINDING: 5/5 candidates classified NOVEL"`. Both rest entirely on
the fixed `novel_T_lt: 0.4` Tanimoto cutoff whose sole cited authority
(`threshold_source: "Bajusz-Rácz-Héberger 2015 J. Cheminform."`) was independently shown to
be fabricated/unsupported by the prior open finding immediately above
(citation-provenance-threshold-source-v1, 2026-08-14, still not yet repaired).

**Attack:** an unledgered, byte-stable DSSE receipt already existed in-tree
(`evidence/audit/conformal-anomaly-detection-v1/conformal-anomaly-detection-receipt.v1.dsse.json`)
that reframed novelty as Vovk-Gammerman-Shafer 2005 conformal anomaly detection, calibrated
directly on the SHA-locked reference corpus's own leave-one-out NN-Tanimoto distribution
(no borrowed/unsupported threshold), and found DDS does not clear alpha=0.05 significance
-- but that receipt was never appended to `logs/falsification-ledger.jsonl` and so was never
mechanically credited under any fire (same orphaning failure mode previously seen and
closed for R-A07v2 under campaign item W-NOV1). This fire independently reproduced the
computation from scratch (own CSV loader, own Morgan(r2,2048)/Tanimoto featurization, own
LOO nonconformity calibration, own conformal p-value code in two different valid formula
conventions -- smoothed VGS2005-sec-2.3 and strict rank-fraction), using the R-A07v2-corrected
IPDA structure throughout, and formally ledgers the result. Anchor check: this
reimplementation reproduces the signed KPI's own DDS/DETA/TETA/m-XDA NN-Tanimoto values to
0 absolute error before any conformal layer is applied. Positive control: a synthetic
"candidate" built from an exact byte-identical corpus duplicate correctly scores
nonconformity 0.0 / conformal p 1.0 / non-novel at every alpha, confirming the detector
discriminates rather than trivially calling everything novel.

**Result:** under BOTH tested conformal p-value conventions, DDS (fixed-cut NN Tanimoto
0.392857, only 0.0071 below the now-unsupported 0.40 cut) fails to reach the standard
alpha=0.05 significance level (smoothed p=0.11486, strict p matches the same qualitative
conclusion). The other 4 candidates (IPDA, DETA, TETA, m-XDA) all reach significance at
alpha=0.05 (p <= 0.0225 in every case). So the defensible, distribution-free statement this
corpus actually supports is **4/5 NOVEL at alpha=0.05, not 5/5** -- the fixed KPI headline
is an artifact of an unsupported borrowed threshold, not a robust finding.

**Scope:** this does NOT contest the raw NN-Tanimoto values themselves (already re-derived
correct many times over; anchor error 0.0 here too) -- only whether the flat 5/5-NOVEL
verdict the KPI signs off on survives replacing the fabricated-citation fixed cut with a
real distribution-free significance test calibrated on the module's own reference corpus.

Verdict: **CLAIM_REFUTED**. Receipt:
`evidence/audit/conformal-novelty-significance-reattack-v1/conformal-novelty-significance-reattack-receipt.v1.dsse.json`.

**Not yet repaired.** No corrected KPI headline is proposed by this entry
(supersede-never-rewrite; nothing here is a supersession, only a new ledgered open
finding). A follow-up R- campaign item should either (a) re-badge the KPI headline as
"4/5 NOVEL at alpha=0.05 (conformal, distribution-free); 5/5 below an internal 0.40
convention" and flag DDS as the disclosed borderline case, or (b) locate a real citable
source for a defensible fixed threshold (see the still-open candidates listed in the
citation-provenance-threshold-source-v1 entry above) and re-run this same conformal
cross-check against it. Neither KPI, scientific receipt, nor any prior audit/repair
receipt is modified by this entry.


## OPEN FINDING (not yet repaired) -- chebi-truthset-second-corpus-v1 (2026-08-17)

**Claim under attack:** the still-live, un-superseded KPI
`evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json`
headline `"REAL FINDING: 5/5 candidates classified NOVEL"` (NN Tanimoto < 0.40 vs the
350-distinct OpenPoly polymer corpus), and by extension the 2026-08-13 W-D-NOV SURVIVED
verdict that this headline is robust to a second reference corpus (PolyInfo, another
polymer repeat-unit corpus).

**Attack:** re-tested the same 5 canonical candidates (IPDA, DDS, DETA, TETA, m-XDA)
against a categorically different, rights-clean, already in-tree reference corpus never
previously used by this module: ChEBI release-252 3-star curated small-molecule entities
(`amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.sdf.gz`, SHA-256-pinned,
CC-BY-4.0, `rights_class: DERIVATIVE_ALLOWED`; 52,806 parsed / 50,383 canonically-distinct
structures). Identical Morgan(r2,2048)/Tanimoto featurization to the signed KPI, plus an
InChIKey-skeleton exact-identity cross-check as a threshold-independent second line of
evidence. Anchor check: OpenPoly-only NN-Tanimoto values reproduced to 0 absolute error
for all 5 candidates before the ChEBI comparison was added. Fully deterministic pipeline
(SHA-256-pinned inputs, no RNG); two independent process replays produced byte-identical
diagnostic JSON.

**Result:** 4 of 5 candidates flip from NOVEL to NOT-NOVEL under the union of
OpenPoly-350 and ChEBI-dedup:
- **DDS**: NN Tanimoto 0.3929 (OpenPoly) -> **1.0** vs ChEBI (exact InChIKey-skeleton
  match to `CHEBI:4325`, 4,4'-sulfonyldianiline).
- **DETA**: 0.1667 -> **1.0** (exact match to `CHEBI:30629`, diethylenetriamine).
- **TETA**: 0.1579 -> **1.0** (exact match to `CHEBI:39501`, triethylenetetramine).
- **m-XDA**: 0.2381 -> **0.7059** vs `CHEBI:40538` (benzylamine) -- above the 0.40 cut,
  though not an exact skeleton match.
- **IPDA** alone survives: 0.1667 -> 0.3548 vs ChEBI, still below 0.40.

DDS, DETA, and TETA are not merely "close to" a known structure -- by InChIKey-skeleton
identity they ARE already-cataloged ChEBI chemical entities. This is a threshold-
independent, categorical result, not a borderline-cutoff argument.

**Why this is a harder test than the prior second-corpus attack (W-D-NOV, SURVIVED):**
PolyInfo, like OpenPoly, contains only capped polymer repeat-unit fragments -- structurally
incapable of representing a discrete small-molecule commodity chemical as itself. ChEBI is
a curated database of real, discrete small-molecule entities: the correct-shaped corpus to
catch "this candidate is already a cataloged known compound," which a polymer-fragment
corpus cannot catch by construction.

**Scope:** does NOT contradict the KPI's own written claim_locks, which already disclaim
`reference_corpus_is_openpoly_only_not_a_comprehensive_prior_art_search` and
`novelty_is_scaffold_and_fingerprint_similarity_only_not_novelty_in_uspto_sense`. It
refutes the informally-relied-upon "5/5 NOVEL" headline as a generalizable claim, the same
way W-D-NOV's own refutation_criterion was designed to test -- using a corpus shaped to
catch this specific failure mode. Does not contest the raw OpenPoly-only NN-Tanimoto values
(anchor-reproduced exactly). Does not modify the KPI or any prior receipt (supersede-never-
rewrite; this is a new open finding).

Verdict: **CLAIM_REFUTED**. Receipt:
`evidence/audit/chebi-truthset-second-corpus-v1/chebi-truthset-second-corpus-receipt.v1.dsse.json`.

**Not yet repaired.** This is the THIRD unrepaired open finding against the same KPI
(alongside citation-provenance-threshold-source-v1, 2026-08-14, and
conformal-novelty-significance-reattack-v1, 2026-08-16). A follow-up R- campaign item
should retire the flat "5/5 NOVEL" headline entirely and replace it with a per-candidate,
per-corpus disclosure: IPDA is the only candidate that is novel by NN-Tanimoto against
every corpus tested so far; DDS/DETA/TETA are literal cataloged small molecules by
InChIKey identity once a small-molecule reference corpus is in scope, and m-XDA is close
(0.71) to a cataloged small molecule. None of this resolves USPTO/EPO patentability or
FTO, which the KPI already and correctly disclaims it does not attempt.


## OPEN FINDING (not yet repaired) -- ipda-structural-correction-propagation-chebi-v1 (2026-08-18)

**Claim under attack:** the still-open, unrepaired `chebi-truthset-second-corpus-v1`
(2026-08-17) finding's specific reported figure for candidate IPDA: NN Tanimoto vs
ChEBI-dedup `0.354838...`, cited as the basis for "IPDA alone survives" novelty across
every corpus tested so far.

**Defect found:** `chebi-truthset-second-corpus-v1`'s own `CANDS['IPDA']` hard-codes
`CC1(CC(CC(C1)N)C)CN` -- byte-identical to the C9H20N2 demethylated structure that
`candidate-structure-identity-audit-v1` (2026-08-03) showed is NOT real isophorone
diamine, and which R-A07v2's `corrected_ipda` block explicitly records as
`superseded_smiles`/`superseded_formula: "C9H20N2"`. Five prior fires (R-A07, V-A07,
R-A07v2, W-NOV1, V-A07v2) established the `v2_canonical` corrected structure
`CC1(C)CC(N)CC(C)(CN)C1` (C10H22N2, CAS 2855-13-2) as authoritative going forward. The
2026-08-17 fire copied IPDA's SMILES from the signed KPI's own (correctly never-edited)
`candidate_smiles` field instead of the retraction-index-recorded correction -- the same
undisclosed-non-propagation failure mode V-A07 found in R-A07, recurring in a brand-new
analysis fourteen days after the fix was established as load-bearing precedent.

**Attack:** independently re-derived IPDA's NN Tanimoto against the identical SHA-256-
pinned ChEBI-dedup corpus (50,383 structures) and OpenPoly-350 corpus used by
`chebi-truthset-second-corpus-v1`, using the correct R-A07v2 `v2_canonical` structure.
Ran a companion `--mutate` self-check (both compared slots forced to the identical wrong
structure) to confirm the wrong-vs-correct diff machinery reports a null result
(delta=0.0) when there is genuinely nothing to detect, rather than vacuously always
firing. Two-replay byte-stability gate passed on the canonical run.

**Result:** correct-structure NN Tanimoto vs ChEBI-dedup is `0.333333` (not
`0.354838`), delta -0.021505. `novel_vs_chebi_dedup=True` under both the wrong and
correct structure (still well below the 0.40 cut); no InChIKey-skeleton match appears
or disappears. **No material flip** -- the correct structure is, if anything, farther
from any ChEBI entry, not closer. OpenPoly-only anchor value confirmed numerically
unchanged (`0.16666666666666666`), matching R-A07v2's own prior finding for that corpus.

**Scope:** this is a provenance/propagation defect in one specific reported number
inside an already-open finding, not a new novelty flip. It does NOT reverse
`chebi-truthset-second-corpus-v1`'s own `CLAIM_REFUTED` verdict against the KPI's
5/5-NOVEL headline (DDS/DETA/TETA/m-XDA results are untouched -- none of those
candidates has ever had a structural correction issued). It does NOT modify the KPI,
R-A07v2, or `chebi-truthset-second-corpus-v1` (supersede-never-rewrite; this is a new
open finding layered on an existing open finding).

Verdict: **CLAIM_REFUTED** (scoped to the specific reported IPDA-vs-ChEBI figure and its
input structure). Receipt:
`evidence/audit/ipda-structural-correction-propagation-chebi-v1/ipda-structural-correction-propagation-chebi-receipt.v1.dsse.json`.

**Not yet repaired.** This is now the FOURTH unrepaired open finding touching the same
KPI lineage (alongside citation-provenance-threshold-source-v1 2026-08-14,
conformal-novelty-significance-reattack-v1 2026-08-16, and
chebi-truthset-second-corpus-v1 2026-08-17). A follow-up R- campaign item that retires
the flat "5/5 NOVEL" headline should use IPDA-vs-ChEBI = `0.333333` (not `0.354838`) as
the correct per-candidate, per-corpus figure, and should audit whether any other still-
open finding in this module reused a candidate SMILES string sourced from the signed
KPI rather than from the retraction-index-recorded corrections.
