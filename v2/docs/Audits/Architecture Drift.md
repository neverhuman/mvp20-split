# Architecture Drift

- Status: BP-06 active; BP-05 closed/audited.
- Last refreshed: `2026-10-03 19:15:58` (America/Chicago).
- Scope: v2 design/implementation alignment.
- Active focus: BP-06.05/B3.02a forced-death/replay barriers; child58.33%, parent76.39%,18/24 closed gates.
- Next gate: forced process-death matrix. B3.01 actual expiry, selected-vector corruption/fresh repair and competing publishers verified alongside inherited adversaries. Scientific-quality UI remains SQ-01.

## Active Findings

- BP-06.05/QD-01: actual Qdrant1.19.1 simultaneous creation of one attempt namespace returned409 and a temporary500 read; a later read recovered expected content. Adapter errors remain operational and no create acknowledgement grants verification. Separate fenced attempt namespaces and exact content comparison preserve authority. Actual fresh-namespace recovery is tested at the adapter boundary; Data generation/index reconstruction passed B2.02c and abrupt process/race proof is B3. No claim that every concurrent backend call succeeds. This does not block bounded adapter work.



- `2026-09-23 09:41:20`: Service isolation replaces broad engine/domain packaging; standalone tool workloads use the existing registry as node index. Cross-service research-acceptance receipts, artifact reservations and revocation/effect checks require concrete protocol fixtures before implementation; atomic runtime commit must not be mistaken for atomic scientific-domain acceptance. Owner: System/Capabilities, prerequisite to service deployment. K3s/Kubernetes mappings remain proposed, with no operational evidence.

- `2026-09-22 21:03:27`: Owner answers recorded in [readiness review](Architecture_Readiness_Review.md#owner-decisions-after-review). AR-01 initial fixture scope and AR-04 deployment/storage wording are aligned in requirements/domain docs. Initial autonomous profile explicitly supersedes routine human gates/live edits; later-profile capabilities remain labeled. Concrete schemas, rule/transition semantics and web-stack decision recording remain engineering follow-ups before dependent implementation. Module replacement boundaries are now explicit in the README template and process.

- `2026-09-22 20:57:10`: [Architecture Readiness Review](Architecture_Readiness_Review.md) records design readiness and open decisions. AR-04 identifies stale deployment/storage open-decision lists in Platform Operations and Campaign Runtime relative to System. Owner: system architecture; resolve before implementation-plan activation. AR-01 requires an explicit delivery/acceptance mapping between the synthetic system proof and the retained epoxy/biology requirements. Other findings are scoped design work or owner decisions, not observed runtime defects.

[BP-01 closeout](BP-01_Foundation_Closeout.md) assessed the implemented contract packages, validation API and isolation/build tooling. No blocking drift remains within that bounded scope. Durable transactions, complete tool/graph schemas, authentication, Rust/UI conformance and scientific acceptance remain owned successor gates. The nonblocking Starlette/httpx test-client deprecation is assigned to dev-tool maintenance. Historical v1 limitations remain in the reuse baseline and frozen evidence.

Use [Development Process](../Development_Process.md) and the [audit template](../Templates/Plan%20Audit%20Template.md). Record scope, revision, claim, observed behavior, evidence, blocking classification, owner and disposition. Keep unresolved/recently closed items here; aligned/no-follow-up records belong in [history](Architecture%20Drift%20History.md).

[BP-01A closeout](BP-01A_Test_and_Graph_Baseline_Closeout.md) aligns module-owned verification and the source-derived v1 graph baseline. The scaffold is structurally valid only; BP-04 owns actual orchestration parity, BP-08 scientific search. No blocking drift in the completed scope.

[Roadmap planning review](Planning_Maturity_Review.md) is aligned for documentation, with explicit current/future evidence boundaries. [Planning readiness](../Build%20Plans/Planning_Readiness.md) now owns cross-plan design handoffs and decision gates. This closes the plan-depth gap, not the still-unimplemented runtime/scientific capabilities.

- `2026-09-26 16:31:31`: frozen-baseline verification reports `ADDED v1/LICENSE`, already introduced in committed baseline `99d219c`; all manifest content hashes match. No v1 edits made. Owner: repository baseline metadata; follow-up requires explicit baseline maintenance authorization, not implementation blocker. Artifact A2-A4 gates pass; service closeout audit remains A6.












[BP-06.04 closeout](BP-06.04_Laboratory_Eligibility_Closeout.md) is aligned; bounded source, context, correction, recovery and replacement evidence is in drift history. No unresolved BP-06.04 finding remains. Scientific quality UI, physical validation and feedback dispatch remain named successor capabilities.

- `2026-10-03 12:46:50`: [BP-06.05 activation](BP-06.05_Activation.md) corrects owner navigation and distinguishes scientific corrections from access revocation. Private cache versus source-specific derived Artifact binding prevents permission merging. Implementation remains0%; later storage/backend gates require named detailed review.

B1.01 representation domain aligns with the bounded design: complete scoped identities and finite fixture vectors verified, with no persistence, rights or retrieval claim. [Evidence](Evidence/BP-06-Representations/Domain_Identities.json) retains the startup-budget repair and failed-run history; B1.02 owns public transport.

B1.02 [public-contract evidence](Evidence/BP-06-Representations/Public_Contracts.json) verifies separate wire/domain roles and preserved predecessor schemas. Storage and source binding authority remain subsequent gates.

B1.03 [storage evidence](Evidence/BP-06-Representations/Profile_Cache_Storage.json) verifies immutable private cache and DB-clock fencing under actual PostgreSQL. Cache results are not public Artifacts; source authority remains B1.04.

B1.04b [binding-state evidence](Evidence/BP-06-Representations/Binding_State.json) verifies exact source/current-rights admission, actor-scoped aliases and actual-owner journal reconstruction. No blocking drift in this milestone. Publication-during-claim barrier belongs to B3; automated orchestration c and broader rights/convergence d remain unimplemented.

B1.04c [workflow evidence](Evidence/BP-06-Representations/Binding_Workflow.json) verifies bounded actual-owner publication recovery without expanding cleanup/deletion authority. No blocking drift in c; independent-source convergence remains d and process/race matrix B3.

B1.04d [convergence evidence](Evidence/BP-06-Representations/Binding_Convergence.json) confirms one computation with independent source-rights/Artifact bindings and publisher attribution. No blocking drift in B1.04; actual process/race acceptance remains B3 and HTTP boundaries B1.05-.06.

B1.05 [API/hosting evidence](Evidence/BP-06-Representations/API_Hosting.json) verifies explicit opt-in and separate historical/current-use authority. No blocking drift in the transport scope; B1.06 owns actual installed representation HTTP reconstruction, B3 process/race acceptance.

B1 [actual HTTP evidence](Evidence/BP-06-Representations/HTTP_Replacement.json) aligns scoped representation profiles/reuse/source-rights/publication/transport with fresh isolated-owner reconstruction. No blocking B1 drift remains. Index lifecycle/Qdrant/retrieval remain B2; abrupt death/races B3; final child replacement/audit V1.
