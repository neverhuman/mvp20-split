# Navy Paint Analysis MVP Feature-Gap Analysis

## Assessment Status

| Field | Value |
|---|---|
| Status | Updated against the time-boxed MVP requirements; implementation not performed |
| Assessed | 2026-08-30 (America/Chicago) |
| Requirements source | `docs/Architecture/MVP_Product_Requirements.md` |
| Implementation assessed | `Z:\mvp20-split` working tree |
| Delivery boundary | One project, one active campaign, one controlled deployment, one to two weeks |
| Product objective | Human-led incumbent characterization plus one bounded candidate/lab-feedback decision |
| Readiness conclusion | Reusable trust and optimization primitives exist, but the integrated Navy workflow is largely missing |

This is an implementation-gap analysis, not a scientific finding, qualification assessment, or authorization to test or release a coating.

## Executive Conclusion

The latest MVP is much smaller than the earlier naval roadmap, but it is not already present in the codebase. The repository is primarily a collection of Rust/Python command-line modules, schemas, fixtures, evidence packages, and orchestration controls. It does not contain the required integrated project workspace, transactional application data model, seven-screen experience, or end-to-end laboratory feedback workflow.

The strongest reusable assets are:

- strict candidate and score envelopes;
- stable hashes, replay, provenance, and authority controls;
- formulation arithmetic and feasibility-oriented modules;
- CRO protocol and capture-template packaging;
- evidence-intake validation patterns;
- optimizer constraint and ranking boundaries;
- report packaging and claim-limiting patterns.

The largest gaps are:

- project, user, role, sample, custody, test, observation, hypothesis, and review persistence;
- protected file upload and evidence-to-record linking;
- a usable operator/scientist interface;
- the Navy-specific CSV and protocol/feedback contracts;
- the LLM adapter and typed, human-reviewed exchanges;
- a small formulation mutation/selection runner joined to accepted laboratory feedback;
- deterministic fitness over approved `GeneticFeedback`;
- application audit, backup/restore, and Markdown/PDF report assembly.

Planning posture:

- **Underlying reusable primitives:** moderate; approximately 40–50% of the needed technical concepts have implementation or contract precedent.
- **Integrated MVP workflow:** low; approximately 15–25% is directly runnable as the required product.
- **User-facing acceptance criteria:** very low; the current modules do not complete the required Navy project end to end.

These ranges are planning estimates, not earned-value metrics. A one-to-two-week delivery is plausible only with aggressive reuse, operator-entered configuration, a simple local deployment, and representative lab-return fixtures if physical testing does not return in time.

## Scope Boundary

This MVP does not require:

- automatic instrument interpretation or proprietary parsers;
- automatic identification of the original recipe;
- a coatings knowledge refinery or neuro-symbolic engine;
- cross-project learning;
- autonomous agents or laboratory coordination;
- multiple simultaneous customers;
- enterprise IAM, multi-tenancy, queues, HA, billing, or integrations;
- performance improvement, production release, naval qualification, or manufacturing authority.

Those items must not expand the one-to-two-week build.

## Current Implementation Baseline

### Reusable without conceptual redesign

| Existing capability | Evidence in repository | MVP use |
|---|---|---|
| Strict candidate contract | `amphora-candidate-contract` | Base identity and typed candidate payloads |
| Stable hashing and deterministic serialization | `amphora-core` and candidate-contract utilities | File, request, result, configuration, and replay fingerprints |
| Run provenance and replay patterns | `amphora-run-provenance` and CLI campaign controls | Genetic seed/version/replay records |
| Formulation arithmetic | `amphora-formulation-arithmetic` | Totals, range validation, and residual calculation after adaptation |
| Evidence validation | `amphora-evidence-intake-validator` | Fail-closed intake and disposition patterns |
| CRO packet and return template | `amphora-cro-protocol-packager` | Starting point for one Navy protocol and return CSV |
| Constraint/ranking governance | `amphora-optimizer-orchestrator` | Deterministic hard gates and fitness authority boundary |
| Human deliverable packaging | `amphora-report-packager` | Starting point for report and manifest |
| CLI orchestration | `amphora-cli` | Operator-run fallback and integration shell |

