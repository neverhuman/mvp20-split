# Primary Service Packages

Navigation only. Each service owns its implementation, state, dependencies, tests and source-adjacent replacement contract; this directory is not a shared backend module.

- [Campaign Runtime](campaign_runtime/README.md): durable prepared invocations, claims/fences, acceptance, delivery and inspection; general graph interpretation is a later gate.
- [Data and Artifacts](data_artifacts/README.md): immutable bytes/catalog, publication, protection and explicit maintenance.
- [Capability Registry](capability_registry/README.md): immutable releases, independent suitability policy and registry-owned registration/inventory API under BP-03.02 verification; executable hosting and installed registry recovery remain pending.

Generated package/dependency facts live in [foundation inventory](../docs/Generated/foundation-packages.json). Cross-owner access uses published contracts and configured public endpoints, never private imports or shared table access. The [Master Build Tracker](../docs/Build%20Plans/Master%20Build%20Tracker.md) selects current implementation work.
