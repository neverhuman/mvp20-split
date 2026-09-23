# amphora-sourceability-ehs RETRACTION INDEX

Refuted claims in signed artifacts of this module, the refuting receipt, and the superseding correction. Superseded artifacts are kept byte-intact; nothing is rewritten.

## R-A04 (2026-08-03) - toluene OSHA table attribution corrected Z-1 -> Z-2

| claim | refuted-by receipt | superseded-by | date |
|---|---|---|---|
| toluene PEL 'OSHA Table Z-1' in kpis.pel_denominator_source + solvent_cards_ranked[toluene] (in reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json; superseded byte-intact, toluene is Table Z-2: TWA 200 ppm + ceiling 300 ppm + peak 500 ppm/10 min, numerics unchanged) | reference/mvp20/data/osha_table_z1_z2_attribution_audit_receipt.v1.json (+ kpi: evidence/phase0/kpis/osha-table-z1-z2-attribution-audit-kpi.v1.json) | evidence/phase0/repairs/R-A04/done/r-a04-osha-table-z2-attribution-correction-receipt.v1.dsse.json | 2026-08-03 |
| toluene PEL 'OSHA Table Z-1' in kpis.solvent_envelopes[toluene].osha_pel_table_z1_name (in reference/mvp20/data/vhr_temperature_envelope_inhalation_prescreen_receipt.v1.json; superseded byte-intact, toluene is Table Z-2: TWA 200 ppm + ceiling 300 ppm + peak 500 ppm/10 min, numerics unchanged) | reference/mvp20/data/osha_table_z1_z2_attribution_audit_receipt.v1.json (+ kpi: evidence/phase0/kpis/osha-table-z1-z2-attribution-audit-kpi.v1.json) | evidence/phase0/repairs/R-A04/done/r-a04-osha-table-z2-attribution-correction-receipt.v1.dsse.json | 2026-08-03 |
| all mixture PEL denominators 'OSHA Table Z-1' in kpis.pel_denominator_source (in reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json; superseded byte-intact, toluene is Table Z-2: TWA 200 ppm + ceiling 300 ppm + peak 500 ppm/10 min, numerics unchanged) | reference/mvp20/data/osha_table_z1_z2_attribution_audit_receipt.v1.json (+ kpi: evidence/phase0/kpis/osha-table-z1-z2-attribution-audit-kpi.v1.json) | evidence/phase0/repairs/R-A04/done/r-a04-osha-table-z2-attribution-correction-receipt.v1.dsse.json | 2026-08-03 |

## R-A12 reinstatement of launcher-discarded fires (interactive-2026-08-03)

Retracted claim: the four signed artifacts below carry a portfolio-valid DSSE signature. They were
in fact signed with the unanchored LOCAL_DEVELOPMENT_AUDIT_ONLY key `local-9028773f49591193`, so
the launcher verifier discarded both fires (verified_new_signed=0, verdicts downgraded to UNKNOWN).
The SCIENCE of both audits was re-executed and reproduced the committed canonical diagnostics
byte-exact; the original verdicts (REFUTED for the OSHA Z1/Z2 attribution audit, CLAIM_SURVIVED
for the VHR cross-method temperature-envelope audit) are reinstated under the pinned
PHASE0_EVALUATOR key.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `reference/mvp20/data/osha_table_z1_z2_attribution_audit_receipt.v1.json` (sha256 `1001f14d...`) is signed under a trust-anchored Phase-0 key; fire 20260802T170001-3280844-63859af6dae2 REFUTED verdict (toluene is OSHA Table Z-2, not Z-1) is portfolio-verifiable as signed | amphora-sourceability-ehs/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json (documents the wrong-key defect) | amphora-sourceability-ehs/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json (anchored re-issue; REFUTED verdict reinstated, re-attack byte-exact) | 2026-08-03 |
| `evidence/phase0/kpis/osha-table-z1-z2-attribution-audit-kpi.v1.json` (sha256 `47863834...`) is signed under a trust-anchored Phase-0 key | same batch receipt (KPI->receipt payload sha binding verified intact) | amphora-sourceability-ehs/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json | 2026-08-03 |
| `reference/mvp20/data/vhr_temperature_envelope_crossmethod_audit_receipt.v1.json` (sha256 `d9f34de8...`) is signed under a trust-anchored Phase-0 key; fire 20260803T050002-2025413-7726cab611c9 SURVIVED verdict is portfolio-verifiable as signed | amphora-sourceability-ehs/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json (documents the wrong-key defect) | amphora-sourceability-ehs/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json (anchored re-issue; CLAIM_SURVIVED verdict reinstated, re-attack byte-exact) | 2026-08-03 |
| `evidence/phase0/kpis/vhr-temperature-envelope-crossmethod-audit-kpi.v1.json` (sha256 `f3a379ee...`) is signed under a trust-anchored Phase-0 key | same batch receipt (KPI->receipt payload sha binding verified intact) | amphora-sourceability-ehs/evidence/phase0/repairs/R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json | 2026-08-03 |

