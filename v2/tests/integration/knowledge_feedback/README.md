# Knowledge feedback verification boundary

Owner: BP-06.06 integration verification. This is verification tooling, not a deployed service, scientific evaluator or joined owner database. [Physical design](../../../docs/Build%20Plans/BP-06/BP-06.06%20Physical%20design.md) owns the staged integration scope.

Implemented: a credential-free, versioned declared-fixture manifest with exact question/need/method, source byte span/trace, graph/assertion, specimen/material/experiment/observation, profile/generation, campaign cut/receipt and named-view pins. The [actual baseline](live/README.md) separately proves public acquisition, graph acceptance/publication, scientific views, Qdrant generation, Runtime receipt consumption/replacement and compiled Studio readback. Parsing a manifest alone does not establish that a record exists, a receipt is accepted, a view is available or science is correct.

`protocol/wire.py` owns private verification DTO shape using existing public owner contracts; no new production schema/package/version is introduced. `protocol/manifest.py` owns immutable canonical bytes/SHA, recursive scope fencing, span bounds, graph identity, unique specimen/sample/observation attribution and nonambiguous view pins. Distinct preparations of the same candidate remain distinct. It retains no caller-owned containers; every DTO is revalidated. `document()` returns a fresh DTO. No inferred cross-owner relationship, rights grant or publication authority comes from structural validity.

Input is at most256KiB strict UTF-8 JSON; duplicate keys/nonfinite values, unknown fields and malformed nesting fail. Source spans are nonempty, within the declared raw Artifact size and at most64KiB; exact content/digest and current access require later Data readback. At most16 specimen and16 view pins. Ordered specimens are part of scenario identity. Any exact pin change yields a new fingerprint while original canonical bytes remain available. There is no I/O, credential storage, provider call, database or service implementation dependency.

Run `dev/.venv/Scripts/python.exe dev/run_tests.py --module knowledge-feedback-integration --coverage` from v2. Tests own valid/invalid pin models, nested foreign scopes, ambiguous attribution, immutable iteration snapshots and bounded/strict JSON. Coverage measures only `protocol/`; test fixtures are excluded from its denominator. Short explicit malformed-input case names prevent filesystem/report overflow. Actual multi-owner/process/browser evidence must be reported separately; these pure tests cannot substitute for it.

## Verified public capability map

| Owner | Verified public boundary | Boundary retained |
|---|---|---|
| Knowledge | Pinned projections, accepted correction race, explicit snapshots and rebuild/replacement | Structural acceptance, not scientific truth |
| Research | Exact records, unmet/sufficient fixture assessments, correction lineage, distinct preparation/eligibility | Purpose/context-specific synthetic authority |
| Data | Verified spans/derivations, reusable profiles, independent Qdrant generation and pending query recovery | Current rights and explicit generation selection |
| Runtime | Old/new pinned waits, retention, replay after replacement, correction barrier | Only Runtime accepts execution; active pins do not change |
| Studio | Actual compiled models and browser traversal in source and independent builds | Read-only acceptance host, no deployed gateway or identity picker |

[Verification index](../../../docs/Build%20Plans/BP-06/BP-06.06%20Verification%20index.md) separates pure, installed owner, model and browser tiers. The actual driver records returned identities and verifies them through their owners. Maintain per-owner credentials/processes, visible synthetic limitations and independent expected outcomes. No private peer SQL/imports or fabricated successful response is permitted. Independent replacement preserves this format/canonical fingerprint and all local invariants; intentional format changes use a new version.
