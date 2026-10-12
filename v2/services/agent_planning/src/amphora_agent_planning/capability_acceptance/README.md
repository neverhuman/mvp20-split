# Reviewed capability acceptance evidence

UI-01.08/P3.2. Owns bounded evidence parsing, mechanical compatibility and public
read collection. It does not authorize a fulfillment command, persist a decision,
install/run a tool or confer Runtime/scientific eligibility. The authenticated
fulfillment command must explicitly endorse this evidence; a report's authority
label or model text cannot grant that permission. Journal/worker integration follows.

The versioned planning.capability-acceptance.v1 JSON report is carried inside the
already approved acceptance_evidence ArtifactRef inputs. Its schema ID/version/hash
is frozen by the module's test fixture. Exactly one report is required. It pins the
original request, proposal hash, gap key and complete Registry lock, every requested
applicability description, selected actual descriptor applicability labels, and one
ordered result for every original acceptance criterion. Each criterion retains its
method/observation and any separately supplied supporting Artifact references.
Failed/unknown/missing/duplicate or unrelated criteria cannot verify fulfillment.

Owner review supplies the semantic judgment relating applicability/criteria to the
selected tool. Code checks exact identities, coverage and typed compatibility; it
does not claim to establish arbitrary natural-language science. The scientific
authority remains not_established. Artifact existence alone is insufficient.

The observed Registry descriptor digest/full lock is reconstructed, and the release
must be registered/active. Requested input/output names, representations and any
specified schemas/units must match. Every extra required tool input rejects; extra
optional inputs/outputs are allowed. A null requested schema/unit is unspecified;
no unit conversion or representation conversion is invented.

AcceptanceCollector makes one exact public Registry read (10s window), then current
Data metadata/processing reads (20s,32calls,16MiB shared budget; each Artifact4MiB).
It verifies metadata identity, size and SHA before review. The report is at most64KiB.
Source rights and peer transport failures propagate; no retry or SQL spans those
calls. Release/processing observations describe the time of review, not future
availability; later compiler/Runtime authority remains independent.

Tests: tests/capability_acceptance. Replacement must preserve the frozen report
schema and reject unrelated claims/evidence without network or authority fallback.
Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md).
Delivery: [UI-01.08](../../../../../docs/Build%20Plans/UI-01.08%20Campaign%20curation%20boundary%20decision.md).

AcceptanceReview.review_report rechecks report/descriptor semantics for retained
fulfillment evidence. It does not establish current Data processing by itself;
live bind still validates every body, and journal replay trusts only its immutable
processed-reference attestation. Report schema/profile bytes remain unchanged.
