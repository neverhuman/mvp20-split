# Research experiment expectations

- Status: BP-06.04/B1.04 domain objects and explicit public mappings implemented in Research0.16.0/contracts0.7.0. New scientific storage, authenticated ingestion and public APIs remain later milestones.
- Owner: Research. Design: [Experiments](../../../../../docs/Architecture/Research/Experiments.md).

identity.py owns scoped ExperimentReference and immutable one-step ExperimentIdentity revision chains. model.py composes an Experiment from ProtocolContext, exact SampleContext entries and MeasurementExpectations. Each expectation identifies its sample, readout criterion, numeric/categorical/series shape, exact units and replicate/control role. ProtocolContext requires a method revision plus scoped applicability/source Artifacts. Applicability is a reference to reported context, not a universal assay-validity policy.

SampleContext composes the existing SampleDefinition boundary. Supplied material state must match the specimen's exact state and candidate references. A missing state stays unresolved even if the sample names a state reference. Experiment lookup returns an exact expected sample/readout or None; it does not search for similar materials. Collections are bounded and reject duplicate sample references/expectation IDs, cross-scope samples and unbound expectations. Multiple controls/replicates remain distinct expectations.

There is no I/O, persistence, authentication, scheduling, LIMS/CRO submission, statistical aggregation or scientific eligibility authority. Dependencies are public core/research contracts and private Research identity/material/measurement objects. Public DTO mappings preserve these boundaries; future storage adapters must also preserve them; callers outside Research cannot import them. Unknown state and weak quality do not impose a global campaign gate.

Replacement tests live in tests/experiments; select with dev/run_tests.py --module research --area experiments. Preserve exact method/context/sample/state identities, control roles, original units, unknown state and correction immutability. Invalid structures raise stable ExperimentError codes; invalid measurement unit tokens retain MeasurementError. Physical experiments and authenticated report reconciliation require later implementation and proof.

BP-06.04/B1.04, Research0.16.0/contracts0.7.0: wire.py now maps ExperimentDefinition, including existing SampleIdentity and optional full MaterialStateRevision. Decode reconstructs the aggregate and rejects unbound/swapped specimens. Public contracts are exported only from amphora_contracts_research. No new storage, source authentication, HTTP API or campaign effects are added by these mappings.
