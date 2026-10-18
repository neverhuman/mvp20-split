# Amphora | Detailed task register

Generated from `task_ledger.json`. Edit the ledger, then rerun this projection. Inspecting a task contract is not an acceptance pass. Future investor work and follow-on execution remain subject to their stated scope.


## F - Source, scope and reconciliation

### DD-001 - Read and fingerprint all three attachments

- Status: **verified**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: none.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/specification_register.json`.

**Acceptance**

- task-dd-001 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-001
```

- accept-dd-001 (manual): All 3 complete readable UTF-8 files; byte sizes, line counts, SHA-256 and full read ranges retained; raw files excluded from Git.

**Evidence:** `v2/docs/Diligence/2026-10-18/specification_register.json`

**Requirement sources:** SPEC-A lines 49-86; SPEC-B lines 708-717; SPEC-C lines 51-81.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-002 - Pin source and preserve scientific attachment

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-001.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/source_lock.json`.

**Acceptance**

- task-dd-002 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-002
```

- functional-dd-002 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-002 (manual): Exact source revision is 9c3018dc; every selected source size/hash matches its Git blob; paper digest remains f2287577...dd33a.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 49-86; SPEC-B lines 708-717; SPEC-C lines 51-81.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-003 - Record bounded interruption and return point

- Status: **verified**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-002.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/REPOSITORY_RECONCILIATION.md`.

**Acceptance**

- task-dd-003 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-003
```

- accept-dd-003 (manual): Preserve POP-01 E2.2a, Data qualification before Runtime binding; POP/RG/ML percentages and serving freezes are unchanged.

**Evidence:** `v2/docs/Diligence/2026-10-18/REPOSITORY_RECONCILIATION.md`

**Requirement sources:** SPEC-A lines 49-86; SPEC-B lines 708-717; SPEC-C lines 51-81.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-004 - Resolve canonical content and test ownership

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-003.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/DECISIONS.md`.

**Acceptance**

- task-dd-004 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-004
```

- accept-dd-004 (manual): One canonical dated v2/docs/Diligence tree; map alternative docs/diligence filenames; tests stay with existing dev owner.

**Evidence:** `v2/docs/Diligence/2026-10-18/DECISIONS.md`

**Requirement sources:** SPEC-A lines 49-86; SPEC-B lines 708-717; SPEC-C lines 51-81.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-005 - Reconcile implemented mechanisms and historical versions

- Status: **verified**; priority: P0.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-002.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/REPOSITORY_RECONCILIATION.md`.

**Acceptance**

- task-dd-005 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-005
```

- accept-dd-005 (manual): Compiler/completion source, curation audit and replacement proof read; stale service README summaries cannot override later exact acceptance scope.

**Evidence:** `v2/docs/Diligence/2026-10-18/REPOSITORY_RECONCILIATION.md`

**Requirement sources:** SPEC-A lines 49-86; SPEC-B lines 708-717; SPEC-C lines 51-81.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-006 - Reconcile scientific facts and metric selectors

- Status: **verified**; priority: P0.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-002.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/claims.json`.

**Acceptance**

- task-dd-006 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-006
```

- functional-dd-006 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-006 (manual): All 12 matrix cells source-bound; counts distinguish 320 formulations, 4870 observations, 3910 suffix targets and 3840 derived loss rows.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 49-86; SPEC-B lines 708-717; SPEC-C lines 51-81.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-007 - Characterize all twelve historical byte mappings

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-002.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/byte_reconstruction.v1.json`.

**Acceptance**

- task-dd-007 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-007
```

- functional-dd-007 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-007 (manual): Exactly 11 explicit LF-to-CRLF mappings plus one browser identity mapping reproduce all original pins without modifying the ledger.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 49-86; SPEC-B lines 708-717; SPEC-C lines 51-81.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-008 - Complete requirement and claim-ID crosswalk

- Status: **verified**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-005, DD-006, DD-004.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/SPECIFICATION_CROSSWALK.md`.

**Acceptance**

- task-dd-008 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-008
```

- accept-dd-008 (manual): Each source heading and all source-specific claim IDs map to canonical tasks/claims or a reasoned deferral; no competing ledger.

**Evidence:** `v2/docs/Diligence/2026-10-18/SPECIFICATION_CROSSWALK.md`

**Requirement sources:** SPEC-A lines 49-86; SPEC-B lines 708-717; SPEC-C lines 51-81.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-009 - Record release scope and authority boundary

- Status: **verified**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-008.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/release_profile.json`.

**Acceptance**

- task-dd-009 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-009
```

- accept-dd-009 (manual): Current delivery is local planning/scaffolding; investor release, public publishing, model fitting and service execution are not silently authorized.

**Evidence:** `v2/docs/Diligence/2026-10-18/release_profile.json`

**Requirement sources:** SPEC-A lines 49-86; SPEC-B lines 708-717; SPEC-C lines 51-81.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-010 - Approve the later investor release selection

