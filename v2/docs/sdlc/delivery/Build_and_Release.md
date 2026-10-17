# Build, CI and release gates

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.


## Purpose and handoff

| Element | Meaning |
|---|---|
| Why it exists | Make the accepted version reproducible and replaceable without corrupting pinned work or state. |
| Inputs | Candidate source/version, dependency closure, evidence, consumer/state impact and existing authorization. |
| Output | Identified artifacts and a release/cutover record, or an explicit blocked transition. |
| Completion test | Required build/compatibility/target checks pass and authorized cutover/recovery criteria are satisfied; a push alone is insufficient. |

## Existing automation and its limits

The repository has local verification scripts, package locks and independent-install/image probes. No hosted CI/CD workflow was found in the reviewed v2/root support material. These gates describe the required delivery process; they do not claim an automated deployment pipeline exists.

Use [local verification](Local_Verification.md) for commands. Run relevant owned checks, boundary/schema checks and required independent installs; retain exact evidence. Build an immutable candidate, review compatibility and state handling, then activate only within existing owner authorization and campaign/review drain boundaries. Pushing a branch is not deployment acceptance. Production targets Linux; Windows is a development host. No infrastructure migration is part of this documentation change.

Fixture or local image success does not prove target-platform operation. Never publish, merge, deploy, reset state or call a paid provider merely because this checklist describes those activities.

## Isolation and replacement gates

- Each service/tool builds and tests from its own dependency manifest and declared workspace packages. Unrelated scientific dependencies must not enter its image.
- Automated import/dependency checks reject private cross-owner imports and cycles. Integration checks reject unauthorized table access and verify public contract fixtures.
- Contract changes identify consumers, support windows and migrations. Pin dependencies; do not require every service to update because a shared convenience library changed.
- A replacement passes boundary fixtures, observable behavior, negative cases and relevant state/recovery tests without relying on old internals. Compare scientific results under declared tolerance and method identity; transport conformance alone is insufficient.
- Finish/drain the active campaign before human-initiated replacements. Preserve old versions, checkpoints and evidence as required for replay; explicitly migrate or reject incompatible state. Rollback means selecting an eligible prior version, not overwriting historical outputs.

## Tool release and replacement

Build and test a new immutable release independently. Publish it as a candidate, evaluate scientific applicability and protocol compatibility, and register eligible deployment capacity. Activate a replacement between campaigns in the initial profile. Keep the previous release available for pinned replay and rollback where permitted. Do not allow a rolling deployment behind a generic service address to send pinned invocations to a different algorithm version; route by release/digest and reject mismatches on the worker.

Scale replicas of the same pinned release subject to resources and admission policy. A deployment change does not alter scientific identity. Graceful termination stops new claims and drains or relinquishes attempts; forced death follows normal fenced recovery. External effects require reconciliation, not automatic resubmission.

Acceptance proves independent build/start and fixtures; schema rejection; two replicas claiming distinct work; duplicate/stale completion rejection; replica death/checkpoint recovery; version-specific routing; unauthorized data/network access rejection; and replacement without changes to unrelated tool code. No cluster is required to prove the pure scientific kernel, but deployment claims require actual target-environment tests.
