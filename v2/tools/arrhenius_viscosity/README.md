# Arrhenius Viscosity

- Status: UI-01.03/E1/E2 verified: independent package/Linux calculations and actual Runtime-retained invocations (scientific-run-c).
- Release:0.1.0. Owner: independent scientific tool; no shared scientific service.

Strict Pydantic payloads validate supplied parameters; frozen domain objects own
calculation and result interpretation. Adapter maps malformed data to
invalid_scientific_parameters. CLI compute reads bounded JSON; describe requires an
externally measured image digest; schema publishes exact owned bytes; worker uses
only public Tool Protocol. No SQL, model calls, external scientific data, candidate
generation or peer-private imports. Deterministic pure calculation with no effects.

This is a narrow Python port of explicit v1 formula functions, not the full scoring
module or its trained models. v1 remains read-only. Inputs require candidate_id and
parameter_context; outputs retain all inputs, intermediate quantities, procedure,
units and explicit unvalidated_screen status. Fixture parameters are synthetic;
calculation success does not establish applicability or experimental validity.
Hansen input parameters use MPa^0.5 and dimensionless RED; viscosity uses Pa.s,
degrees C, J/mol and R=8.31446261815324 J/(mol.K). No hidden fitted parameters.

Source: v1/amphora-viscosity-score/src/lib.rs,
arrhenius_viscosity.
Positive finite result guards preserved. Inputs have conservative numeric bounds.
Hansen RED==1 is explicitly boundary, not silently compatible. Viscosity overflow
and underflow-to-zero reject. No synthesis, biology, mixture/cure or generative claim.

Owned tests: tests/kernel. Independent installs must exclude Runtime, Data, Planning
and sibling scientific implementations. Rebuild acceptance preserves schema bytes,
source-equivalent formula, domain limits, safe failure mapping and worker protocol.
Schema/behavior changes require a new release; retained artifacts remain owner data.