- Status: **planned**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-009.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/approval/release_selection.json`.

**Acceptance**

- task-dd-010 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-010
```

- accept-dd-010 (manual): Named selected claims, audience, required checks and payload allowlist approved before release mode is enabled; no elapsed-time inference.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 49-86; SPEC-B lines 708-717; SPEC-C lines 51-81.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.


## T - Offline integrity and claim tooling

### DD-011 - Implement bounded strict JSON and path objects

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-004.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/diligence/core.py`.

**Acceptance**

- task-dd-011 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-011
```

- functional-dd-011 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py check-plan
```

- accept-dd-011 (manual): Duplicate keys, NaN/Infinity, oversized documents, absolute paths, traversal and linked inputs reject before evaluation.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-012 - Implement closed historical byte reconstruction

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-007, DD-011.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/diligence/core.py`.

**Acceptance**

- task-dd-012 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-012
```

- functional-dd-012 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-012 (manual): Source digest checked first; declared transform only; output must equal original frozen digest; no normalization fallback.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-013 - Compose unchanged original platform checker

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-012.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/diligence/capsule.py`.

**Acceptance**

- task-dd-013 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-013
```

- functional-dd-013 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-013 (manual): Original four-file checker closure and all required assertions run on temporary reconstructed bytes; nested 12-gate report retained.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-014 - Bind typed scientific claims to exact selectors

- Status: **verified**; priority: P0.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-006, DD-011.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/claims.json`.

**Acceptance**

- task-dd-014 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-014
```

- functional-dd-014 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-014 (manual): Every numerical cell has source pointer, full precision, unit, denominator, rounding policy and study classification; drift rejects.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-015 - Validate task DAG and evidence-backed statuses

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-008, DD-011.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/diligence/core.py`.

**Acceptance**

- task-dd-015 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-015
```

- functional-dd-015 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py check-plan
```

- accept-dd-015 (manual): Unknown/duplicate task IDs, missing dependencies, cycles and verified tasks without evidence reject; verified prerequisites must be satisfied.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-016 - Provide a read-only source verification command

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-013, DD-014, DD-015.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/diligence/cli.py`.

**Acceptance**

- task-dd-016 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-016
```

- functional-dd-016 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-016 (manual): One source-profile command runs claim checks, unchanged PLGA checker, unchanged BP-09 checker and fresh source dependency guard without models/services.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-017 - Provide opt-in bootstrap environment behavior

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-016.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/diligence/capsule.py`.

**Acceptance**

- task-dd-017 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-017
```

- functional-dd-017 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source --bootstrap
```

- accept-dd-017 (manual): Requested missing NumPy returns exit 3; no installation/downgrade. Present NumPy runs 4 pilot and 10 stage-2 intervals plus Holm and records actual version.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/pinned_arithmetic.json`, `v2/docs/Diligence/2026-10-18/evidence/missing_dependency.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-018 - Implement an internal standalone verification capsule

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-013, DD-014.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/diligence/cli.py`.

**Acceptance**

- task-dd-018 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-018
```

- functional-dd-018 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-018 (manual): Exported python3 verify.py works from a new directory with no original checkout; source-boundary result is explicitly not rerun.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-019 - Implement complete manifest and deterministic ZIP

- Status: **verified**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-018.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/diligence/cli.py`.

**Acceptance**

- task-dd-019 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-019
```

- functional-dd-019 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-019 (manual): Exact payload membership and hashes; no self hash; detached manifest digest; sorted fixed ZIP metadata; repeated exports agree byte for byte.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-020 - Qualify corruption and parser rejection cases

- Status: **verified**; priority: P0.
- Owner: quality reviewer; reviewer: release owner.
- Dependencies: DD-019, DD-015, DD-017.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/tests/diligence/test_integrity.py`.

**Acceptance**

- task-dd-020 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-020
```

- functional-dd-020 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 -m unittest discover -s v2/dev/tests/diligence -v
```

- accept-dd-020 (manual): Alter source, historical transform, metric, missing gate, qualifier, task dependency, delivered byte and unexpected payload; all required negative outcomes reject.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/tooling_test_receipt.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-021 - Measure scoped test coverage and platform support

- Status: **verified**; priority: P0.
- Owner: quality reviewer; reviewer: release owner.
- Dependencies: DD-020.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/tooling_test_receipt.json`.

**Acceptance**

- task-dd-021 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-021
```

- functional-dd-021 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 -m unittest discover -s v2/dev/tests/diligence -v
```

- accept-dd-021 (manual): Record actual Python/platform and line plus branch coverage; any unavailable coverage is explicitly unmeasured, never inferred from test count.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/tooling_test_receipt.json`

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-022 - Close duplicate-check and timeout failure semantics

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-016.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/diligence/capsule.py`.

**Acceptance**

- task-dd-022 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-022
```

