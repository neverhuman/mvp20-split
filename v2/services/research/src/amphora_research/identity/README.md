# Research Identity Policy

`QuestionDefinition` validates scoped applicability, unique predeclared criterion IDs and exact one-step supersession within a question identity. `bind_need` requires the exact question revision, matching need/context scope, unique known criterion IDs and one-step need supersession. Errors contain stable codes, never document text. `BoundEvidenceNeed` is a declaration binding, not evidence eligibility or a Knowledge claim.

The private owner ledger now checks predecessor existence/current head; artifact rights still require a public Data client. Pure policy does not prove either; it has no I/O, authorization or persistent side effects. No default answer/measurement policy is invented. Tests belong to `services/research/tests/identity/` and cover adversarial scope, stale question revision, criteria and predecessor mismatches. Replacement preserves these semantics independently of transport/ORM choices.

CandidateDefinition and SampleDefinition enforce same-owner scope and exact correction-chain shape. IdentityMatch.reconcile compares explicit requested references to owner-supplied records; unknown/mismatched records quarantine without synthesizing rows. A successful match says exact_identity_only, leaves absent material state unknown and grants no fitness/Knowledge acceptance. Candidate/sample predecessor existence is enforced by the private owner ledger.

Verification:26 owned tests; questions.py41/41 lines and24/24 branches, samples.py54/54 lines and30/30 branches covered. Isolated Research wheels repeat these tests without Data, Runtime, SQLAlchemy or FastAPI installed. This earlier pure-policy checkpoint does not cover the later persistence module, rights, process recovery or scientific policies.
