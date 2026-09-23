# Integration Deployment and Service Operations

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Platform_Architecture.md)
- Requirement source: [Product Requirements](../Product_Requirements.md#enterprise-platform-requirements)

## Owned Contract

Versioned APIs/events specify compatibility, idempotency, pagination, filtering, bulk limits, correlation, signed webhooks, replay protection, retries/reconciliation and dead-letter handling. Scientific/enterprise adapters retain source/format identity, health and support boundaries. Listing an integration is not proof it exists.

Classify SaaS, dedicated, private-cloud, on-premises, disconnected and hybrid profiles as supported/planned/out of scope. Supported profiles define ownership, identity/keys, egress/residency, tool/model eligibility, installation, upgrades, rollback and recovery. Assign measurable availability, latency, throughput, capacity, freshness, RPO/RTO and incident objectives by workflow/tier before acceptance; do not invent universal targets.

## Service and Commercial Boundaries

Service ownership includes load/failure exercises, support/escalation and evidence-preserving incident response. Meter tenant/project/task/tool/provider usage; reconcile billing, budgets, quotas and spend approvals separately from scientific authority. Version customer configuration without changing shared defaults. Business continuity names recovery priorities and fallbacks.

Entitlements bind contract dates, feature/tool/model access, seats, support tiers and provider licensing, including geography, concurrency and offline restrictions. Trial, suspension, renewal and offboarding transitions preserve historical evidence; expiry or budget exhaustion must reconcile in-flight effects. Configuration is layered, typed and previewable. Feature flags need ownership, scope, expiry and rollback; migrations require rehearsal and compatibility/forward-repair plans. Customer extensions need supported boundaries rather than invisible forks.

## Invariants and Verification

Required durable commitments precede success. Verify provider outages, restore exercises, upgrade rollback, webhook duplication, schema drift, metering reconciliation and budget exhaustion. Telemetry must diagnose without disclosure. Storage/queue/deployment technologies remain bounded plan decisions rather than inherited v1/JARVIS defaults.

## Component and Service Design

| Proposed component | Owned contract |
|---|---|
| Integration gateway | Versioned external APIs/events, authentication, throttling and delivery reconciliation |
| Execution environment manager | Supported tool/agent deployment profiles, resource placement and health |
| Usage/entitlement ledger | Idempotent billable usage, budgets, grants, expiry and reconciliation |
| Service operations | SLOs, alerts, incidents, support ownership and recovery runbooks |
| Release/configuration authority | Versioned configuration, migrations, rollout/rollback and impact records |

Define system-of-record versus derived caches explicitly for every deployed store. Storage products are not selected here. A support profile binds service capabilities to infrastructure, provider availability, security/rights posture and measured limits; unsupported combinations must be visible during capability resolution.

## Operational Flow

Changes are prepared with compatibility/impact assessment, evaluated in their declared environment, activated under policy and observed against rollback criteria. Usage records bind logical task/action/provider identities so retries do not accidentally double bill. External callback processing authenticates, deduplicates and reconciles state; delivery acknowledgement is not proof that the scientific operation completed.

Backups must cover authoritative metadata and referenced artifact generations coherently. Recovery restores a consistent point, verifies relationships and resumes reconciliation for effects whose outcomes are uncertain. A durable source plus a stale/missing projection must yield explicit recovery/freshness state, not an empty successful result.

## Failure and Boundary Example

A provider times out after accepting a paid job. Preserve the submission identity and reconcile before retrying; metering records distinguish reservation, actual usage and adjustment. If a quota expires mid-experiment, stop newly unauthorized work while preserving evidence and handling already-issued effects under the configured policy.

## Design Basis and Open Decisions

System owns the initial single-server, separate-worker topology, PostgreSQL metadata baseline and database-backed dispatch direction. Initial use is internal/demo, one user and one active campaign, on a DGX Spark or partner Threadripper host. Broader enterprise profiles, capacity and contractual SLO/RPO/RTO targets are later-stage work. Remaining initial choices include host packaging, basic restore procedures, worker resource bounds and observability. Historical MVP stack suggestions are not inherited decisions.