- accept-dd-022 (manual): Timeout/oversized checker stdout/child dependency failure emits bounded rejection; each required check runs once; no shell-selected commands.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-023 - Add portable CLI receipt output semantics

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-022.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/dev/diligence/cli.py`.

**Acceptance**

- task-dd-023 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-023
```

- accept-dd-023 (manual): Optional output is a new explicit path, atomic after successful validation; existing receipts are not overwritten silently; errors preserve failure evidence.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-024 - Publish schema interoperability fixtures

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-023.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Internal plan/tooling qualification
- Deliverables: `v2/docs/Diligence/2026-10-18/schemas/README.md`.

**Acceptance**

- task-dd-024 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-024
```

- accept-dd-024 (manual): Versioned JSON schemas and positive/negative independent fixtures agree with domain validation; unsupported versions and unknown keys reject.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 556-745; SPEC-B lines 448-591; SPEC-C lines 350-518.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.


## C - Claim qualification and release policy

### DD-025 - Review graph and execution ownership claims

- Status: **planned**; priority: P0.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-005.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/approval/claims_systems.json`.

**Acceptance**

- task-dd-025 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-025
```

- accept-dd-025 (manual): Campaign/Knowledge/derived lineage and Runtime single execution authority linked to exact owner source and acceptance workload.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 148-294; SPEC-B lines 465-546; SPEC-C lines 520-574.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-026 - Review original model proposal and budget claims

- Status: **planned**; priority: P0.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-005.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/approval/claims_agents.json`.

**Acceptance**

- task-dd-026 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-026
```

- accept-dd-026 (manual): Use retained original proposal and four unchanged scientific nodes; reservations, reported estimates and unknown usage kept distinct.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 148-294; SPEC-B lines 465-546; SPEC-C lines 520-574.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-027 - Review replay, corrections and reuse claims

- Status: **planned**; priority: P0.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-005.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/approval/claims_context.json`.

**Acceptance**

- task-dd-027 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-027
```

- accept-dd-027 (manual): Accepted-log reconstruction, future-campaign correction and synthetic producer-backed reuse scoped independently; no biological equivalence claim.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 148-294; SPEC-B lines 465-546; SPEC-C lines 520-574.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-028 - Review evaluator reconstruction proof

- Status: **planned**; priority: P0.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-013.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/platform_cases.json`.

**Acceptance**

- task-dd-028 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-028
```

- accept-dd-028 (manual): Recorded run ID, versions, 15/6/3/15 counts and stale-fence oracle exactly match source; independent installation distinguished from authored reconstruction.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 148-294; SPEC-B lines 465-546; SPEC-C lines 520-574.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-029 - Review search and synthetic comparison claims

- Status: **planned**; priority: P0.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-005.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/platform_cases.json`.

**Acceptance**

- task-dd-029 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-029
```

- accept-dd-029 (manual): If included, sphere objectives, 1D/2D, five seeds, 16 attempts per arm, all ten pairs/320 evaluations remain together; not a drug-performance benchmark.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 148-294; SPEC-B lines 465-546; SPEC-C lines 520-574.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-030 - Review all scientific context and contrasts

- Status: **planned**; priority: P0.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-014, DD-017.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/approval/claims_science.json`.

**Acceptance**

- task-dd-030 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-030
```

- accept-dd-030 (manual): Full precision and all ten planned intervals/Holm agree; post-pilot exposed-corpus status appears adjacent to any point estimate.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 148-294; SPEC-B lines 465-546; SPEC-C lines 520-574.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-031 - Review disclosure and current-use permission

- Status: **planned**; priority: P0.
- Owner: rights reviewer; reviewer: release owner.
- Dependencies: DD-009.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/approval/disclosure_matrix.json`.

**Acceptance**

- task-dd-031 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-031
```

- accept-dd-031 (manual): Each selected public/derived/internal object has explicit inclusion, source rights, allowed audience and review; historical identity is not fresh-use permission.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 148-294; SPEC-B lines 465-546; SPEC-C lines 520-574.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-032 - Review attribution, authorship and related work

- Status: **planned**; priority: P0.
- Owner: rights reviewer; reviewer: release owner.
- Dependencies: DD-009.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/references_review.json`.

**Acceptance**

- task-dd-032 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-032
```

- accept-dd-032 (manual): Bao CC BY 4.0 attribution and repository license preserved; author/affiliation metadata verified; new related-work detail checked against primary sources.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 148-294; SPEC-B lines 465-546; SPEC-C lines 520-574.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-033 - Freeze approved external claim set

- Status: **planned**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-025, DD-026, DD-027, DD-028, DD-029, DD-030, DD-031, DD-032, DD-010.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/approval/claims_release.json`.

**Acceptance**

