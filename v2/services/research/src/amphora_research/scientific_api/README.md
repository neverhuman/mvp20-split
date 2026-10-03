# Research scientific input orchestration

- Status: BP-06.04/B1.08b implemented in Research0.23.0/contracts0.11.0; 792 source/792 isolated installed tests pass. Optional hosted routes verified in Research0.24.0:827 source/827 installed and119 compatibility/dev tests; independently installed HTTP and replacement verified under d.
- Owner: Research. Design: [Scientific API boundary](../../../../../docs/Build%20Plans/BP-06/BP-06.04%20Scientific%20API%20design.md).

## Configuration and source boundary

boundary.py owns ConfiguredScientificInput/BoundScientificAssessment. Reviewed EligibilityInputProfile and SynthesisInputProfile reconstruct private policy objects and hash full configuration (2MiB ceiling). Exact scoped references bind actor and at most16 unique report Artifacts. profiles.py selects reviewed configurations for new work; it does not overwrite configuration in accepted intents. No caller-supplied policy or verdict is accepted.

resolution.py authenticates reports using one fresh bounded AssessmentDataReader per attempt. It checks schema/media/8MiB size before peer reads, actual allowed publisher, issuer, adapter transformation and required source lineage/current access. Policy context is also read. Up to1024 claims or64 alternatives are preserved across reports. Missing eligibility source attaches the authenticated report Artifact; explicit original sources stay explicit. All consumed reports, raw evidence and contexts are retained in the decision dependency set. Producer assertions retain synthetic authority. No scientific truth, numerical interpretation, imputation or normalization is inferred.

## State and replay

intent.py pins full request/profile/actor under research.scientific-intent.v1. store.py commits this intent before peer resolution. research_0010 introduces scientific_input_intents and scientific_input_outcomes with scoped foreign keys and SELECT/INSERT grants only. ScientificIntent checks exact resolved binding, scoped unique consumed inputs and complete dependencies. DecisionJournal.publish_prepared composes owner policy result, dependency indexes and exact outcome association into one transaction. A standalone same-id decision is not automatically treated as a completed submission. Scoped intent locks precede decision locks; no transaction spans network I/O. Conflicting actor, profile, input or result fails without rewriting history.

workflow.py composes separately owned LabIntakeWorkflow and ScientificAssessmentWorkflow. Existing lab stores/resolvers retain observation/partial-return semantics. Pending work resumes its stored profile even if removed from active configuration, with fresh source authorization. Outage, denial or malformed input leaves pending work and raises an operational error; none becomes a negative scientific finding. Exact completed submit/read uses stored results without current configuration or peer calls. Historical reads grant no new source-use rights. Optional hosted authentication/grants are described below; private callers must still supply an authenticated scope and actor.

## Replacement and verification

Tests/scientific_api owns pure binding/resolver/intent tests, PostgreSQL replay/concurrency/rollback/grants, orchestration and actual separately installed Data input authentication. Tests/eligibility and tests/synthesis preserve old default decision bytes when optional consumed sources are absent. Fault injection proves transaction rollback and postcommit reply recovery, not process-death durability. Rich quality UI is SQ-01; Runtime acceptance is outside this module.

A replacement must preserve configuration hashes, canonical intent bytes, original actor/profile, complete dependencies and exact outcomes, including optional weaknesses and independently blocked alternatives. Forward migration only: older Research environments lacking0010 must not migrate the upgraded database. Existing assessment/sufficiency publication command and receipt semantics are unchanged. Contracts expose scientific Artifact publication and consumer/impact selections, and their separately granted routes/authenticated consumer registration are implemented under B1.08c.

Verification `2026-10-03 03:23:00`:44 focused tests cover308 statements/38 branches100%;119 compatibility/dev tests, unchanged376 public schemas, lint and service dependency guards pass. Coverage measures exercised code, not every combination of scientific inputs.

## Optional scientific hosting

