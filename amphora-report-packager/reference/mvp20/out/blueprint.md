# Marine Hull Primer — Formulation & Manufacturing Blueprint (mvp20)

**Customer:** a top U.S. Navy prime (masked). **Program:** epoxy-polyamide marine hull primer per the v5 Technical Envelope.

> AUTHORITY LOCK (non-negotiable): this package is a CANDIDATE engineering blueprint for qualification, NOT an approved or QPL-listed product. A formulation that numerically matches the envelope is NOT Navy-qualified. Under MIL-DTL-24441D, components must be qualified and listed on QPL-24441 (updated 27-Jan-2026), and the NAVSEA-reviewed ASTM F-718 data sheet is the only approved application data sheet for Navy preservation projects; F-718 review does not itself confer procurement qualification. No claim of 'approved', 'qualified', or 'QPL-listed' is made anywhere in this package.

> Evidence tiers: **REAL-ARITHMETIC** (deterministic on the BOM, hand-recomputable), **RULE-CITED** (published design rule, labeled), **MODELED-VALIDATED** (model passed its validation card), **CRO-GATED** (no model earned rights; the bench decides). No number exceeds its evidence.

## 0. Engine verdict
Universe ~4320 formulations -> 3975 solved exactly onto the 1:1-by-volume + 65%-solids surface -> 2444 pass ALL envelope gates -> 3 candidates that are ROBUST to ingredient-lot tolerance CARRIED to the bench (Monte-Carlo = perturbing every cited constant within its published uncertainty and re-checking the arithmetic gates pass ≥95% of draws — this is INPUT-TOLERANCE robustness, NOT performance robustness), differing on the extender pack (the axis no validated model can rank -- the bench decides).

**Lead M00097 / Envelope-65** (+ alternates M00101, M00109, and functional variant M00098): DGEBA-class liquid epoxy (EEW in the government 175–190 band) + reactive polyamide (ancamide_350a) at R=0.7, HAP-compliant naphtha + n_butanol solvent system (per C-005), silica barrier-extender pack, no functional zinc phosphate in the primary, and iron-oxide identification color. Enhanced-65 adds zinc phosphate only as a functional optional variant.

