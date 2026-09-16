# MVP Product Requirements — Navy Paint Analysis

## Purpose

Provide one secure workspace for a human scientific team to organize and report the analysis of an existing Navy paint whose formulation is unknown.

The MVP does not reverse-engineer the paint automatically. Humans select the tests, interpret the results, decide what the paint may contain, and approve the conclusions. The software keeps the samples, files, observations, hypotheses, calculations, and report connected and auditable.

The MVP succeeds when the team can defensibly answer:

- What material was received?
- What tests were performed?
- What evidence was returned?
- What does the team believe the paint contains, and in what ranges?
- What supports or conflicts with those conclusions?
- What remains unidentified?
- Is there enough evidence to plan a baseline reconstruction, or is more testing needed?
- Can one small, bounded formulation-hypothesis batch be proposed, tested, returned through human-reviewed LLM extraction, and used for one reproducible genetic feedback decision?

## One-to-Two-Week Build Boundary

The implementation window is one to two weeks. The build must reuse existing candidate, lineage, hashing, report, and genetic-loop primitives wherever practical and avoid creating generalized platforms.

The closed-loop target is deliberately narrow:

```text
human-approved reconstruction variables and screening rules
  -> one small genetic proposal batch
  -> scientist selects candidates for testing
  -> one manually issued lab protocol/template
  -> report + CSV/raw-file return
  -> deterministic completeness checks
  -> LLM extraction into typed draft feedback
  -> scientist correction and acceptance
  -> deterministic fitness calculation
  -> one next-generation or stop decision
```

Implementation limits:

- one project and one active campaign;
- one formulation representation;
- one numeric mutation strategy and simple parent selection;
- no recombination requirement;
- one approved objective profile;
- one generic laboratory return CSV schema plus uploaded reports/raw files;
- one LLM provider/adapter;
- one human feedback/review screen;
- one or two small generations, subject to available laboratory turnaround;
- synchronous execution or one locally managed background job;
- manual candidate manufacture, lab coordination, and data cleanup;
- configuration files or operator-entered JSON are acceptable where building a full editor would exceed the time box.

If real laboratory turnaround cannot fit the implementation window, acceptance may use a clearly labeled representative return fixture to verify the software loop, while real scientific acceptance remains pending.

## Operating Assumptions

- One Navy paint-analysis project.
- A small, named internal project team.
- One controlled deployment and one project data boundary.
- Manual setup of users, samples, tests, methods, and laboratories.
- Manual communication with the Navy/customer and laboratories.
- Manual scientific interpretation and review.
- Generic file upload and one CSV import format; no proprietary instrument parsing.
- One basic, human-approved LLM-to-genetic round trip for generating or explaining bounded reconstruction hypotheses.
- One human-reviewed laboratory-feedback round trip into deterministic fitness and genetic selection.
- Operator-assisted configuration, imports, cleanup, support, backup, and report preparation are acceptable.
- Full automation, polished role portals, and enterprise-scale operations are not required.

## Scientific Boundary

A cured coating is a crosslinked, multiphase formulation rather than one recoverable molecule. The MVP produces a **human-reviewed composition hypothesis**, not a uniquely recovered original recipe.

It must keep these distinct:

- uploaded laboratory files;
- reported observations;
- normalized values;
- deterministic mass-balance arithmetic;
- human interpretations and component hypotheses;
- LLM-drafted requests/explanations and genetic-run hypotheses;
- unidentified material and uncertainty;
- readiness to plan a reconstruction;
- external Navy evaluation or qualification.

The system must allow the scientifically correct conclusion to be “insufficient evidence.” It must never force unknown material into an identified component or silently normalize a proposed composition to 100%.

## Users

- **Operator:** creates users/project, manages access, files, imports, backup, restore, and support.
- **Project scientist:** registers samples/tests, enters evidence, authors hypotheses, and drafts the report.
- **Scientific reviewer:** accepts or rejects evidence and conclusions and decides reconstruction readiness.
- **Program lead:** owns schedule, external coordination, and final report release.

One person may hold multiple roles. Scientific acceptance and final release must still record the responsible named person.

Laboratories and customer contacts do not need accounts. Project staff manually exchange material with them and record it in the workspace.

## Required Records

The MVP needs eight record groups.

### 1. Project

- project identifier, purpose, questions, status, dates, and team;
- known incumbent/product information;
- sample ownership and permitted use;
- confidentiality, handling, retention, and release notes;
- relevant specification or method references;
- open questions, assumptions, and limitations;
- uploaded project documents.