Original artifacts left byte-intact in place (supersede-never-rewrite); before/after sha256 recorded in the batch receipt payload.

## R-N01 fire 1 (2026-08-03) - GHS/CLP CID-attribution audit re-banked under pinned key

Ledger divergence: fire 20260803T210001-26108-aa59817794da (2026-08-03T21:08:14Z) recorded verdict
REFUTED for this attack, but its declared artifact was signed with the unanchored
LOCAL_DEVELOPMENT_AUDIT_ONLY key `local-9028773f49591193`, so the launcher verifier discarded it
(verified_new_signed=0, downgraded to UNKNOWN) -- the finding was never portfolio-verifiable even
though the ledger text still reads REFUTED. This fire independently re-derived the same audit from
freshly-fetched (not copied) live PubChem PUG-REST/PUG-View data and signed it under the pinned
PHASE0_EVALUATOR key. Same finding reproduced: 2/5 candidates (IPDA, m-XDA) cite a PubChem CID that
resolves to a chemically unrelated substance. Fire scope is the audit re-bank only (campaign item
R-N01 FIRE 1 of 3); the superseding hazard-card receipt with CAS-correct CIDs and re-evaluated
procurement gates is deferred to a later fire of the same campaign item, so this receipt is filed
under `attempts/`, not `done/`.

| claim | refuted-by receipt path (unbanked) | superseded-by (properly banked) | date |
|---|---|---|---|
| `reference/mvp20/data/ghs_clp_cid_attribution_audit_receipt.v1.json` (sha256 `76a80a0d...`) is signed under a trust-anchored Phase-0 key | fire 20260803T210001-26108-aa59817794da (ledger REFUTED, but wrong-key signed, never portfolio-verifiable) | amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/attempts/r-n01-fire1-ghs-clp-cid-attribution-audit-rebank-receipt.v1.dsse.json | 2026-08-03 |
| `evidence/phase0/kpis/ghs-clp-cid-attribution-audit-kpi.v1.json` (sha256 `b480634a...`) is signed under a trust-anchored Phase-0 key | same defect (sibling KPI, same wrong key) | amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/attempts/r-n01-fire1-ghs-clp-cid-attribution-audit-rebank-receipt.v1.dsse.json | 2026-08-03 |

Original artifacts left byte-intact in place (supersede-never-rewrite); before/after sha256 recorded
in the new receipt's `supersedes` block. The audited hazard-card receipt/KPI
(`ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json` and its KPI) were
corrected by R-N01 fire 2 below.

## R-N01 fire 2 (2026-08-04) - superseding hazard-card correction, CAS-correct CIDs