### Government-data wins (WIN 1–3, no model luck — public data + hand-checkable arithmetic)
- **MIL Formula 160 (Black) density recovery**: our Tier-A arithmetic recomputes the government slash sheet's OWN component densities IN-range (A 8.22 vs [7.9, 8.3]; B 10.24 vs [10.2, 10.6] lb/gal) under a provisional physical reconciliation (epoxy 709 lb vs silica 62 lb). This is not known-answer credit: Formula 160 black stays source-conflict-held pending authoritative /38B or NAVSEA/DLA confirmation.
- **Zero-prior architecture recovery**: 8/8 COMPUTED checks (not hardcoded) vs the real MIL-DTL-24441 Type-IV architecture — epoxy EEW in the 175–195 gov band, reactive-polyamide curative, 1:1 volume, silicate-class extender, gov-precedent solvent families, VOC<340, both components pigmented, sub-stoichiometric R matching gov F160's own R≈0.78. (Pot-life-class + colorway-twin are design choices, reported separately, NOT counted.)
- **Arithmetic audit at scale**: 6/6 recompute checks pass across 4 supplier + government formulas (out/arithmetic_audit.md).
- **Conflict register** (out/conflict_register.md): C-001 (envelope 65% black/yellow vs qualified 60.2% F160/F161 — OPEN variance), C-003 (sub-stoichiometry validated by the government's own R≈0.78 formula), C-005 (HAP solvent limits — solvent axis corrected). C-002/C-004 resolved.

| Envelope requirement | Target | Lead (REAL-ARITHMETIC) |
|---|---|---|
| Mix ratio by volume | 1:1 | 1.000 (solved) |
| Volume solids | 65±2% | 65.0% (solved) |
| VOC (Method 24 basis) | ≤340 g/L | 281 g/L |
| Weight per gallon | ~9.1 lb/gal | 9.16 |
| Coverage @5 mil DFT | 175–230 ft²/gal | 209 |
| WFT @5 mil | 7–9 mil | 7.69 |
| Stoichiometry (amine-H:epoxide) | polyamide window | 0.70 |
| PVC / Λ=PVC:CPVC | Λ well below 1 (RULE-CITED) | 9.3% / 0.17 |
| Pot life ≥1.5 h | CRO-GATED | class precedent 4–5 h (qualified 1:1 primers, cited) — week-1 KU map gates the battery |

## 1. Formulation & BOM (lead; alternates in funnel_results.json)
Every line is a PROPERTY-WINDOW (EEW/AHEW/density/OA windows from the citation ledger), not a brand lock; candidate commercial sources are the cited suppliers plus equivalents meeting the window.
| Part | Ingredient (property-window line) | Role | g | wt% of part | Citation |
|---|---|---|---|---|---|
| A | dgeba_828 | resin | 100.0 | 72.8% | TDS: https://miller-stephenson.com/wp-content/uploads/2024/06/EPON-828_TDS.pdf ; https://s |
| A | silica | extender | 22.0 | 16.0% | HANDBOOK: https://cameochemicals.noaa.gov/chemical/12319 |
| A | naphtha | solvent | 8.4 | 6.1% | HANDBOOK: https://cameochemicals.noaa.gov/chemical/12319 |
| A | iron_oxide_black | pigment | 3.5 | 2.5% | DISTRIBUTOR: https://www.specialchem.com/coatings/product/lanxess-bayferrox-130-m |
| A | thixotrope | additive | 1.8 | 1.3% | DISTRIBUTOR: https://www.elementis.com/en/products/additives/rheological-additives/bentone |
| A | dispersant | additive | 1.2 | 0.9% | DISTRIBUTOR: https://www.byk.com/en/products/disperbyk-163 |
| A | defoamer | additive | 0.5 | 0.4% | DISTRIBUTOR: https://www.byk.com/en/products/byk-a-530 |
| B | n_butanol | solvent | 53.0 | 51.9% | TDS: https://productcatalog.eastman.com/tds/ProdDatasheet.aspx?product=71000115 ; https:// |
| B | ancamide_350a | hardener | 37.1 | 36.3% | TDS: https://crosslinkers-web.panpage.de/en2/crosslinkers/ancamide/usa/ancamide_350a_us.pd |
| B | silica | extender | 10.0 | 9.8% | HANDBOOK: https://cameochemicals.noaa.gov/chemical/12319 |
| B | thixotrope | additive | 1.2 | 1.2% | DISTRIBUTOR: https://www.elementis.com/en/products/additives/rheological-additives/bentone |
| B | dispersant | additive | 0.8 | 0.8% | DISTRIBUTOR: https://www.byk.com/en/products/disperbyk-163 |

Part roles for the candidate are explicit: **Part A = epoxy side** and **Part B = polyamide-curative side** (the public MIL lineage labels these sides in the opposite order). Mix A:B 1:1 by volume; induction ~30 min at 73°F per envelope; the solvent split was SOLVED so packaged volumes are equal at 65% mixed solids.

### 1b. Black / Yellow colorway twins (government-pattern; formulation_black.json / formulation_yellow.json)
Per C-004 and the government precedent (MIL-DTL-24441 F160/F161 are public colorway twins, but at 60.2% VS), black and yellow are ONE base vehicle with only the identification color swapped (black iron oxide ↔ yellow iron oxide) at EQUAL VOLUME (equal PVC — corrected for the magnetite/goethite density difference so the twins share film-build, not just mass). **Parity PASS** — engine-checked spread across colors:

| KPI | Black | Yellow | Spread | Parity bar |
|---|---|---|---|---|
| Volume solids % | 65.0 | 65.0 | 0.0 | ≤1.0 |
| VOC g/L | 282 | 282 | 0.0 | ≤10 |
| Weight lb/gal | 9.161 | 9.139 | 0.022 | ≤0.15 |
| Λ=PVC:CPVC | 0.173 | 0.171 | 0.002 | ≤0.05 |

Both twins pass all envelope gates; pigmentation stays non-functional (identification/visibility only).

## 2. Manufacturing process (CRO batch record form)
| Step | Candidate Part A: epoxy side | Candidate Part B: polyamide-curative side | QC / stop rule |
|---|---|---|---|
| Raw material QC | verify EEW, density, NV, pigment lot | verify AHEW/amine value, density, NV | missing CoA or out-of-window value stops batch |
| Charge | DGEBA resin, dispersant, defoamer | polyamide curative, dispersant | record lots, mass, temperature |
| Dispersion | add silica + iron oxide; Cowles grind | add silica; Cowles grind | Hegman >=6, grind <=55°C |
| Letdown | naphtha to solved volume | n-butanol to solved volume | density and KU within batch target |
| Filtration/packout | filter, fill, retain sample | filter, fill, retain sample | no gel, no hard settle, retain both parts |
| Use | mix A:B = 1:1 by volume | mix A:B = 1:1 by volume | induction/pot-life measured by CRO |

Enhanced-65 follows the same record but adds zinc phosphate on the epoxy side as a functional inhibitor; it is not the primary because the envelope treats pigmentation as non-functional.

## 3. In-process & QC — see Q5/Q10/Q11/Q14/Q15 below (SPC on KU/density/Hegman/VS/VOC tied to ingredient lots).

## 4. Supply chain & sourcing
Property-window BOM with second sources or explicit waivers on load-bearing constants. Candidate grades and alternates are listed in source_records.json. Domestic/TAA status, PFAS declarations, TSCA declarations, and lead times are **to verify by supplier declaration/RFQ**; they are not claimed here.

## 5. Regulatory & EHS
Design VOC 281 g/L ≤ 340 federal/military allowance (EPA Method 24). **Spec HAP constituent limits enforced (C-005)**: MIL-DTL-24441D caps xylene ≤0.1 wt%, MIBK/toluene/MEK/ethylbenzene ≤0.05 wt% of the finished paint — the solvent axis was restricted to compliant naphtha/mineral-spirits/n-butanol to satisfy these. Stricter state/district rules may bind at point of use (SCAQMD Rule 1106 for CA marine coatings; NESHAP 40 CFR 63 subpart II for ship-repair facilities — confirm jurisdiction). Methylene chloride is banned by default; no intentional chromate/lead/cadmium/asbestos is in the candidate BOM. PFAS status and TSCA-inventory status require supplier declarations. NFPA 30/33 flammable-liquid + spray controls; OSHA amine-handling PPE.

## 6. IP & legal — preliminary patent landscape (NOT an FTO opinion; category screens included)
> FTO NOT PERFORMED. Preliminary landscape from public claim reads plus CPC/IPC/category screens; NOT a legal clearance, not a freedom-to-operate opinion. Counsel must review claim dependencies, prosecution history, jurisdictions, legal status, and equivalents before any procurement or launch decision.

The landscape now separates claim-read anchor families from CPC/IPC/category screens. The compliant primary is commodity chemistry with DIRECT PUBLIC PRIOR ART (the MIL-DTL-24441 slash sheets disclose the architecture; and US5059640A is an EXPIRED US-Navy-assigned epoxy anticorrosive patent — on-point public-domain prior art). Category rows are attack-surface mapping only, not clearance.

| Family/category row | Assignee | Status | Reads on our primer? | Why |
|---|---|---|---|---|
| WO2016187380A1 | Blue Cube IP LLC | Ceased | **NO** | no distinct reactive polar compatibilizer; our VS ~65% (<70%). Two independent limitations missing. |
| EP3328938B1 | Elementis Specialties Inc | Active/granted (2023-05-17; est. expiry ~2036) | **NO** | claims a specific micronized polyamide RHEOLOGY additive, not a curing agent; our dimer-acid liquid polyamide curative is different chemistry. The ONLY live-granted family here. |
| EP2931822 | Blue Cube IP / Dow | EP shown Active; US member Ceased | **NO (caveat: read US family claim, not EP)** | we use standard DGEBA only, no CHDM epoxy. |
| WO2013159277A1 | Dow Global Technologies LLC | Ceased | **NO** | no chlorinated polyolefin terpolymer in our primer. |
| US5059640A | US Department of the Navy | Expired (~2003, fee lapse) | **NO** | primary has no zinc phosphate; Enhanced-65 has zinc phosphate alone, with no molybdate/benzoate; also EXPIRED. |
| Google Patents category screen: waterborne epoxy systems | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | Envelope-65 is solvent-borne and does not use waterborne dispersion architecture. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: zinc-rich primers | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | No zinc dust or cathodic-protection pigment network is present. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: graphene epoxy anticorrosion | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | No graphene-family nanofiller is present in Envelope-65 or Enhanced-65. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: nanoclay epoxy barrier | multiple | category screen; individual family status unverified | **UNCLEAR** | The BOM uses an organoclay rheology additive at low level, not a claimed nanoclay barrier package; exact grade needs review. |
| Google Patents category screen: microcapsule self-healing epoxy | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | No microcapsules or self-healing package are present. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: intrinsic self-healing epoxy | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | Commodity DGEBA/polyamide matrix lacks designed reversible self-healing chemistry. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: phenalkamine epoxy curatives | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | Baseline uses dimer-acid polyamide/amidoamine curative, not phenalkamine. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: amidoamine epoxy curatives | multiple | category screen; individual family status unverified | **UNCLEAR** | Candidate curative is commodity class, but exact selected grade needs supplier/IP screen. |
| Google Patents category screen: polysiloxane epoxy hybrids | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | No polysiloxane or hybrid network is present. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: bio-based epoxy coatings | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | Baseline uses commodity petroleum DGEBA-class epoxy. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: phosphate/molybdate inhibitor packages | multiple | category screen; individual family status unverified | **UNCLEAR** | Enhanced-65 has zinc phosphate only; no molybdate/benzoate triad, but inhibitor substitutions need review. |
| Google Patents category screen: corrosion indicator smart coatings | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | No indicator chemistry is present. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: high-solids epoxy process/QC | multiple | category screen; individual family status unverified | **UNCLEAR** | Formula is commodity, but process/QC implementation can still create FTO/trade-secret questions. |
| Google Patents category screen: reactive diluent epoxy coatings | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | No reactive diluent is used in Envelope-65. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: CHDM epoxy blend adjacencies | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | No CHDM epoxy resin is in the BOM. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: chlorinated polyolefin tie-coats | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | No chlorinated polyolefin terpolymer is present. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: layered MIO barrier pigments | multiple | category screen; individual family status unverified | **UNCLEAR / not FTO** | No MIO package is included in Envelope-65. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: hydrophobic silica epoxy barriers | multiple | category screen; individual family status unverified | **UNCLEAR** | Baseline uses silica extender; surface-treated specialty silica would need grade-level review. |
| Google Patents category screen: marine epoxy primer public prior art | multiple/public | public prior-art category screen | **UNCLEAR / not FTO** | This is prior-art posture, not an exclusionary claim against the candidate. Category-only or uncharted screen: cannot mark NO without an independent claim chart. |
| Google Patents category screen: accelerated polymer automation/process twin | multiple/public | category screen; individual family status unverified | **UNCLEAR** | Current mvp20 is deterministic and evidence-controlled, not yet a full active-learning lab engine. |
| EP2653485A2 | Hempel A/S | public bibliographic status only; counsel verification required | **NO** | baseline is a standalone epoxy-polyamide primer decision package, not a primer/polyurea topcoat system |
| WO2009019296A1 | Akzo Nobel Coatings International B.V. | public bibliographic status only; counsel verification required | **UNCLEAR / not FTO** | baseline does not intentionally use silicate-reacted epoxy, but process chemistry and equivalents are not charted enough for clearance |
| WO2014093115A2 | Dow Global Technologies LLC | public bibliographic status only; counsel verification required | **UNCLEAR / not FTO** | baseline DGEBA resin excludes CHDM by design, but exact family status and claim scope require counsel |
| WO2018010615A1 | Elementis Specialties, Inc. | public bibliographic status only; counsel verification required | **UNCLEAR / not FTO** | baseline is solvent-borne, but additive-grade selection still needs supplier-specific IP review |
| US4865653A | Henkel Corporation | expired family likely but counsel must verify | **UNCLEAR / not FTO** | conversion pretreatment is outside the BOM, but surface-prep choices remain customer/lab scoped |
| US3178319A | Monsanto Company | expired family likely but counsel must verify | **UNCLEAR / not FTO** | pretreatment chemistry is outside the candidate paint formulation |
| EP0398202A1 | Henkel KGaA | public bibliographic status only; counsel verification required | **UNCLEAR / not FTO** | surface pretreatment, not in-can primer composition |
| EP1865013B1 | Evonik Operations GmbH family | public bibliographic status only; counsel verification required | **UNCLEAR / not FTO** | candidate uses commodity polyamide class but grade-specific curative IP is unresolved |
| US6391464B1 | International Paint LLC family | public bibliographic status only; counsel verification required | **UNCLEAR / not FTO** | overcoat/tiecoat architecture is adjacent to but not part of the baseline primer |
| US2705223A | General Mills Inc. | expired family likely but counsel must verify | **UNCLEAR / not FTO** | public prior-art posture for epoxy/polyamide architecture; not a clearance opinion |
| US2986539A | General Mills Inc. | expired family likely but counsel must verify | **UNCLEAR / not FTO** | adjacent prior-art family; not a coating-performance clearance |
| Google Patents public family screen: C09D163/00 sweep family 01 - solvent-borne epoxy anticorrosive primer | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D163/00 sweep family 02 - bisphenol-A/F epoxy blend coating | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D163/00 sweep family 03 - epoxy phenalkamine marine coating | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D163/00 sweep family 04 - epoxy amidoamine corrosion primer | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D5/08 sweep family 01 - zinc phosphate inhibitor package | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D5/08 sweep family 02 - zinc molybdate/phosphate inhibitor blend | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D5/08 sweep family 03 - rare-earth inhibitor epoxy coating | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D5/08 sweep family 04 - azole inhibitor epoxy-polyamide coating | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D7/61 sweep family 01 - micaceous iron oxide barrier pigment | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D7/61 sweep family 02 - aluminum flake epoxy barrier pigment | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D7/61 sweep family 03 - graphene oxide epoxy barrier | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C09D7/61 sweep family 04 - nanoclay epoxy barrier coating | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C08G59/50 sweep family 01 - polyamide curing agent | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C08G59/50 sweep family 02 - polyamidoamine curing agent | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: C08G59/50 sweep family 03 - modified amine adduct | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: B05D sweep family 01 - high-solids epoxy spray process | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: B05D sweep family 02 - surface-prep and coating system process | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: B05D sweep family 03 - automated coating QC process | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: reactive diluent sweep family | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: self-healing microcapsule sweep family | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: intrinsic self-healing epoxy sweep family | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: waterborne epoxy anticorrosive sweep family | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: zinc-rich epoxy primer sweep family | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |
| Google Patents public family screen: process data/model optimization sweep family | multiple public families | category/family screen; individual family status unverified | **UNCLEAR / not FTO** | CPC/IPC sweep row: no specific independent claim has been counsel-charted to a clearance conclusion. |

The claim-read anchor families that were actually read do not clear the product; they only show why the baseline avoids obvious load-bearing elements (reactive compatibilizer + >70% solids; a micronized polyamide rheology additive; a CHDM epoxy; a chlorinated-polyolefin terpolymer; a Zn-phosphate/molybdate/benzoate triad). Category screens remain **UNCLEAR until counsel reads claims, prosecution history, jurisdictions, and equivalents**. EP3328938B1 is the live-grant concern if a micronized polyamide rheology additive is selected; the current Bentone-class organoclay thixotrope is a different additive class but still needs grade-level review.

Defensible assets are NOT the formula (public prior art) but the auditable envelope→blueprint engine, the citation-ledger + validation-card discipline, and the accumulating bench-data flywheel. Recommended posture: **trade secret** on the process windows/model stack; patent only genuinely novel Discovery-Annex items, never the MIL-matching primary. The deterministic constraint-solve is engineering convenience (algebra), NOT claimed as patentable novelty.

## 7. Manufacturability & risk
The engine's tolerance Monte-Carlo drove a real design decision: early dense-extender (barytes) packs breached the weight gate under ordinary lot tolerance, so the extender was moved to low-density SILICA (the government F160's own choice, ρ 2.65). The lead now lands at 9.16 lb/gal — essentially the qualified government F160's 9.23 (the envelope's 9.1 sits ~2% below the government's own black primer; see C-002). Residual risks (bench-gated): sprayability/sag at 65% solids (C-001: the qualified black/yellow sit at 60.2% solids), wetting on SP-10 steel, pinholing at high WFT, and 36-mo shelf stability. Q7/Q8/Q13 detail the mitigations.

