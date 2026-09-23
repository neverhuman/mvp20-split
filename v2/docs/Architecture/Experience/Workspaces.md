# Role Workspaces and Deliverables

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Experience_Architecture.md)
- Requirement source: [Product Requirements](../Product_Requirements.md#user-experience-and-role-workspaces)

## Owned Contract

Role workspaces project shared objects instead of copying them. Scientific/experiment views expose intake, samples, candidates, controls, uncertainty, route feasibility, lab results and selections. Data-scientist views expose dataset/model/embedding/policy versions and evaluations. Reviewers inspect authority, contradictions and evidence.

External customers clarify requirements, approve authorized decisions and receive scoped deliveries. Internal customer administration exposes customer -> program/project -> experiment/campaign -> run portfolios, rights/consent, contacts and budgets. Operator/DevOps and agent-management views expose health, work, failures, cost, support and intervention without automatic access to scientific content.

## Interaction and Delivery

Reports, CRO packets, release-readiness and audit exports reference immutable records and limitations. Separate customer-visible artifacts, internal work and privileged reviews. Accessibility, keyboard/screen-reader use, localization, unit display and onboarding follow supported audiences. Feedback remains structured and attributable.

Provide accessible alternatives to graph-only interactions, explicit focus/error behavior, reduced-motion support and supported-device testing. Canonical scientific units remain separate from display conversion; retain conversion lineage and unambiguous numbers/timestamps with source/display timezones. Onboarding, help, sandbox examples, runbooks and competency acknowledgments follow the role and deployment profile. Product analytics remains privacy-scoped and is not silently reused as scientific evidence.

## Invariants and Verification

Presentation cannot raise evidence authority or imply external qualification. Test representative user workflows, decision explanation without database/log access, cross-role/tenant disclosure, accessible interaction, pending approvals and delivered snapshot integrity.

## View Ownership and Contracts

| Workspace | Main domain records | Command owner |
|---|---|---|
| Scientist/experiment | Objectives, samples, candidates, results and decisions | Research; Campaigns for execution |
| Data scientist/curator | Sources, datasets, models, embeddings and claims | Data; Knowledge for assertions |
| Reviewer/customer | Review packets, bounded approvals and deliverables | Owning domain with Platform authority |
| Operator/agent manager | Tasks, runs, incidents, costs and deployment health | Agents/Campaigns/Platform by action |

A workspace owns presentation and navigation, not copies of these entities. A shared object reference includes scope, identity, revision and display policy. Customer-visible projections must be deliberately derived rather than internal objects with a few fields hidden in the browser.

## Workflow and Delivery Design

Workspaces assemble task-focused read models from authorized domain projections. Changes submit typed commands with expected revision and get an attributable disposition. Approval inbox entries bind exact proposed actions, costs, evidence and expiration; displayed summaries cannot silently approve changed payloads.

Deliverable assembly pins selected records and template/version, then produces an immutable package with included/omitted content and authority limits. Corrections create a new package linked to the old delivery. Customer notices and support workflows consume approved status without exposing privileged scientific or operational details.

## Failure and Boundary Example

A reviewer opens a package after one supporting measurement is superseded. Keep the original package intact and show the affected status/new revision if authorized. Do not edit the delivered report in place. A screen-reader user must be able to inspect the same decision/evidence relationships through a structured alternative rather than lose functionality because the primary view is graphical.

## Design Basis and Open Decisions

Role-workspace and accessibility requirements supply the intended journeys. Remaining decisions: task-level screen/navigation design, accessibility targets, supported devices/locales and customer disclosure templates. Acceptance should use realistic role scenarios, not only component rendering tests.
