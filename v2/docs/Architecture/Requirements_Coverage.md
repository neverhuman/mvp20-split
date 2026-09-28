# Requirements Ownership Coverage

- Design status: decomposition coverage, not implementation acceptance
- Last reviewed: `2026-09-23 09:51:08` (America/Chicago)
- Source: Requirements/Product_Requirements.md; all level-two through level-four headings included
- Source SHA-256: `845fd4d7cc4528deedf931a904ade1fafda8567893c50e003059e41ff3f84b69`

Each row names the primary architecture owner. Parent-level rows own integration; focused contracts own their behavior and delegate cross-domain mechanisms by name. Administrative/whole-product sections map to the master for scope, not a claim that it repeats their detailed criteria. This map is an audit surface, not a replacement for one-level-at-a-time navigation. Coverage of headings does not certify every implementation detail or scientific acceptance.

| Requirement section | Primary architecture owner |
|---|---|
| [Initial Delivery Profile](Requirements/Product_Requirements.md#initial-delivery-profile) | [System/System_Architecture.md](System/System_Architecture.md) |
| [Status](Requirements/Product_Requirements.md#status) | [../../Architecture.md](../../Architecture.md) |
| [Document Map](Requirements/Product_Requirements.md#document-map) | [../../Architecture.md](../../Architecture.md) |
| [Product Mission](Requirements/Product_Requirements.md#product-mission) | [../../Architecture.md](../../Architecture.md) |
| [Primary Users](Requirements/Product_Requirements.md#primary-users) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Core Jobs To Be Done](Requirements/Product_Requirements.md#core-jobs-to-be-done) | [Research/README.md](Research/Research_Architecture.md) |
| [Graph-Native Research Engine](Requirements/Product_Requirements.md#graph-native-research-engine) | [Campaigns/README.md](Campaigns/Campaign_Architecture.md) |
| [Authored graphs and derived lineage](Requirements/Product_Requirements.md#authored-graphs-and-derived-lineage) | [Campaigns/Definitions.md](Campaigns/Definitions.md) |
| [Executable campaign semantics](Requirements/Product_Requirements.md#executable-campaign-semantics) | [Campaigns/Definitions.md](Campaigns/Definitions.md) |
| [Neuro-symbolic domain graph requirements](Requirements/Product_Requirements.md#neuro-symbolic-domain-graph-requirements) | [Knowledge/Reasoning.md](Knowledge/Reasoning.md) |
| [Human decomposition to neuro-symbolic graph](Requirements/Product_Requirements.md#human-decomposition-to-neuro-symbolic-graph) | [Knowledge/Authoring.md](Knowledge/Authoring.md) |
| [LLM campaign design and activation](Requirements/Product_Requirements.md#llm-campaign-design-and-activation) | [Campaigns/Definitions.md](Campaigns/Definitions.md) |
| [Campaign evolution and cross-project discovery](Requirements/Product_Requirements.md#campaign-evolution-and-cross-project-discovery) | [Campaigns/Search.md](Campaigns/Search.md) |
| [Graph-engine delivery and acceptance gates](Requirements/Product_Requirements.md#graph-engine-delivery-and-acceptance-gates) | [Campaigns/README.md](Campaigns/Campaign_Architecture.md) |
| [Scientific and Product Workflows](Requirements/Product_Requirements.md#scientific-and-product-workflows) | [Research/README.md](Research/Research_Architecture.md) |
| [Envelope Intake](Requirements/Product_Requirements.md#envelope-intake) | [Research/Intent.md](Research/Intent.md) |
| [Formulation Design](Requirements/Product_Requirements.md#formulation-design) | [Research/Candidates.md](Research/Candidates.md) |
| [Incumbent Characterization and Baseline Reconstruction](Requirements/Product_Requirements.md#incumbent-characterization-and-baseline-reconstruction) | [Research/Intent.md](Research/Intent.md) |
| [Candidate Compilation](Requirements/Product_Requirements.md#candidate-compilation) | [Research/Candidates.md](Research/Candidates.md) |
| [Synthesis Feasibility and Route Planning](Requirements/Product_Requirements.md#synthesis-feasibility-and-route-planning) | [Research/Candidates.md](Research/Candidates.md) |
| [Route proposals and feasibility assessment](Requirements/Product_Requirements.md#route-proposals-and-feasibility-assessment) | [Research/Candidates.md](Research/Candidates.md) |
| [Domain-specific tools and graph integration](Requirements/Product_Requirements.md#domain-specific-tools-and-graph-integration) | [Research/Candidates.md](Research/Candidates.md) |
| [Synthesis-feasibility acceptance](Requirements/Product_Requirements.md#synthesis-feasibility-acceptance) | [Research/Candidates.md](Research/Candidates.md) |
| [Lab-In-The-Loop Optimization](Requirements/Product_Requirements.md#lab-in-the-loop-optimization) | [Research/Experiments.md](Research/Experiments.md) |
| [Experimental evidence contract](Requirements/Product_Requirements.md#experimental-evidence-contract) | [Research/Experiments.md](Research/Experiments.md) |
| [Two explicit feedback paths](Requirements/Product_Requirements.md#two-explicit-feedback-paths) | [Research/Experiments.md](Research/Experiments.md) |
| [Asynchronous operation and acceptance](Requirements/Product_Requirements.md#asynchronous-operation-and-acceptance) | [Research/Experiments.md](Research/Experiments.md) |
| [Evolutionary Candidate Campaigns](Requirements/Product_Requirements.md#evolutionary-candidate-campaigns) | [Campaigns/Search.md](Campaigns/Search.md) |
| [Intelligence, Reasoning, and Optimization](Requirements/Product_Requirements.md#intelligence-reasoning-and-optimization) | [Knowledge/README.md](Knowledge/Knowledge_Architecture.md) |
| [Biological and Cross-Domain Research](Requirements/Product_Requirements.md#biological-and-cross-domain-research) | [Research/Candidates.md](Research/Candidates.md) |
| [Representations and scientific context](Requirements/Product_Requirements.md#representations-and-scientific-context) | [Research/Candidates.md](Research/Candidates.md) |
| [Composable execution and evidence](Requirements/Product_Requirements.md#composable-execution-and-evidence) | [Research/Candidates.md](Research/Candidates.md) |
| [Biological-support acceptance](Requirements/Product_Requirements.md#biological-support-acceptance) | [Research/Candidates.md](Research/Candidates.md) |
| [LLM Prompt Integration](Requirements/Product_Requirements.md#llm-prompt-integration) | [Agents/Planning.md](Agents/Planning.md) |
| [Neuro-Symbolic Reasoning and Evolutionary Search](Requirements/Product_Requirements.md#neuro-symbolic-reasoning-and-evolutionary-search) | [Knowledge/Reasoning.md](Knowledge/Reasoning.md) |
| [Neuro-symbolic uses](Requirements/Product_Requirements.md#neuro-symbolic-uses) | [Knowledge/Reasoning.md](Knowledge/Reasoning.md) |
| [Genetic and evolutionary uses](Requirements/Product_Requirements.md#genetic-and-evolutionary-uses) | [Campaigns/Search.md](Campaigns/Search.md) |
| [Required interaction boundary](Requirements/Product_Requirements.md#required-interaction-boundary) | [Knowledge/Reasoning.md](Knowledge/Reasoning.md) |
| [Cross-project learning and reusable experience](Requirements/Product_Requirements.md#cross-project-learning-and-reusable-experience) | [Data/Learning.md](Data/Learning.md) |
| [Knowledge and Data Platform](Requirements/Product_Requirements.md#knowledge-and-data-platform) | [Data/README.md](Data/Data_Architecture.md) |
| [Data Sources and Campaign Acquisition](Requirements/Product_Requirements.md#data-sources-and-campaign-acquisition) | [Data/Acquisition.md](Data/Acquisition.md) |
| [Knowledge Refinery](Requirements/Product_Requirements.md#knowledge-refinery) | [Knowledge/Reasoning.md](Knowledge/Reasoning.md) |
| [Scientific Library](Requirements/Product_Requirements.md#scientific-library) | [Data/Acquisition.md](Data/Acquisition.md) |
| [Embedding and Representation Layer](Requirements/Product_Requirements.md#embedding-and-representation-layer) | [Data/Representations.md](Data/Representations.md) |
| [Versioned representation profiles and compatibility](Requirements/Product_Requirements.md#versioned-representation-profiles-and-compatibility) | [Data/Representations.md](Data/Representations.md) |
| [Identity, provenance and shared reuse](Requirements/Product_Requirements.md#identity-provenance-and-shared-reuse) | [Data/Representations.md](Data/Representations.md) |
| [Index lifecycle, changes and access controls](Requirements/Product_Requirements.md#index-lifecycle-changes-and-access-controls) | [Data/Representations.md](Data/Representations.md) |
| [Representation quality and acceptance](Requirements/Product_Requirements.md#representation-quality-and-acceptance) | [Data/Representations.md](Data/Representations.md) |
| [Scientific Tools in the Execution Graph](Requirements/Product_Requirements.md#scientific-tools-in-the-execution-graph) | [Capabilities/Execution.md](Capabilities/Execution.md) |
| [Tool, node, and runtime boundaries](Requirements/Product_Requirements.md#tool-node-and-runtime-boundaries) | [Capabilities/Execution.md](Capabilities/Execution.md) |
| [Domain-specific science under shared execution contracts](Requirements/Product_Requirements.md#domain-specific-science-under-shared-execution-contracts) | [Capabilities/Execution.md](Capabilities/Execution.md) |
| [Knowledge and LLM feedback](Requirements/Product_Requirements.md#knowledge-and-llm-feedback) | [Campaigns/Runtime.md](Campaigns/Runtime.md) |
| [Tool delivery and acceptance](Requirements/Product_Requirements.md#tool-delivery-and-acceptance) | [Capabilities/Execution.md](Capabilities/Execution.md) |
| [Extensible Capability-Node Platform](Requirements/Product_Requirements.md#extensible-capability-node-platform) | [Capabilities/README.md](Capabilities/Capability_Architecture.md) |
| [Node concepts](Requirements/Product_Requirements.md#node-concepts) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Node definition contract](Requirements/Product_Requirements.md#node-definition-contract) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Semantic module capability index](Requirements/Product_Requirements.md#semantic-module-capability-index) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Project-to-node matching](Requirements/Product_Requirements.md#project-to-node-matching) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Capability-gap and node-build workflow](Requirements/Product_Requirements.md#capability-gap-and-node-build-workflow) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Node developer experience](Requirements/Product_Requirements.md#node-developer-experience) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Registry, composition, and dependency resolution](Requirements/Product_Requirements.md#registry-composition-and-dependency-resolution) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Node lifecycle and authority](Requirements/Product_Requirements.md#node-lifecycle-and-authority) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Domain packs and reuse](Requirements/Product_Requirements.md#domain-packs-and-reuse) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Capability-node acceptance posture](Requirements/Product_Requirements.md#capability-node-acceptance-posture) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Enterprise Platform Requirements](Requirements/Product_Requirements.md#enterprise-platform-requirements) | [Platform/README.md](Platform/Platform_Architecture.md) |
| [Enterprise identity and access management](Requirements/Product_Requirements.md#enterprise-identity-and-access-management) | [Platform/Security.md](Platform/Security.md) |
| [API and integration platform](Requirements/Product_Requirements.md#api-and-integration-platform) | [Platform/Operations.md](Platform/Operations.md) |
| [Quantitative non-functional requirements](Requirements/Product_Requirements.md#quantitative-non-functional-requirements) | [Platform/Operations.md](Platform/Operations.md) |
| [Supported deployment models](Requirements/Product_Requirements.md#supported-deployment-models) | [Platform/Operations.md](Platform/Operations.md) |
| [Security assurance and software supply chain](Requirements/Product_Requirements.md#security-assurance-and-software-supply-chain) | [Platform/Security.md](Platform/Security.md) |
| [Business continuity and service management](Requirements/Product_Requirements.md#business-continuity-and-service-management) | [Platform/Operations.md](Platform/Operations.md) |
| [Commercial entitlements, metering, and cost governance](Requirements/Product_Requirements.md#commercial-entitlements-metering-and-cost-governance) | [Platform/Operations.md](Platform/Operations.md) |
| [Configuration, customization, and change management](Requirements/Product_Requirements.md#configuration-customization-and-change-management) | [Platform/Operations.md](Platform/Operations.md) |
| [Accessibility, localization, and adoption](Requirements/Product_Requirements.md#accessibility-localization-and-adoption) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Enterprise platform acceptance posture](Requirements/Product_Requirements.md#enterprise-platform-acceptance-posture) | [Platform/README.md](Platform/Platform_Architecture.md) |
| [User Experience and Role Workspaces](Requirements/Product_Requirements.md#user-experience-and-role-workspaces) | [Experience/README.md](Experience/Experience_Architecture.md) |
| [Human Graph Studio](Requirements/Product_Requirements.md#human-graph-studio) | [Experience/Studio.md](Experience/Studio.md) |
| [Operator and DevOps Slice](Requirements/Product_Requirements.md#operator-and-devops-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [External Customer Slice](Requirements/Product_Requirements.md#external-customer-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Internal Data Scientist Slice](Requirements/Product_Requirements.md#internal-data-scientist-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Agent Management Slice](Requirements/Product_Requirements.md#agent-management-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Customer Slice](Requirements/Product_Requirements.md#customer-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Experiment Slice](Requirements/Product_Requirements.md#experiment-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Cross-Domain UI and Functional Auditability](Requirements/Product_Requirements.md#cross-domain-ui-and-functional-auditability) | [Platform/Audit.md](Platform/Audit.md) |
| [Common audit event contract](Requirements/Product_Requirements.md#common-audit-event-contract) | [Platform/Audit.md](Platform/Audit.md) |
| [Domain-object history and state reconstruction](Requirements/Product_Requirements.md#domain-object-history-and-state-reconstruction) | [Platform/Audit.md](Platform/Audit.md) |
| [Decision and calculation auditability](Requirements/Product_Requirements.md#decision-and-calculation-auditability) | [Platform/Audit.md](Platform/Audit.md) |
| [Evidence and scientific-claim auditability](Requirements/Product_Requirements.md#evidence-and-scientific-claim-auditability) | [Platform/Audit.md](Platform/Audit.md) |
| [UI audit experience](Requirements/Product_Requirements.md#ui-audit-experience) | [Platform/Audit.md](Platform/Audit.md) |
| [Search, reporting, and audit packages](Requirements/Product_Requirements.md#search-reporting-and-audit-packages) | [Platform/Audit.md](Platform/Audit.md) |
| [Security, privacy, and tenant boundaries](Requirements/Product_Requirements.md#security-privacy-and-tenant-boundaries) | [Platform/Audit.md](Platform/Audit.md) |
| [Reliability and failure posture](Requirements/Product_Requirements.md#reliability-and-failure-posture) | [Platform/Audit.md](Platform/Audit.md) |
| [Auditability acceptance posture](Requirements/Product_Requirements.md#auditability-acceptance-posture) | [Platform/Audit.md](Platform/Audit.md) |
| [Fully Agent-Orchestrated and Supported Environment](Requirements/Product_Requirements.md#fully-agent-orchestrated-and-supported-environment) | [Agents/Work.md](Agents/Work.md) |
| [Agent roles and responsibilities](Requirements/Product_Requirements.md#agent-roles-and-responsibilities) | [Agents/Work.md](Agents/Work.md) |
| [Orchestration model](Requirements/Product_Requirements.md#orchestration-model) | [Agents/Work.md](Agents/Work.md) |
| [Human control and approval](Requirements/Product_Requirements.md#human-control-and-approval) | [Platform/Security.md](Platform/Security.md) |
| [Tools, credentials, and execution safety](Requirements/Product_Requirements.md#tools-credentials-and-execution-safety) | [Platform/Security.md](Platform/Security.md) |
| [Observability, provenance, and support](Requirements/Product_Requirements.md#observability-provenance-and-support) | [Agents/Work.md](Agents/Work.md) |
| [Agent quality and lifecycle](Requirements/Product_Requirements.md#agent-quality-and-lifecycle) | [Agents/Work.md](Agents/Work.md) |
| [Agent-orchestration acceptance posture](Requirements/Product_Requirements.md#agent-orchestration-acceptance-posture) | [Agents/Work.md](Agents/Work.md) |
| [Non-Goals](Requirements/Product_Requirements.md#non-goals) | [../../Architecture.md](../../Architecture.md) |
| [Acceptance Posture](Requirements/Product_Requirements.md#acceptance-posture) | [../../Architecture.md](../../Architecture.md) |