These are foundations, not completed MVP features. Most operate on module envelopes and files rather than the required application records and review lifecycle.

### Partial or mismatched foundations

| Area | Current posture | Gap |
|---|---|---|
| Candidate lineage | Hashes and candidate identities are well represented | No Navy formulation/campaign workflow joining candidates to tests and feedback |
| Evidence | Candidate-bound packages and validation rules exist | No observation ledger with source locations, review states, and corrections |
| Custody | CRO templates contain some custody/raw-file fields | No sample, derived-sample, or custody-event model and UI |
| Protocol packaging | CRO packager and capture template exist | No Navy protocol bound to controls, replicates, candidate versions, and return fields |
| Optimization | Constraint/ranking orchestration exists | No small numeric mutation loop, campaign persistence, or lab-feedback next-generation decision |
| Reporting | Report artifacts and claim controls exist | No project report assembling custody, evidence, hypotheses, mass balance, and approvals |
| Operations | CLI and control-plane patterns exist | No protected web workspace, role workflow, backup/restore proof, or application errors |

### Missing as an integrated capability

- authenticated project workspace and role assignments;
- durable project database and protected project file store;
- sample registry and custody timeline;
- test plan and result-package lifecycle;
- observation CSV import, correction history, and evidence review;
- composition hypotheses, support/conflict links, and distinct mass-balance bases;
- readiness decision and approval workflow;
- configured external LLM exchange with typed validation and human approval;
- lab-report extraction with source locations, confidence, discrepancies, and missing-output flags;
- approved `GeneticFeedback`, deterministic fitness, and next-generation/stop decision;
- seven minimal product screens;
- application audit export and tested database/file restore.

No production FastAPI/React application matching `docs/Architecture/Implementation_Architecture.md` was found. That document is a target design, not evidence of implemented routes, tables, or screens.

## Requirement-by-Requirement Gap

Status meanings: **Reusable** means directly useful implementation exists; **Partial** means related code or a contract exists but does not satisfy the requirement; **Missing** means no supported implementation was found; **Manual** is intentionally outside the software.

### Project, people, samples, and files

| Requirement | Status | Required MVP work |
|---|---|---|
| One project with team, status, questions, limitations, and documents | Missing | Add project/membership records and document upload |
| Named operator, scientist, reviewer, and program-lead actions | Missing | Add authentication, roles, and named approvals |
| Sample types, lots, condition, quantity, storage, photos, and notes | Missing | Add sample records and file associations |
| Derived-sample parentage | Partial | Reuse lineage concepts in a simpler sample relationship |
| Custody events | Partial | Turn CRO custody fields into an append-only sample timeline |
| Protected original files with SHA-256 | Partial | Reuse hash utilities; add storage, access checks, and download |

### Tests, observations, and review

| Requirement | Status | Required MVP work |
|---|---|---|
| Manual test plan and outcome states | Missing | Add test and result-package records/forms |
| Versioned protocol bound to candidates, controls, replicates, and process | Partial | Specialize the CRO packager and persist approval/version |
| One generic return CSV | Partial | Reduce the capture template to one documented and tested contract |
| Return completeness and identity checks | Partial | Adapt evidence intake for files, columns, units, controls, replicates, deviations, and hashes |
| Manual observation entry and CSV import | Missing | Add preview, row validation, visible errors, and editable drafts |
| Immutable originals and correction history | Missing | Add observation revisions rather than destructive overwrite |
| Evidence and fitness dispositions | Missing | Add reviewer workflow and eligibility enforcement |
| Source-file and page/table/row references | Missing | Add source locators to observations and extracted fields |

### Composition and decision

