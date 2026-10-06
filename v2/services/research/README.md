# Research Service

- Status: BP-06.01/.03 are closed. BP-06.04 scientific storage, authenticated intake, exact normalization, per-action interpretation, immutable corrections/impacts and Artifact publication are implemented and verified. Independent rebuild/replacement and process recovery pass; scoped closeout is recorded in the BP-06.04 audit.
- Package: `amphora-research` 0.36.0; Research contracts0.14.0 and migration research_0014. Exact dependencies belong to pyproject.toml, uv.lock and the generated package inventory.
- Design: [Research architecture](../../docs/Architecture/Research/Research_Architecture.md).

Research owns candidate/sample/question/evidence-need identities and purpose-bound evidence sufficiency. It does not own Artifact bytes, Knowledge assertions, model execution or campaign acceptance. Dependencies are public contracts and the tool-protocol SDK plus Pydantic/FastAPI/Uvicorn and SQLAlchemy/psycopg/Alembic. No peer implementation imports, peer SQL or shared ORM.

| Module | Replacement boundary |
|---|---|
| [Fitness identity](src/amphora_research/fitness/README.md) | Context-complete declared evaluation identity; no reuse authorization |
| [Candidate registration](src/amphora_research/candidate_registration/README.md) | Explicit synthetic candidate declaration, current Artifact access and atomic first-public-origin history; actual worker/Data/Research handoff verified |
| [Identity](src/amphora_research/identity/README.md) | Scoped candidate/sample/question/need invariants and corrections |
| [Persistence](src/amphora_research/persistence/README.md) | Immutable identity revisions, local links, exact replay and declaration reads |
| [Synthesis](src/amphora_research/synthesis/README.md) | Route/step evidence and independent project-execution gates; synthetic authority |
| [Eligibility](src/amphora_research/eligibility/README.md) | Exact purpose/context, explicit action prerequisites and retained iteration focus |
| [Material state](src/amphora_research/material_state/README.md) | Distinct preparation/feature evidence and exact candidate/state revisions |
| [Experiments](src/amphora_research/experiments/README.md) | Exact specimen, method/context and replicate/control expectations |
| [Observations](src/amphora_research/observations/README.md) | Exact measurement values, immutable reported results and exact experiment matching; authenticated synthetic report resolution; atomic durable intake; optional intake APIs in scientific_api |
| [Assessment](src/amphora_research/assessment/README.md) | Reviewed profiles, authenticated public-peer resolution, exact applicability, explicit gaps/conflicts and immutable decisions |
| [Publication](src/amphora_research/publication/README.md) | Reviewed payload/lineage, fenced durable recovery, actual Data publication and atomic synthetic receipt |
| [Scientific API](src/amphora_research/scientific_api/README.md) | Reviewed input contracts and full-profile binding; authenticated input intents and separately granted optional scientific routes |
| [Normalization](src/amphora_research/observations/normalization/README.md) | Exact directed conversions with preserved originals; no inferred unit ontology |
| [Observation quality](src/amphora_research/observations/quality/README.md) | Per-action requirements, independent focus and explicit return coverage |
| [Interpretation](src/amphora_research/observations/interpretation/README.md) | Complete policy/input pins, immutable derived projections and dependency indexes |
| [Interpretation API](src/amphora_research/interpretation_api/README.md) | Fresh authenticated dependency reads, separate grants and offline history |
| [Scientific publication](src/amphora_research/scientific_publication/README.md) | Immutable lab/eligibility/synthesis Artifact output and fenced recovery; no DomainReceipt authority |
| [Corrections](src/amphora_research/corrections/README.md) | Append-only owner correction chains, exact/head selection and future-campaign-only effects |
| [Declarations](src/amphora_research/declarations/README.md) | Explicit authenticated question/need registration, immutable provenance and exact retry identity |
| [Transport](src/amphora_research/transport/README.md) | Separately granted authenticated APIs and explicit optional assessment hosting |