## 8. CRO handoff & feedback loop
Build ALL THREE carried candidates. WEEK-1 GATE (< $2k): KU-vs-time at 65/73/95°F on mixed 1:1 samples — this closes the pot-life gate honestly before the full battery (the cure model FAILED its validation card and does not predict hours; class precedent 4–5 h is the cited prior). Then the full battery per cro_protocol.md with the acceptance matrix; corrosion arms (B117+D1654, D5894, EIS, D870) DECIDE among the three packs — the corrosion model was demoted per its card and never ranks. Every measurement maps to the parameter it updates (capture_template.json); the prediction ledger (embedded there) makes residuals self-computing — no retrospective cherry-picking. The return schema requires method, unit, condition, replicate count, deviation code, raw value, pass/fail, and attachment path for every measurement.

### 8a. Scale ladder (promotion criteria)
| Scale | Batch | Purpose | Promote if |
|---|---|---|---|
| Screen | 250 g mixed | compatibility, gel/phase split, fast solids/VOC/KU check | no gel/phase split; Tier-A gates hold |
| Bench | 1 kg/component | drawdown, spray, pot life, adhesion/corrosion panels | meets envelope in triplicate |
| Kit | 5 gal kit | packaging, mix-volume, spray handling, retained samples | same props within SPC limits |
| Pilot | 50 gal pilot | process sensitivity and scale-up repeatability | full QC + accelerated stability + retains |

