# Dataset Reconnaissance, Multilingual Literature & Candidate Formulation Directive

### Companion to the Formulation Charter — Evidence-Sourcing and First-Recipe Program for the Coatings Portfolio

**Artifact class:** Engine directive (objectives + constraints only — not a dataset list, not a formulation instruction)
**Scope:** All scored modules in the amphora-* portfolio, the marine hull primer technical envelope, and any adjacent scientific gap the engine identifies
**Authority ceiling:** AUDIT-ONLY / EVIDENCE-ONLY. Discovery, recommendation, and draft formulation only — **no acquisition, no execution authorization**. Rights review and lab execution remain human steps.
**Version:** v2 (adds the Candidate Formulation mandate; template-first — reusable for future partner programs by swapping the envelope and gap-inventory sources)

---

## 1. Mandate (twin, coupled)

**Mandate A — Dataset Reconnaissance.** The engine conducts an exhaustive, self-directed reconnaissance of the world's experimental data and scientific literature relevant to the coatings portfolio — and returns a ranked, cited, rights-annotated **Dataset Ledger** identifying the best available evidence sources for closing each module's scientific gaps. The engine determines for itself what data it needs, derived from the portfolio's own gap inventory, and searches the global record **in every language where the relevant science is published**.

**Mandate B — Candidate Formulation.** The engine delivers a complete, concrete, CRO-executable **candidate formulation-and-process blueprint** conforming to the attached technical envelope — a real recipe the wet-lab program can mix, apply, and test. Waiting for perfect data is not permitted: the engine formulates with the best evidence available today, declares exactly where that evidence is strong, modeled, or assumed, and lets the wet lab close the gap. The bench results returned against this recipe feed back to fine-tune the engine, per the Charter's closed loop.

**The coupling is the point.** The recipe is the demand signal for data; the ledger is the supply. Every element of the recipe that rests on weak or absent evidence must cross-reference the specific Dataset Ledger entry (or commissioned-measurement candidate) that would harden it. Every ledger recommendation must state which recipe element or module gap it serves. Neither deliverable is complete without the other.

This is a discovery-and-draft directive, not an acquisition or execution directive. The engine recommends and drafts; humans review rights, clear licenses, and authorize lab work. Nothing in this directive authorizes downloading external material or executing any formulation.

## 2. Operating Principle — Zero Prior, Self-Directed, Fully Accountable

The engine approaches both the data landscape and the formulation problem as if for the first time. It must:

- Derive its search strategy and its formulation from the envelope, first principles, and the open literature — not from any pre-supplied list or pre-selected answer. Previously furnished dataset lists are **candidates to be evaluated, not defaults to be trusted**.
- Construct and publish its own evaluation rubric for datasets and its own design rationale for the recipe, so a human can audit both. Rubric and ranking must be deterministic and reproducible over the same candidate snapshot.
- **Formulate under uncertainty, honestly.** An incomplete evidence base is not a reason to withhold a recipe; it is a reason to rate confidence per element and route the uncertainty into the test plan. Hidden uncertainty is a violation; declared uncertainty is the deliverable working as intended.
- Surface its own assumptions explicitly. Where a data gap is unfillable by any known public source, an **empty result is a valid and reportable answer** — it converts into a commissioned-measurement candidate, never into silent padding.
- Render a verdict on **every** candidate dataset it evaluates, including every entry from previously supplied lists. No candidate may be silently dropped (Section 8, Disposition Ledger).

**The one binding limit on this freedom:** however wide the search and however sophisticated the internal machinery, the delivered ledger and recipe must be human-interpretable, fully cited (native script preserved), license-annotated, confidence-rated, and — for the recipe — executable by a contract lab exactly as written, without reverse-engineering intent or filling gaps. Novelty in method is unbounded; opacity in the deliverable is not permitted.

## 3. Gap-Derived Targeting

The engine's data targeting is anchored to declared and discovered needs:

- Every open data ask in the current data-acquisition queue.
- Every Pre-Tier-0 module whose promotion blocker names a missing dataset or measurement class.
- Every lab-in-the-loop experiment specification that references an external corpus, comparator, or label source.
- **Every recipe element (Section 7) whose evidence tier is MODELED or ASSUMED** — the formulation itself generates targeted data asks.
- Any additional gap the engine's own research identifies that the human authors did not — flagged as engine-identified and justified from the module's mission and evidence record.

For each gap, the engine states in plain language: what measurement or label class is missing, at what minimum n, under what measurement standard, and what a qualifying dataset would have to contain.

## 4. Multilingual Scope (binding)

A substantial fraction of the world's coatings, polymer, corrosion, and formulation science is published outside English — and some of the deepest experimental corpora (marine corrosion exposure series, polymer property handbooks, cure-kinetics studies, national standards test data) exist only in their language of origin. The engine must therefore:

- **Query in the language of the literature.** Formulate native-language search queries — not translated-from-English keyword guesses — using the domain terminology a practitioner in that language community would actually use. Illustrative, non-exhaustive language communities with deep relevant literature: Chinese, Japanese, German, Russian, Korean, French, Spanish, Portuguese, Polish, Czech, Dutch, Italian. The engine extends this list wherever its research indicates relevant publication activity.
- **Search native repositories and indexes, not only English-language aggregators.** Illustrative, non-binding examples of the *class* of source intended: national materials databases (e.g., Japan's NIMS/PoLyInfo class), national standards bodies and their test-data annexes (GB/T, JIS, DIN, GOST, KS, NF class), national research-institute archives, regional journal indexes (CNKI/Wanfang, J-STAGE, KCI, eLIBRARY, SciELO class), theses and dissertation repositories, and government/defense technical-report archives. These examples define the search's *shape*, not its boundary.
- **Map foreign standards to their ASTM/ISO analogues.** Where a dataset's measurements were taken under a non-US standard (e.g., a GB/T salt-spray protocol vs. ASTM B117, a JIS viscosity method vs. ASTM D2196), the engine must identify the closest ASTM/ISO equivalent, state the known methodological deltas, and rate the comparability. A dataset is not disqualified by its standard — but an unmapped standard is an integrity gap that must be declared.
- **Guard translation and locale integrity.** The portfolio has already documented a 13–169× literal-reading trap from locale typography in a transcribed comparator. The engine must treat every cross-language transfer as a potential unit, decimal-convention, nomenclature, or transliteration hazard: state units as published, convert explicitly with the conversion shown, preserve the native-script citation alongside any romanization, and flag machine-translation passages whose technical meaning it cannot verify with a translation-confidence rating rather than silent acceptance.

## 5. Fixed Constraints (binding)

- **No acquisition.** The engine never downloads, caches, scrapes at volume, or ingests candidate datasets. It reads enough (abstracts, documentation, data descriptors, license pages, sample records where openly displayed) to evaluate — nothing more.
- **No execution authorization.** The candidate formulation is packaged as a draft for CRO feasibility review (`execution_authorized: false`). It carries no safety, synthesis, procurement, or qualification authority. Only the human transfer path (draft packet → rights and safety review → contracted lab under custody) may execute it.
- **Envelope conformance.** The primary recipe must satisfy every fixed constraint and performance target of the attached technical envelope exactly — two-component epoxy-polyamide, nominal 1:1 by volume, solvent-borne, ~65% (±2%) volume solids, VOC ≤340 g/L, and the full application/performance envelope. Superior non-conforming chemistries go to the Discovery Annex, never into the primary recipe.
- **Rights before enthusiasm.** Every ledger entry carries its license or rights status as published, verbatim where possible, with any ambiguity flagged for counsel rather than resolved optimistically. Paywalled, restricted, or license-ambiguous sources are eligible for the ledger — clearly marked — because knowing a blocked source exists is itself actionable.
- **Evidence-tier discipline.** Claims about a dataset's contents are cited to its documentation. Every recipe element carries a tier (Section 7). Estimates are labeled as estimates. Nothing is asserted about data the engine has not seen, and no number is fabricated to make a table complete.
- **No gate-weakening.** If honest formulation cannot land a target inside the envelope with defensible confidence, the engine says so and specifies the experiment that resolves it. Thresholds are never relaxed and fixtures never substituted to make the recipe look finished.
- **Confidentiality preserved.** No output names the masked customer, the CTO, or any internal identity. Chemistry in any externally shareable rendering remains at role-class level; the full-detail recipe is LOCKED-INTERNAL and CRO-facing only.
- **AUDIT-ONLY framing** appears on every page of every deliverable.

## 6. Dataset Evaluation Dimensions (floor, not ceiling)

The engine constructs and publishes its own rubric, which must address at least:

- **Gap fit** — which module gap or recipe element the dataset addresses, and whether it meets the stated minimum n and measurement class.
- **Provenance & measurement quality** — who measured, under what standard, with what instrumentation and uncertainty reporting; primary experimental data ranked above compilations, compilations above extracted/estimated values.
- **Rights clarity** — license as published, redistribution terms, and the specific human action needed to clear it.
- **Uniqueness** — whether the dataset supplies evidence unavailable in any already-held or already-recommended source; overlap declared to prevent double-counting and leakage.
- **Integrity risk** — translation/unit/locale hazards, digitization quality, known errata, version instability.
- **Acquisition cost & friction** — free/open vs. request-gated vs. commercial, estimated lead time, and the single next human action that unblocks it.

## 7. Candidate Formulation Package (Mandate B deliverable — floor, not ceiling)

A complete blueprint a contract lab can execute as written. At minimum:

- **Formulation & BOM.** Every raw material in both components — resin, curative, solvents, pigments, extenders, additives — with its function, target % by weight, key grade/spec attributes, and at least one candidate commercial source (domestic-sourcing preference flagged per the Charter). Explicit arithmetic showing how the formulation lands the 1:1 mix ratio, ~65% volume solids, ≤340 g/L VOC, pot-life, and DFT targets — mass balance and stoichiometry (EEW/AHEW) shown, not asserted.
- **Mixing, induction & application.** Component A/B preparation, induction behavior, thinning limits, and application parameters against the envelope's WFT/coverage/cure schedule.
- **Bench-scale process.** The mix/dispersion sequence and parameters at wet-lab batch scale, with the scale-sensitive steps flagged for the later pilot path.
- **Per-element evidence tier.** Every ingredient choice, loading level, and process parameter is tagged **MEASURED** (cited primary data), **MODELED** (engine or literature model, method named), or **ASSUMED** (stated rationale, no direct evidence) — each with a confidence rating. Every MODELED/ASSUMED element cross-references the Dataset Ledger entry or commissioned measurement that would harden it. This crosswalk is mandatory: it is how the recipe and the ledger justify each other.
- **Alternates.** Where evidence cannot distinguish between candidate ingredients (e.g., two curatives, two thinner systems), the engine ships the primary plus ranked alternates with the discriminating experiment named — so the lab tests a decision, not a guess.
- **Pre-registered test plan.** A formulation-and-test protocol qualifying the system against the envelope and the relevant MIL-DTL-24441-class requirements, conforming to the portfolio's common transfer path and promotion/kill gates: methods and standards named, acceptance thresholds and kill criteria locked before any measurement, splits declared, uncertainty quantified (not point-only).
- **Structured data-capture template.** Exactly which bench measurements, conditions, deviations, and outcomes the lab must return — candidate-bound, units specified — so results flow back to fine-tune the engine on the next iteration.
- **Known failure modes.** Pinholing/wetting/film-build and pot-life risks specific to this recipe, the application-limit parameters most likely to be exceeded, and their mitigations.

A recipe element the engine cannot defend is reported as such, with its resolving experiment — an honest hole in the blueprint is compliant; a confident-looking guess is not.

## 8. Required Deliverables (complete set)

**A. Dataset Ledger.** One structured entry per recommended source, in the portfolio's existing data-ask schema: identity and native-script citation; language; publisher/custodian; URL/DOI; license as published; measurement standard(s) with ASTM/ISO mapping and comparability rating; estimated records and coverage; the module gap **and/or recipe element** it unlocks; integrity risks; translation-confidence rating where applicable; the exact next human action; overall confidence flag.

**B. Disposition Ledger.** Every candidate evaluated — engine-discovered and human-supplied alike — receives exactly one verdict with a stated reason: **RECOMMENDED** (enters the Dataset Ledger), **CONDITIONAL** (scientifically fit but blocked; blocker named and routed to the human/counsel action that clears it), or **REJECTED** (specific disqualifying finding). "Not selected" without a reason is not a permitted state.

**C. Coverage Map.** Gap-by-gap and recipe-element-by-element: the best recommended source, the best conditional source, and — where nothing public exists — an explicit statement converting the gap into a commissioned-measurement candidate for the lab-in-the-loop program.

**D. Search Record.** The rubric used, language communities and repository classes searched, and the queries' native-language forms — sufficient for a human to audit what was and was not looked at, and for the next run to extend rather than repeat the search.

**E. Candidate Formulation Package.** The full Section 7 blueprint, packaged per the portfolio's CRO-packet conventions (`execution_authorized: false`, claim locks intact), with its evidence-tier crosswalk into A and C.

## 9. Discovery Annex (separate, quarantined)

Superior chemistries, alternative feedstocks, adjacent coating systems, and data sources for adjacent problems uncovered during research are valuable and must be reported — in this quarantined annex, never substituted into the compliant primary recipe or mingled with the gap-targeted ledger.

## 10. Cadence & Freshness

Each run records its snapshot date; subsequent runs diff against the prior ledger and prior recipe revision — new sources, changed licenses, superseded datasets, and every recipe element whose evidence tier improved (or degraded) since the last run. As lab results return, the recipe revision history must show which elements moved from MODELED/ASSUMED to MEASURED and on what evidence. A recommendation or recipe element is never silently carried forward — it is re-verified or re-flagged.

---

*Reuse: for subsequent partner programs, replace the technical envelope (Section 5, envelope conformance) and the gap-inventory source (Section 3) with that program's equivalents. Sections 1–2, 4, and 6–10 are the standing scaffold.*

*AUDIT-ONLY: no procurement, product qualification, safety, synthesis, execution, rights determination, or freedom-to-operate authority is asserted or granted by this directive or by any deliverable it produces.*
