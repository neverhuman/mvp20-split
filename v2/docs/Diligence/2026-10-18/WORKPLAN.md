# Amphora | Investor diligence engineering workplan

**DD-01 - Internal engineering review draft - 18 October 2026**

Amphora's strongest review story is executable research with inspectable decisions and evidence. The work below turns that story into a small, coherent, reproducible technical package. It connects each substantive statement to a particular implementation boundary or scientific result, and makes verification practical for an outside adviser.

This document is the delivery plan and architecture for that package. The current assignment delivers the plan, a machine-readable task ledger, a professionally rendered review PDF and useful offline scaffolding. It does not certify that the proposed executive brief, systems note, investor capsule, recording or future scientific work is complete. The original eight-page PLGA paper and all reported results remain unchanged.

## 1. Execution tracker and authority

The inspected implementation snapshot is `9c3018dcdd17f40be27fc3c6dc7057d2d7cb05bc`. The local branch is `docs/investor-diligence-workplan-20261018`. The canonical task state is [task_ledger.json](task_ledger.json); [TASK_REGISTER.md](TASK_REGISTER.md) is its generated human-readable projection. [PROGRESS.md](PROGRESS.md) contains the generated numerical rollup. One task is one delivery unit: implemented, verified and planned are distinct states. Planning earns no completion credit for the investor release or any engine capability.

The release owner is an accountable role, not a person appointed by this document. Engineering, systems, scientific, design, rights and quality reviewers have distinct responsibilities. Role assignments do not imply that those people have already reviewed or signed anything. The independent reviewer accepts evidence against a stated gate; a successful script cannot appoint a reviewer or confer authorship.

The current scope is an explicit documentation/tooling interruption of the existing queue. Preserve the recorded POP-01 E2.2a return point: Data closure-retention qualification before Runtime retention-profile/transport/recovery and population-worker acceptance. Preserve POP-01 -> RG-01 -> ML-01 order. Existing engine percentages and serving-installation freezes are not recalculated. No production service, database, runtime policy, model provider, public contract, scientific protocol or frozen v1 file needs to change.

All changes stay local for review. The three raw specifications remain outside Git. Public pushing, investor messages, invitations, websites, access grants and attachment disclosure require a later instruction about the concrete selected output. This boundary comes from the current task scope, not from an invented approval requirement for harmless local work.

### Current and next positions

The local implementation covers source/requirement reconciliation, fixed historical byte reconstruction, strict source/claim/task checks and an internal verification capsule. Focused tests and the final review document establish the bounded tooling acceptance. Investor editorial approval, raw historical-record disclosure, complete investor prose, final figures and release qualification remain separate tasks. The next investor-release task is DD-010, selection of audience and claim/evidence set, followed by the C-phase role reviews. Routine plan/scaffold fixes can continue locally without that release decision.

Full task cards give concrete deliverables, dependencies, acceptance commands or manual criteria, evidence paths, owner/reviewer roles, source section ranges, estimated effort and failure disposition. An `inspect-task` command retrieves a contract; it does not certify its completion. Future commands are marked planned. No fabricated shell command prints success to stand in for an acceptance check.

## 2. Requirement reconciliation

All three specifications were read in full. [specification_register.json](specification_register.json) records exact filenames, sizes, line counts, SHA-256 and complete read ranges. SPEC-A has 1,097 lines/81,314 bytes, SPEC-B has 1,035 lines/84,461 bytes, and SPEC-C has 999 lines/93,841 bytes. They share the same reviewed repository revision. Their review receipts describe work done by the specification authors; they are source assertions until checked in this execution environment.

[SPECIFICATION_CROSSWALK.md](SPECIFICATION_CROSSWALK.md) maps source headings, differing claim IDs, output filenames and release obligations into this plan. It preserves differences rather than treating one attachment as authoritative merely because it is longest. This workplan adopts the strongest compatible verification contract and a smaller current delivery scope.

### Decisions resolving differences

