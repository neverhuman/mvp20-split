# Research Identity Contracts

- Package: `amphora-contracts-research` 0.2.0, wire1; BP-06.01/B1 initial subset.
- Design: [Candidates](../../docs/Architecture/Research/Candidates.md), [experiments](../../docs/Architecture/Research/Experiments.md).

Public imports use `amphora_contracts_research`; only Core and Pydantic dependencies. DTOs are immutable, strict, bounded and extra-forbidden. No service code, storage, scientific evaluation or permission is provided.

CandidateRevision identifies an intended design with its exact representation artifact. SampleIdentity identifies a physical sample, its exact candidate revision, optional exact material-state revision, and identity-evidence artifact. Missing material state stays null; nominal equality never invents a preparation history or specimen. MaterialStateRevisionRef is only a reference here; processing/morphology records and scientific eligibility remain BP-06.04.

ResearchQuestion pins objective, scoped applicability artifact and predeclared answer criteria. EvidenceNeed pins an exact question revision, selected criterion IDs, required method schema and scoped context artifact. These records describe required evidence; they neither assert that a question is answered nor publish Knowledge claims. Text/criterion descriptions are data, never executable instructions.

The Research owner verifies matching scope, duplicate/unknown criteria, exact predecessor chains and referenced candidate/question existence. Artifact availability/current rights require public Data checks. JSON Schema shape validity cannot authorize evidence use. A future owner store must enforce immutable identity/revision, compare-and-swap heads and replay; this package alone has no durability. Corrections use a new revision rather than silently changing an existing record.

Tests in `tests/` exercise Python/JSON Schema parity and distinct scientific identities. The schema exporter publishes both modes. Replacement preserves public roots and shape fixtures; service behavior is specified separately in the source-adjacent Research README.

Version0.2.0 adds ResolveIdentity and IdentityResolution for authenticated scoped reads. authority is the literal identity_only; matching proves exact owner record correspondence, not artifact rights or scientific eligibility. These additive roots leave prior identity/question schemas unchanged.
