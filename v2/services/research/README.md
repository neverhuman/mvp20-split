# Research Service

- Status: BP-06.01 closed; BP-06.03 assessment/publication/correction boundaries implemented. Actual Runtime receipt acceptance and partial exploratory output verified; BP-06.03 recovery/closeout accepted; BP-06.04 has pure scientific domain objects, synthetic synthesis/eligibility policies and explicit public mappings; separate scientific revision storage is implemented; authenticated synthetic report resolution is implemented; atomic intake and immutable eligibility/synthesis decision/dependency storage are implemented; scientific Artifact publication is implemented; new authenticated scientific APIs remain pending.
- Package: `amphora-research` 0.22.0; exact dependencies belong to pyproject.toml, uv.lock and the generated package inventory.
- Design: [Research architecture](../../docs/Architecture/Research/Research_Architecture.md).

Research owns candidate/sample/question/evidence-need identities and purpose-bound evidence sufficiency. It does not own Artifact bytes, Knowledge assertions, model execution or campaign acceptance. Dependencies are public contracts and the tool-protocol SDK plus Pydantic/FastAPI/Uvicorn and SQLAlchemy/psycopg/Alembic. No peer implementation imports, peer SQL or shared ORM.

| Module | Replacement boundary |
|---|---|
| [Identity](src/amphora_research/identity/README.md) | Scoped candidate/sample/question/need invariants and corrections |
| [Persistence](src/amphora_research/persistence/README.md) | Immutable identity revisions, local links, exact replay and declaration reads |
| [Synthesis](src/amphora_research/synthesis/README.md) | Route/step evidence and independent project-execution gates; synthetic authority |
| [Eligibility](src/amphora_research/eligibility/README.md) | Exact purpose/context, explicit action prerequisites and retained iteration focus |
| [Material state](src/amphora_research/material_state/README.md) | Distinct preparation/feature evidence and exact candidate/state revisions |
| [Experiments](src/amphora_research/experiments/README.md) | Exact specimen, method/context and replicate/control expectations |
| [Observations](src/amphora_research/observations/README.md) | Exact measurement values, immutable reported results and exact experiment matching; authenticated synthetic report resolution; atomic durable intake; hosted intake APIs remain later milestones |
| [Assessment](src/amphora_research/assessment/README.md) | Reviewed profiles, authenticated public-peer resolution, exact applicability, explicit gaps/conflicts and immutable decisions |
| [Publication](src/amphora_research/publication/README.md) | Reviewed payload/lineage, fenced durable recovery, actual Data publication and atomic synthetic receipt |
| [Scientific API](src/amphora_research/scientific_api/README.md) | Reviewed input contracts and full-profile binding; input orchestration and hosted routes pending |
| [Scientific publication](src/amphora_research/scientific_publication/README.md) | Immutable lab/eligibility/synthesis Artifact output and fenced recovery; no DomainReceipt authority |
| [Corrections](src/amphora_research/corrections/README.md) | Append-only owner correction chains, exact/head selection and future-campaign-only effects |
| [Transport](src/amphora_research/transport/README.md) | Separately granted authenticated APIs and explicit optional assessment hosting |

Default hosting exposes identity/declaration reads. The optional reviewed assessment profile enables reference-only submit/read, publication and correction APIs. Requests cannot supply trusted observations or scientific verdicts. Source bytes and producer derivations are resolved through authenticated Data/Knowledge public contracts; source rights are checked for new consumption. Terminal history replays exact committed records without reevaluating evidence or granting fresh source access. Correction writes load this owner's published source; correction reads never repin an active campaign.

Research migrations0001 through0009 apply forward only, under the owner migrator. Runtime serving checks tables and never migrates. Service credentials have narrowly scoped grants; immutable assessment/correction histories have SELECT/INSERT only. Use config.example.json for identity hosting and config.assessment.example.json for optional synthetic assessment hosting, with real environment credentials and pre-established exact artifact/schema references. No default credential or external binding is supplied.

An assessment distinguishes answered, sufficient for a declared synthetic decision, and scientifically established; the last is always false in this profile. Unknown, contradictory, opinion-only and wrong-context evidence remain explicit. Campaign execution may retain useful context and use declared partial paths without turning an abstention into accepted evidence. Rich quality visualization and next-campaign proposals remain SQ-01/BP-07.03. Laboratory/material-state/route-specific eligibility remains BP-06.04.

Module-owned tests live under tests/identity, persistence, assessment, publication, corrections, observations, material_state, experiments, synthesis, eligibility and api. Select with dev/run_tests.py --module research --area <area>; PostgreSQL requires AMPHORA_TEST_POSTGRES=1 and serial execution. Scripted peers prove client behavior only. test_actual_resolution.py uses separately hosted Data/Knowledge/Research and optional Runtime; private migrations/seeding stay inside their owner's process. dev/verify_research_assessment.py independently installs Research and rejects peer implementation imports. Runtime/partial/fault helpers live under Runtime's owned acceptance folder.

[Assessment API evidence](../../docs/Audits/Evidence/BP-06-Research/Assessment_API.json), [correction transitions](../../docs/Audits/Evidence/BP-06-Research/Receipt_Correction_Transitions.json), [live Runtime receipts](../../docs/Audits/Evidence/BP-06-Research/Runtime_Domain_Receipts.json) and [partial progress](../../docs/Audits/Evidence/BP-06-Research/Partial_Campaign_Progress.json) retain exact versions, cases and limitations. Earlier coverage is module-scoped and excludes child processes; no aggregate end-to-end percentage or scientific/target-host durability claim is inferred. A replacement must preserve schemas, fingerprints, actor/scope authority, migrations, immutable histories and failure semantics or explicitly version the boundary.
