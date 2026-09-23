# System Parameters

This document lists the operational parameters the system must represent, compute, enforce, or expose.

## Product Envelope Parameters

- program name and customer/partner context
- material class and domain pack
- intended service environment
- substrate or target application
- process limits and equipment limits
- feedstock and supplier constraints
- cost ceiling and volume assumptions
- restricted substance list
- regulatory jurisdiction
- qualification path and test methods
- hard gates, soft objectives, and information-only rows
- sign-off state and ambiguity register

## Coatings MVP Parameters

### Ingredient Parameters

- name and unique identity
- CAS number where available
- supplier and supplier tier
- role: binder, pigment, filler, solvent, cosolvent, additive, water, curing agent, other
- density in g/mL
- solids fraction
- glass-transition temperature where applicable
- oil absorption for pigments/fillers
- VOC-exempt flag
- water flag
- cost per kg
- restriction/sourcing status
- evidence/provenance notes

### Formulation Parameters

- formulation code and version
- parent formulation id
- status: draft, active, archived, or retired
- component mass fractions, summing to 1.0
- part A / part B assignment for two-component systems
- mix ratio by volume
- stoichiometric balance parameters where applicable
- process notes
- computed property snapshot for display, not authority

### Computed Coating Properties

- wet density
- solids by weight
- solids by volume
- pigment volume concentration
- critical pigment volume concentration
- VOC in g/L using EPA Method 24 convention
- binder Tg by Fox equation
- cost per kg
- cost per liter
- warnings for composition sum, VOC, PVC > CPVC, missing constants, or unsupported roles

### Naval Hull Primer Envelope Examples

From the maritime coating artifacts, the system must be able to represent:

- two-part epoxy-polyamide chemistry
- solvent-borne vehicle
- 1:1 by-volume mix ratio
- ambient amine-epoxy cure
- induction time around 30 minutes
- pot life >= 1.5 hours at about 73 F / 50% RH
- VOC <= 340 g/L where required
- volume solids target around 65% where envelope-specific
- dry film thickness range around 4.5-6.0 mils where envelope-specific
- viscosity and spray-equipment fit
- salt-spray resistance targets
- cathodic disbondment resistance
- underfilm corrosion creep
- adhesion and flexibility
- anti-fouling/biofilm requirements where in scope
- shelf-life targets
- MIL-DTL-24441 qualification path
- NAVSEA/QPL status as external authority, not internal claim

## Suggestion Parameters

- objective property or objective bundle
- eligible ingredient set
- per-ingredient min/max mass fractions
- candidate count
- observed experiments used
- optimizer mode: space-filling under 5 observations, GP/EI at 5 or more observations
- predicted mean and uncertainty
- computed physics properties
- failed constraints and abstentions

## Evidence Parameters

- source artifact id and hash when available
- source type: customer, public, supplier, internal, lab, model output
- license/rights status
- custody state
- module id and version
- method/model card id
- authority tier
- candidate id
- result status: pass, fail, abstain, not applicable, unknown
- limitation statement
- reviewer/signature state
- replay or re-derivation command where available

## Biological and Cross-Domain Parameters

- entity/sequence revision, identifier namespace/mapping, biological system, organism/species, tissue/cell line, and disease/model context
- sample/batch identity, assay/method version, controls, replicates, dose/concentration and units, timing, and route where applicable
- endpoint definition, measured/predicted/inferred posture, uncertainty, censoring/detection limits, contradictory results, and quality disposition
- capability applicability across species, route, formulation, assay, process scale, and endpoint, including explicit unsupported or missing context
- permitted-use/privacy/consent constraints for restricted data and lineage through derived artifacts
- fixed product requirements versus evolvable continuous, categorical, integer, and conditional variables; adapter/operator versions and validation rules
- separate scientific-review, experiment-approval, model-validation, and deployment/authority states

## Source and Acquisition Parameters

The [source/acquisition contract](Data_Sources_and_Acquisition.md) requires:

- source identity/revision, domain/product/project associations, owner/tenant, applicability, and review state
- connector/module version, operations, format/schema, typed ports, identifier namespaces, units, and method context
- endpoint/location and protected credential reference; no secret values in graph definitions or provenance exports
- rights, permitted purpose, access scope, retention/deletion policy, and sharing restrictions
- resolved campaign binding, query/filters, provider version, acquisition timestamp, and required/optional input policy
- snapshot/refresh mode, freshness limit, stream window/cursor/watermark and late/duplicate-event policy where supported
- request/page/record/byte, time, cost, rate, and retry limits; stop conditions and failure dispositions
- completeness, quality/review state, ambiguity, duplicates, contradictions, and unavailable/stale/incompatible-input status
- artifact revision/hash, upstream lineage, transform versions, evidence-bundle membership, consumed inputs, and replay limitations

## Manufacturing Release Parameters

The future terminal artifact must carry:

- locked formulation or composition
- process window
- batch recipe with sequence and operating limits
- supplier-qualified BOM
- QC/SPC release criteria
- batch record template
- lab and pilot evidence package
- deviation handling rules
- customer-specific IP/data restrictions