Closes the correction deferred by fire 1 above. Independent fresh live fetch (2026-08-04, both
PUG-REST CAS->CID and PUG-View CID->GHS Classification endpoints) reproduced fire 1's CID
resolution exactly (IPDA claimed CID 6944 -> correct 17857; m-XDA claimed CID 15642 -> correct
15133; DDS/DETA/TETA CIDs already correct, unchanged). Corrected the two affected cards' PubChem
citation and PubChem-sourced H-statement codes to the CAS-correct CID's own live aggregate.
**Headline result: m-XDA's H334 (respiratory sensitiser) gate FALLS against the correct record** —
H334 is absent from CID 15133's own aggregated GHS Classification, and also absent from the
wrongly-cited CID 15642's own aggregate, so it traced to neither citation. Of the 5 candidates,
only m-XDA's procurement gate changes: `RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED` ->
`CORROSIVE_PPE_PLAN_REQUIRED` (H314 still present). IPDA's gate is unchanged
(`CORROSIVE_PPE_PLAN_REQUIRED`, H314 still present at the correct CID) despite its own CID
citation also being wrong. DDS/DETA/TETA cards are untouched (no CID-attribution defect). Re-attack
of fire 1's exact refutation criterion against the corrected cards: 0/5 mismatches remain (PASS).
Out-of-scope aside (not actioned): PubChem CID 2955's (DDS) own live aggregate does not itself
carry H351 -- DDS's H351 is grounded in a separately-cited IARC Monograph, unaffected by CID
correctness, and is a distinct open question left for a future fire.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `reference/mvp20/data/ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json` candidate_hazard_cards[IPDA/m-XDA].regulatory_sources cite PubChem CIDs 6944/15642, chemically unrelated substances; m-XDA's H334-driven `RESPIRATORY_SENSITISER_CONTAINMENT_REQUIRED` gate does not hold against the CAS-correct record | amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/attempts/r-n01-fire1-ghs-clp-cid-attribution-audit-rebank-receipt.v1.dsse.json | amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json | 2026-08-04 |
| `evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json` (sibling KPI, same defect) | same | amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json | 2026-08-04 |

Original artifacts left byte-intact in place (supersede-never-rewrite); before/after sha256 recorded
in the new receipt's `supersedes` block. `docs/mission.md` prose updated in the same fire (front
matter untouched). R-N01 is now closed: audit banked (fire 1) + superseding hazard cards with
CAS-correct CIDs and re-evaluated gates (fire 2).


## W-EHS1 (2026-08-05) - DDS H351 IARC-vs-PubChem citation reconciliation (disclosure only, gate unchanged)

Closes the aside R-N01 fire 2 left unresolved: DDS's H351 (suspected carcinogen) flag cites a
separately-cited "IARC Monograph Vol. 24 (1980)" source, independent of the (already-correct)
PubChem CID citation. This fire fetched both sources live and independently (2026-08-05): PubChem
CID 2955's own aggregated GHS Classification still does not carry H351 (H302, H371, H373, H411
only); IARC's own official live classification data (webapi.iarc.who.int/loc/loc.app.js) confirms
CAS 80-08-0 (Dapsone) is Group 3 -- "not classifiable as to its carcinogenicity to humans" -- last
evaluated 1987 (Vol. 24 + Suppl. 7), unchanged since. Group 3 is IARC's own negative/inconclusive
bottom line, not a Group 1/2A/2B suspected-or-probable-carcinogen finding, so **neither cited
source substantiates H351**; the original card's citation is a source-to-claim mapping error. Per
the conservative-default rule stated in the receipt (never silently resolve a disputed hazard flag
to the permissive reading), this fire does **not** strip H351 or change DDS's procurement gate --
`CARCINOGEN_CAT_2_MONITORING_REQUIRED` is retained and flagged for mandatory human toxicological
review. This is a disclosure supersede of R-N01 fire 2's receipt (adding the reconciliation that
receipt's out_of_scope_observation deferred), not a correction of any H-code or gate value.

| claim | refuted-by / basis | superseded-by | date |
|---|---|---|---|
| `evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json`'s `out_of_scope_observation` on DDS's H351/IARC citation is left unresolved ("left for a future falsification fire, not actioned here") | live PubChem PUG-View (CID 2955) + live IARC webapi.iarc.who.int/loc/loc.app.js fetch, both 2026-08-05, this fire | `amphora-sourceability-ehs/evidence/phase0/repairs/W-EHS1/done/w-ehs1-dds-h351-iarc-pubchem-reconciliation-receipt.v1.dsse.json` | 2026-08-05 |