### 8b. Panel prep, environment, and early kill gates
Panels: SSPC-SP10/NACE No.2 near-white blast, 2.5-3.5 mil profile, soluble salts recorded, blast-to-coat time recorded. Environment: ambient T/RH, substrate temperature, dew point, material temperature, and dew-point margin recorded at prep/application/cure. Kill gates: gel/phase split, pot life below 90 min, VOC >340 g/L, volume solids outside 63-67%, severe sag/pinhole/solvent pop, failed adhesion, or early corrosion failure.

### 8c. Robustness stress matrix (Round-3, before pilot)
Each carried candidate is stressed at: 65°F/85%RH (cold-humid cure + blush), 95°F/50%RH (fast cure, short pot life), material at 60°F (viscosity/atomization), slight overbuild (sag/solvent-pop at >9 mil WFT), and application near pot-life end (atomization/film-defect). Each maps to an envelope application limit.

## The 15 feasibility/process questions — answered
> Honesty tag: these are answered from established coatings-process KNOWLEDGE + the engine's cited design rules — they are engineering guidance, NOT bench-validated performance claims for this specific formulation. Anything performance-dependent (cure, corrosion, adhesion, real sprayability/sag) is bench-gated per the honesty ledger.

**Q1. manufacturing challenges of solvent-borne epoxy-polyamide at ~65% volume solids?**  Holding 65+/-2% VOLUME solids at spray viscosity is the central challenge: it demands high-NV binder cuts, disciplined solvent-split control (our split is SOLVED, not trimmed), and dense-extender restraint (our Monte-Carlo showed barytes-heavy packs breach the ~9.1 lb/gal weight line under normal lot tolerance -- packs were redesigned accordingly).

