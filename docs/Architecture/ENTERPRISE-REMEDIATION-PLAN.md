# Enterprise Product Remediation Plan

## Plan status

| Field | Value |
|---|---|
| Status | Proposed for review and prioritization |
| Created | 2026-08-30 (America/Chicago) |
| Planning horizon | Approximately one year |
| Requirements source | [`Product_Requirements.md`](Product_Requirements.md) |
| Gap source | [`FEATURE-GAP-ANALYSIS.md`](FEATURE-GAP-ANALYSIS.md) |
| Target outcome | Enterprise coatings R&D pilot |
| Scope boundary | Delivery sequencing and remediation; this document does not redefine requirements or current-state findings |

## Objective

Convert the existing scientific trust and execution kernel into a secure, persistent, user-facing, extensible, and operable enterprise coatings R&D product. The year-one outcome should support a small number of explicitly contracted enterprise customers through one primary deployment profile and one complete scientific workflow.

The target is not universal materials discovery, unrestricted third-party plugins, autonomous scientific authority, manufacturing release, or naval qualification. Those outcomes require additional product maturity, scientific evidence, and external authority.

## Delivery principles

- Deliver complete vertical outcomes rather than many disconnected horizontal foundations.
- Preserve and productize the existing contracts, provenance, authority, abstention, replay, and evidence controls.
- Build tenancy, authorization, audit events, node-version binding, and telemetry into every slice from its first implementation.
- Keep operational readiness, scientific validation, and external authority separate.
- Prefer one supported deployment and integration path before multiplying variants.
- Treat missing capability as a typed gap; do not fabricate results or silently weaken methods.
- Require real, accepted laboratory evidence before enabling scientific ranking or cross-project model learning.
- Keep customer evidence private by default and promote reusable material only through explicit rights and applicability review.

## Critical path

```text
tenant + identity + persistent domains
  -> signed ProductEnvelope
  -> node registry/matching + immutable CapabilityPlan
  -> formulation/characterization workflow
  -> lab return + evidence disposition
  -> candidate package + bounded campaign
  -> customer delivery + controlled reusable-knowledge promotion
```

Work outside this chain should be justified by a contracted dependency, material risk reduction, or direct support for a critical-path gate.

## Workstreams

### Product and tenancy backbone

- Tenant, customer, program, project, experiment, campaign, run, task, and node-execution ownership.
- Enterprise federation baseline, role/attribute authorization, workload identity, and customer administration.
- Persistent domain repositories for envelopes, ingredients, formulations, samples, experiments, measurements, candidates, evidence dispositions, and audit events.
- PostgreSQL/object storage, migrations, transaction boundaries, durable jobs, and tenant-safe indexing/search.
- Retention, export, deletion, legal hold, consent, and offboarding foundations.

### Scientific workflow

- Source intake, structured requirement extraction, ambiguity review, and signed `ProductEnvelope`.
- Ingredient and formulation management with immutable experiment-bound versions.
- Incumbent characterization, sample/custody, method, instrument, observation, hypothesis, mass-balance, unknown-fraction, fingerprint, and reconstruction workflow.
- Candidate compilation, complete BOM/process/evidence package, CRO/lab issue, return intake, deviation, and reviewer disposition.
- Bounded formulation campaigns with real authorized operators, evidence-eligible fitness, human selection, and replay.

### Capability-node platform

- Typed node manifest and immutable node-version records.
- Registry service and role-appropriate registry UI.
- `CapabilityNeed`, `CapabilityPlan`, `CapabilityGap`, `NodeBuildRequest`, and project capability lockfile.
- Deterministic, explainable project-to-node matching with human approval and explicit no-match behavior.
- SDK/templates for deterministic nodes and adapter/model nodes.
- Contract, known-answer, negative-control, authority, security, packaging, and compatibility checks.
- Separate operational and scientific lifecycles with shadow, limited-active, quarantine, rollback, deprecation, and retirement.

### Enterprise product surface

- Versioned API, service identities, idempotency, webhooks, SDK, and reconciliation.
- Operator/DevOps, external customer, data scientist, agent management, customer, and experiment UI slices.
- Initial integrations for identity, object storage, generic laboratory file/CSV intake, CRO exchange, and API/webhook automation.
- Entitlements, quotas, budgets, provider/agent/node cost attribution, and safe suspension.
- Accessibility, units, time zones, onboarding, documentation, training, and supported-client posture.

### Reliability, security, and support

