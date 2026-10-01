# Research Service

- Status: BP-06.01/B3; independent identity/question policies and PostgreSQL revision ledger implemented. Authenticated identity-only read API and explicit loopback hosting implemented.
- Package: `amphora-research` 0.4.0.
- Design: [Research](../../docs/Architecture/Research/Research_Architecture.md).

Research owns intended candidate, physical sample, question and evidence-need identity. It does not own artifact bytes, Knowledge assertions, model execution or campaign acceptance. Dependencies are public Core/Research contracts and SQLAlchemy/psycopg/Alembic, FastAPI/Pydantic and Uvicorn; no imports of Data/Runtime/Knowledge implementation or access to their SQL tables.

The [identity module](src/amphora_research/identity/README.md) implements candidate/sample scope and correction-chain checks, exact identity reconciliation and question/need invariants. It supplies no public endpoint and must not be imported by another owner. The [transport module](src/amphora_research/transport/README.md) exposes authenticated exact identity reads; no scientific adjudicator is implemented. [Private persistence](src/amphora_research/persistence/README.md) now owns immutable candidate/sample/question/need revisions, exact local links, atomic head updates and replay. Data owns artifact-rights enforcement. B3 verifies actual peer reads of questions/needs and their finalized Data references; the declaration itself grants neither artifact access nor scientific acceptance. Independent installed-owner replacement remains V1. Full material-state/processing and observation eligibility remain BP-06.04.

Use [config.example.json](config.example.json) for environment references only; apply owner migrations explicitly, then run amphora-research check/serve with configured research_service credentials. No default credential or external binding is provided. Public clients consume versioned DTOs over HTTP, never import this service.