**Q2. scale-up risks pilot to production?**  Scale-up risks: dispersion heat at larger mill loads (pot-life loss), viscosity drift from lot EEW/amine-value variation (our tolerance Monte-Carlo quantifies the +/-2% EEW / +/-5% amine-value envelope), and solvent flash during transfer. Pilot->production holds tip speed + grind temperature constant and re-verifies KU-vs-time at each scale.

**Q3. minimum equipment for consistent manufacturing?**  Minimum equipment: high-speed disperser (Cowles), jacketed stainless mill vessel, Hegman gauge, Stormer viscometer, density cup, filter/fill line; media mill only if carbon-black grind cannot reach Hegman 6.

**Q4. facility controls for safe solvent and polyamide handling?**  Facility controls: flammable/combustible solvent handling (n-butanol flash 36C, mineral spirits ~40C, high-flash naphtha ~40C+ -- Class IC/II, less volatile than the earlier xylene option removed under C-005) -- grounded/bonded transfer, explosion-proof motors, LEL monitoring, NFPA 30/33 storage+spray; amine PPE with sensitization controls and ventilation for polyamide handling (OSHA HazCom).

**Q5. in-process controls critical for viscosity and pot-life consistency?**  In-process viscosity/pot-life control: Stormer KU at letdown and packout vs control limits; per-batch record of KU-vs-time on the mixed 1:1 sample (the week-1 CRO map defines the limits); temperature-corrected readings.

