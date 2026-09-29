# Graph Runtime Contracts

- Package: `amphora-contracts-graph-runtime` 0.2.0; existing wire-v1 shapes unchanged, new receipt/wait roots and separately versioned graph observations.
- Owner: Campaign Runtime coordination boundary; Runtime 0.5.0 preserves accepted wire-v2 graph hosting and adds B1 await contracts/compiler/storage. External-wait execution and peer acceptance remain BP-04.03/B2-V1.
- Architecture: [Graph Execution Model](../../docs/Architecture/System/Graph_Execution_Model.md).

Public root imports expose graph admission/advance commands, bounded values, limits and paginated node observations. They reference executable campaign wire-v2 identity while retaining the existing attempt budget and command envelope. This separate package prevents graph authoring dependencies from entering the pinned scientific worker/SDK closure. Existing worker commands and campaign schemas retain their serialized behavior; campaign exports add names for existing literal-value DTOs only.

Values are finite typed scalars, scoped immutable artifact references or one bounded collection layer with explicit missing members. They cannot contain node/input/result references or arbitrary embedded scientific payload objects. Admission carries an exact reviewed plan hash, named values, attempt budget and expansion/time limits. Runtime owns input compatibility, plan trust, scope/authority, readiness, budget and transition behavior; the DTOs do not decide any of them. Command parsing rejects direct or collection artifact references outside the envelope scope before registration.

Number values use plain decimal **strings**, for example `{"kind":"number","value":"2.5","unit":"g/mol"}`. The portable regex bounds magnitude to +/-1e100, at most 100 integer/324 fractional digits (plus the exact 1e100 boundary); exponents, NaN/infinity and JSON floats are rejected. Compiler-authored numeric literals keep their existing representation and are explicitly converted by the Runtime value resolver. This preserves the existing 256-KiB/64-container, safe-integer/float-free command fingerprint profile and all old receipts. Equivalent textual spellings are not silently normalized into the same caller command.

Reads are bounded pages of graph node/path/status observations, not a claim of live worker authority. No public ORM, database client, scientific code, evaluator or service implementation is included. Preserve published wire schemas and command fingerprints across replacement, or explicitly version their boundary. Owned tests live in `tests/`; actual persistence/interpreter proof belongs to Runtime.

B1 scoped verification: 17 command/value cases pass, including decimal fingerprints, artifact scope in collections, rejection of dynamic/untyped inputs and unchanged legacy family dispatch. Contract coverage is 77/79 statements and all six branches; the uncovered unknown-family error path remains part of B2 transport integration. These declaration/parser numbers are not coordinator behavior coverage.

## External receipt and wait extension

`DomainReceipt` separates accepted artifact evidence, rejected, abstained and superseded dispositions. `SubmitDomainReceipt` binds it to run, activation, exact wait revision and expectation hash. `parse_graph_command("graph.submit_receipt", raw)` checks receipt/subject/output scope and requires the envelope actor to match the named issuer before registration. This is a shape/identity check; authenticated configured authority still belongs to Runtime. The unchanged worker parser rejects this command family.

`WaitExpectation` pins issuer/purpose/external revision, exact subject, output schema/representation/unit/media type, plan/activation and deadline in UTC microseconds. `WaitClosure` distinguishes accepted evidence from explicit terminal unfulfilled reasons; an accepted closure cannot embed a rejected domain receipt. `WaitObservation` carries the immutable expectation and optional closure. Cross-field matching, deadline/race policy, retention and closure authority belong to owner domain objects and transactions.

`GraphRunPageV2` adds the await node kind without changing `GraphRunPage` wire-v1 bytes. Campaign wire-v3 also reuses the unchanged ActivationPath wire-v2 shape. These new DTOs are published boundaries, not claims that the corresponding HTTP handlers or execution transitions exist. Runtime rejects admission of v3 plans until the B2 integration gate. Preserve the old roots and exact fingerprints when replacing this package; do not send the new node tag under an old observation version.