| Requirement | Status | Required MVP work |
|---|---|---|
| Human component/role hypotheses and ranges | Missing | Add hypothesis editor and review state |
| Supporting and conflicting observations | Missing | Add explicit evidence links |
| Alternatives, unknowns, assumptions, and limitations | Missing | Persist without forcing identity resolution |
| Mass balance by declared basis | Partial | Adapt arithmetic for min/best/max totals and unidentified residual |
| Invalid-value, unit, basis, and total warnings | Partial | Add visible blocking/warning states |
| Reconstruction-readiness decision | Missing | Add allowed decisions, rationale, blockers, reviewer, and time |

### LLM communication

| Requirement | Status | Required MVP work |
|---|---|---|
| One configured LLM adapter | Missing | Implement one provider; keep secrets outside source control |
| Typed `GeneticRunRequest` draft | Missing | Define schema, assemble approved context, parse strictly, require approval |
| Typed lab-return extraction | Missing | Include identity, endpoints, units, deviations, failures, missingness, confidence, and source |
| Typed `GeneticFeedback` draft | Missing | Map validated fields into a scientist-editable draft |
| Exchange audit | Missing | Persist request, response, context, model, validation, reviewer, and cost where available |
| Safety boundary | Missing | Prevent free-form/malformed output from launching runs, accepting evidence, or calculating fitness |

Existing Claude-oriented controller material is engineering/campaign automation, not an in-product Navy scientific LLM adapter. It does not satisfy these requirements.

### Genetic proposal and lab feedback

| Requirement | Status | Required MVP work |
|---|---|---|
| One formulation genome | Partial | Define a typed list of existing ingredient/loading and optional process variables |
| Mutable/fixed flags, bounds, and precision | Partial | Add one reviewed configuration schema |
| One numeric mutation strategy | Missing | Implement deterministic bounded perturbation; no recombination |
| Simple parent selection | Partial | Reuse selection concepts but implement one explicit MVP rule |
| Feasibility checks | Partial | Adapt arithmetic for totals, negatives, ranges, and basis |
| One objective profile | Partial | Define hard/soft/informational endpoints, weights, units, uncertainty, and missing-data rules |
| Complete attempt and lineage ledger | Partial | Reuse candidate/provenance patterns in one campaign store |
| Approved feedback eligibility | Missing | Require evidence references and scientist approval before fitness |
| Deterministic fitness | Partial | Reuse optimizer boundaries; implement transparent calculation outside LLM |
| Next-generation or stop | Missing | Add reviewer decision and pause/stop rules |
| Replay from seed/versioned inputs | Reusable/partial | Reuse hashing/provenance and test full campaign replay |

The current optimizer is not itself the required genetic loop. It consumes governed score envelopes and protects ranking authority, but the MVP still needs a formulation mutation operator, small campaign model, and explicit lab-return-to-fitness bridge.

### UI, audit, report, and operations

| Requirement | Status | Required MVP work |
|---|---|---|
| Seven minimal screens | Missing | Build compact forms/tables; routes may combine panels |
| Actor/time/action/reason audit | Partial | Extend provenance to CRUD, review, LLM, run, report, and admin events |
| End-to-end conclusion trace | Missing | Join conclusion through evidence, source, protocol, candidate/sample, custody, and lineage |
| Markdown/PDF report | Partial | Assemble Navy sections from records and permit scientist editing |
| Evidence manifest and hashes | Partial | Assemble a project-scoped manifest using existing hashing |
| Backup and restore | Missing | Add simple database/file backup and perform one restore test |
| Visible failures without accepted partial data | Missing | Add transactional imports and error visibility |

## Acceptance-Criteria Coverage

