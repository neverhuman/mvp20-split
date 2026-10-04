# Research declaration registration

- Status: BP-07.02/B2.03a.ii verified 2026-10-04 10:04:40;382 installed owner/contract cases and2 actual HTTP interruption stages passed.
- Package: Research0.34; public Research DTOs0.14 unchanged; forward migration research_0013.
- Design: [owner handoff](../../../../../docs/Build%20Plans/BP-07/BP-07.02%20Owner%20handoff%20and%20accepted%20replay.md).

## Boundary

Registration owns authenticated question/evidence-need declaration writes and their first-public-registration provenance. It does not fulfill questions, assess answers, validate scientific methods, consume Artifact contents, check source rights, publish Knowledge or modify campaign pins. Artifact and SchemaRef fields remain exact declared references, not verified peer capabilities.

`DeclarationRegistrar.register(principal, record)` accepts only ResearchQuestion or EvidenceNeed, revalidates the wire DTO even for private callers, requires the exact scope and separate declare_question/declare_evidence_need grant, then prepares an IdentityDocument. QuestionDefinition and the identity ledger own scope, criteria, immediate predecessor/head and exact question binding rules. A need may reference an explicitly selected historical question revision; no implicit latest selection occurs.

## Transaction and recovery

IdentityLedger.publish_prepared composes within the registrar's short transaction. A stable scoped identity advisory lock serializes record/head/link changes and registration insertion. Canonical declaration bytes and first-registration metadata commit together; no network or model call occurs under SQL. The metadata stores actor, canonical digest, database timestamp and whether an identical private record already existed. That actor is the first public registrant, not a retroactively inferred original creator.

An exact reference and canonical bytes are the retry identity. Identical retries return the stored declaration and retain original public metadata, including when another authorized actor retries. Changed bytes conflict; skipped/stale succession conflicts. A failed metadata insertion rolls back identity and head effects. A lost response is reconciled through exact read/retry, never a fresh identity. Service grants on metadata are SELECT/INSERT only. Existing identity and historical bytes are unchanged.

## Public hosting

Explicit configuration `"declarations": true` enables POST /v1/questions and /v1/evidence-needs. Missing/false leaves write routes absent. Registration grants without enabled configuration fail startup; read grants remain distinct. Startup checks the registration table and never migrates. Existing /read routes return exact declarations.

Writes accept application/json, at most256KiB, with a5s body deadline and strict duplicate/nonfinite/DTO validation. Success200 acknowledges a declaration only. Authentication401, permission/scope403, missing question404, immutable/head conflict409, malformed/policy422, body limit413, SQL failure503 remain distinct with safe codes. Database connect/statement bounds are provided by the host. No automatic infrastructure retry occurs.

## Replacement and verification

Apply research_0013 with Research0.34 or later; never invoke <=0.33 migrators on the upgraded database. Declarations require the new owner package; old read-only hosts do not expose writes. Historical seeded records remain readable and retain explicit preexisting provenance when first publicly registered.

Tests live in tests/declarations; identity-ledger regressions stay in tests/persistence and existing API tests stay in tests/api. The declaration suite covers replay/origin, exact binding, conflict/concurrency, atomic rollback, grants, DTO revalidation, default-off hosting and wire limits. Test-only fault_host.py pauses the production transaction before commit or after commit/before response; it is excluded from wheels. dev/verify_research_declarations.py builds two isolated installs and runs real HTTP interruption/replacement against retained PostgreSQL. Synthetic registration proves software ownership only.