- task-dd-033 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-033
```

- accept-dd-033 (manual): Editorial state advances only after role review; no unreviewed candidate becomes approved; unsupported wording replaced or deferred transparently.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 148-294; SPEC-B lines 465-546; SPEC-C lines 520-574.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-034 - Define qualifying release tiers before execution

- Status: **planned**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-033.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/release_profile.json`.

**Acceptance**

- task-dd-034 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-034
```

- accept-dd-034 (manual): Core-required vs optional checks frozen before running; full release requires both arithmetic tiers and all selected platform assertions.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 148-294; SPEC-B lines 465-546; SPEC-C lines 520-574.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.


## D - Investor document authoring

### DD-035 - Author the one-page reading entry point

- Status: **planned**; priority: P0.
- Owner: technical writer; reviewer: release owner.
- Dependencies: DD-034.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/00_START_HERE.md`.

**Acceptance**

- task-dd-035 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-035
```

- accept-dd-035 (manual): 5/20/60-minute routes, revision/date, exact file inventory, offline command and separate full-model guide; one obvious start.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-036 - Author executive brief page one

- Status: **planned**; priority: P0.
- Owner: technical writer; reviewer: release owner.
- Dependencies: DD-034.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/01_TECHNICAL_INVESTMENT_BRIEF.md`.

**Acceptance**

- task-dd-036 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-036
```

- accept-dd-036 (manual): Affirmative proposition, research workflow problem, three source-linked proof cards and legible relationship figure; no service-count lead.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-037 - Author executive brief page two

- Status: **planned**; priority: P0.
- Owner: technical writer; reviewer: release owner.
- Dependencies: DD-036.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/01_TECHNICAL_INVESTMENT_BRIEF.md`.

**Acceptance**

- task-dd-037 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-037
```

- accept-dd-037 (manual): Integration thesis, bounded proof strip and next milestones; moat/customer/time-saving statements clearly hypotheses; two readable pages.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-038 - Author systems note objects and owners

- Status: **planned**; priority: P0.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-034.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/02_SYSTEMS_WHITEPAPER.md`.

**Acceptance**

- task-dd-038 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-038
```

- accept-dd-038 (manual): Explain two authored graph types/derived lineage, pure compilation and versioned owner map with one actual definition/plan/run example.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-039 - Author acceptance and recovery mechanism

- Status: **planned**; priority: P0.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-038.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/02_SYSTEMS_WHITEPAPER.md`.

**Acceptance**

- task-dd-039 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-039
```

- accept-dd-039 (manual): Prepare/reserve/recheck/local commit shown; network outside transaction; one actual stale-fence/reconciliation trace; no remote exactly-once claim.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-040 - Author attributable agent and future revision flow

- Status: **planned**; priority: P0.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-039.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/02_SYSTEMS_WHITEPAPER.md`.

**Acceptance**

- task-dd-040 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-040
```

- accept-dd-040 (manual): Original context/request/proposal/local validation/admission/retained outcome explained; bounded curation and queued RG-01 remain distinct.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-041 - Author search, replacement and reuse chapters

- Status: **planned**; priority: P0.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-040.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/02_SYSTEMS_WHITEPAPER.md`.

**Acceptance**

- task-dd-041 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-041
```

- accept-dd-041 (manual): One recorded reconstruction case plus context-qualified reuse and deterministic numerical search; original implementation and evidence versions visible.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-042 - Author neutral foundations and contribution section

- Status: **planned**; priority: P0.
- Owner: technical writer; reviewer: release owner.
- Dependencies: DD-041.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/02_SYSTEMS_WHITEPAPER.md`.

**Acceptance**

- task-dd-042 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-042
```

- accept-dd-042 (manual): Credit workflow/provenance/agent/search precedents using verified primary references; no unverified competitor absence or patentability assertion.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-043 - Generate the scientific reading guide

- Status: **planned**; priority: P0.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-034.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/03_PLGA_RESEARCH_GUIDE.md`.

**Acceptance**

- task-dd-043 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-043
```

- accept-dd-043 (manual): First-three-record illustration, metric formula, cohort, all 12 cells, interpretation, pinned source/notice and existing full paper links.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-044 - Generate the claim/evidence index

- Status: **planned**; priority: P0.
- Owner: technical writer; reviewer: release owner.
- Dependencies: DD-034.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/04_EVIDENCE_INDEX.md`.

**Acceptance**

- task-dd-044 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-044
```

- accept-dd-044 (manual): Each included claim has source revision, full digest, workload/version, evidence class, qualifier and actual verification tier; immutable links resolve.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-045 - Author a retained-workflow storyboard

- Status: **planned**; priority: P0.
- Owner: technical writer; reviewer: release owner.
- Dependencies: DD-044.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/05_WALKTHROUGH.md`.

**Acceptance**

- task-dd-045 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-045
```

- accept-dd-045 (manual): 3-5 minute script names actual retained identities; static storyboard labeled; no implied live call or fictional PLGA engine execution.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-046 - Draft the next scientific validation milestone

- Status: **planned**; priority: P0.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-045.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/06_NEXT_VALIDATION.md`.