- Environments, CI/release, secrets/key management, signed artifacts, software bills of materials, vulnerability operations, and threat models.
- Service objectives, metrics, logs, traces, capacity tests, admission control, and degraded-mode behavior.
- Backup/restore, RPO/RTO, disaster recovery, integrity verification, and continuity exercises.
- Incident, problem, change, maintenance, status communication, support case, and escalation workflows.
- Tenant-isolation, privacy, audit-integrity, penetration, supply-chain, and recovery evaluation.

### Auditability and agents

- Common tenant-scoped audit events with transactional delivery, correlation/causation, and integrity protection.
- Search, timelines, lineage, version diff, point-in-time reconstruction, affected-consumer analysis, and verifiable exports.
- Durable agent tasks, dependency graph, registry, tool/credential policy, approvals, cost controls, recovery, and UI.
- Bounded agents for intake, evidence assembly, node scaffolding, status/support, and operator triage.
- Agent evaluation, shadow/limited-active activation, quarantine, rollback, and emergency stop.

## Quarterly plan

### Quarter 1 — tenant and product foundation

Deliver:

- tenant/customer/program/project hierarchy;
- federation baseline and authorization model;
- persistent envelope, ingredient, formulation, experiment, sample, measurement, candidate, evidence-disposition, and audit-event domains;
- API foundation, PostgreSQL/object storage, durable jobs, migrations, environment/release baseline, secrets, and telemetry;
- initial SLO, capacity, durability, RPO, and RTO targets;
- node manifest/registry v1, baseline-node migration, and capability lockfile;
- first source-intake/envelope and formulation-editor web slices.

Exit gates:

- tenant scope is enforced through API, storage, jobs, events, and object references;
- a signed envelope can bind immutable project and capability versions;
- a scientist can create and clone a formulation through the supported UI;
- audit events reconstruct the critical actions performed in the slice;
- backup and restore of the initial authoritative stores is demonstrated.

### Quarter 2 — complete scientific vertical slice

Deliver:

- characterization, sample, custody, method, instrument, observation, and hypothesis workflow;
- generic lab/CRO import, raw-file handling, review/disposition, and results UI;
- candidate package with integrated BOM, process, sourcing, evidence, and limitations;
- capability needs, planning, gaps, deterministic node matching, and human approval;
- node registry UI and SDK v1;
- one new deterministic node onboarded through the governed workflow;
- audit timelines, version comparison, and source/evidence-to-decision trace.

Exit gates:

- one candidate or incumbent sample traverses intake through reviewed laboratory evidence;
- a capability gap cannot silently become a result;
- the new node is built, evaluated, packaged, deployed in shadow, and rolled back without orchestrator-core changes;
- raw evidence, normalized observations, interpretations, and claims remain distinct and traceable;
- the role-based UI supports the workflow without manual database or artifact editing.

### Quarter 3 — campaigns and enterprise operations

Deliver:

- real bounded formulation operators, campaign review/selection, and accepted lab feedback;
- customer portal, customer portfolio, experiment lifecycle, Operator/DevOps, and data-scientist baseline views;
- versioned API/webhooks and the highest-priority enterprise/laboratory integration;
- quotas, admission, budgets, cost attribution, incident/support, backup/restore, and load/failure tests;
- durable bounded agents for intake, evidence assembly, node scaffolding, status, and triage;
- a second project-driven node onboarded without orchestrator-core changes.

Exit gates:

- an authorized formulation variable changes across a replayable campaign while hard constraints remain enforced;
- only accepted evidence affects eligible decisions;
- customer and internal views remain tenant- and role-correct;
- node, agent, provider, and customer costs are attributable and bounded;
- queue, dependency, retry, cancellation, and failure recovery do not duplicate consequential effects.

### Quarter 4 — hardening and controlled pilot

Deliver:

- security, privacy, tenant-isolation, audit, accessibility, recovery, performance, and node-supply-chain evaluations;
- shadow/limited-active node and agent promotion, quarantine, and rollback;
- customer administration, access review, consent, export/offboarding, support procedures, and service reporting;
- an end-to-end naval characterization/baseline workflow or another contracted coatings program using real lab returns;
- user acceptance and closure of release-blocking failures;
- evidence-supported authority only, with explicit abstention elsewhere.

Exit gates:

- the enterprise-pilot acceptance outcomes in the gap analysis are demonstrated or explicitly waived by accountable owners;
- isolation, authorization, backup/restore, RPO/RTO, audit integrity, incident response, and safe offboarding have rehearsal evidence;
- the pilot workflow completes without manual context/file shuttling outside declared integration boundaries;
- scientific reviewers accept the evidence posture of every live decision-capable node;
- unsupported qualification, safety, procurement, or release claims remain impossible through UI, API, report, and agent paths.