Default hosting exposes identity/declaration reads. Explicit declarations=true enables separately granted question/need writes with atomic first-public-registration provenance; this does not assess answers or authorize Artifact processing. Research0.34+ migrators are required after0013. The optional reviewed assessment profile enables reference-only submit/read, publication and correction APIs. Requests cannot supply trusted observations or scientific verdicts. Source bytes and producer derivations are resolved through authenticated Data/Knowledge public contracts; source rights are checked for new consumption. Terminal history replays exact committed records without reevaluating evidence or granting fresh source access. Correction writes load this owner's published source; correction reads never repin an active campaign.

Research migrations0001 through0013 apply forward only, under the owner migrator. Runtime serving checks tables and never migrates. Service credentials have narrowly scoped grants; immutable assessment/correction histories have SELECT/INSERT only. Use config.example.json for identity hosting and config.assessment.example.json for optional synthetic assessment hosting, with real environment credentials and pre-established exact artifact/schema references. No default credential or external binding is supplied.

An assessment distinguishes answered, sufficient for a declared synthetic decision, and scientifically established; the last is always false in this profile. Unknown, contradictory, opinion-only and wrong-context evidence remain explicit. Campaign execution may retain useful context and use declared partial paths without turning an abstention into accepted evidence. Rich quality visualization and next-campaign proposals remain SQ-01/BP-07.03. Synthetic laboratory/material-state/route-specific eligibility is implemented; real scientific evaluators and physical laboratory adapters remain later capabilities.

Module-owned tests live under tests/identity, declarations, persistence, assessment, publication, corrections, observations, material_state, experiments, synthesis, eligibility and api. Select with dev/run_tests.py --module research --area <area>; PostgreSQL requires AMPHORA_TEST_POSTGRES=1 and serial execution. Scripted peers prove client behavior only. test_actual_resolution.py uses separately hosted Data/Knowledge/Research and optional Runtime; private migrations/seeding stay inside their owner's process. dev/verify_research_assessment.py independently installs Research and rejects peer implementation imports. Runtime/partial/fault helpers live under Runtime's owned acceptance folder.

[Assessment API evidence](../../docs/Audits/Evidence/BP-06-Research/Assessment_API.json), [correction transitions](../../docs/Audits/Evidence/BP-06-Research/Receipt_Correction_Transitions.json), [live Runtime receipts](../../docs/Audits/Evidence/BP-06-Research/Runtime_Domain_Receipts.json) and [partial progress](../../docs/Audits/Evidence/BP-06-Research/Partial_Campaign_Progress.json) retain exact versions, cases and limitations. Earlier coverage is module-scoped and excludes child processes; no aggregate end-to-end percentage or scientific/target-host durability claim is inferred. A replacement must preserve schemas, fingerprints, actor/scope authority, migrations, immutable histories and failure semantics or explicitly version the boundary.

Optional science hosting is documented in the scientific API module. config.science.example.json demonstrates read-only history configuration with no active profiles. New routes have separate grants and Artifact-only publication; actual independently installed HTTP/replacement is verified under BP-06.04/B1.08d.

Explicit directed conversion catalogs preserve original decimal values, units, censoring, uncertainty and series order. Unknown conversions remain unresolved. Durable interpretation pins the entire reviewed profile, actor and exact input revisions before fresh Data access; completed results replay offline.

Weak and contradictory evidence remains visible for exploratory use and next-campaign focus. Only explicit prerequisites block a named action. Correction views and known dependent indexes preserve original pending pins and committed history; no global consumer discovery or scientific truth is inferred. The separately granted interpretation API exposes normalization, observation-use and impact/correction reads.

BP-06.06/B1.02 compatibility0.31.1 changes only the exact public Knowledge contract dependency to0.8.0. No Research behavior, schema or migration change.

BP-06.06 Research0.32 adds pure bounded [exploration](src/amphora_research/exploration/README.md) through public research-views0.1. Existing scientific contracts and behavior remain unchanged; owner/API projection integration follows in Research0.33.

Research0.33 exposes authenticated research-explore catalog/specimens/properties/observation-series routes through optional scientific hosting. No schema/migration/new-grant change; complete selected-set existence is checked before bounded record loads. See exploration module for read and replacement contracts.