Original R-N01 fire 2 receipt left byte-intact in place (supersede-never-rewrite); before/after
sha256 recorded in the new receipt's `supersedes` block. DDS's `h_statement_codes` and
`procurement_gate_outcome` in the audited receipt/KPI are unchanged by this fire -- see
`docs/mission.md` for the corresponding prose disclosure.

## X-EHS-CID (2026-08-14) - independent re-verification of R-N01's CID correction, plus DETA/TETA H-statement scope-gap disclosure

Founder-directive-scoped (AMPHORA-DIRECTIVE-2026-08-05 A.3) closure of the CID defect. Landed the
X-EHS-CID campaign item's own done-receipt (R-N01 fire 2 above already contains the substantive
correction; this fire independently re-derives it from a FRESH live PubChem fetch 10 days later,
2026-08-14, a new HTTP round-trip distinct from both R-N01 fires) and confirms it holds: IPDA's
CAS-correct CID (17857) and m-XDA's (15133) reproduce exactly; DDS/DETA/TETA's CIDs (2955/8111/5565)
are unchanged; R-N01 fire 2's DSSE signature independently reverifies against the pinned
PHASE0_EVALUATOR key; the solver-lab P3 demo's caveat is live-confirmed RESOLVED
(action_taken=USED_SUPERSEDING_R_N01_FIRE2_CORRECTED_HAZARD_CARDS). No further procurement-gate
change beyond the one R-N01 fire 2 already made (m-XDA).

**New disclosure (not actioned, flagged for a future fire):** re-deriving H-statement codes purely
from each candidate's live PubChem notification-aggregate (the same aggregate group already cited
in each card's `pubchem_notifications_summary`, confirmed by matching report/notification counts)
shows DDS/DETA/TETA's *current* cards diverge from that aggregate — this was already flagged for
DDS by R-N01 fire 2's `out_of_scope_observation` (reproduced identically today, not new drift), and
this fire extends the same observation to DETA and TETA, which fire 2 never checked because their
CID citations were never wrong. Most notable: DETA's live aggregate (3716 reports / 49
notifications) additionally carries H318 (serious eye damage), H330 (**Fatal if inhaled**) and H335
(respiratory irritation), none of which are on DETA's card today; this KPI's `gate_rule` also has no
branch for H330/H331/H332 acute-inhalation-toxicity codes at all. Not actioned in this fire — no
gate was changed on this basis — because doing so without a dedicated, carefully-scoped
falsification fire against the H-statement-derivation methodology and gate-rule coverage would risk
an unreviewed change to a procurement-safety-relevant gate.

| claim | basis | superseded-by / re-verified-by | date |
|---|---|---|---|
| `reference/mvp20/data/ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json` (sha256 `4835ff73...`) IPDA/m-XDA CID citations, independently re-derived a second time from a fresh 2026-08-14 fetch | fresh live PubChem PUG-REST/PUG-View fetch, this fire, cross-checked against R-N01 fire 2 | `amphora-sourceability-ehs/evidence/phase0/repairs/X-EHS-CID/done/x-ehs-cid-done-receipt.v1.dsse.json` | 2026-08-14 |
| `evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json` (sha256 `6bfd9343...`) (sibling KPI, same defect) | same | `amphora-sourceability-ehs/evidence/phase0/repairs/X-EHS-CID/done/x-ehs-cid-done-receipt.v1.dsse.json` | 2026-08-14 |

Original artifacts left byte-intact in place (supersede-never-rewrite); R-N01 fire 2's receipt is
also left byte-intact and is NOT superseded (it is not defective — it is the correction; this fire
independently corroborates it). Before/after sha256 recorded in the new receipt's `supersedes`
block. `docs/mission.md` updated in the same fire with the DETA/TETA H-statement scope-gap
disclosure (front matter untouched).


## Y-EHS-GATE (2026-08-14) - gate_rule acute-inhalation-toxicity (H330/H331/H332) blind-spot, mechanically proven (disclosure only, gate unchanged)

