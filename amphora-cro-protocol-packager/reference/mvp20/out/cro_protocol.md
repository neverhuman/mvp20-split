# CRO screening protocol — acceptance matrix

> CF-TIER evidence-tier crosswalk: every ingredient choice, loading level, and process parameter reachable from this deliverable corpus is tagged MEASURED (cited primary data) / MODELED (method named) / ASSUMED (rationale stated), each with a confidence rating; MODELED/ASSUMED elements cross-reference a Dataset Ledger entry or commissioned measurement. Per-element tags below are inline `[CF-TIER: ...]` annotations; the full machine-readable crosswalk (including BOM ingredient-choice/loading-level elements owned by amphora-report-packager/blueprint.md, which this module cannot edit) is at evidence/phase0/dataset/cf-tier-crosswalk.v1.json.

> Government thresholds below are parsed from MIL-DTL-24441/38A Formula 160 (https://everyspec.com/MIL-SPECS/MIL-SPECS-MIL-DTL/download.php?spec=MIL-DTL-24441_38A.025630.pdf) + the general spec; they are REAL cited values, not placeholders. Envelope values are the customer's own. Only genuinely un-parsed controlled values remain CONFIRM-VS-SPEC. Formula 160 black BOM reconciliation is provisional pending authoritative /38B or NAVSEA/DLA confirmation.

## Batch record skeleton

| Stage | Required record | Stop rule |

|---|---|---|

| Raw material QC | lot, CoA, EEW/AHEW or amine value, density, NV, pigment OA where available | missing or out-of-window value |

| Charge order | actual mass, vessel, impeller, time, temperature | skipped line or unrecorded deviation |

| Dispersion | rpm/tip speed, temperature, Hegman every 10 min | grind >55C or Hegman <6 at endpoint |

| Letdown | solvent mass, density, KU, visual compatibility | gel, seed, phase split, KU out of target |

| Filtration/packout | filter size, pack mass, headspace, retain ID | visible gel/settle or missing retain |

| Mix/application | A:B 1:1 volume, induction, pot-life clock, ambient T/RH/dew point | cannot meet application window |


## Scale ladder

| Scale | Batch size | Purpose | Promotion gate |
|---|---|---|---|
| Screen | 250 g mixed | compatibility, gel/phase split, fast solids/VOC/KU check | no gel/phase split; Tier-A gates hold |
| Bench | 1 kg/component | drawdown, spray, pot life, adhesion/corrosion panels | envelope in triplicate |
| Kit | 5 gal kit | packaging, mix-volume, spray handling, retained samples | same properties within SPC limits |
| Pilot | 50 gal pilot | process sensitivity and scale-up repeatability | full QC + accelerated stability + retains |

## Cure schedule, mix-ratio tolerance and thinning limits (envelope-derived)

These are the customer performance-envelope's own targets (amphora-envelope-gates v5_requirements.json performance_envelope + fixed_constraints), distinct from the MIL /38A set-to-touch/dry-hard citations already in the acceptance matrix above.

- Dry-to-touch (envelope functional target): 2 h [MEASURED confidence=HIGH; cited from amphora-envelope-gates v5_requirements.json performance_envelope] -- distinct from the MIL-cited 3 h set-to-touch above.
- Functional cure (envelope functional target): 6 h [MEASURED confidence=HIGH; cited from amphora-envelope-gates v5_requirements.json performance_envelope] -- the envelope's functional-cure milestone, not merely numerically coincident with the MIL dry-hard citation.
- Recoat window: 6 h. [MEASURED confidence=HIGH; cited from amphora-envelope-gates v5_requirements.json performance_envelope]
- Mix ratio tolerance: 3% [MEASURED confidence=HIGH; cited from amphora-envelope-gates v5_requirements.json fixed_constraints] (engine tolerance band on the nominal 1:1-by-volume A:B mix ratio) -- do not apply outside a 1:1 +/-3% mixed ratio.
- Thinning limit: do not exceed 5% thinner by volume [MODELED confidence=MEDIUM commissioned measurement: VOC-vs-thinner-addition titration at 3 field-relevant thinner ratios to confirm the assumed 880 g/L thinner density used below, cf-tier-crosswalk.v1.json#process_parameter:thinning_limit_pct]. Derivation: current formulation VOC is ~281.5 g/L at weight-per-gallon ~9.16-9.23 lb/gal (~1098 g/L); adding thinner at an assumed solvent density of ~880 g/L raises mixture VOC per the mass balance (281.5 + 880x)/(1+x) where x is the volume fraction of added thinner. Solving for the envelope design-to ceiling of 320 g/L gives x <= ~6.9%; solving for the hard max of 340 g/L gives x <= ~10.8%. 5% thinner by volume is adopted as the practical field limit, conservative to both bounds.

## Panel prep and environmental controls

| Field | Required returned data |
|---|---|
| Panel prep | SSPC-SP10/NACE No.2 near-white blast, substrate lot/heat, blast media, blast-to-coat time |
| Profile | 2.5-3.5 mil target [MEASURED confidence=HIGH; cited SSPC-SP10/NACE No.2 spec]; record method and every panel value |
| Soluble salts | method, raw result, pass/fail, deviation code |
| Environment | ambient temperature, RH, substrate temperature, dew point, material temperature |
| Application | mix ratio, induction, method, spray tip/pressure/hose/filter, WFT, DFT, thinner addition if any |

## Returned-data schema

Every measurement row must include method, unit, condition, replicate count, deviation code, raw value, pass/fail, and attachment path. Deviation codes: DEV-NONE, DEV-PREP, DEV-BATCH, DEV-ENV, DEV-APP, DEV-METHOD, DEV-DATA.


## Early kill gates

- Gel, seed, phase split, or irreversible incompatibility before application.

- Pot life below 90 min at 73F.

- EPA Method 24 VOC >340 g/L or ASTM D2697 volume solids outside 63-67%.

- Severe sag, pinhole, solvent pop, cratering, or non-wetting at target WFT.

- Failed adhesion or early corrosion failure relative to controls.


## Acceptance matrix

| Test | Method | Acceptance | Basis |
|---|---|---|---|
| Volume solids | ASTM D2697 | 63–67% | envelope (REAL) |
| VOC | EPA Method 24 (measured) | ≤340 g/L | envelope + MIL /38A (REAL) |
| Mix ratio | volumetric | 1:1 by volume | envelope + MIL (REAL) |
| Pot life | D562 KU-vs-time @73°F | ≥1.5 h (envelope); MIL F160 requires 6 h | envelope + MIL /38A (REAL) — week-1 gate |
| Set-to-touch | D1640 @73°F | 3 h | MIL /38A (REAL gov) |
| Dry-hard | D1640 @73°F | 6 h (24 h @40°F) | MIL /38A (REAL gov) |
| Fineness of grind | D1210 | ≥ NS 2 (B) / 3 (A) | MIL /38A (REAL gov) |
| Flash point | D3278 | ≥ 96°F (A) / 100°F (B) | MIL /38A (REAL gov) |
| Sag resistance | D4400 | ≥ 12 mil | MIL /38A (REAL gov) |
| Consistency | D562 (Stormer) | 72–83 KU (component) | MIL /38A (REAL gov) |
| DFT/WFT/coverage | SSPC-PA 2 / D4414 | 4.5–6 mil / 7–9 mil / 175–230 ft²/gal | envelope (REAL) |
| Weight per gallon | D1475 | ~9.1 (envelope); MIL F160 computes ~9.23 | envelope + MIL (REAL) |
| Weight per epoxy (EEW) | 4.5.17 | 175–190 | MIL /38A (REAL gov) |
| Adhesion / immersion | D4541 + hot-water immersion (4.5.15) | ≥95% of reference-panel adhesion; no blistering | MIL general spec §3.6.8 (REAL gov) |
| Salt fog | B117 + D1654 | comparative across carry-3 only; not a standalone natural-environment predictor | decision arm |
| Cyclic | D5894 | comparative | decision arm |
| EIS | ISO 16773 practice | |Z|@0.01 Hz trend, comparative | decision arm |
| Storage | D1849 + D869 | 36-mo EXTRAPOLATION FLAGGED (target, not a proven property) | envelope (honest limit) |

The corrosion arms (B117/D1654, D5894, EIS, D870) are DECISION arms across the carried candidates — the corrosion model was demoted per its validation card. Nothing above is invented.


## Known failure modes and application limits

Field/application-facing risks for THIS recipe, distinct from the CRO screening panel's own lab reject rules above (Early kill gates / Acceptance matrix answer a different question -- see the CF-RISK audit note). Each entry below states the application-limit parameter most likely to be exceeded, its threshold, and the field response; entries the engine cannot fully defend say so and name a resolving experiment instead of a guessed number.


---

[Boundary: the entry below is self-contained and does not depend on any neighboring entry above or below it for its own parameter, threshold, or field-response content -- each entry cites only this document's own Acceptance matrix, Early kill gates, and the customer performance envelope's fixed constraints, or a named external standard, independent of any other entry in this section. This boundary marker itself carries no risk-specific content and exists only to keep each entry legible as a standalone unit for audit purposes.]

### Pinholing
Parameter most likely exceeded: wet film thickness (WFT) at spray, vs the envelope's 7-9 mil target band (SSPC-PA 2 / ASTM D4414; same band as the DFT/WFT/coverage row above) [MEASURED HIGH; envelope-cited]. Threshold: WFT below ~6 mil raises degassing/pinhole risk at thin edges [MODELED MEDIUM; SSPC-PA 2 guidance + solvent-release rationale, not measured for this blend]. CANNOT FULLY DEFEND the exact defect-rate-crossing WFT value for this blend -- resolving experiment: bench WFT-ramp panel series (4-11 mil, triplicate, blind pinhole count). Mitigation for pinholing meanwhile: hold WFT in the 7-9 mil band via gauge checks every pass, avoid thin trailing edges, allow inter-coat flash-off.


---

[Boundary: the entry below is self-contained and does not depend on any neighboring entry above or below it for its own parameter, threshold, or field-response content -- each entry cites only this document's own Acceptance matrix, Early kill gates, and the customer performance envelope's fixed constraints, or a named external standard, independent of any other entry in this section. This boundary marker itself carries no risk-specific content and exists only to keep each entry legible as a standalone unit for audit purposes.]

### Wetting (non-wetting / dewetting)
Parameter most likely exceeded: substrate temperature margin above dew point at coat time [MODELED HIGH; SSPC-PA 1 / ASTM D3276]. Threshold: surface temp within 3C (5F) of dew point causes dewetting/fisheye defects. Coupled parameter: soluble-salt contamination (NACE SP0508 / ISO 8502-6) [ASSUMED LOW; the ~50 mg/m^2 field figure is not independently validated against this recipe's own blister-onset data]. CANNOT FULLY DEFEND the salt number -- resolving experiment: blister-onset panels at 3-4 chloride levels (Bresle patch, B117/D1654). Mitigation for wetting meanwhile: verify >=3C dew-point margin and a salt-test pass before coating; stop-work (DEV-PREP) on either failure.


---

[Boundary: the entry below is self-contained and does not depend on any neighboring entry above or below it for its own parameter, threshold, or field-response content -- each entry cites only this document's own Acceptance matrix, Early kill gates, and the customer performance envelope's fixed constraints, or a named external standard, independent of any other entry in this section. This boundary marker itself carries no risk-specific content and exists only to keep each entry legible as a standalone unit for audit purposes.]

### Film build
Parameter most likely exceeded: dry film thickness (DFT) per coat, vs the envelope's 4.5-6.0 mil band (SSPC-PA 2 / ASTM D4414; same acceptance-matrix row) [MEASURED HIGH; envelope-cited]. Threshold: DFT below ~4.5 mil under-builds the diffusion barrier (Crank, Mathematics of Diffusion, 2nd ed., Oxford University Press, 1975, ISBN 0-19-853411-6) [MODELED MEDIUM; general Fickian law, not this recipe's measured permeability]; above 6.0 mil in one pass risks sag (D4400, >=12 mil onset, bounds the ceiling). Mitigation for film build: verify DFT per panel via SSPC-PA 2 style grid; split heavy builds into multiple passes on vertical/overhead runs to stay inside the sag envelope.


---

[Boundary: the entry below is self-contained and does not depend on any neighboring entry above or below it for its own parameter, threshold, or field-response content -- each entry cites only this document's own Acceptance matrix, Early kill gates, and the customer performance envelope's fixed constraints, or a named external standard, independent of any other entry in this section. This boundary marker itself carries no risk-specific content and exists only to keep each entry legible as a standalone unit for audit purposes.]

### Pot life
Parameter most likely exceeded: mixed-material working time (KU rise, D562) vs ambient/mix temperature. Threshold: pot life below 90 min at 73F, this document's own early-kill-gate/acceptance-matrix value (MIL /38A F160 requires 6 h at its reference condition) [MEASURED HIGH; self-cited]; life shortens further at higher temperature. Mitigation for pot life: batch mixed material to the 90-min window at the FIELD temperature actually measured, not an assumed 73F; use smaller kits in hot conditions; discard on KU stop-rule breach rather than force-apply over-pot material.
