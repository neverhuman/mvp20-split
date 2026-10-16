# Amphora v2

Development procedures: [SDLC framework](docs/sdlc/README.md). Load the relevant topic rather than treating architecture as a coding checklist.

The active workspace for the graph-native research engine. Runtime owns durable
campaign execution; independently packaged tools provide scientific and search
capabilities through public contracts. Current implementation and remaining gates
are tracked in the [Master Build Tracker](docs/Build%20Plans/Master%20Build%20Tracker.md).

- [Foundation setup and verification](dev/README.md)
- [Contract packages](contracts/README.md) and [runtime foundation](services/campaign_runtime/README.md)

- [Product requirements](docs/Architecture/Requirements/Product_Requirements.md)
- [Architecture entry point](Architecture.md) and [document index](docs/Architecture/README.md)
- [Relaunch handoff](Restore.md) and [agent instructions](AGENTS.md)
- [Existing-code reuse assessment](docs/Architecture/Evolutionary_Code_Reuse_Baseline.md)
- [Presentation guide](docs/Presentations/README.md)

Develop new code here. The [v1 implementation](../v1/README.md) is read-only reference material; copy and adapt selected components with source provenance rather than modifying the baseline.

Commands in the presentation guide run from this directory. Its builders resolve outputs relative to this v2 root. Historical assessments and source artifacts inform the design but do not override the active requirements.