Sharpens the aside X-EHS-CID flagged and did not act on. m-XDA's *current authoritative* hazard
card (R-N01 fire 2's correction, corrected_hazard_cards, independently re-verified byte-identical
by X-EHS-CID 4 hours before this fire) already carries H330 ("Fatal if inhaled", Cat 1), H331
("Toxic if inhaled", Cat 2), and H332 ("Harmful if inhaled", Cat 3) -- added to the card by R-N01
fire 2 itself (`h_codes_added_vs_prior_receipt`) from a 1105-report/43-notification ECHA C&L
aggregate, corroborated by the GHS06 skull-and-crossbones pictogram already present in the same
card's `ghs_pictograms_live`. This fire re-implemented the KPI's documented `gate_rule` verbatim
and ran an ablation test: gate_for(m-XDA's actual H-codes) == gate_for(m-XDA's H-codes with
H330/H331/H332 removed) == `CORROSIVE_PPE_PLAN_REQUIRED` in both cases -- proving the rule is
structurally blind to acute-inhalation-toxicity hazard codes: m-XDA's outcome is identical to
IPDA's, DETA's, and TETA's, none of which carry any such hazard code at all. A fresh independent
2026-08-14 live re-fetch of CID 15133 reproduces the identical code set today. Per the module's
conservative-default rule (established W-EHS1), this fire discloses and flags the defect without
patching `gate_rule` itself -- an unreviewed change to a procurement-safety-relevant gate is left
for a dedicated repair fire.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `evidence/phase0/repairs/X-EHS-CID/done/x-ehs-cid-done-receipt.v1.dsse.json`'s H330/H331/H332
gate-rule-coverage aside is left unresolved ("flagged for a dedicated future falsification fire ...
explicitly NOT actioned here") | independent re-implementation of `gate_rule` + ablation test against
R-N01 fire 2's DSSE-verified m-XDA card, plus fresh live PubChem re-fetch (CID 15133), this fire |
`amphora-sourceability-ehs/evidence/phase0/repairs/Y-EHS-GATE/done/y-ehs-gate-done-receipt.v1.dsse.json` | 2026-08-14 |

X-EHS-CID's done receipt is left byte-intact in place (supersede-never-rewrite); this fire does not
modify any candidate's `h_statement_codes` or `procurement_gate_outcome` -- see `docs/mission.md`
for the corresponding prose disclosure.


## EHS-HCOMP (2026-08-15) - DETA/TETA H-statement completeness audit, mechanically proven (disclosure only, gate unchanged)

Closes the "dedicated future falsification fire against the H-statement-derivation methodology"
that X-EHS-CID and Y-EHS-GATE (both 2026-08-14) flagged and declined to action. Independent fresh
live PubChem PUG-View fetch (2026-08-15, a third independent HTTP round-trip distinct from R-N01
fire 2's 2026-08-04 fetch and X-EHS-CID's 2026-08-14 fetch), matched by report/notification count
to the exact aggregate each card's own `pubchem_notifications_summary` already cites as its source.
**DETA's card omits H318 (68.3% of reports), H330 "Fatal if inhaled" (71.7%), and H335 (70.7%)**,
all majority-prevalence in the card's own self-cited aggregate. **TETA's card omits H318 (39.4%)**
and states an aquatic-toxicity tier (H411) its own majority aggregate does not support (majority
reports H412, a lower tier, at 99.5%). Both findings reproduce byte-for-byte against X-EHS-CID's
already-committed 2026-08-14 raw fetch of the same two CIDs (two independent HTTP round-trips a day
apart agree exactly), and do NOT reproduce when the identical audit is run against IPDA/m-XDA (the
two cards R-N01 fire 2 actually re-derived from PubChem) -- zero missing codes for either, ruling
out a methodology artifact. `gate_rule`'s H314 branch already fires for DETA and TETA regardless of
the omitted codes (same blind spot Y-EHS-GATE proved on m-XDA), so `procurement_gate_outcome` is
unchanged for both. Per the conservative-default rule established by W-EHS1, this fire does **not**
patch `h_statement_codes` or any gate -- disclosed and flagged for a dedicated, reviewed repair.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `evidence/phase0/repairs/R-N01/done/r-n01-fire2-ghs-clp-hazard-card-correction-receipt.v1.dsse.json` `corrected_hazard_cards[DETA,TETA].h_statement_codes` faithfully represent the ECHA C&L aggregate each card itself cites | `amphora-sourceability-ehs/reference/mvp20/data/deta_teta_h_statement_completeness_audit_receipt.v1.json` | not yet superseded -- disclosure only, flagged for a dedicated repair fire | 2026-08-15 |

R-N01 fire 2's receipt is left byte-intact in place (supersede-never-rewrite); this fire does not
modify any candidate's `h_statement_codes` or `procurement_gate_outcome` -- see `docs/mission.md`
for the corresponding prose disclosure.


## EHS-REDCHEM (2026-08-16) - Red-team-dossier regression-coverage gap, mechanically proven (disclosure only, no gate/KPI value changed)

Attacks `docs/mission.md`'s "Red-team dossier" commitment directly, rather than a single-substance
scientific-evidence receipt (the target of every prior EHS falsification fire). A full-repository
grep for every call site invoking `AssuranceCapability::new("amphora-sourceability-ehs")` found
exactly one: `amphora-assurance-capabilities/tests/sourceability_ehs_phase0_kpi.rs:205`. Its 5
scenarios plus 3 fail-closed probes exercise only dispatch-layer axes (candidate_type, module_id);
zero cases exist anywhere in the repository for malformed chemistry, mixtures/fragments/polymers,
unit ambiguity, zero-mass ingredients, out-of-domain inputs, group/source/time leakage, mutated
sources, computed-as-measured records, spoofed identity, content-level authority escalation, or
stripped/unknown claim locks -- 11 of the 15 axes the dossier paragraph names. Source reading
(`amphora-assurance-capabilities/src/lib.rs` `fn evaluate_sourceability() -> ModuleResult` takes no
candidate-derived argument) plus a fresh, isolated, byte-stable two-replay probe against the real
compiled runtime (13 adversarial content variants, all byte-identical in output to a known-good
baseline) confirms the runtime is provably content-blind. Every probed case still safely "remains an
explicit evidence gap" (the dossier's OR-clause), so no procurement/regulatory authority is ever
mis-granted -- but the *coverage claim itself*, that regression tests exercise these axes, is false as
written.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `docs/mission.md` "Red-team dossier" -- "Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; ... group/source/time leakage; mutated sources; computed-as-measured records; spoofed identity; authority escalation; stripped or unknown claim locks" against this module's checked fixture | `amphora-sourceability-ehs/reference/mvp20/data/redchem_regression_coverage_gap_audit_receipt.v1.json` | not yet superseded -- disclosure only, flagged for a dedicated repair fire (would require editing shared `amphora-assurance-capabilities/tests/`, outside this module's write confinement) | 2026-08-16 |