**Acceptance**

- task-dd-046 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-046
```

- accept-dd-046 (manual): Freeze intended decision, unexamined overlap-screened panel, schedule/horizon, estimand/margin, comparator, missing-data and replicate policy; power/sample size remains evidence-based.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-047 - Run the ten-minute reader test

- Status: **planned**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-046.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/reader_review.json`.

**Acceptance**

- task-dd-047 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-047
```

- accept-dd-047 (manual): Unfamiliar reviewer can explain product, authority, demonstrated scope, verification route and next evidence; record reviewer role/outcome without invented signoff.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 419-516; SPEC-B lines 419-446; SPEC-C lines 575-636.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.


## B - Brand, figures and document generation

### DD-048 - Define declarative Amphora brand tokens

- Status: **verified**; priority: P0.
- Owner: design reviewer; reviewer: release owner.
- Dependencies: DD-004.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/brand_tokens.json`.

**Acceptance**

- task-dd-048 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-048
```

- accept-dd-048 (manual): Navy/teal/amber roles, local embedded fonts, Letter grid, body/caption size and header/footer rules are one versioned input.

**Evidence:** `v2/docs/Diligence/2026-10-18/brand_tokens.json`

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-049 - Provide executable branded plan renderer

- Status: **implemented**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-048, DD-015.
- Execution scope: current_local_plan_and_scaffolding.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Current review-plan renderer only; future investor brief/note outputs remain planned.
- Deliverables: `v2/dev/diligence/render_plan.py`.

**Acceptance**

- task-dd-049 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-049
```

- accept-dd-049 (manual): Renderer consumes validated inputs, embeds available fonts, emits selectable text and reproducible output metadata without remote fonts.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-050 - Provide shared LaTeX publication templates

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-048.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/dev/diligence/templates/amphora_note.tex`.

**Acceptance**

- task-dd-050 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-050
```

- accept-dd-050 (manual): Shared brand macro file plus brief/note layout contract; generated values escaped; no shell escape or arbitrary TeX from evidence.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-051 - Generate the owner relationship diagram

- Status: **planned**; priority: P0.
- Owner: design reviewer; reviewer: release owner.
- Dependencies: DD-050.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/figures/ownership.svg`.

**Acceptance**

- task-dd-051 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-051
```

- accept-dd-051 (manual): At most 8-9 boxes, no more than 4 across; owner boundaries clear; actual profile caption and separate PLGA adapter label.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-052 - Generate acceptance/recovery vector trace

- Status: **planned**; priority: P0.
- Owner: design reviewer; reviewer: release owner.
- Dependencies: DD-051.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/figures/acceptance.svg`.

**Acceptance**

- task-dd-052 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-052
```

- accept-dd-052 (manual): Worker/Runtime/Data lanes; remote reservation outside local commit; stale fence branch; one evidence-backed scenario.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-053 - Generate original/successor evidence figure

- Status: **planned**; priority: P0.
- Owner: design reviewer; reviewer: release owner.
- Dependencies: DD-052.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/figures/successor.svg`.

**Acceptance**

- task-dd-053 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-053
```

- accept-dd-053 (manual): Exact retained original proposal and changed future context; unchanged scientific nodes labeled; no spliced unrelated scenarios.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-054 - Generate PLGA information boundary figure

- Status: **planned**; priority: P0.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-053.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/figures/prefix.svg`.

**Acceptance**

- task-dd-054 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-054
```

- accept-dd-054 (manual): Three irregularly timed visible records, later query times and scoring-only labels; no fixed-day reinterpretation.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-055 - Generate complete scientific table and plot

- Status: **planned**; priority: P0.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-054.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/figures/plga_matrix.svg`.

**Acceptance**

- task-dd-055 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-055
```

- accept-dd-055 (manual): All six protocol-order arms for both learners, common pp axis and 3-decimal display; no invented arm CIs or winner badges.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-056 - Generate figure provenance sidecars

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-055.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/figures/figure_sources.json`.

**Acceptance**

- task-dd-056 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-056
```

- accept-dd-056 (manual): Every visual binds claim IDs, source hashes/selectors, units, rounding, mandatory caption and generation command.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-057 - Render final brief and systems note PDFs

- Status: **planned**; priority: P0.
- Owner: design reviewer; reviewer: release owner.
- Dependencies: DD-056.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/dist/Amphora_Systems_Technical_Note.pdf`.

**Acceptance**

- task-dd-057 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-057
```

- accept-dd-057 (manual): Brief exactly 2 pages; systems target 6 pages with permitted 7-8 for legibility; embedded fonts, proper metadata and no tiny type.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-058 - Validate text, references and external metadata

- Status: **planned**; priority: P0.
- Owner: quality reviewer; reviewer: release owner.
- Dependencies: DD-057.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/document_text_checks.json`.

**Acceptance**

- task-dd-058 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-058
```