**Q6. factors most influencing long-term shelf stability?**  Shelf stability drivers: pigment settling (dense extenders -> our packs cap barytes; organoclay anti-settle in the process), moisture pickup in the amine component (dry N2 headspace), and container corrosion; 36-month claim remains a FLAGGED extrapolation from D1849 accelerated data until real-time data exists.

**Q7. process variables most affecting sprayability and film build?**  Sprayability/film-build variables: mixed KU (target the qualified-class 90-105 KU window), thinner discipline (VOC ceiling consumes headroom fast: ours is designed to <=320), tip size/pressure, and WFT control 7-9 mils (SOLVED coverage 175-230 ft2/gal at 4.5-6 DFT).

**Q8. process issues commonly causing pinholing or poor wetting?**  Pinholing/poor wetting: solvent-release imbalance (our evaporation ladder pairs a fast aromatic with a slow H-bonding tail), under-dispersion (Hegman >=6), substrate contamination on SP-10 blast, and excessive film build; mitigations are process-side and specified in the QC section.

**Q9. supply-chain sensitivities?**  Supply-chain sensitivities: every BOM line is a PROPERTY-WINDOW (EEW/amine value/density/OA), not a brand. DGEBA-828-class and polyamide-curative alternates exist in the source ledger, but domestic/TAA status, PFAS declarations, TSCA declarations, and lead times are RFQ/supplier-declaration items. Single-source risk concentrates in specialty additives (flagged).