1. **One canonical content tree.** Use `v2/docs/Diligence/2026-10-18/` under the active v2 documentation owner. SPEC-B's `docs/diligence/` is an alternative naming proposal, not a second maintained tree. A later root/docs pointer may link here after the investor materials exist. Do not create links to missing documents.
2. **One task authority.** `task_ledger.json` owns DD-01 task state. Human tables, the canonical plan mirror and MBT interruption note are projections or pointers. They do not compete with engine owning trackers.
3. **One claim vocabulary.** Use stable semantic IDs such as `CLM-RUNTIME-01` and `CLM-PLGA-03`. Preserve the attachments' C01-C12, C01-C08, N01-N09 and sample IDs through a crosswalk. Do not assume equal IDs mean equal claims across attachments.
4. **Two payload profiles.** The implemented capsule is an internal engineering witness. A later investor release has a separately reviewed allowlist, editorial approval, disclosure decisions, freshness and visual gates. Successful internal verification cannot promote it to an investor-approved package.
5. **Separate evidence dimensions.** Evidence class, original execution version/profile/date, source inspection, current verification and editorial status are independent fields. A source hash is not a fresh run; a fresh receipt check is not a scientific replication.
6. **Python first, declarative contracts, optional LaTeX.** Use Python for bounded file parsing, extraction, reconciliation, generation, packaging and verification. Use shared brand tokens and LaTeX publication templates. Use the already available PDF renderer for the current workplan. There is no existing v2 Cargo/Rust package to reuse; adding a second toolchain gives this bounded task no demonstrated benefit.
7. **Minimum versus preferred release.** A two-page brief, a concise systems note, the unchanged scientific attachment, evidence index and a genuinely runnable verification path form the later minimum. Six-page systems formatting, additional science wrapper, figures, FAQ and recording follow their declared priorities. None requires a new predictive discovery.
8. **Effort is a planning estimate.** The attachments' two-, three- and six-hour schedules are alternatives, not measured promises. The 93-task full register includes preparation, review, qualification and follow-on work beyond a single six-hour release. Choose a bounded subset explicitly; never imply all 93 tasks fit today.

## 3. Baseline assessment and evidence limits

The current repository already supplies real technical substance. Pure campaign compilation checks typed bindings, control constructs and exact schema/tool references. Runtime completion source rechecks current attempt/fence and artifact reservation bindings before local transactional acceptance. Knowledge rebuild operates on accepted history and expected-head publication. Numerical search preserves original specification, deterministic random stream, ancestry and checkpoints. The synthetic reuse owner binds actual producers and complete declared context. Source-adjacent contracts explain these boundaries; dated acceptance records establish narrower demonstrated workloads.

The managed-curation delivery audit describes Planning0.142, Deployment0.20.2 and Studio0.34.3, an original proposal, actual successor launch and four numerical outputs. The body preserved baseline scientific invocations while title/future context changed. An older introductory Planning README still describes incomplete earlier checkpoints. Bind a statement to its actual source/release and owning acceptance instead of flattening these historical differences into one current-health claim.

The recorded reconstruction example identifies restored run `3cb8621ad9d54f5086727ef183ec3884`, 15 invocations, six evaluations, three generation checkpoints and 15 confirmed retentions. This is an internal synthetic evaluator-reconstruction and recovery proof. Its Windows owner host and Linux tool image remain accurately labeled. It is neither external scientific validation nor a measured Linux whole-stack production qualification.

The source-reviewed numerical comparison can be a later proof card only after its exact evidence is bound. The proposed card retains both sphere dimensions, five seeds, all ten pairs, a fixed midpoint-grid comparator, 16 attempts per arm and the complete 320 evaluations. Better objective values in those declared pairs do not establish general optimizer or scientific superiority.

The broader engine still has separately owned population, research-graph-generation, inherited scientific-tool and deployment gates. The PLGA study used an isolated adapter and the ranking primitive. It made no LLM calls and was not an end-to-end run through the deployed campaign engine. A unifying engineering philosophy does not combine those separate executions into one fictional scientific discovery.

### Existing scientific evidence retained exactly

The benchmark predicts later recorded release from static formulation descriptors, the first three valid recorded time/release observations and the requested later time. It contains 320 eligible formulations, 4,870 valid distinct-time observations and 3,910 suffix targets per evaluation pass. Stage 2 uses 78 joint connected drug/DOI groups and 113 eligible publication DOIs. The third observation's median time is about 1.93 days; 317 prefixes include the recorded origin. This is a record-count information budget, not a fixed 24-hour assay.

There are six representation/target arms, two learners, five outer folds, three inner folds and four configurations per arm/learner. The main matrix uses `6 x 2 x 5 x (4 x 3 + 1) = 780` learner fits; the recorded full replay brings computation to 1,560 fits, not additional independent experiments. The metric averages absolute suffix error within each formulation, then gives every formulation equal weight, in release percentage points. Do not call it accuracy, pooled-observation MAE or whole-trajectory RMSE.

The complete twelve-cell table and all ten paired contrasts are generated from the original summary, never retyped into competing tables. All ten planned conditional 95% intervals include zero and none survives Holm correction. The study is post-pilot internal validation on a development-exposed corpus. Its contribution is controlled representation characterization and inspectable evaluation. Nonsignificance is not equivalence, and good prefix fit does not identify a physical release mechanism.