### 2. Samples and Custody

- sample identifier and type: Part A, Part B, mixed, cured, aged, control, or unknown;
- lot/container, received date, quantity/unit, condition, storage, photographs, and notes;
- parent sample for aliquots, cuts, extracts, residues, or other derived material;
- custody events: received, transferred, shipped, subdivided, prepared, consumed, returned, retained, or disposed;
- actor, time, source, destination, and note for each custody event.

Barcode support and automated inventory reconciliation are deferred.

### 3. Tests and Result Packages

A manually created test row contains:

- question, sample, laboratory, requested method, status, due date, and notes;
- expected report, raw files, and metadata;
- actual outcome: completed, completed with deviation, partial, failed, cancelled, or awaiting information.

A result package contains uploaded reports, raw/native files, CSV/spreadsheets, method information, and any calibration, control, replicate, uncertainty, deviation, consumption, or return information supplied by the laboratory.

The issued protocol/template must bind:

- candidate/formulation identity and version;
- actual material lots where available;
- batch preparation, mix/application, substrate, cure, and test instructions entered by the scientist;
- incumbent or reconstructed baseline control;
- requested replicates and endpoint names/units;
- required deviations, actual process values, raw files, and result CSV fields.

For a genetic screening batch, the human-approved protocol must include the incumbent or accepted baseline as a control and repeated specimens where feasible. Candidates and controls must use the same declared preparation, substrate, application, cure, conditioning, and test method. The laboratory records actual values and deviations. The reviewer must pause selection when a control fails or observed variation makes candidate differences uninterpretable.

The system does not generate scientifically authoritative protocols. It formats the human-approved protocol and preserves its version.

The system stores original bytes and a content hash. It does not need to interpret proprietary instrument files.

Before LLM extraction, deterministic checks must verify candidate/protocol identity, required files and CSV columns, parseable values/units, replicate/control labels, declared deviations, and file hashes. Missing or invalid items remain visible and cannot silently become zero, failure, or accepted feedback.

### 4. Observations and Evidence Review

Observations are entered manually or imported with one documented CSV template. Each observation contains:

- sample and test;
- reported property, analyte, peak, phase, or finding;
- original value/text and unit;
- optional normalized value/unit;
- optional detection limit, uncertainty, and quality flag;
- source file and optional page/table/row reference;
- notes.

Original values remain unchanged. Corrections create history and require a reason.

Evidence review states are:

- `PENDING`;
- `ACCEPTED`;
- `ACCEPTED_WITH_LIMITATION`;
- `QUARANTINED`;
- `REJECTED`;
- `SUPERSEDED`.

For measurements considered by the genetic component, the reviewer additionally chooses:

- `ACCEPTED_FOR_FITNESS`;
- `ACCEPTED_INFORMATIONAL`;
- `RETEST_REQUIRED`.

The reviewer records a reason. Only accepted evidence may support an approved conclusion.

### 5. Composition Hypotheses and Mass Balance

Each human-authored hypothesis contains:

- proposed component, chemical family, or formulation role;
- applicable sample, part, or fraction;
- minimum, maximum, and optional best-estimate composition;
- unit and basis, such as wet Part A mass percent or cured-film mass percent;
- supporting accepted observations;
- conflicting observations;
- alternative identities;
- uncertainty, assumptions, limitations, and review state.

Generic identities such as “epoxy-family binder,” “polyamide/amidoamine-family curative,” “iron-oxide pigment,” or “unidentified inorganic fraction” are valid. Exact compounds and commercial grades are not required.

The only required scientific calculation is transparent mass-balance arithmetic:

- total identified best estimate;
- total identified minimum/maximum;
- residual/unidentified fraction;
- warnings for invalid values, incompatible bases/units, or totals outside plausible bounds;
- separate balances for Part A, Part B, mixed material, cured film, or analytical fraction.

The system must not automatically rank identities, deconvolve spectra, infer a recipe, or allocate the residual.

### 6. Decision and Report

The scientific reviewer selects:

- `INSUFFICIENT_EVIDENCE`;
- `MORE_TESTING_RECOMMENDED`;
- `COMPOSITION_HYPOTHESIS_READY`;
- `BASELINE_RECONSTRUCTION_CAN_BE_PLANNED`.

The decision includes rationale, blocking unknowns, contradictions, recommended next tests, reviewer, and date.

The system exports a Markdown and PDF report containing:

- purpose and scientific claim boundary;
- sample/custody summary;
- requested and completed test table;
- accepted, limited, rejected, quarantined, and missing evidence;
- component hypotheses and ranges;
- mass balances and unidentified fractions;
- alternatives, contradictions, uncertainty, and limitations;
- reconstruction-readiness decision;
- recommended next actions;
- scientific review and release approval;
- evidence-file manifest and hashes.

Scientists remain responsible for the report narrative.

### 7. LLM Exchange

The MVP may call one configured LLM through a simple adapter. Each exchange records:

- project and initiating user;
- provider/model and timestamp;
- typed request and response;
- exact human-approved context supplied to the model;
- parsing/validation result;
- token/cost information when available;
- reviewer status and limitations.

The LLM may:

- convert human-written reconstruction goals into a draft structured genetic-run request;
- propose candidate variables, ranges, constraints, or starting hypotheses for human review;
- convert typed genetic-run output into a draft human-readable comparison or explanation;
- identify questions or missing information for a scientist to review;
- extract endpoint values, units, candidate identities, deviations, failures, and missing outputs from a returned laboratory report;
- reconcile report prose with the generic return CSV and flag discrepancies;
- draft a typed `GeneticFeedback` record for scientist review.

The LLM may not:

- directly launch a run;
- change approved variables, ranges, constraints, fitness definitions, or evidence;
- act as the fitness function;
- treat its suggestions as measured facts;
- approve, rank, retain, or reject reconstruction hypotheses;
- send project data to an unapproved provider;
- accept evidence for fitness or convert missing/failed/censored measurements into numeric values without an approved rule.

Only successfully parsed typed output is eligible for human review. Free-form output remains an attachment or draft note and cannot drive the genetic component.

The lab-feedback extraction must retain source file and source location for each extracted value, extraction confidence, discrepancies, missing required outputs, and model/provider identity. A scientist must be able to correct every field before acceptance.

### 8. Basic Genetic Run

The MVP may run a small bounded genetic or evolutionary process over human-approved reconstruction-hypothesis variables. It is intended to explore plausible composition hypotheses, not improve or qualify the Navy paint.

Each `GeneticRun` records:

- human-approved objective and run purpose;
- seed hypotheses;
- allowed variables and numeric ranges;
- hard constraints and deterministic fitness components;
- population size, generation limit, random seed, and stop condition;
- candidates attempted, rejected, duplicated, retained, and selected for review;
- parentage and changed fields;
- exact genetic implementation/version;
- typed results returned to the LLM and human reviewer;
- launch approval and final human disposition.

The one supported formulation genome is a human-configured list of existing ingredient/load variables and optional process variables. Each variable declares current value, minimum, maximum, step/precision, part/role, and mutable/fixed state. The run may not introduce an ingredient, molecule, role, test, or process variable absent from the approved configuration.

The one required mutation operator perturbs one or more approved numeric variables within their ranges and then performs deterministic feasibility checks. At minimum, checks must reject invalid totals, negative quantities, out-of-range variables, and incompatible mass-balance basis. Epoxy/curative balance, VOC, solids, or other chemistry checks are used only when the scientist supplies the required constants and approved rule.

The run must be small enough to execute synchronously or as one locally managed background job. One mutation approach and one selection approach are sufficient. Recombination, distributed execution, active learning, surrogate models, and automatic laboratory feedback are deferred.

The genetic component may use only human-approved deterministic quantities such as range compliance, mass-balance residual, incumbent-distance measures, and accepted laboratory endpoints. It must not claim that a numerically favored hypothesis is chemically correct or equivalent to the incumbent.

The single objective profile must classify every endpoint as:

- a hard constraint;
- a soft minimize/maximize/target objective with weight;
- informational only.

It must declare endpoint name, unit, method/protocol scope, direction/target, acceptable range where applicable, missing-data behavior, and whether uncertainty/replicates are required. LLM prose cannot define or change an objective.

The `GeneticFeedback` consumed by fitness contains only:

- candidate and formulation identity;
- protocol version;
- scientist-accepted endpoint values and units;
- replicate summary and uncertainty when available;
- control-normalized value when the approved rule requests it;
- hard-gate results;
- explicit missing endpoint mask;
- evidence/source references;
- reviewer identity and approval time.

The deterministic fitness calculation, not the LLM, converts that feedback into typed fitness components. Missing measurements remain missing unless the approved objective profile explicitly defines another behavior.

The required communication is:

