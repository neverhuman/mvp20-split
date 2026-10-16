# Research Studio Interaction References

- Design status: reference patterns for prototype evaluation; no frontend/framework/product dependency selected.
- Reviewed: `2026-09-24 12:10:07` (America/Chicago).
- Parent: [Graph Studio](../../Architecture/Experience/Studio.md).
- Provenance: user-supplied Claude reference list, checked against primary documentation. Adaptations below are Amphora design recommendations, not claims that these products implement Amphora semantics.

## Reference Map

| Need | Reference and documented pattern | Amphora adaptation / boundary | Delivery owner |
|---|---|---|---|
| Compose and inspect execution graphs | [ComfyUI interface](https://docs.comfy.org/interface/overview): node workspace, node library and queue/history; [LangSmith Studio](https://docs.langchain.com/langsmith/studio), the reference formerly called LangGraph Studio: graph execution inspection | Search registered tools, connect typed ports and inspect actual node inputs/results. Separate draft composition from the pinned live run; do not import debugger-style live state editing into autonomous campaigns. | BP-05 P1-P3; engagement detail BP-07 |
| Non-technical pipeline editing | [Node-RED editor](https://nodered.org/docs/user-guide/editor/) and [first flow](https://nodered.org/docs/tutorials/first-flow): palette/workspace and explicit deploy step | Human-readable capability names, forms, examples and validation. Separate Design and Monitor modes is our adaptation; the cited docs establish editor/deploy distinction, not a claim of a separate monitoring product surface. | BP-05 P1/P3 |
| Staged execution with status | [Dagster asset catalog](https://docs.dagster.io/guides/observe/asset-catalog): asset-oriented observation/navigation | Stage/iteration summaries with drill-down to activations, attempts and accepted artifacts. A Dagster asset/materialization is not automatically equivalent to an Amphora candidate/generation or scientific acceptance. | BP-05 P2; generation detail BP-08 |
| Explore domain knowledge | [Neo4j Bloom overview](https://neo4j.com/docs/bloom-user-guide/current/bloom-visual-tour/bloom-overview/) and [search](https://neo4j.com/docs/bloom-user-guide/current/bloom-visual-tour/search-bar/): search-first scenes, contextual perspectives and expansion | Search a scientific question/entity, expand a bounded neighborhood and inspect sources, applicability and contradictions. Human authoring remains source text plus reviewed changes; users need not maintain predicates manually. Reference does not select Neo4j as our database. | BP-06; extraction BP-07 |
| Compare candidates and generations | [W&B parallel coordinates](https://docs.wandb.ai/models/app/features/panels/parallel-coordinates): multiple parameter/metric axes and filtered run lines; [MLflow tracking](https://mlflow.org/docs/latest/ml/tracking): run comparisons, metrics and artifacts | Start with a sortable candidate table and linked selections; offer parallel coordinates/Pareto views for multi-objective comparison. Pin generation, evaluator and evidence context. Show unknown/ineligible separately, never as zero fitness. | BP-05 comparison shell; evidence BP-06; fitness/generations BP-08 |

## Proposed Connected Modes

**Design:** objective/context and tool palette, draft graph, selection inspector and validation/diff. The LLM can propose composition; humans can inspect and customize a next-campaign draft. Preserve the active campaign's immutable revision.

**Monitor:** active or historical graph with stage/iteration navigation, frontier, attempts and accepted outputs. Clearly distinguish running, failed, abstained, skipped, pending scientific acceptance and accepted. Emergency termination is an explicit operational command. Selecting an older generation must not silently switch its evidence to live data.

**Explore:** search-first domain graph with bounded expansion, evidence/source details and the ability to traverse from a result or decision into its supporting knowledge. Layout changes are view preferences, not edits to scientific meaning.

**Compare:** selected candidates/generations as a table plus optional linked plots. Expose objective units/direction, constraints, uncertainty and evaluation versions; do not imply differently measured populations are comparable. Choose a candidate to open its lineage, execution node and evidence in the other modes.

These modes share project/campaign/revision/selection context, with explicit historical pins and preserved navigation. They are focused views of connected objects, not four unrelated applications or four always-visible panels. Progressive loading and keyboard-accessible lists/details remain required.

## Prototype Review Tasks

1. A non-programmer finds a capability, changes a permitted parameter in a draft and explains why the active run has not changed.
2. A user finds the failed attempt inside an iteration, distinguishes it from scientific abstention and opens the accepted or missing artifact.
3. A researcher searches a domain entity, expands a bounded neighborhood and traces a claim to its source without entering relationship syntax.
4. A researcher compares candidates, identifies missing/ineligible fitness and traces a selected result to its generation and evaluator revision.
5. A user moves among these views without losing selection or confusing draft/live/historical context; keyboard and narrow-screen paths remain usable.

BP-05 prototypes the first two tasks and connected navigation using real available runtime data. BP-06 and BP-08 supply the later evidence and fitness tasks; sketches or synthetic data must be labeled accordingly. These references refine existing tasks and do not add implementation credit or activate later plans. Prefer interaction lessons over cloning visual chrome; confirm layouts with actual browser/usability evidence before selecting a canvas library.