Recorded main RF and LightGBM process times are approximately 648.9 and 54.4 seconds; maximum recorded process RSS is approximately 239.4 MiB. These describe that matrix and environment. They are not parallel elapsed wall time, assay savings, total platform cost or customer return on investment. Any future use of these values needs exact provenance selectors and units.

The retained PDF SHA-256 is `f228757745d9d4836f6d048120867348ef6718e9763ca48ea0710f60b11dd33a`. Packaging copies those bytes. Rebuilding the existing paper, if necessary, occurs only in a disposable copy with `make -B all check`; a new PDF cannot inherit the old visual receipt.

## 4. Target build architecture

The documentation pipeline is offline development tooling with no execution authority over Amphora campaigns. Its components own focused behavior:

| Component | Input | Owned output | Explicit boundary |
|---|---|---|---|
| Source lock | Fixed implementation revision and selected paths | Source size/hash inventory | Git blob bytes; no host credentials or mutable latest references |
| Evidence pins/reconstruction | Reviewed source pin, transform and historical pin | Exact historical bytes in a new directory | No JSON reserialization, repinning or generic normalization |
| Claim registry | Reviewed statements, exact sources, selectors and scopes | Canonical numeric/text inputs | Editorial approval is distinct from scientific validity |
| Task ledger | Authored tasks and evidence references | Dependency ordering and progress projection | No task execution from JSON commands |
| Document assembler | Approved claims, prose slots, brand/template inputs | Markdown, TeX and figure data | Missing claim/qualifier blocks a release render |
| Renderer | Validated generated inputs and local fonts/toolchain | Selectable PDF and vector figures | No remote assets, arbitrary shell escape or model generation |
| Capsule builder | Reviewed file allowlist and fixed verifier closure | Manifested external payload | No whole-repository archive or raw attachment copy |
| Reviewer verifier | Capsule bytes and explicitly requested arithmetic tier | Structured result to stdout | No installation, network, models, services or database activity |
| Release gate | All required receipts and exact artifact digests | Qualified immutable delivery identity | No public distribution as a build side effect |

The implemented source directory is `v2/dev/diligence/`. `core.py` owns bounded parsing, paths, evidence transformations and claim/task/manifest validation. `capsule.py` composes unchanged original checkers. `cli.py` exposes fixed commands and internal capsule export. `render_plan.py` produces the current review PDF. Tests live in `v2/dev/tests/diligence/` under the existing dev owner. The module README records actual behavior and gaps. No Runtime/Planning/Data private imports, cross-service SQL or shared business/ORM layer is introduced.

The original deployment checker is copied with exact source bytes into its own importable package. Renaming its parent import directory does not alter its internal relative imports or assertions. Its source closure, policy, ledger, historical profile and output are recorded. The new tooling does not substitute a hash-only report for the original semantic assertions.

### Why these languages and formats

Python 3.12 is the minimum core runtime. The default reviewer path needs only the standard library and the selected original checkers. NumPy 1.26.4 is an explicitly optional arithmetic dependency; absence under `--bootstrap` is an environment failure, not permission to report a smaller success. Renderer dependencies remain separate from reviewer dependencies.

JSON is the canonical transport format for tasks, claims, source pins, brand tokens and receipts. Strict bounded parsing rejects duplicate keys, nonfinite numeric values and unknown version/field profiles where implemented. Stable key ordering and finite values support deterministic data. JSON schemas and independent interchange fixtures are a named follow-on task; custom validation is not misrepresented as published schema interoperability.

Markdown is the canonical prose source. LaTeX templates are the intended repeatable publication path for future brief/note releases; authoring need not duplicate freehand prose in both Markdown and TeX. The current workplan PDF uses ReportLab and installed embedded fonts to avoid making a new TeX installation critical. Neither PDF mechanism changes the retained IEEE paper.

Rust becomes useful only if a future measured validator/kernel requirement or an existing Rust component justifies it. It is not necessary for file hashing, small registries, task graphs or publication orchestration. A new performance language should not create avoidable installation and reproducibility work for the reviewer.

## 5. Data contracts and state transitions

### Claim and evidence contracts

Each candidate claim has a stable semantic ID, exact statement, evidence class, scope, nonempty source pins, explicit numerical measurements where applicable, mandatory qualifiers, editorial state, reviewer role, verification status and intended placements. Quantitative records include full source precision, JSON pointer, unit, denominator, display decimals and study scope. A string saying '320' in a paragraph is not the source of truth for a count.

Separate `source_reviewed`, `recorded_acceptance`, `retrospective_research` and `planned` classes. Current verification remains `inspected`, `recorded_only` or `not_run` inside the candidate registry. Fresh command receipts are separate artifacts that bind actual interpreter, invocation and result. A later profile may associate them with approved release statements; the current validator rejects silent promotion to `fresh_execution` or `approved`.