No KPI, gate, or `procurement_gate_outcome` is modified by this fire; see `docs/mission.md` for the
corresponding prose disclosure.


## R-A13 (2026-08-18) - VHR base-panel wrong-key reinstatement + module-wide signing sweep

Continues R-A12 (2026-08-03), which reinstated 2 of this module's wrong-key-signed artifact pairs
(osha_table_z1_z2, vhr_temperature_envelope_crossmethod) but scoped its fix to 2 specific
launcher-downgraded fires rather than auditing every KPI/receipt file. A full cryptographic
re-verification sweep of every `*.json` under `evidence/phase0/kpis/` and `reference/mvp20/data/`
against the pinned `PHASE0_EVALUATOR` key (`config/phase0-trust-store.v1.json`) found the base
9-solvent Vapor Hazard Ratio panel (`vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json`,
worst_actor=methanol, cited as "pinned, signed" by R-S04 and the Antoine/temperature-envelope
audits) still signed with the unanchored repo `LOCAL_DEVELOPMENT_AUDIT_ONLY` key
(`local-9028773f49591193`), same defect class as R-A12, never itself reinstated. Re-imported the
committed harness (`benchmarks/vapor-hazard-ratio-v1/run_vhr_prescreen.py`), reproduced
`diagnostic.canonical.json` byte-exact across two in-process replays, confirmed the science
(worst_actor=methanol, 9 solvents scored) is unchanged, and reinstated both files under the pinned
key.