```text
human goal + accepted project evidence
  -> LLM draft GeneticRunRequest
  -> human review/edit/approval
  -> bounded genetic run
  -> typed GeneticRunResult
  -> optional LLM draft explanation
  -> human scientific disposition
```

The feedback cycle continues:

```text
selected GeneticCandidate + versioned lab protocol
  -> lab report + CSV/raw files
  -> deterministic completeness validation
  -> LLMExtraction draft
  -> scientist corrections and evidence disposition
  -> approved GeneticFeedback
  -> deterministic FitnessComponents
  -> human-reviewed SelectionDecision
  -> one next generation or stop
```

The campaign must retain every attempted, rejected, duplicate, failed, untested, and reviewed candidate so a later run does not silently repeat or erase failures.

Stop or pause when controls fail, accepted feedback is incomplete, laboratory variability makes the comparison unusable, all candidates fail hard constraints, no valid parent remains, the approved generation limit is reached, or the scientist stops the campaign. Changing variables, objectives, methods, missing-data rules, or operators requires a new reviewed run configuration.

## Minimal Workflow

1. Operator creates the project and named users.
2. Scientist uploads project documents and registers samples.
3. Scientist records the human-selected test plan.
4. Project team sends samples/files to the laboratory outside the system.
5. Scientist uploads returned reports/raw files and reconciles test status.
6. Scientist manually enters or CSV-imports observations.
7. Reviewer dispositions the evidence.
8. Scientist authors component hypotheses and composition ranges.
9. System calculates mass-balance totals and unidentified fraction.
10. Optionally, the LLM drafts a bounded genetic-run request from the human goal and accepted project context.
11. Scientist edits and approves the variables, constraints, fitness, and launch.
12. Genetic component runs and returns typed candidate hypotheses and lineage.
13. Scientist selects a small test batch and approves a versioned protocol containing incumbent/baseline control and feasible replication.
14. Project team coordinates candidate manufacture/testing outside the system and uploads the return package.
15. System performs deterministic completeness and identity checks.
16. LLM extracts a typed draft feedback package and flags discrepancies/missing outputs.
17. Scientist corrects the extraction and dispositions each endpoint for fitness, information, or retest.
18. System computes deterministic fitness from only approved feedback.
19. Scientist reviews the selection and chooses one next generation or stop.
20. Optionally, the LLM drafts a comparison of typed results for human editing.
21. Reviewer records reconstruction readiness.
22. Scientist edits the report; reviewer and program lead approve it.
23. System exports the report and evidence manifest.

## Minimal UI

Seven simple screens are sufficient:

1. **Project:** setup, documents, team, open questions, and status.
2. **Samples:** sample table, derived-sample relationships, and custody timeline.
3. **Tests and Files:** test plan/status, result packages, uploads, and deviations.
4. **Observations:** editable table, CSV import/export, evidence links, and review state.
5. **Composition and Exploration:** hypotheses, ranges, support/conflict links, mass balance, LLM draft request, human run approval, genetic-run status/results, and human disposition.
6. **Decision and Report:** readiness decision, report editor/preview, approvals, and export.
7. **Administration:** users/roles, audit history, backup/export status, and system errors.

Tables, forms, file links, validation messages, filters, and status badges are sufficient. Specialized scientific plotting, separate customer/laboratory portals, mobile design, branding, localization, and advanced dashboards are deferred.

## Minimal Technical Requirements

- One web application with a transactional database and protected file storage.
- Local file storage is acceptable for the controlled pilot if access-controlled and backed up.
- Named accounts and basic project roles; no shared logins.
- Secure password storage or one available identity provider.
- TLS when used over a network.
- Secrets outside source code and project files.
- Uploaded-file hashing and durable storage.
- One documented observation CSV schema.
- One configurable LLM adapter with typed request/response validation and a disabled-by-default external-data policy.
- One bounded local genetic runner with deterministic seeds, retained lineage, constraints, results, and replay inputs.
- Markdown-to-PDF report generation.
- Database and file backup plus at least one successful restore test before final report approval.
- Visible upload/import errors; failed operations cannot create accepted partial evidence.
- No project data sent to external models or services without explicit authorization.

High availability, multiple regions, formal SLA, SSO/SCIM, multi-tenant isolation, billing, durable distributed queues, and enterprise integrations are deferred.

## Minimal Auditability

Record actor, time, action, affected record/file, and reason for:

- project and sample changes;
- custody events;
- file upload/replacement;
- observation creation/correction/import;
- evidence acceptance/rejection/supersession;
- hypothesis and range changes;
- LLM request/response, validation, human edit, and approval;
- genetic-run launch, configuration, candidates, result, replay, and human disposition;
- readiness decisions;
- report generation, approval, and export;
- user/role changes and backup/restore.

A reviewer must be able to follow:

`report conclusion -> hypothesis/GeneticFeedback -> accepted endpoint/observation -> source file -> protocol/test -> candidate/sample -> custody and lineage history`

Audit history must be viewable and exportable. Distributed event infrastructure, cryptographic signing of every event, SIEM integration, legal-hold automation, and point-in-time database reconstruction are deferred.

## Human Support and Manual Work

The MVP intentionally depends on humans:

- Operators configure the workspace, users, imports, storage, and backups.
- Scientists define methods, resolve mappings, interpret evidence, and write conclusions.
- Scientists manually review and edit every LLM-drafted genetic request and every LLM-drafted result explanation.
- Scientists define the genetic variables, constraints, deterministic fitness, and scientific disposition; the system does not infer these authorities.
- Program staff communicate with laboratories and the customer.
- Support staff correct configuration/import problems with recorded reasons.
- Developers may create one-off conversion scripts, provided the produced file is reviewed, uploaded, and identified in provenance.

The configured in-product LLM is limited to the typed genetic communication and drafting functions above. No general agent, neuro-symbolic engine, autonomous research loop, capability matching, or generated nodes are required.

## Deferred Features

- Automatic document extraction or method selection.
- Proprietary instrument parsers and scientific visualization.
- Automatic spectral/chromatographic interpretation.
- Neuro-symbolic inference.
- Genetic optimization of improved/qualified paint candidates beyond the bounded reconstruction-hypothesis run.
- Scale-up, manufacturing release, or validated production baseline beyond the small screening batch.
- General knowledge library or web research.
- Cross-project learning.
- Node SDK, plugin platform, or dynamic capability matching.
- Customer and laboratory self-service portals.
- Multiple simultaneous customers.
- Enterprise IAM, integrations, deployment profiles, commercial controls, and autonomous agents.
- Manufacturing, procurement, safety, legal, performance, or qualification authority.

Manual files and reviewed attachments may substitute for deferred integrations and calculations during this project.

## Acceptance Criteria

The MVP is accepted when a real Navy paint project can, with ordinary operator and scientific support:

1. Create the project and users.
2. Register samples and custody events.
3. Record the test plan and laboratory outcomes.
4. Upload reports, raw files, and available method metadata.
5. Enter/import observations and bind them to samples, tests, and files.
6. Review evidence using the required dispositions.
7. Record component hypotheses, ranges, alternatives, conflicts, and unknowns.
8. Calculate transparent mass balances without forcing 100% identification.
9. Complete one typed LLM draft request → human approval → bounded genetic proposal run.
10. Select a small screening batch under a versioned human-approved protocol with an incumbent/baseline control and feasible replication.
11. Ingest a real or clearly labeled representative lab return and reject mismatched identities, malformed values, and missing required fields without converting them to fitness.
12. Complete LLM extraction → scientist correction → endpoint disposition → approved `GeneticFeedback`.
13. Compute fitness deterministically from only approved feedback and retain uncertainty, missingness, controls, and source references.
14. Make one human-reviewed next-generation or stop decision and retain rejects, duplicates, failures, and untested candidates.
15. Reproduce genetic proposal and selection calculations from retained inputs/seeds, or explicitly record the non-reproducible portion.
16. Show that malformed/free-form LLM output cannot launch a run or supply unapproved fitness, variables, constraints, or missing-data rules.
17. Prevent genetic/LLM outputs from appearing as measured facts or proof of chemical correctness/equivalence.
18. Record a human-approved reconstruction-readiness decision.
19. Generate an approved Markdown/PDF report and evidence manifest.
20. Trace every conclusion through evidence, sample/candidate, custody, protocol, LLM extraction, feedback, fitness, and selection.
21. Restore the project database and files from backup with hashes intact.

The workflow must not require a developer to edit authoritative database records or evidence files. Operator-assisted setup, CSV preparation, cleanup, training, and troubleshooting are acceptable.

`INSUFFICIENT_EVIDENCE` and `MORE_TESTING_RECOMMENDED` are valid final outcomes. The MVP exists to make the team's evidence and uncertainty defensible, not to force a composition answer.