## Cross-cutting gates

Every delivered vertical slice must satisfy:

- tenant and customer ownership;
- least-privilege human, service, node, and agent authorization;
- immutable version and content identity;
- complete audit events and downstream consumption lineage;
- explicit applicability, uncertainty, limitations, abstentions, and authority;
- operational metrics, costs, errors, retry/cancellation, and support ownership;
- security, privacy, rights, retention, and deletion posture;
- tests for happy path, negative controls, malformed input, authority escalation, tenant leakage, and recovery;
- UI and machine-readable API access appropriate to intended roles;
- documented rollback or forward-repair behavior.

## Dependencies outside software

- Real incumbent and control samples with ownership and permitted-use documentation.
- Qualified analytical and coatings personnel to select and interpret methods.
- Rights-eligible laboratory measurements with custody, methods, controls, uncertainty, and review.
- Customer decisions on requirements, sharing, deployment, integrations, service objectives, and acceptance.
- Supplier grades, declarations, quotes, qualification evidence, and change notifications.
- Security, privacy, legal, IP, export-control, and procurement review.
- External naval/manufacturing qualification bodies where those outcomes are pursued.

Unavailable external dependencies must become visible program blockers; agents or models cannot synthesize their authority.

## Highest risks and mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| Insufficient accepted lab evidence | Scientific nodes cannot become decision-eligible | Contract samples, methods, CRO capacity, rights, and review early; retain abstention |
| Tenancy retrofitted around file assumptions | Customer leakage or irreconcilable ownership | Establish tenant/object/event keys and isolation tests in Quarter 1 |
| Excessive horizontal scope | Many foundations, no usable workflow | Fund and measure the critical vertical slice; gate parallel work by dependencies |
| Too many deployment profiles | Multiplied security, release, support, and upgrade burden | Select one primary and at most one constrained secondary profile |
| Premature dynamic nodes/agents | Supply-chain, execution, and authority risk | Signed packages, sandboxing, typed tools, shadow activation, review, quarantine |
| Cross-project negative transfer/leakage | Bad science or confidentiality breach | Private by default; rights/applicability review; shared knowledge before pooled learning |
| Enterprise integration sprawl | Schedule and support failure | Generic contracts first; add vendor adapters only for contracted workflows |
| Scientific and operational status conflated | Unsafe decisions from healthy but unvalidated code | Separate lifecycle dimensions in registry, UI, policy, and acceptance |
| Requirements expansion during delivery | One-year target becomes indeterminate | Baseline scope quarterly; route additions through trade-off and deferral decisions |

## Explicit year-one deferrals

Unless contractually required, defer:

- public third-party node marketplace;
- arbitrary untrusted or self-generated node execution;
- every private-cloud, on-premises, disconnected, and air-gapped deployment combination;
- full billing/invoicing beyond entitlement, budget, usage, and export controls;
- broad vendor-specific LIMS/ELN/ERP/PLM/QMS connector catalogs;
- autonomous scientific, knowledge, model, node, or release promotion;
- generalized neuro-symbolic reasoning across all material domains;
- cross-customer model training before sufficient compatible accepted evidence;
- manufacturing, safety, procurement, or naval qualification claims;
- multiple production domain packs beyond coatings and one limited extensibility proof.

Deferral means the architecture preserves a path without representing the capability as supported.

## Program measures

Track at least:

- percentage of critical workflow completed through supported UI/API without manual artifact editing;
- enterprise-pilot acceptance gates passed;
- tenant-isolation and authorization test coverage/failures;
- node needs matched, explicit gaps, nodes onboarded through SDK, time-to-node, and rollback success;
- scientific nodes by operational and scientific state;
- experiments with complete custody/raw/method/reviewer lineage;
- accepted versus rejected/quarantined evidence and reasons;
- agent task completion, intervention, escalation, policy violation, recovery, latency, and cost;
- SLO attainment, queue time, incidents, restore/DR results, and support response;
- customer decisions waiting, blocked critical-path time, and dependency age;
- unsupported claim, incorrect applicability, and incorrect abstention rates;
- delivery effort spent on critical-path outcomes versus deferred breadth.

Counts of modules, evidence files, agent turns, generated candidates, or lines of code are not delivery outcomes without corresponding user, scientific, operational, and acceptance evidence.

## Plan completion

This plan is complete when the defined enterprise coatings R&D pilot is accepted against the gap analysis, or when accountable product leadership replaces it with a versioned successor plan. Completion does not imply manufacturing release, scientific proof beyond accepted evidence, universal domain support, or external qualification.