The same sweep found **5 more un-repaired defects, NOT fixed by this fire**, flagged for a
dedicated follow-on repair:
- Wrong-key-signed (same `local-9028773f49591193` defect): `antoine_vp_crosscheck_receipt.v1.json`
  + KPI, `ghs_clp_cid_attribution_audit_receipt.v1.json` + KPI, `mixture_additivity_raoult_osha_
  inhalation_prescreen_receipt.v1.json` + KPI, `vhr_temperature_envelope_inhalation_prescreen_
  receipt.v1.json` + KPI (distinct from the crossmethod pair R-A12 already fixed).
- **No DSSE envelope at all** (more severe than wrong-key): `sourceability-ehs-public-prescreen-
  kpi.v1.json` -- the module's CORE Phase-0 KPI, cited in `docs/mission.md`'s "Current benchmark
  result" section as backing 14 passing deterministic gates -- and `ghs-clp-public-hazard-
  prescreen-5-canonical-epoxy-amines-kpi.v1.json`.
- Signed with a **third, different unknown key** (`toolkit-reviewer-...`, neither pinned nor
  local-dev): `ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json`.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-sourceability-ehs/reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json` is validly DSSE Ed25519-signed under the pinned PHASE0_EVALUATOR key | `amphora-sourceability-ehs/evidence/phase0/repairs/R-A13/done/r-a13-done-receipt.v1.dsse.json` (self-contained: diagnosis + reattack + reinstatement) | `amphora-sourceability-ehs/evidence/phase0/repairs/R-A13/done/r-a13-done-receipt.v1.dsse.json` | 2026-08-18 |
| `amphora-sourceability-ehs/evidence/phase0/kpis/vapor-hazard-ratio-inhalation-prescreen-kpi.v1.json` is validly DSSE Ed25519-signed under the pinned PHASE0_EVALUATOR key | same as above | same as above | 2026-08-18 |

Both original files are left byte-intact in place (supersede-never-rewrite); this fire does not
modify the VHR science, ranking, or any KPI gate value -- only the signing authority is corrected.
The 5 remaining defects above are disclosed, not patched; see the done receipt's
`module_wide_signing_sweep` field for full per-file diagnostics.


## R-A14 (2026-08-18) - core module KPI no-envelope reinstatement