Preserve original execution time, source revision, review time and recheck time separately. A new documentation commit does not change the version that produced a historical run. `source_revision`, `documentation_revision`, `historical_execution_revision` and `verification_toolchain` have different meanings and must never share an invented universal version field.

An evidence export record binds source path/revision/blob digest, declared transform, original frozen digest, delivered digest/length, historical profile/workload, supported claims, current verification level and inclusion decision. Redaction or summarization creates a new derivative. Its digest and explanatory scope must differ from the original; it cannot replace an original record while claiming the original twelve-gate result.

### Task and progress contracts

The ledger provides 93 stable task IDs. Each has owner and reviewer roles, priority, phase, dependencies, concrete paths, acceptance contract, evidence references, source line ranges, execution authority, bounded estimate and failure disposition. A task may be planned, in progress, implemented, verified, blocked or deferred. Verified status needs evidence files and verified dependencies. The checker detects cycles, missing references and unsupported states.

Implementation and acceptance are separate: a renderer can exist before its final pages are inspected; an investor brief can be authored before editorial approval. A blocked required gate stays blocked. An optional task can remain unperformed only because the profile declared it optional in advance. Failure is not a reason to reclassify a required check as optional.

Estimates are per-task planning ranges, not a delivery date. Role effort is not parallel elapsed time. The full task set includes the eventual investor release and separately authorized follow-on work; do not sum it into a promise of a six-hour result. Record denominator changes explicitly if scope is later expanded.

### Historical transport contract

`byte_reconstruction.v1.json` contains the twelve fixed mappings characterized against the pinned revision. Eleven are `lf-to-crlf-v1`; the browser receipt is `identity`. Source pins are checked before transformation, then output is checked against the original ledger pin. LF transformation requires UTF-8, no CR bytes and the reviewed LF profile. It changes newline bytes only. No indentation, Unicode, numerical spelling, key order, spaces or terminal-newline presence is changed.

Unknown transforms, unexpected CRLF/mixed CR input, source drift, missing/extra gates or a historical-pin mismatch reject. There is no fallback that tries encodings until a digest matches. Exact Git blobs are acquired through fixed subprocess arguments, never shell text from evidence. Materialization occurs in a new external temporary directory and leaves tracked evidence untouched.

### Manifest and receipt contract

Every payload file appears once in the manifest with its path, size and SHA-256. The manifest does not list itself; its digest is detached. The complete membership check rejects an extra file, missing file, duplicate path, unexpected symlink or altered byte. Stable archive paths, timestamps, permissions, ordering and compression policy give reproducible ZIP payloads under the exercised toolchain. Build/verification timestamps and measured timing belong outside the deterministic payload.

SHA-256 establishes consistency with a selected pin, not publisher identity, rights, scientific truth or current service health. Signing is future scope unless a real signing process and trust distribution are implemented. Do not call a checksum manifest a signature.

## 6. Phases, dependency sequencing and stopping points

### F - Source and scope: DD-001 through DD-010

Read/fingerprint the three inputs, pin the repository, preserve the scientific paper, record the queue interruption, choose canonical ownership and resolve source assertions. Characterize the exact historical mappings and crosswalk the inconsistent labels before drafting release claims. DD-010 is a later release-selection decision and is distinct from permission to complete this current plan/scaffold task.

Exit: source and requirement inventory, candidate evidence classes, unchanged scientific attachment, exact return point and an explicit audience/scope profile. No later document should need an invented source or broad 'platform proven' statement to tell the story.

### T - Offline tooling: DD-011 through DD-024

Build strict bounded parsing and file/path objects, then the closed byte bridge and original-checker composition. Add numerical selector binding, task DAG validation, source/capsule interfaces and manifest/archive integrity. Functional positive and negative tests qualify the bounded behavior. Coverage, timeout/reporting hardening, optional receipt writes and schema interoperability retain their own task states.

Exit for the current scaffold: a new-directory internal capsule runs the original twelve assertions and PLGA aggregate check without the original checkout. The source profile separately reruns the dependency guard. Opt-in arithmetic reports its actual environment. No model, provider, service, download or database effect occurs in verification.

### C - Editorial and disclosure qualification: DD-025 through DD-034

Systems review covers owner authority, original proposals, budget uncertainty, Knowledge/corrections/reuse, search and the exact reconstruction case. Scientific review covers the complete matrix, inference family and applicability. Rights review covers original source terms, data attribution, authorship, references and payload audience. The release owner freezes approved claims and required tiers only after those reviews.