- accept-dd-058 (manual): No placeholders/forbidden brand/unsupported titles; complete citation references and exact numbers; document prose is checked beyond keyword scans.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 747-787; SPEC-B lines 593-695; SPEC-C lines 658-695.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.


## P - Portable investor package

### DD-059 - Review the exact investor payload allowlist

- Status: **planned**; priority: P0.
- Owner: rights reviewer; reviewer: release owner.
- Dependencies: DD-031, DD-034.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/export_allowlist.json`.

**Acceptance**

- task-dd-059 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-059
```

- accept-dd-059 (manual): No raw attachments, credentials, private correspondence, full papers, data trees, runtime configs or unrelated operational reports; every entry has a role.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-060 - Define investor-safe historical evidence strategy

- Status: **planned**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-059.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/DECISIONS.md`.

**Acceptance**

- task-dd-060 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-060
```

- accept-dd-060 (manual): Exact original receipts require disclosure review; summaries remain clearly new derivatives and cannot masquerade as original 12-gate proof.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-061 - Implement approved-claim-only document assembly

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-060.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/dev/diligence/documents.py`.

**Acceptance**

- task-dd-061 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-061
```

- accept-dd-061 (manual): Unapproved/unknown claim IDs, missing qualifiers and roadmap promoted to present proof reject; every source/value is canonical.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-062 - Implement document-to-claim location coverage

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-061.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/dev/diligence/documents.py`.

**Acceptance**

- task-dd-062 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-062
```

- accept-dd-062 (manual): All substantive assertions and quantified captions reference approved records; manual review closes claims a keyword linter cannot identify.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-063 - Implement investor release-mode builder

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-062.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/dev/diligence/release_gate.py`.

**Acceptance**

- task-dd-063 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-063
```

- accept-dd-063 (manual): Release mode is separate from internal capsule; requires approved profile, disclosure, source/code closure, freshness and selected verifier results.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-064 - Include offline reviewer source closure

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-063.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/reviewer/verify.py`.

**Acceptance**

- task-dd-064 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-064
```

- accept-dd-064 (manual): Only fixed required original checkers and bounded helpers copied; code hashes and original source identities retained; no checkout dependency.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-065 - Implement package-local link remapping

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-064.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/dev/diligence/links.py`.

**Acceptance**

- task-dd-065 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-065
```

- accept-dd-065 (manual): Relative links work in the delivered tree; deep code links pin immutable source; offline-required links never silently depend on the internet.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-066 - Attach source and attribution notices

- Status: **planned**; priority: P0.
- Owner: rights reviewer; reviewer: release owner.
- Dependencies: DD-065.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/NOTICES.md`.

**Acceptance**

- task-dd-066 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-066
```

- accept-dd-066 (manual): Original repository/license and Bao notice travel with every derived table/figure; no new blanket license or publisher-authenticity claim.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-067 - Separate deterministic payload from execution receipts

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-066.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/release/RELEASE_RECEIPT.json`.

**Acceptance**

- task-dd-067 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-067
```

- accept-dd-067 (manual): Source vs documentation vs historical execution revisions separated; no manifest/archive self-cycle; receipt records actual environment and result.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-068 - Rebuild, archive and extract from a new directory

- Status: **planned**; priority: P0.
- Owner: quality reviewer; reviewer: release owner.
- Dependencies: DD-067.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/fresh_export.json`.

**Acceptance**

- task-dd-068 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-068
```

- accept-dd-068 (manual): Two builds deterministic; exact archive extracts under one root and verifies with stated dependencies and no original checkout.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-069 - Measure required offline check duration

- Status: **planned**; priority: P0.
- Owner: quality reviewer; reviewer: release owner.
- Dependencies: DD-068.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/verification_timing.json`.

**Acceptance**

- task-dd-069 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-069
```

- accept-dd-069 (manual): Record measured elapsed time on named hardware; target <120s evaluated honestly; no performance promise inferred from proposed budget.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-070 - Freeze final qualified payload identities

- Status: **planned**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-069.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/release/RELEASE_RECEIPT.json`.

**Acceptance**

- task-dd-070 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-070
```

- accept-dd-070 (manual): Final PDF/source/manifest/archive hashes and required receipt references match exact delivered bytes after last edit.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 642-689; SPEC-B lines 966-977; SPEC-C lines 776-814.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.


## Q - Qualification, freshness and handoff

### DD-071 - Run functional integrity and CLI regression suite

- Status: **verified**; priority: P0.
- Owner: quality reviewer; reviewer: release owner.
- Dependencies: DD-020.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/tooling_test_receipt.json`.

**Acceptance**

- task-dd-071 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-071
```