host.py validates the optional science configuration and verifies existing Research tables; serving never migrates. At most32 reviewed profiles total across lab_profiles, eligibility_profiles, synthesis_profiles, normalization_profiles and observation_use_profiles; empty lists support history-only hosting. Data read/publication tokens are environment references, loopback only, validated even with no active profiles. consumer_publishers names at most32 unique trusted producers. The CLI retains its64KiB configuration limit; do not interpret per-profile2MiB library limits as hosted configuration capacity. [History-only example](../../../config.science.example.json) contains no credentials or enabled write grants. To admit new work, provision immutable owner fixtures and exact published input references, install reviewed profiles and explicitly grant the named operation. Default host remains identity/declaration only; health and CLI check report synthetic_science when enabled.

records.py checks original decision/intake actor for attributed results; immutable material/experiment/observation reads are scope-authorized. operations.py applies one explicit grant before each owner operation. publications.py reads exact results, publishes Artifact-only output and authenticates explicit consumers through actual Data producer proof plus lineage containing the exact published decision Artifact. Consumers are indexed only after proof; read-only consumer/impact pages use append-only owner indexes. They neither discover global consumers nor mutate current campaigns. ScientificPublicationStore.lookup recovers the original publisher from history using SELECTs only. Pending publication resumes that publisher; changing current publisher config does not rewrite accepted commands. Credentials must still authorize its peer calls.

| POST /v1/ suffix | Request | Grant |
|---|---|---|
| lab-intakes | LabIntakeRequest | submit_lab_intake |
| lab-intakes/read | LabIntakeSelection | read_lab_intake |
| scientific-assessments | ScientificAssessmentRequest | assess_eligibility or assess_synthesis, by profile kind |
| scientific-assessments/read | Exact ScientificAssessmentRequest | read_scientific_assessment |
| scientific-decisions/read | ScientificDecisionRef | read_scientific_record |
| material-states/read, experiments/read, observations/read | Respective exact revision reference | read_scientific_record |
| scientific-publications, scientific-publications/read | ScientificPublicationRequest | publish_scientific_result, read_scientific_publication respectively |
| scientific-impact | ScientificImpactRequest | read_scientific_impact |
| scientific-consumers | RegisterScientificConsumer | register_scientific_consumer |
| scientific-consumers/read | ScientificConsumersRequest | read_scientific_impact |

routes.py bounds JSON bodies256KiB/5seconds, rejects duplicates/nonfinite/extra fields, and marks successes and errors no-store. Missing records/profiles404, denied authentication401 or authorization403, identity conflict/pending publication409, malformed or invalid scientific input422, unavailable owner/peer503. Operational failure is never a computed negative finding. Old transport routes keep their own compatible policies. Source/private HTTP tests remain a separate tier from the independently installed process proof under d.

Hosting verification `2026-10-03 03:42:21`:59 focused tests,529 statements/64 branches98%. Material/experiment read pass-through awaits d actual HTTP proof; owner-failure, generic malformed request and body-timeout responses remain B3/V1 defensive probes (9 statements total). CLI readiness and health report the same authority.

Actual HTTP verification `2026-10-03 03:53:36`:test_actual_workflow.py/peer_fixtures.py exercise independently installed Research/Data and a fresh Research environment, no scripted peers. Partial lab/eligibility/synthesis submissions, all three Artifact-only outputs, producer-proven consumers, separate grants/original actor, material/experiment/observation reads, offline completed history and pending original-profile recovery all pass. Idle replacement is not B3 process-barrier fault proof. The prior material/experiment read coverage gap is now covered behaviorally through actual HTTP (subprocess statements are not counted by parent coverage).

Research0.31.0 composes [interpretation API](../interpretation_api/README.md) as a focused optional-science component: reviewed normalization/use profiles, four separate interpretation grants and exact correction/material/interpretation impact routes. Old science configuration remains valid with omitted optional profile fields. All reviewed profile types share the total32 bound; host checks0011/0012 tables without migration. Existing scientific request/result schemas and publication authority are unchanged.

B3.03 verified `2026-10-03 12:06:32`: test_defensive_routes.py covers owner errors before and after result commit and an actual ASGI incomplete-body deadline. Pending work and committed history remain distinct; timeout accepts no intent; retries preserve original outcomes. Common routes cover58 statements/6 branches100% in the surrounding108-test source and installed suites. The observed Starlette/httpx deprecation remains nonblocking dev debt.