| AC | Outcome | Coverage |
|---:|---|---|
| 1 | Project and users | Missing |
| 2 | Samples and custody | Missing/partial primitives |
| 3 | Test plan and outcomes | Missing |
| 4 | Reports, raw files, and metadata | Partial primitives |
| 5 | Source-bound observations | Missing |
| 6 | Evidence dispositions | Missing |
| 7 | Hypotheses, conflicts, and unknowns | Missing |
| 8 | Transparent mass balance | Partial arithmetic |
| 9 | LLM draft → approval → proposal | Missing integration |
| 10 | Screening batch and controlled protocol | Partial packager |
| 11 | Validated lab return | Partial validator |
| 12 | Extraction → correction → approved feedback | Missing |
| 13 | Deterministic approved-feedback fitness | Partial optimizer foundation |
| 14 | Human next-generation/stop and retention | Partial lineage foundation |
| 15 | Reproducible proposal and selection | Partial replay foundation |
| 16 | Malformed LLM output cannot gain authority | Missing in-product enforcement |
| 17 | LLM/genetic output separated from measured fact | Partial claim controls |
| 18 | Reconstruction-readiness decision | Missing |
| 19 | Approved report and manifest | Partial packaging foundation |
| 20 | End-to-end trace | Missing |
| 21 | Hash-preserving restore | Missing |

None of the 21 criteria is currently satisfied end to end as a supported Navy workflow. Several have strong reusable components, making a focused integration effort feasible.

## Minimum Build Needed

### Must complete

1. **Thin application shell:** one deployment, local authentication/four named roles, transactional database, protected project files, and simple server-rendered pages or a minimal SPA/API.
2. **Project evidence spine:** project, membership, sample, custody, test, result package, file, observation/revision, evidence disposition, hypothesis/evidence link, decision, and audit event; hash every upload; provide one fail-closed CSV importer.
3. **Human scientific workflow:** sample/test/file/observation forms, hypotheses and evidence links, mass balance, readiness decision, report, PDF, and manifest.
4. **Bounded proposal loop:** one genome, seeded mutation, feasibility gates, simple selection, complete attempt lineage, and one objective profile.
5. **Lab feedback bridge:** one protocol/return CSV, deterministic validation, one LLM adapter, scientist correction/disposition, approved feedback, deterministic fitness, and human next-generation/stop.
6. **Operational proof:** audit export, malformed-input and authority-boundary tests, replay test, backup/restore test, and representative Navy fixture if real lab data is unavailable.

### Explicit shortcuts

- One hard-coded or configuration-driven project type.
- One formulation JSON shape and return CSV shape.
- Operator-entered JSON for variables, objectives, and protocol details.
- One LLM provider and prompt/version pair.
- Synchronous generation with a small population.
- One weighted deterministic fitness formula plus hard gates.
- Local project-scoped protected file storage.
- Simple role matrix instead of generalized policy administration.
- Incumbent or scientist-approved baseline as the only control type.
- Fixture data if laboratory turnaround exceeds the sprint.

### Cut first if time is lost

- Merge UI screens while preserving all required tasks.
- Make optional LLM result explanation a downloadable draft.
- Use operator-assisted report layout cleanup.
- If reliable PDF extraction cannot be completed, make structured CSV authoritative for numeric intake, retain the uploaded report, and record report reconciliation as manual.
- Support exactly one next-generation decision.

Do not cut human approval, source references, missing-data visibility, deterministic fitness, identity checks, controls, audit records, or replay inputs. They are the minimum trust boundary.

## One-to-Two-Week Critical Path

### Days 1–2: Contracts and storage

- Freeze project, observation CSV, protocol, extraction, `GeneticRunRequest`, `GeneticFeedback`, objective-profile, and audit schemas.
- Implement migrations and project file storage.
- Adapt candidate IDs, SHA-256, and canonical serialization.

### Days 3–5: Characterization slice

- Implement users/project, samples/custody, tests/files, observations/import/review, hypotheses, and mass balance.
- Establish minimal forms/tables.
- Verify corrections, rejected evidence, unknown fractions, and incompatible bases remain visible.

### Days 5–7: Proposal and protocol

- Implement genome, seeded mutation, gates, selection, lineage, and objective profile.
- Adapt CRO packaging to one Navy protocol and return template.
- Retain attempted, invalid, duplicate, selected, and untested candidates.