Exit: each external sentence has its actual implementation/evidence object, mandatory scope and declared placement. Unsupported promotional claims are rewritten to supported statements or omitted, while the complete relevant scientific record remains available. Release approval does not confer scientific validity or patentability.

### D - Investor authoring: DD-035 through DD-047

Draft the reader entry, two-page executive brief and systems note from the approved registry. Give the systems note a worked proposal-to-output story rather than a service inventory. Explain graphs, compilation, prepare/reserve/recheck/commit, future revisions, deterministic search and replacement/reuse. Generate the scientific reading guide and claim index. A storyboard and a future validation outline can be useful without pretending a recording or study happened.

Exit: a five-minute investor can state the proposition, a systems reviewer can trace a concrete mechanism in twenty minutes, and a scientist can find complete methods and arithmetic. The reader test is a manual review with an actual role and outcome, not a fabricated score from a linter.

### B - Brand and generation: DD-048 through DD-058

Freeze typography, palette, spacing, metadata and semantic color roles. Build reproducible templates and figure data from claims. Produce the owner map, one-scenario acceptance trace, retained successor/context figure and scientific information-boundary/matrix outputs only where they improve understanding. Figure sidecars retain exact source IDs, units, rounding, captions and generator commands.

Exit: all new PDFs have comfortable type, selectable text, embedded fonts and honest metadata. The brief stays two pages. The systems note targets six pages; an explicit seven/eight-page variant is preferable to shrinking text. The existing eight-page PLGA attachment stays byte-identical.

### P - Investor package: DD-059 through DD-070

Approve an exact payload allowlist. Resolve whether original historical receipts are suitable for the audience; their source metadata and historical identifiers cannot be stripped while preserving original pins. Build an approved-claim-only document assembler and investor release gate, separate from the current internal capsule. Include a controlled verifier closure, package-local links and notices. Separate stable payload from fresh execution receipts, rebuild twice and verify from an extracted directory.

Exit: the precise advertised reviewer command succeeds from only the delivered bytes and advertised dependencies. All required files are included, all private/extraneous files are excluded, all source/figure/claim bindings are current, and archive/manifest/PDF identities are frozen. No public publishing or third-party communication occurs as a side effect.

### Q - Qualification and handoff: DD-071 through DD-081

Run focused tooling tests, source preservation, current source/capsule checks and the requested arithmetic environment. Inspect every new PDF page. Validate freshness, qualify the intended CI profile and conduct a component-scoped drift review. Update the ledger, generated progress and canonical handoff pointers without claiming the engine queue advanced. Owner review of the local plan is separate from a later public release decision.

Exit for this assignment: detailed source-grounded local plan, reviewable PDF, task ledger, useful tested scaffolding, honest status, a precise commit/path and private delivery. Investor release gates can remain planned. DD-081 records the later explicit distribution decision rather than assuming previous publication approval covers these new attachments.

### N - Follow-on milestones: DD-082 through DD-093

After a qualified core package, optionally record a labeled retained walkthrough, prepare a concise FAQ or obtain a reviewer-machine receipt. Full frozen scientific replay and an actual-owner recovery witness require separately scoped execution decisions. Future science freezes a genuinely new overlap-screened panel and assay uncertainty. A workflow-value pilot measures effort, reconstruction, replacement, reuse correctness and compute on matched tasks. POP/RG/ML and Linux production-profile qualification retain their owning prerequisites and evidence.

These tasks are planning only. No new model search, live provider call, production restart, remote lab action or novel scientific result is created by this document.

## 7. A realistic minimum-release route

The later same-day route starts from the current source/tooling foundation. First choose the audience and approved claim subset. Require exact historical assertions only if the corresponding records clear disclosure; otherwise ship a smaller correctly labeled evidence route and do not advertise an absent systems pass. Preserve the existing PLGA attachment and standard-library review tier in either case.

For a three-hour narrative candidate, prioritize a one-page entry, two-page brief, concise systems Markdown note, one clear owner diagram, complete scientific paper/evidence links and approved claim index. These are drafting allocations; the candidate is not called a qualified portable release until its clean-export and document gates pass. A four-page systems fallback can be a deliberately selected profile, not a silent truncation of a six-page requirement.

For a six-hour target after the claims/source freeze, allocate roughly: 45-75 minutes to evidence/profile/portable checks, 90-120 minutes to source-linked systems writing, 45-60 minutes to brief/entry/scientific wrapper, 45-60 minutes to figures/rendering and 45-60 minutes to clean export, page review and fixes. These overlap only if actual people are assigned independent work. Re-estimate after the first timed build; do not promise these ranges as measured capacity.

Cut optional recording, FAQ, secondary figures, extra format copies, new scientific replay, live calls and additional case studies first. Keep source traceability, complete relevant scientific inference, original byte integrity, readable typography and clean export verification. If a required check fails, keep the task open and fix it; never award partial publication success through weaker assertions.

