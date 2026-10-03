# Research scientific input orchestration

- Status: BP-06.04/B1.08b implemented in Research0.23.0/contracts0.11.0; 792 source/792 isolated installed tests pass. Hosted routes and independent HTTP replacement remain c/d.
- Owner: Research. Design: [Scientific API boundary](../../../../../docs/Build%20Plans/BP-06/BP-06.04%20Scientific%20API%20design.md).

## Configuration and source boundary

boundary.py owns ConfiguredScientificInput/BoundScientificAssessment. Reviewed EligibilityInputProfile and SynthesisInputProfile reconstruct private policy objects and hash full configuration (2MiB ceiling). Exact scoped references bind actor and at most16 unique report Artifacts. profiles.py selects reviewed configurations for new work; it does not overwrite configuration in accepted intents. No caller-supplied policy or verdict is accepted.

resolution.py authenticates reports using one fresh bounded AssessmentDataReader per attempt. It checks schema/media/8MiB size before peer reads, actual allowed publisher, issuer, adapter transformation and required source lineage/current access. Policy context is also read. Up to1024 claims or64 alternatives are preserved across reports. Missing eligibility source attaches the authenticated report Artifact; explicit original sources stay explicit. All consumed reports, raw evidence and contexts are retained in the decision dependency set. Producer assertions retain synthetic authority. No scientific truth, numerical interpretation, imputation or normalization is inferred.

## State and replay

intent.py pins full request/profile/actor under research.scientific-intent.v1. store.py commits this intent before peer resolution. research_0010 introduces scientific_input_intents and scientific_input_outcomes with scoped foreign keys and SELECT/INSERT grants only. ScientificIntent checks exact resolved binding, scoped unique consumed inputs and complete dependencies. DecisionJournal.publish_prepared composes owner policy result, dependency indexes and exact outcome association into one transaction. A standalone same-id decision is not automatically treated as a completed submission. Scoped intent locks precede decision locks; no transaction spans network I/O. Conflicting actor, profile, input or result fails without rewriting history.

workflow.py composes separately owned LabIntakeWorkflow and ScientificAssessmentWorkflow. Existing lab stores/resolvers retain observation/partial-return semantics. Pending work resumes its stored profile even if removed from active configuration, with fresh source authorization. Outage, denial or malformed input leaves pending work and raises an operational error; none becomes a negative scientific finding. Exact completed submit/read uses stored results without current configuration or peer calls. Historical reads grant no new source-use rights. Network authentication and grant mapping remain c; private callers must supply an authenticated scope and actor.

## Replacement and verification

Tests/scientific_api owns pure binding/resolver/intent tests, PostgreSQL replay/concurrency/rollback/grants, orchestration and actual separately installed Data input authentication. Tests/eligibility and tests/synthesis preserve old default decision bytes when optional consumed sources are absent. Fault injection proves transaction rollback and postcommit reply recovery, not process-death durability. Rich quality UI is SQ-01; Runtime acceptance is outside this module.

A replacement must preserve configuration hashes, canonical intent bytes, original actor/profile, complete dependencies and exact outcomes, including optional weaknesses and independently blocked alternatives. Forward migration only: older Research environments lacking0010 must not migrate the upgraded database. Existing assessment/sufficiency publication command and receipt semantics are unchanged. Contracts expose scientific Artifact publication and consumer/impact selections, but their separately granted routes and authenticated consumer registration are still B1.08c work.

Verification `2026-10-03 03:23:00`:44 focused tests cover308 statements/38 branches100%;119 compatibility/dev tests, unchanged376 public schemas, lint and service dependency guards pass. Coverage measures exercised code, not every combination of scientific inputs.
