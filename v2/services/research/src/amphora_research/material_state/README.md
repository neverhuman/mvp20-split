# Research material state

- Status: BP-06.04/B1.04 domain objects and explicit public mappings implemented in Research0.16.0/contracts0.7.0. New scientific storage, authenticated ingestion and public APIs remain later milestones.
- Owner: Research. Design: [Experiments](../../../../../docs/Architecture/Research/Experiments.md).

state.py binds a MaterialState to an exact CandidateRevisionRef and MaterialStateRevisionRef. Distinct preparations never collapse on nominal candidate equality. StateIdentity requires root revision1 or an exact one-step predecessor in the same scope and identity. Constructing a successor does not mutate the predecessor or select a new campaign pin.

preparation.py preserves ordered ProcessingEvents, each with method, named conditions and original units, optional duration/atmosphere, actor, optional equipment and source Artifact. A supplied duration must be nonnegative. None means unreported; an empty equipment tuple is distinct. PreparationHistory exposes unknown/proposed/observed/mixed posture. Observed is the source's assertion, not independently verified physical truth. Events, conditions and equipment have bounded immutable collections and unique identifiers; no implicit sorting or deduplication occurs.

features.py preserves measured/inferred/unknown feature evidence. Measured and inferred assertions require method and source; unknown requires MissingValue. An all-missing series cannot claim measured morphology. Numeric, categorical, censored and series values retain measurement uncertainty and original representation. State rejects sources from another scope. It does not decide scientific applicability or material equivalence.

These frozen objects have no I/O, SQL, authorization, lab submission, evidence promotion or Runtime effects. Dependencies are public core/research contracts, Pydantic identifier validation and private Research observation values. Other services must use public versioned contracts, never these implementation imports. Source resolution, storage and corrections are later BP-06.04 milestones.

Replacement verification: tests/material_state, selectable with dev/run_tests.py --module research --area material_state. Preserve same-design/different-preparation identity, ordered conditions/units, explicit unknowns, measured versus inferred attribution, exact predecessor chains and scoped source checks. Malformed structures raise stable MaterialStateError codes; malformed measurement quantities retain MeasurementError.

BP-06.04/B1.04, Research0.16.0/contracts0.7.0: wire.py now maps MaterialStateRevision and reconstructs StateIdentity, ordered preparation and attributed features. Shape-valid duplicates and invalid revision/scope relationships fail owner validation. Public contracts are exported only from amphora_contracts_research. No new storage, source authentication, HTTP API or campaign effects are added by these mappings.