## 8. Document and generation contracts

### D01 - Start here

One screen/page, approximately 400-600 words. State the product in two sentences, give five-/twenty-/sixty-minute reading routes and bind the snapshot/release identity. The file table tells the reader which question each artifact answers. Show the standard-library command, separately optional arithmetic and a direct link to full model reproduction. Identify the systems demonstration and separate scientific study.

### D02 - Executive technical brief

Two pages, approximately 700-900 words at 11-point or larger body text. Page one presents research-workflow friction, the product proposition, a compact owner diagram and three proof cards. Page two explains the implemented combination and what additional tools, compatible context and qualified pathways could accumulate. A short proof strip and next milestones make the thesis concrete. Savings and a commercial moat are hypotheses until measured. No issue inventory, giant service map or test-count headline is necessary.

### D03 - Systems technical note

Six-page target, approximately 2,200-2,800 words plus figures/references. Explain object roles and ownership, typed compilation, durable attempt/result acceptance, bounded model proposals, pinned historical meaning, search/representation/reuse and a concrete reconstruction/recovery example. Every present-tense mechanism has a claim ID, exact source and demonstrated workload. Put full hashes and verification details in the linked evidence index, not tiny footnotes. Related work credits established workflow, provenance, agent and search foundations; a future detailed comparison must be checked against primary sources.

### D04 - Scientific reading guide

One or two pages, approximately 600-900 words. Explain first-three-record prediction, permitted inputs, formulation-balanced MAE, cohort/grouping and nested matched budgets. Generate the complete twelve-cell table and link all ten contrasts; put the exposed-corpus interpretation beside the result. Cite Bao version 2 and its CC BY 4.0 source. Keep the PLGA adapter separate from the platform. Link the original paper, frozen protocols, source pins and full reproduction route.

### D05 - Evidence index and reviewer instructions

Two to four pages or a navigable Markdown reference. Each claim points to its implementation owner, exact immutable source, historical version/workload, digest, evidence class, qualifier and actual verification tier. A compact proof matrix distinguishes recorded process proof, fresh hash/assertion checking and fresh arithmetic. An exported guide must work from its packaged paths and must not require a private server. Optional training instructions link to the existing full-history/public-data procedure rather than duplicating a drifting multi-step recipe.

### D06/D07 - Walkthrough and next milestone

The core recording is optional after qualification. A three-to-five-minute script shows a real objective/campaign, original proposal, owner validation, accepted result/artifact, preserved history and reviewer check. Retained/static/live segments are labeled. No source token, access URL, private address, personal file or invented progress transition appears. The scientific milestone freezes task, sampling times/horizon, representation/comparator, estimand/margin, overlap rules, missing-data handling and assay replicates before new outcomes. Do not invent powered sample size without variance/margin evidence.

### Single-source generation rules

Approved prose uses claim references and controlled template slots. Numerical slots are extracted from exact JSON pointers; rounded values are display only. Generate result tables, chart coordinates, captions and sidecars from the same canonical values. Fail if an expected learner/arm is absent or if a value is silently substituted. An arbitrary numerical literal in a paragraph still needs human editorial review; a keyword linter is a guard, not a proof of truthfulness.

Escape evidence strings for Markdown/TeX before interpolation. Do not treat attachments, source files or JSON fields as commands. Rendering consumes validated values and safe authored text. External links use immutable repository URLs; package-local routes are remapped explicitly. The generation contract records every template, font, tool version, source/claim/brand digest and output digest.

## 9. Amphora visual system

Use the declared `brand_tokens.json` rather than hard-coded per-document themes. Navy is the reading ink, teal denotes execution/evidence and restrained amber denotes human/model proposal input. White backgrounds, a pale wash, thin rules, generous margins and direct labels keep the package technical and legible. Use the Amphora wordmark; no invented affiliation, endorsement or credential appears in metadata.

Letter portrait uses approximately 0.7-inch margins, 10.5-11.5-point body type and captions of at least 9 points. The executive brief uses at least 11-point body text. Prefer locally installed DejaVu Sans and a mono companion, embedded in PDFs; record the actual font files and hashes. No last-minute remote font dependency is required. Titles, draft status, date and organization remain consistent across pages.

Authored vectors explain ownership and evidence. Avoid decorative laboratory photos, AI-brain imagery, gradients, 3D charts, radar plots and giant unreadable canvas screenshots. A source table is often clearer than a new plot. If plotting scientific scores, show both learners, all six protocol-order arms, the same pp axis and point-estimate labels. A dot plot may use a disclosed focused range; a bar chart starts at zero. Paired contrast intervals must never be reused as absolute-arm error bars.

