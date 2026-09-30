# Research Service

- Status: BP-06.01/B1 partial; independent identity/question policies and PostgreSQL revision ledger implemented. No public server yet.
- Package: `amphora-research` 0.2.0.
- Design: [Research](../../docs/Architecture/Research/Research_Architecture.md).

Research owns intended candidate, physical sample, question and evidence-need identity. It does not own artifact bytes, Knowledge assertions, model execution or campaign acceptance. Dependencies are public Core/Research contracts and SQLAlchemy/psycopg/Alembic; no imports of Data/Runtime/Knowledge implementation or access to their SQL tables.

The [identity module](src/amphora_research/identity/README.md) implements candidate/sample scope and correction-chain checks, exact identity reconciliation and question/need invariants. It supplies no public endpoint and must not be imported by another owner. Independent packaging is a replacement boundary, not evidence that a live Research service or scientific adjudicator exists. [Private persistence](src/amphora_research/persistence/README.md) now owns immutable candidate/sample/question/need revisions, exact local links, atomic head updates and replay. Authenticated lookup, artifact-rights checks and process-kill recovery remain B1-B3/V1 work. Full material-state/processing and observation eligibility remain BP-06.04.
