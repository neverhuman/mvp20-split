# Identity Policy and Isolation

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Platform_Architecture.md)
- Requirement source: [Product Requirements](../Requirements/Product_Requirements.md#enterprise-identity-and-access-management)

## Owned Contract

Identity covers people, services, agents and delegated workloads with tenant/project/purpose/action scope. Federation, MFA/session policy, provisioning, revocation, access reviews, separation of duties and emergency access follow supported profiles. Authentication, commercial entitlement and scientific approval remain separate.

Policy precedes reads, commands and external effects. Grants are bounded and revocable. Approvals bind exact action/revision, impact, cost, eligible reviewer, expiry and compensation. Secrets remain managed references. Enforce current access on snapshots, retrieval caches and exports.

## Boundary and Flow

Domains own scientific/workflow policies; Platform supplies enforcement. Data supplies rights/consent; Experience exposes administration. Audit records decision/actor chains without unrestricted private payloads.

## Invariants and Verification

Isolation includes payloads, counts, errors, timing, telemetry and search metadata. Enforce purpose, residency, retention, legal hold and deletion with permitted tombstones. Security lifecycle includes threat modeling, signed provenance/SBOMs, dependency/license/vulnerability review and incident handling. Verify revocation, forbidden delegation, approval tampering and cross-scope leakage; controls alone do not establish certification.

## Component and Policy Design

| Proposed component | Owned behavior |
|---|---|
| Identity gateway | Authentication/federation, subject/workload identity and session lifecycle |
| Policy decision/enforcement boundary | Action/object/scope evaluation and reason-coded allow/deny |
| Grant/approval aggregate | Exact delegated authority, reviewer decisions, expiration and revocation |
| Rights/retention enforcement | Purpose, residency, disclosure and retention/legal-hold constraints |
| Secret/key broker | Scoped credential resolution and rotation without payload exposure |

Authorization inputs include subject, delegation chain, tenant/project, resource classification/revision, action, purpose and environment. Commercial entitlement is an additional eligibility check, not a substitute for rights or scientific authority. Approval records bind target and payload hashes or equivalent immutable identities.

## Enforcement Protocol

Authenticate -> resolve scope/classification -> evaluate current policy/grants -> validate approval binding where required -> execute under a bounded identity -> commit decision/effect audit. Recheck mutable grants at consequential effect boundaries. Cached policy decisions need revocation/version invalidation; a historical run snapshot cannot freeze permissions forever.

Administrative break-glass access has reason, scope, duration and independent review. Field-level projections protect sensitive content while preserving authorized audit metadata. Untrusted input cannot introduce an authority override by being embedded in a prompt, graph or tool result.

## Failure and Boundary Example

An approval covers one lab submission but a revised proposal changes the target or spend. The original approval no longer matches; deny the effect or route a new review. If the policy/identity service is unavailable, explicitly deny or enter a non-final state for protected actions, rather than treating lookup failure as permission.

## Design Basis and Open Decisions

Enterprise security and agent authority requirements define the controls. Remaining decisions: identity providers, policy language, key ownership, residency profiles and legal retention conflict handling. These require deployment/threat-model decisions; architecture must not claim certification or jurisdictional compliance from control names alone.