Every figure sidecar records generating command, source hashes/pointers, claim IDs, units, rounding and required caption. A successor diagram uses one actual scenario and explicitly labels unchanged scientific nodes. A supplied molecular depiction is a finite-structure/provenance example, not a drug-quality prediction. Original historical receipt bytes are never changed for branding; if a selected receipt contains a legacy name, keep it out of branded narrative and resolve raw inclusion through the disclosure gate or use a clearly new derivative summary.

## 10. Security, privacy, attribution and authority gates

These are bounded package-quality requirements, not a new compliance program. Start from an explicit allowlist, never a recursive repository zip. Exclude the raw specifications, credentials, sign-in/invitation artifacts, private Drive files, emails, full provider packets, raw measurement tables, local environments, third-party full texts and unrelated operational data. Scan the actual final tree as well as source configuration; an allowlist file alone does not establish what was shipped.

Treat all paths as relative reviewed names. Reject absolute paths, traversal, duplicate/colliding outputs, unsupported symlinks and unexpected payload members. Bounded reads and strict JSON defend the supported trusted-directory profile. Do not claim complete hostile-filesystem/TOCTOU protection without implementing and testing it. No JSON-selected executable or shell interpolation is allowed.

Preserve source/data attribution, original repository license and provenance. Bao data and derived metrics/figures retain CC BY 4.0 attribution and changes notice. Public repository visibility does not create blanket open-source rights. New review documents do not establish author rights, patentability or freedom to operate. Rights/legal review tasks identify concrete unresolved decisions instead of inventing conclusions.

Exact BP-09 historical export and investor-safe disclosure are different gates. The implemented internal capsule retains original scope and historical identifiers so the original checker can work. It is not automatically suitable for investor distribution. If redacted material is necessary, preserve original pins privately and label any public summary as a new derivative. A smaller reviewer profile must truthfully say which checks are available; it cannot claim all twelve original gates without running their unchanged assertions on their exact required bytes.

## 11. Verification plan and acceptance matrix

The default command uses only Python standard-library dependencies and starts no services, models, network requests or database work. Assertions remain enabled because the original scientific checker uses them. `--bootstrap` is opt-in and requires NumPy; the tool never installs it automatically. Exit 0 means all requested required checks completed; exit 2 means evidence rejection; exit 3 means a requested dependency/environment is absent. The source profile includes a fresh static dependency check. The capsule reports that static check as not rerun, rather than pretending to inspect omitted production source.

The source and capsule time budget target is 120 seconds, measured on the actual release workstation. A target is not a performance result. Record elapsed time and environment when exercised. Original acceptance limitations remain in the nested report and are not rewritten for promotional tone.

### Required negative categories

The qualification suite covers or explicitly assigns remaining coverage for:

1. Changed source bytes before historical reconstruction.
2. Altered transform identity or historical pin.
3. Unexpected CRLF, mixed CR and invalid UTF-8.
4. Missing or extra original gates.
5. Changed mandatory historical scope/assertion under the unchanged checker.
6. Duplicate, unknown or omitted required claims.
7. Missing learner/arm matrix cell and inconsistent formulation membership.
8. Rounded display value substituted for full precision.
9. Mutated scientific loss/contrast rejected by the existing scientific checker.
10. Qualitative source promoted to quantitative science.
11. Historical receipt marked as fresh execution.
12. Future milestone promoted to delivered evidence.
13. Missing mandatory qualifier and, in the later assembler, missing adjacent caption placement.
14. Absolute/traversing/linked paths and output collisions.
15. Duplicate JSON keys, NaN, Infinity, invalid digest and oversized input.
16. Missing requested bootstrap dependency with explicit exit 3.
17. Unexpected payload member and delivered-byte corruption.
18. Manifest self-hash cycles and duplicate file identities.
19. Two identical exports/archives with stable metadata.
20. Default read-only/no-network effects and no provider/service/training imports.
21. Checkout-free capsule and accurate static-check scope.
22. Stale claim/brand/template/source changes invalidating dependent PDFs and QA.
23. Every new PDF page, text/links/fonts and final visual appearance.
24. Clean extraction with complete notices and the exact advertised reviewer command.

The implemented functional suite addresses the core parser/pin/claim/task/capsule cases. Investor document assembly, caption-location coverage, CI, exhaustive matrix-mutation fixtures and freshness closure remain named tasks until their actual checks exist. Test count and line coverage do not establish scientific validity or prove every item above is already implemented. The module README and retained receipt enumerate the exercised cases and remaining gaps.

### Positive evidence tiers

