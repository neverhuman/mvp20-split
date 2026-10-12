# Retained generation comparison

Owner: UI-01/N2.3, remaining generation group. Implementation in progress;
2026-10-11 19:38:00 America/Chicago. Prerequisites: published SearchCheckpoint,
Runtime observation reads, protected Data content reads. No new public API.

The research reviewer asks whether recorded numerical search populations changed
between two retained generations, and which objectives, unknowns and constraints
explain that change. Primary action: select two checkpoints in one campaign.
There are no mutation commands. This does not run evolution or build POP-01 waves.

Bounded delivery and gates, in order:
1. Exact published schema decoder and comparison objects with module unit tests.
2. Same-cut discovery through existing Runtime pages; cancellation and independent
   protected Data reads of at most two selected checkpoint artifacts.
3. Results presentation, desktop/narrow browser inspection, actual retained-owner
   qualification and scoped audit. Only then complete parent N2.3's second group.

Discovery scans at most100 activations and128 unique direct checkpoint outputs.
Collection outputs and unvisited nodes are explicitly incomplete. It never walks
the checkpoint predecessor chain or downloads an entire population history.
At most two256KiB JSON checkpoint artifacts are retained in the comparison model.
Exact metadata, bytes/hash, validation-schema identity, scope and referenced
candidate/objective/evaluator identities are checked. Schema validation is not
tool resume validation; the UI does not reimplement selection/ranking algorithms.

Compare only equal declared specification hashes AND equal decoded specifications;
preserve original generation IDs, stages, population/selection distinction and
synthetic/predicted/measured labels. Never turn missing outcomes into zero, use
generation number as proof of direct ancestry, collapse Pareto objectives into one
fitness, or call a numerical genotype a molecule. Per-objective extrema refer only
to evaluated feasible population members and may belong to different candidates.
Different specs/stages are separate contexts, with no improvement score. Same
generation means stage comparison, not generational progress.

Page model owns loading/empty/partial/ready/stale/denied/failed state. Cancelled or
replaced selections cannot repopulate old protected data. Discovery refresh clears
both selections; denied reads clear both records. Presentation uses shared tokens,
compact selection controls and one objective comparison table; candidate/ancestry
detail is optional. Empty scientific demo campaigns state that no search checkpoints
were found; no synthetic generations are invented for the four-tool demo.

Tests belong under tests/page_models/generation_comparison. Actual owner and browser
verification remain required; no delivery credit is claimed for this contract alone.

Checkpoint 2026-10-11 19:44:00:13 focused checks and full362 Studio checks pass.
Scripted browser B verifies exact tool bytes, two stages,1440/390, accessibility
and denied-data clearing. Header wrapping corrected after screenshot inspection.
Actual retained campaign/independent serving qualification remains the active gate.
Focused command after build: node --test dist/tests/page_models/generation_comparison/*.test.js.
