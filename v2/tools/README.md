# Standalone Tools

- [Numeric affine](numeric_affine/README.md): bounded synthetic affine transformation.
- [Sequence statistics](sequence_statistics/README.md): explicit synthetic symbol counts.
- Source-derived solver fixtures: [seed](solver_seed/README.md), [select](solver_select/README.md), [mutate](solver_mutate/README.md), [score](solver_score/README.md) and [retain](solver_retain/README.md). Independently packaged bounded stages; graph orchestration and scientific evidence have separate gates.

Each tool owns independent source, schemas, descriptor, manifest/lock, image recipe and tests. Only the public worker SDK/contract roots are shared. These are execution fixtures, not scientific efficacy models; the frozen v1 tool implementations remain under v1.
