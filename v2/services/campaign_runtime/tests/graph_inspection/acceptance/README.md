# Installed graph observation acceptance

Accepted checkpoint `2026-09-29 18:50:04`: BP-04.05 and BP-04 closed/audited. Independent DTO-only observer and Runtime replacement preserve old cursors and all graph/detail/attempt/value/event records across actual five-tool initial/successor execution;17 invocations,44 confirmed reservations. [Evidence](../../../../../docs/Audits/Evidence/BP-04-Recovery/V1.json). Earlier B1-B3/pending statements below describe historical gate positions; no gate in this child remains open.

Owner: [graph inspection](../../../src/amphora_campaign_runtime/graph_inspection/README.md). BP-04.05/V1 acceptance harness, verification pending.

`dev/verify_graphs.py --profile observations --images <accepted-solver-image-manifest>` builds the public contract/owner/tool wheels and independently installs Registry, Artifact, Runtime, SDK and all five solver tools. A separate graph-runtime-contract-only reader and fresh reader/Runtime replacements exercise the actual HTTP boundary. Run with explicit PostgreSQL fixture opt-in; never concurrently with other one-active-campaign suites.

`probe.py` reuses the accepted solver/successor scenarios, adding `reader.py` before/after execution and owner replacement. The observer validates public DTOs, follows node pages and all attempt/value pages, drains contiguous invalidations with duplicate-page checks, and resumes pre-replacement page/event cursors in a fresh independent install. Both observer installs assert absence of owner packages, SQLAlchemy and FastAPI. The controller also has no owner imports or SQL.

The five actual tools, Registry and Artifact retention remain the original installed scenario's required peers. Source orchestration, successor lineage, receipts, output bytes and protection evidence must survive unchanged. Reader replacement is acceptance isolation, not a production Studio implementation. Windows installed-process evidence remains separate from accepted Linux/amd64 tool-image evidence, scientific validity and target-host power-loss/throughput.
