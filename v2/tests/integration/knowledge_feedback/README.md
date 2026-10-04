# Knowledge feedback verification boundary

Owner: BP-06.06/B1.01. This is verification tooling, not a deployed service, scientific evaluator or joined owner database. [Physical design](../../../docs/Build%20Plans/BP-06/BP-06.06%20Physical%20design.md) owns the staged integration scope.

Implemented: a credential-free, versioned declared-fixture manifest with exact question/need/method, source byte span/trace, graph/assertion, specimen/material/experiment/observation, profile/generation, campaign cut/receipt and named-view pins. Actual public owner acquisition, mutation and readback are later milestones. Parsing a manifest does not establish that a record exists, a receipt is accepted, a view is available or science is correct.

`protocol/wire.py` owns private verification DTO shape using existing public owner contracts; no new production schema/package/version is introduced. `protocol/manifest.py` owns immutable canonical bytes/SHA, recursive scope fencing, span bounds, graph identity, unique specimen/sample/observation attribution and nonambiguous view pins. Distinct preparations of the same candidate remain distinct. It retains no caller-owned containers; every DTO is revalidated. `document()` returns a fresh DTO. No inferred cross-owner relationship, rights grant or publication authority comes from structural validity.

Input is at most256KiB strict UTF-8 JSON; duplicate keys/nonfinite values, unknown fields and malformed nesting fail. Source spans are nonempty, within the declared raw Artifact size and at most64KiB; exact content/digest and current access require later Data readback. At most16 specimen and16 view pins. Ordered specimens are part of scenario identity. Any exact pin change yields a new fingerprint while original canonical bytes remain available. There is no I/O, credential storage, provider call, database or service implementation dependency.

Run `dev/.venv/Scripts/python.exe dev/run_tests.py --module knowledge-feedback-integration --coverage` from v2. Tests own valid/invalid pin models, nested foreign scopes, ambiguous attribution, immutable iteration snapshots and bounded/strict JSON. Coverage measures only `protocol/`; test fixtures are excluded from its denominator. Short explicit malformed-input case names prevent filesystem/report overflow. Actual multi-owner/process/browser evidence must be reported separately; these pure tests cannot substitute for it.

## Public capability map at activation

| Owner | Existing usable public boundary | Required next addition |
|---|---|---|
| Knowledge | Exact graph/profile/head/snapshot/change/rebuild; reasoning and correction/publication reads | Bounded scoped search/neighborhood/detail capability and projections |
| Research | Question/need declarations; exact scientific records, observation/material corrections, interpretation/impact/consumer pages | Versioned material/property named views preserving actual measurement semantics |
| Data | Source/trace history, current rights, Artifact/content reads, profile/binding/generation/query APIs | Consumer span-integrity/access adapter; no shared provenance database |
| Runtime | Campaign cuts, accepted receipts, actual waits/continuations and successor lineage | Scenario wiring through existing public commands; no science adjudication in harness |
| Studio | Runtime topology/lineage catalog, strict transport, request lanes, graph/evidence selection and comparison policy | Separate scientific-owner adapters, page models and Explore views |

Subsequent actual driver records exact returned identities and verifies them through owners before claiming a checkpoint. Maintain per-owner credentials/processes, visible synthetic limitations and independent expected outcomes. No private peer SQL/imports or fabricated successful response is permitted. Independent replacement preserves this format/canonical fingerprint and all local invariants; intentional format changes use a new version.