Tier A checks exact file membership/hashes, claim-source bindings, original PLGA aggregates and original historical assertions. Tier B independently recomputes the paired bootstrap/Holm calculations. Tier C is optional full model reproduction using the existing frozen code, full Git history, public checksum-pinned data and external work directory. Tier D is a separate actual-owner/product acceptance environment. This task runs no Tier C/D workflow.

The currently available command forms are listed in the module README and [COMMANDS.md](COMMANDS.md). Commands are fixed reviewed code, not executed from registry strings. Future commands are labeled planned, and manual gates give a real reviewer criterion rather than a token shell test.

## 12. CI, clean build and freshness design

The proposed CI job runs under the existing dev owner with read-only repository permissions and no production secrets. It checks Python 3.12, strict schemas/records, focused functional/negative tests, the source dependency guard, scientific evidence and source preservation. An optional recorded arithmetic environment pins NumPy. Rendering is a separate job/toolchain so a TeX/font failure does not masquerade as an evidence failure or force reviewer dependencies.

Build twice from a clean source stage to two external output directories. Compare deterministic data, manifests, figures and archives. PDF byte determinism is claimed only after the chosen renderer/toolchain and metadata actually demonstrate it. Otherwise require content correctness, final digest and exact QA binding. Repeated builds must never rewrite the scientific originals to force equality.

Freshness is a directed dependency graph: source blobs -> extracted facts -> approved claims -> generated table/figure inputs -> rendered documents -> visual/text receipts -> manifest/archive -> detached release receipt. Brand/template/font changes invalidate all dependent outputs. Any edit after page review invalidates that PDF's review receipt. The final release gate compares input digests and command/tool versions, not filesystem modification time alone.

CI is currently a designed follow-on deliverable; this local branch does not install an active public workflow. Pin third-party Actions by reviewed immutable digest when implementing. No network egress is needed in verification jobs after dependencies/source acquisition. Keep optional human visual review as an explicit signed-off gate; automatic rendering alone does not inspect layout.

## 13. Failure and recovery behavior of the tooling

Malformed or missing evidence rejects before rendering/promotion. A failed required checker retains a failure outcome and prevents a qualified release. The tool does not change source pins, relax a tolerance, silently skip a learner/arm or relabel a recorded receipt. Independent drafting may continue while a specific gate is blocked, but the package cannot be marked verified.

All generated payloads go to a new explicitly chosen external directory. Existing outputs are not silently overwritten. Verification defaults to stdout and does not mutate authored sources. The internal capsule is safe to discard/rebuild because it contains copies; original evidence remains immutable. A future atomic-output/receipt-writer task owns stronger interruption and overwrite behavior. The current implementation does not claim transactional filesystem publication under a hostile directory race.

Bound checker runtime and retain the fixed command, interpreter and exit result. Commands from data are descriptive acceptance records, never executable input. A missing optional dependency produces a clear environment result; a timeout or failed assertion cannot become a successful partial tier. A new failure should produce the smallest focused repair and rerun, not an unnecessary full-platform test campaign.

## 14. Deliverables and completion for this request

The local review includes this comprehensive plan; the 93-task JSON ledger and generated task register; the requirement/claim-ID crosswalk; repository reconciliation; source locks and 26 candidate claim records; a twelve-entry exact byte map; brand tokens; executable offline verification/export tools; templates; focused tests/receipts; a professional review PDF; and a scoped handoff/drift record.

Source metadata describes attachments without committing their raw bytes or private Library links. Delivery is private and user-accessible. The local Git commit captures code, configuration and source documents. The PDF and any selected private review archive have their own actual hashes. No new public push occurs.

This current assignment closes when those concrete artifacts open, run and agree with their evidence. The investor release is a follow-on objective with its remaining claim, disclosure, authoring, visual and clean-export gates tracked honestly. The next scientific milestone remains a frozen genuinely new PLGA evaluation; the next product work remains the owner-ordered POP/RG/ML sequence.

## 15. Source register and interpretation

The attached specification register and crosswalk give exact source line ranges. [source_lock.json](source_lock.json) binds the selected repository files to exact Git blob bytes at the inspected revision. [claims.json](claims.json) provides their role, scope and numerical selectors. [REPOSITORY_RECONCILIATION.md](REPOSITORY_RECONCILIATION.md) distinguishes prior author assertions, inspected implementation and fresh checks. [HANDOFF.md](HANDOFF.md) gives the final branch/commit workflow, actual verification and exact remaining tasks.

The useful claim is a specific, inspectable engineering synthesis: research can be expressed as executable objects, proposals cross explicit authority boundaries, and decisions/results retain their context through bounded iteration and replacement. The workplan makes that proposition concrete without manufacturing an experiment, a deployment, a reviewer signoff or a scientific winner.