- functional-dd-071 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 -m unittest discover -s v2/dev/tests/diligence -v
```

- accept-dd-071 (manual): New positive and corruption cases exercise parser, source/reconstruction pins, claims, DAG, manifest and requested-dependency semantics.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/tooling_test_receipt.json`

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-072 - Run source guard and preservation comparison

- Status: **verified**; priority: P0.
- Owner: quality reviewer; reviewer: release owner.
- Dependencies: DD-016.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/preservation.json`.

**Acceptance**

- task-dd-072 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-072
```

- functional-dd-072 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-072 (manual): Boundary checker passes; v1, PLGA source/results/PDF, original ledger and production modules are unchanged against baseline.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-073 - Run a fresh source and capsule evidence check

- Status: **verified**; priority: P0.
- Owner: quality reviewer; reviewer: release owner.
- Dependencies: DD-019, DD-072.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/current_verification.json`.

**Acceptance**

- task-dd-073 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-073
```

- functional-dd-073 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source
```

- accept-dd-073 (manual): Actual original 12-gate nested result and PLGA aggregate checker succeed; source profile reruns static guard; capsule does not misreport it.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/source_python312.json`

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-074 - Run arithmetic in pinned optional environment

- Status: **verified**; priority: P0.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-017.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/pinned_arithmetic.json`.

**Acceptance**

- task-dd-074 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-074
```

- functional-dd-074 (implemented): Run the owned functional check and retain its actual environment, exit status and scope; the independent criteria below still govern acceptance.

```sh
python3.12 v2/dev/diligence/cli.py verify-source --bootstrap
```

- accept-dd-074 (manual): Use NumPy1.26.4/Python3.12 when available; otherwise record actual tested environment and keep pinned qualification task open; zero fits.

**Evidence:** `v2/docs/Diligence/2026-10-18/evidence/pinned_arithmetic.json`, `v2/docs/Diligence/2026-10-18/evidence/missing_dependency.json`

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-075 - Inspect every new PDF page visually

- Status: **planned**; priority: P0.
- Owner: design reviewer; reviewer: release owner.
- Dependencies: DD-049.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/pdf_visual_qa.json`.

**Acceptance**

- task-dd-075 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-075
```

- accept-dd-075 (manual): Render all pages at 100% and laptop width; inspect tables, breaks, footers, glyphs, clipping and contrast; bind final PDF hash and page count.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-076 - Test source/claim/figure artifact freshness

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-075.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/freshness.json`.

**Acceptance**

- task-dd-076 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-076
```

- accept-dd-076 (manual): Changing source/claim/brand/template invalidates dependent outputs; stale PDF cannot inherit an earlier QA receipt.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-077 - Design and qualify offline CI workflow

- Status: **planned**; priority: P0.
- Owner: build engineer; reviewer: release owner.
- Dependencies: DD-076.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/ci/diligence-checks.yml`.

**Acceptance**

- task-dd-077 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-077
```

- accept-dd-077 (manual): Pinned Python3.12 tests/negative cases, clean twice-build, source preservation and optional rendering; minimal permissions, no secrets/network/runtime services in verification jobs.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-078 - Complete scoped architecture drift review

- Status: **planned**; priority: P0.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-071, DD-072, DD-075.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/evidence/scoped_drift_audit.md`.

**Acceptance**

- task-dd-078 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-078
```

- accept-dd-078 (manual): Compare plan, module contract, implemented source and checks; outstanding release behavior remains named, never credited as complete.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-079 - Update canonical handoff and task status mirrors

- Status: **planned**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-078.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/HANDOFF.md`.

**Acceptance**

- task-dd-079 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-079
```

- accept-dd-079 (manual): Machine ledger owns this bounded plan; generated progress mirrored in plan/MBT; current and next task plus POP return point explicit.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-080 - Review concrete local deliverables

- Status: **planned**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-079.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/approval/local_review.json`.

**Acceptance**

- task-dd-080 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-080
```

- accept-dd-080 (manual): Plan/ledger/PDF/scaffolds open and run; reviewer can inspect before any public push; current request scope completed independently of future investor-release work.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-081 - Authorize any later public push or sharing

- Status: **planned**; priority: P0.
- Owner: release owner; reviewer: independent technical reviewer.
- Dependencies: DD-080, DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 5-15 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/approval/distribution.json`.

**Acceptance**

- task-dd-081 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-081
```

- accept-dd-081 (manual): Explicit later instruction names exact qualified artifact/audience/repo; no automatic push, message, invitation or site publication.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 964-1009; SPEC-B lines 930-977; SPEC-C lines 798-846.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.


## N - Optional and follow-on milestones

### DD-082 - Record a retained three-to-five-minute walkthrough

- Status: **planned**; priority: P1.
- Owner: technical writer; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/optional/Amphora_Walkthrough.mp4`.

**Acceptance**

- task-dd-082 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-082
```

- accept-dd-082 (manual): Only after core release; label retained/static/live segments with profile/date; playback and privacy review; no new calls or serving restart.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-083 - Prepare the short contribution-focused FAQ

