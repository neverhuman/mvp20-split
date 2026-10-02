# Research Service

- Status: BP-06.01 accepted; independent identity/question policies and PostgreSQL revision ledger implemented. Authenticated identity-only read API and explicit loopback hosting implemented.
- Package: `amphora-research` 0.6.1.
- Design: [Research](../../docs/Architecture/Research/Research_Architecture.md).

Research owns intended candidate, physical sample, question and evidence-need identity. It does not own artifact bytes, Knowledge assertions, model execution or campaign acceptance. Dependencies are public Core/Research contracts and SQLAlchemy/psycopg/Alembic, FastAPI/Pydantic and Uvicorn; no imports of Data/Runtime/Knowledge implementation or access to their SQL tables.

The [identity module](src/amphora_research/identity/README.md) implements candidate/sample scope and correction-chain checks, exact identity reconciliation and question/need invariants. It supplies no public endpoint and must not be imported by another owner. The [transport module](src/amphora_research/transport/README.md) exposes authenticated exact identity reads; no scientific adjudicator is implemented. [Private persistence](src/amphora_research/persistence/README.md) now owns immutable candidate/sample/question/need revisions, exact local links, atomic head updates and replay. Data owns artifact-rights enforcement. B3 verifies actual peer reads of questions/needs and their finalized Data references; the declaration itself grants neither artifact access nor scientific acceptance. Independent installed-owner replacement passed:70 owner tests,36 replacement API tests and actual Data peer/history proof. Full material-state/processing and observation eligibility remain BP-06.04.

Use [config.example.json](config.example.json) for environment references only; apply owner migrations explicitly, then run amphora-research check/serve with configured research_service credentials. No default credential or external binding is provided. Public clients consume versioned DTOs over HTTP, never import this service.

BP-06.03/B1 adds the private [assessment policy](src/amphora_research/assessment/README.md): pinned question/need requirements, exact answer/method/context/issuer/purpose matching, explicit gaps and contradiction retention. It distinguishes answered, sufficient for a synthetic decision and scientific establishment. This pure module performs no I/O and creates no owner receipt. Authenticated evidence resolution, durable assessments and public assessment routes remain pending. Existing public schemas and research_0001/0002 are unchanged.

B1.06 adds public Research contracts0.3.0 and ConfiguredAssessment/BoundAssessment mappings. Profiles bind trusted publishers, expected target digests and exact subject; request inputs remain reference-only. Eight additive schemas preserve all286 predecessors.294 scoped tests and177 isolated installed-owner/contract tests pass. No new assessment HTTP operation or migration is introduced; B1.07 owns authenticated producer resolution next.

B1.07 checkpoint: AssessmentDataReader verifies public Data bytes/derivation producers under bounded authenticated reads.184 Research/dev tests pass (32 reader cases). Actual owner compatibility, payload interpretation and declaration/target binding remain; B1.07 is not complete. Public Artifacts0.2.0 is now an explicit dependency; no peer implementation import or SQL access.