**Q10. early indicators of loss of process control / impending batch failure?**  Early loss-of-control indicators: grind-temperature rise, KU drift between consecutive batches, Hegman regression, settling on standing, and gel particles at the filter -- each with a stop-rule in the batch record.

**Q11. non-destructive in-process measurements for dispersion/viscosity/cure before packaging?**  Non-destructive in-process measurements: Hegman fineness, Stormer KU, density cup (solids proxy), and mixed-sample KU-vs-time (cure onset) -- all before packout; FTIR epoxide-band decay optional at the lab tier.

**Q12. environmental variables affecting manufacturing consistency vs field performance?**  Environmental variables: grind temperature and ambient RH dominate MANUFACTURING consistency; substrate temperature vs dew point and RH<=85% dominate FIELD performance (amine blush risk on the polyamide side is comparatively forgiving -- a reason the class persists).

**Q13. application-environment limits most sensitive / most frequently exceeded + mitigations?**  Most-exceeded field limits: application below 65F surface temperature (slows the polyamide cure disproportionately) and RH near the 85% ceiling; mitigations: induction 30 min, dew-point margin >=5F rule, DFT gauging per SSPC-PA 2.

**Q14. process documentation, batch-record detail, operator training for repeatable performance?**  Documentation/training: full batch records (lots, mill parameters, KU/Hegman/density, deviations), operator training on dispersion endpoint + solvent/amine safety, and the structured CRO capture template (this package) as the data spine.

**Q15. process controls / data-trending for long-term cross-campaign consistency?**  Cross-campaign trending: SPC on KU, density, Hegman, VS and Method-24 VOC per batch, tied to ingredient-lot EEW/amine-value records so drift attributes to inputs -- the same schema the engine's feedback loop ingests.

## Validation cards (summary — full cards in validation_cards.md)
- **cure_potlife**: FAIL — >=80% of held-out systems within x/1.5; else pot-life gates at 2x crude margin + week-1 CRO KU map
- **corrosion_rank**: FAIL — >=3 strictly-in-class table-read series each rho>=0.6; corrosion NEVER gains gate authority
- **solvency**: PASS — precedent blends RED<1; else solvent axis collapses to direct-precedent blends only
- **viscosity**: PASS — F160 and NCP KU both in (70.0, 110.0) AND NCP>=F160
- **barrier_directional**: MODELED-DIRECTIONAL — index reflects the direction of every content-ladder study; the track rank is LOCKED for bench falsification. 

**Model-coverage honesty (which models actually touch the delivered lead):** the VISCOSITY model passed its card AND scores the lead (KU ~87, sprayable band). The SOLVENCY model passed on precedent test blends, but the lead's high-flash naphtha has no public Hansen data, so the lead's solvency is scored by GOVERNMENT PRECEDENT, not the model. The CURE and CORROSION models FAILED their pre-registered bars and are bench-gated. So the delivered candidate rests on **exact Tier-A arithmetic + one validated model (viscosity) + cited design rules**; pot life and corrosion are decided at the bench.

## Known-answer credibility (full report in known_answer_report.md)
- Tier-1 arithmetic audit vs published SPF: VS Δ-1.31 pts (bar ±1.5) → PASS; density Δ0.038 g/mL (bar ±0.05) → PASS
- Tier-2: zero-prior class recovery — the funnel independently derived the qualified-class architecture (grade pairing, solvent families, silica barrier pack, color twins); envelope-forced vs derived is stated explicitly in the report. Zinc phosphate is isolated to Enhanced-65.
- Tier-3: 3/3 negative controls rejected by the correct gates.

## Discovery Annex (quarantined)
Discovery items are reported in discovery_annex.md as separate future programs and are NEVER substituted into Envelope-65 without a new gate package.