- Status: **planned**; priority: P1.
- Owner: technical writer; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/optional/TECHNICAL_FAQ.md`.

**Acceptance**

- task-dd-083 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-083
```

- accept-dd-083 (manual): Approved claims and explicit future milestones answer practical reviewer questions; 2-page target; no new unsupported comparisons.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-084 - Run independent reviewer-machine Tier A/B checks

- Status: **planned**; priority: P1.
- Owner: quality reviewer; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/optional/reviewer_machine_receipt.json`.

**Acceptance**

- task-dd-084 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-084
```

- accept-dd-084 (manual): New machine/environment and exact acquired artifact identified; actual checks recorded; no assumed cross-platform qualification.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-085 - Plan an optional fresh frozen model replay

- Status: **planned**; priority: P1.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/optional/full_replay_protocol.md`.

**Acceptance**

- task-dd-085 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-085
```

- accept-dd-085 (manual): Separate explicit execution authority, full history, public data, frozen grid/resource caps and complete outputs; no new searches; not run for this task.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-086 - Plan an isolated actual-owner recovery witness

- Status: **planned**; priority: P1.
- Owner: systems reviewer; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/optional/recovery_witness_protocol.md`.

**Acceptance**

- task-dd-086 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-086
```

- accept-dd-086 (manual): Existing owned fixture/oracle, disposable isolated state and cleanup; no production/review manipulation; retained proof fallback.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-087 - Design prospective new-panel PLGA evaluation

- Status: **planned**; priority: P1.
- Owner: scientific reviewer; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/follow_on/new_panel_protocol.md`.

**Acceptance**

- task-dd-087 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-087
```

- accept-dd-087 (manual): Unexamined overlap-screened cohort, fixed information schedule/model/comparator, uncertainty and assay replicates frozen before outcomes; no invented power.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-088 - Design a matched workflow-value pilot

- Status: **planned**; priority: P1.
- Owner: product reviewer; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/follow_on/workflow_value_protocol.md`.

**Acceptance**

- task-dd-088 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-088
```

- accept-dd-088 (manual): Predeclare composition/change/reconstruction/replacement effort, reuse correctness and compute; matched tasks and no retrospective savings claim.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-089 - Resume population qualification at canonical gate

- Status: **planned**; priority: P1.
- Owner: runtime owner; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/follow_on/POP-01_link.md`.

**Acceptance**

- task-dd-089 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-089
```

- accept-dd-089 (manual): Actual Data retention qualification then Runtime profile/transport/recovery and population worker gates; preserve current owning plan sequence.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-090 - Qualify objective-driven research graph generation

- Status: **planned**; priority: P1.
- Owner: knowledge owner; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/follow_on/RG-01_link.md`.

**Acceptance**

- task-dd-090 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-090
```

- accept-dd-090 (manual): After POP-01; LLM proposes/refines scientific graph with Knowledge acceptance and evidence/inference separation; no corpus prerequisite assumption.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-091 - Qualify inherited scientific tools and PLGA integration

- Status: **planned**; priority: P1.
- Owner: scientific tool owner; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/follow_on/ML-01_link.md`.

**Acceptance**

- task-dd-091 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-091
```

- accept-dd-091 (manual): After canonical prerequisites; endpoint-specific corrected benchmarks, tool packaging, Registry/Runtime/data provenance and admitted execution acceptance.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-092 - Qualify the selected Linux production profile

- Status: **planned**; priority: P1.
- Owner: deployment owner; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/follow_on/linux_profile_protocol.md`.

**Acceptance**

- task-dd-092 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-092
```

- accept-dd-092 (manual): Separate host install/recovery/access/workload/soak proof; historical Windows or one Linux image cannot substitute.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.

### DD-093 - Expand references and ownership review when needed

- Status: **planned**; priority: P1.
- Owner: rights reviewer; reviewer: release owner.
- Dependencies: DD-070.
- Execution scope: future_scope_direction_required.
- Planning estimate: 10-30 minutes; unmeasured.
- Boundary: Later investor release or separately scoped follow-on; not completed by authoring this workplan.
- Deliverables: `v2/docs/Diligence/2026-10-18/follow_on/reference_rights_review.md`.

**Acceptance**

- task-dd-093 (implemented): Inspect the task contract; this command does not certify task completion.

```sh
python3 v2/dev/diligence/cli.py inspect-task DD-093
```

- accept-dd-093 (manual): Current primary sources for any added detailed comparisons; author/license/export rights decisions recorded; no patent or freedom-to-operate inference.

**Evidence:** Not yet retained; no acceptance pass is implied.

**Requirement sources:** SPEC-A lines 789-845; SPEC-B lines 892-907; SPEC-C lines 723-745.

**Failure rule:** Keep this task open, preserve any failed receipt and block dependent acceptance; do not downgrade a required gate.
