# Graph Runtime Contracts

Current BP-05.03/B1 partial: Partial B1 authoring contracts/domain checkpoint: graph-runtime0.8.0 and Runtime0.14.0 add public draft save/validate/revision/page/validation/receipt DTOs and pure immutable revision objects.86 scoped contract/domain/dev tests pass;194 schemas published and all182 predecessor schema bytes preserved. No draft database/API/activation integration or Studio authoring yet; B1 remains0/4, Build0%, Acceptance0%; parent50% unchanged.

Authoring commands use their own DraftCommandReceipt; unchanged Runtime CommandReceipt cannot represent draft commits and is not widened. parse_authoring_command recognizes only definition.save/definition.validate and binds saved definition scope to command identity. Draft validation records pin revision/content/universe and explicitly cannot establish scientific acceptance. Revision conflict decisions belong to Runtime definitions domain objects, not DTO constructors. Owned tests: tests/test_authoring.py. No transport endpoints are implied by schema publication.

Earlier accepted publication history follows.

Package0.7.0 adds GraphViewCatalog and typed view/filter descriptors under BP-05.02/B1. Runtime0.13.0 advertises only its implemented execution topology and successor lineage projections. All180 predecessor schema bytes remain unchanged;182 schemas are now published. No migration.

Package0.6.0 adds bounded scope/topology read roots under BP-05.02/B1; Runtime0.12.0 owns their authority and authored-edge projection. campaigns0.4.1 publicly exports the existing Occurrence union. All predecessor schemas remain byte-identical; no migration. Navigation acceptance passed BP-05.02.

Package 0.5.0 adds graph snapshot, node detail, value page and invalidation page roots under BP-04.05/B1. Runtime 0.11.0 owns their read authority and revision/cursor policy. These are additive observations; prior command and graph page contracts remain unchanged. See [observation protocol](../../docs/Architecture/System/Graph_Observation_Protocol.md) and `tests/test_observations.py` for bounded examples and rejection cases. Earlier 0.4.0 notes below describe the accepted predecessor.

Package 0.4.0 adds `SuccessorProposal`, `CarrySources` and `SuccessorLineage` without changing earlier graph/worker schema bytes. Runtime 0.10.0 owns admission authority. The new `graph.admit_successor` family names a precise predecessor plan/revision, explicit final-export or succeeded-node sources, expected value digests and distinct target inputs. Fresh Artifact input scope checks remain in the public parser; predecessor/retention/type policy belongs to Runtime domain objects.

- Package: `amphora-contracts-graph-runtime` 0.8.0; campaigns dependency 0.4.1. Existing versioned graph observations and worker receipts are unchanged.
- Owner: Campaign Runtime read/coordination boundary; active BP-05.03/B1 additive authoring contracts.
- Architecture: [Graph Execution Model](../../docs/Architecture/System/Graph_Execution_Model.md).

Public root imports expose graph admission/advance commands, bounded values, limits and paginated node observations. They reference executable campaign wire-v2 identity while retaining the existing attempt budget and command envelope. This separate package prevents graph authoring dependencies from entering the pinned scientific worker/SDK closure. Existing worker commands and campaign schemas retain their serialized behavior; campaign exports add names for existing literal-value DTOs only.

Values are finite typed scalars, scoped immutable artifact references or one bounded collection layer with explicit missing members. They cannot contain node/input/result references or arbitrary embedded scientific payload objects. Admission carries an exact reviewed plan hash, named values, attempt budget and expansion/time limits. Runtime owns input compatibility, plan trust, scope/authority, readiness, budget and transition behavior; the DTOs do not decide any of them. Command parsing rejects direct or collection artifact references outside the envelope scope before registration.

Number values use plain decimal **strings**, for example `{"kind":"number","value":"2.5","unit":"g/mol"}`. The portable regex bounds magnitude to +/-1e100, at most 100 integer/324 fractional digits (plus the exact 1e100 boundary); exponents, NaN/infinity and JSON floats are rejected. Compiler-authored numeric literals keep their existing representation and are explicitly converted by the Runtime value resolver. This preserves the existing 256-KiB/64-container, safe-integer/float-free command fingerprint profile and all old receipts. Equivalent textual spellings are not silently normalized into the same caller command.

Reads are bounded pages of graph node/path/status observations, not a claim of live worker authority. No public ORM, database client, scientific code, evaluator or service implementation is included. Preserve published wire schemas and command fingerprints across replacement, or explicitly version their boundary. Owned tests live in `tests/`; actual persistence/interpreter proof belongs to Runtime.

B1 scoped verification: 17 command/value cases pass, including decimal fingerprints, artifact scope in collections, rejection of dynamic/untyped inputs and unchanged legacy family dispatch. Contract coverage is 77/79 statements and all six branches; the uncovered unknown-family error path remains part of B2 transport integration. These declaration/parser numbers are not coordinator behavior coverage.

## External receipt and wait extension

`DomainReceipt` separates accepted artifact evidence, rejected, abstained and superseded dispositions. `SubmitDomainReceipt` binds it to run, activation, exact wait revision and expectation hash. `parse_graph_command("graph.submit_receipt", raw)` checks receipt/subject/output scope and requires the envelope actor to match the named issuer before registration. This is a shape/identity check; authenticated configured authority still belongs to Runtime. The unchanged worker parser rejects this command family.

`WaitExpectation` pins issuer/purpose/external revision, exact subject, output schema/representation/unit/media type, plan/activation and deadline in UTC microseconds. `WaitClosure` distinguishes accepted evidence from explicit terminal unfulfilled reasons; an accepted closure cannot embed a rejected domain receipt. `WaitObservation` carries the immutable expectation and optional closure. Cross-field matching, deadline/race policy, retention and closure authority belong to owner domain objects and transactions.

`GraphRunPageV2` adds the await node kind without changing `GraphRunPage` wire-v1 bytes. Campaign wire-v3 reuses unchanged ActivationPath wire-v2. Runtime 0.7.0 exposes the new graph page at `/v2/graph-runs/{run}`, expectation/closure at `/v1/graph-runs/{run}/waits/{activation}`, and authenticated receipt commands at `/v1/graph-receipts` when Artifact protection is configured. The old page endpoint requires v3 callers to use the v2 observation route; it never emits a new node tag under the old schema. DTO declarations themselves establish no scientific authority, persistence or peer-acceptance evidence. Preserve old roots and exact fingerprints when replacing this package.