### Days 7–9: Lab return and LLM

- Validate identity, files, columns, units, controls, replicates, deviations, and hashes.
- Implement the LLM adapter and strict typed parsing.
- Implement scientist correction/disposition and approved feedback.
- Calculate deterministic fitness and record next-generation/stop.

### Days 9–10: Report and proof

- Assemble Markdown/PDF report, manifest, and audit export.
- Run malformed-input, authority-boundary, replay, and backup/restore tests.
- Complete the representative end-to-end acceptance run.

For a two-week window, remaining days should be reserved for integration defects, scientist review, deployment, and handoff. Candidate manufacture and laboratory testing are external schedule dependencies.

## Principal Risks

| Risk | Effect | MVP response |
|---|---|---|
| Schemas are not frozen immediately | Rework consumes sprint | Decide one protocol, CSV, genome, and objective profile before UI work |
| Existing modules are treated as drop-in services | Integration delays | Reuse algorithms/contracts selectively behind MVP adapters |
| Real lab turnaround exceeds build | Physical loop cannot finish in sprint | Use a clearly labeled representative fixture for software acceptance |
| PDF extraction is unreliable | LLM reconciliation becomes brittle | Make CSV authoritative and permit manual report reconciliation |
| LLM output is trusted directly | Invalid fitness/fabricated evidence | Strict parse, source binding, scientist approval, deterministic fitness |
| UI consumes schedule | Core workflow remains incomplete | Prefer compact forms/tables and operator-entered configuration |
| Backup/audit is deferred | Acceptance fails late | Implement audit and restore from the first data model |
| Scientific decisions remain unresolved | Objectives/tests cannot be encoded | Named scientists must supply methods, controls, ranges, and fitness policy |

## Decisions Required Before Coding

- Which incumbent samples and component states are available?
- What is the single MVP formulation representation?
- Which fields and units are mandatory in the return CSV?
- Which control, replication, and stop/pause rules are acceptable?
- What are the mutable variables, bounds, steps, fixed variables, and mass-balance basis?
- What is the objective profile, including hard gates, weights, uncertainty, and missing-data rules?
- Which LLM provider may receive project data, and what may leave the deployment?
- Is PDF extraction required, or may the LLM use reviewed report text plus authoritative CSV?
- Who may approve evidence, launch runs, approve feedback, decide selection, and release reports?
- Which fixture will be used if real lab feedback is unavailable?

## MVP Completion Gate

The MVP is complete only when one representative Navy project demonstrates this trace without a developer editing authoritative records:

```text
project and named users
  -> sample and custody
  -> test plan and uploaded files
  -> source-bound observations and review
  -> hypotheses, unknowns, and mass balance
  -> approved LLM-drafted run request
  -> reproducible bounded candidate batch
  -> selected candidates and versioned protocol
  -> validated lab return
  -> LLM extraction draft
  -> scientist correction and evidence disposition
  -> approved GeneticFeedback
  -> deterministic fitness
  -> human next-generation or stop
  -> readiness decision and approved report
  -> audit/evidence manifest
  -> successful restore with matching hashes
```

`INSUFFICIENT_EVIDENCE` and `MORE_TESTING_RECOMMENDED` remain successful outcomes. The MVP proves a controlled, reproducible evidence and decision loop; it does not prove exact reconstruction or naval qualification.

## Bottom Line

The framework is useful as a trust and computation kernel, but this MVP is principally an integration and workflow build. The practical gap is not a new scientific AI platform; it is a thin, durable evidence application joining samples, files, human review, one constrained genetic proposal, one LLM-assisted lab-return review, deterministic fitness, and a defensible report.

The one-to-two-week target is credible only if scope stays at that boundary. Generalized agent orchestration, neuro-symbolic inference, instrument integrations, multi-customer support, or a polished enterprise UI would put delivery at material risk.