Follow-on to R-A13's own priority flag: `evidence/phase0/kpis/sourceability-ehs-public-prescreen-
kpi.v1.json` -- the module's **CORE** Phase-0 KPI, cited in `docs/mission.md`'s "Current benchmark
result" section as backing 14 passing deterministic gates -- carried **no DSSE envelope at all**,
not even a wrong-key one. Independently re-derived the science via two separate `cargo test -p
amphora-assurance-capabilities --test sourceability_ehs_phase0_kpi --locked` subprocess invocations
of the real compiled `evaluate_sourceability` runtime (not a copy, not a cached replay); both runs
produced byte-identical canonical benchmark-result bytes, and those bytes match the shipped
`evidence/phase0/benchmark/result.v1.json` byte-exact (sha256
`189390bfa08cfda9d88895aaae8e20fd9b2db6f67d60e662f58f4bb3e4f033f2`). All 14/14 KPI gates confirmed
passing. Reinstated the KPI under the pinned `PHASE0_EVALUATOR` key; externally re-verified the
resulting envelope against the pinned trust-store public key outside the signing script.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `amphora-sourceability-ehs/evidence/phase0/kpis/sourceability-ehs-public-prescreen-kpi.v1.json` is validly DSSE Ed25519-signed under the pinned PHASE0_EVALUATOR key | `amphora-sourceability-ehs/evidence/phase0/repairs/R-A14/done/r-a14-done-receipt.v1.dsse.json` (self-contained: diagnosis + reattack + reinstatement) | `amphora-sourceability-ehs/evidence/phase0/repairs/R-A14/done/r-a14-done-receipt.v1.dsse.json` | 2026-08-18 |

Original file left byte-intact in place (supersede-never-rewrite); this fire does not modify any
of the 14 KPI gate observations -- only the signing authority is added where none existed. Still
NOT fixed by this fire (unchanged from R-A13's disclosure): 4 wrong-key artifact pairs, the
`ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json` no-envelope sibling, and the
third-unknown-key `ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json`.


## R-A15 (2026-08-19) - remaining R-A13 sweep defects closed: 4 wrong-key pairs + third-unknown-key file + 2nd no-envelope KPI

Closes the full remainder of R-A13's disclosed-but-unpatched defect list (R-A14 closed the core
module KPI; this fire closes everything else). Re-verified live on-disk state matches R-A13's
diagnosis exactly (all 10 file sha256 values unchanged since 2026-08-18, confirming nothing else
touched them in the interim). For the 4 harness-backed wrong-key pairs (`antoine_vp_crosscheck`,
`ghs_clp_cid_attribution_audit`, `mixture_additivity_raoult_osha`, `vhr_temperature_envelope`),
independently re-imported each committed `benchmarks/*/run_*.py` and called `compute()` twice
in-process; all 4 reproduced their committed `diagnostic.canonical.json` byte-exact, confirming the
science is sound and this is purely a signing-authority defect. Re-signed all 8 files' existing
payload bytes (byte-identical, unchanged) under the pinned `PHASE0_EVALUATOR` key. The third-
unknown-key file (`ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json`,
`toolkit-reviewer-...` key, verifies against neither the pinned nor local-dev key) and its
no-envelope sibling KPI were also reinstated under the pinned key over their existing/canonicalized
bytes -- but this pair's **content** is separately stale (superseded in substance by R-N01 fire 2's
IPDA/m-XDA correction and EHS-HCOMP's DETA/TETA completeness finding); this fire closes only the
signing defect and explicitly does not revive the stale content as current-authoritative.

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `evidence/phase0/kpis/antoine-vp-crosscheck-vhr-kpi.v1.json` + `reference/mvp20/data/antoine_vp_crosscheck_receipt.v1.json` are validly DSSE Ed25519-signed under the pinned PHASE0_EVALUATOR key | `amphora-sourceability-ehs/evidence/phase0/repairs/R-A15/done/r-a15-done-receipt.v1.dsse.json` | same | 2026-08-19 |
| `evidence/phase0/kpis/ghs-clp-cid-attribution-audit-kpi.v1.json` + `reference/mvp20/data/ghs_clp_cid_attribution_audit_receipt.v1.json` are validly DSSE Ed25519-signed under the pinned PHASE0_EVALUATOR key | same | same | 2026-08-19 |
| `evidence/phase0/kpis/mixture-additivity-raoult-osha-inhalation-prescreen-kpi.v1.json` + `reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json` are validly DSSE Ed25519-signed under the pinned PHASE0_EVALUATOR key | same | same | 2026-08-19 |
| `evidence/phase0/kpis/vhr-temperature-envelope-inhalation-prescreen-kpi.v1.json` + `reference/mvp20/data/vhr_temperature_envelope_inhalation_prescreen_receipt.v1.json` are validly DSSE Ed25519-signed under the pinned PHASE0_EVALUATOR key | same | same | 2026-08-19 |
| `reference/mvp20/data/ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json` is validly DSSE Ed25519-signed under the pinned PHASE0_EVALUATOR key (was signed with an unregistered third key) | same | same | 2026-08-19 |
| `evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json` is validly DSSE Ed25519-signed under the pinned PHASE0_EVALUATOR key (previously had no DSSE envelope at all) | same | same | 2026-08-19 |

All 10 original files left byte-intact in place (supersede-never-rewrite); before/after sha256 for
every file recorded in the done receipt's `supersedes` block. This fire does not modify the science,
ranking, or any KPI gate value of the 4 harness-backed pairs. This fire closes R-A13's full disclosed
defect list; a fresh full-module re-sweep would be needed to certify no further undisclosed defects
exist.
