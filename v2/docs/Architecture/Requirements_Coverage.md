# Requirements Ownership Coverage

- Design status: decomposition coverage, not implementation acceptance
- Last reviewed: `2026-09-22 21:03:27` (America/Chicago)
- Source: Product_Requirements.md; all level-two through level-four headings included
- Source SHA-256: `1fb204adcb95a2105fb9b7a44df3496c0492b09c595b2ac19977a828acbe01a8`

Each row names the primary architecture owner. Parent-level rows own integration; focused contracts own their behavior and delegate cross-domain mechanisms by name. Administrative/whole-product sections map to the master for scope, not a claim that it repeats their detailed criteria. This map is an audit surface, not a replacement for one-level-at-a-time navigation. Coverage of headings does not certify every implementation detail or scientific acceptance.

| Requirement section | Primary architecture owner |
|---|---|
| [Initial Delivery Profile](Product_Requirements.md#initial-delivery-profile) | [System/System_Architecture.md](System/System_Architecture.md) |
| [Status](Product_Requirements.md#status) | [../../Architecture.md](../../Architecture.md) |
| [Document Map](Product_Requirements.md#document-map) | [../../Architecture.md](../../Architecture.md) |
| [Product Mission](Product_Requirements.md#product-mission) | [../../Architecture.md](../../Architecture.md) |
| [Primary Users](Product_Requirements.md#primary-users) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Core Jobs To Be Done](Product_Requirements.md#core-jobs-to-be-done) | [Research/README.md](Research/Research_Architecture.md) |
| [Graph-Native Research Engine](Product_Requirements.md#graph-native-research-engine) | [Campaigns/README.md](Campaigns/Campaign_Architecture.md) |
| [Authored graphs and derived lineage](Product_Requirements.md#authored-graphs-and-derived-lineage) | [Campaigns/Definitions.md](Campaigns/Definitions.md) |
| [Executable campaign semantics](Product_Requirements.md#executable-campaign-semantics) | [Campaigns/Definitions.md](Campaigns/Definitions.md) |
| [Neuro-symbolic domain graph requirements](Product_Requirements.md#neuro-symbolic-domain-graph-requirements) | [Knowledge/Reasoning.md](Knowledge/Reasoning.md) |
| [Human decomposition to neuro-symbolic graph](Product_Requirements.md#human-decomposition-to-neuro-symbolic-graph) | [Knowledge/Authoring.md](Knowledge/Authoring.md) |
| [LLM campaign design and activation](Product_Requirements.md#llm-campaign-design-and-activation) | [Campaigns/Definitions.md](Campaigns/Definitions.md) |
| [Campaign evolution and cross-project discovery](Product_Requirements.md#campaign-evolution-and-cross-project-discovery) | [Campaigns/Search.md](Campaigns/Search.md) |
| [Graph-engine delivery and acceptance gates](Product_Requirements.md#graph-engine-delivery-and-acceptance-gates) | [Campaigns/README.md](Campaigns/Campaign_Architecture.md) |
| [Scientific and Product Workflows](Product_Requirements.md#scientific-and-product-workflows) | [Research/README.md](Research/Research_Architecture.md) |
| [Envelope Intake](Product_Requirements.md#envelope-intake) | [Research/Intent.md](Research/Intent.md) |
| [Formulation Design](Product_Requirements.md#formulation-design) | [Research/Candidates.md](Research/Candidates.md) |
| [Incumbent Characterization and Baseline Reconstruction](Product_Requirements.md#incumbent-characterization-and-baseline-reconstruction) | [Research/Intent.md](Research/Intent.md) |
| [Candidate Compilation](Product_Requirements.md#candidate-compilation) | [Research/Candidates.md](Research/Candidates.md) |
| [Synthesis Feasibility and Route Planning](Product_Requirements.md#synthesis-feasibility-and-route-planning) | [Research/Candidates.md](Research/Candidates.md) |
| [Route proposals and feasibility assessment](Product_Requirements.md#route-proposals-and-feasibility-assessment) | [Research/Candidates.md](Research/Candidates.md) |
| [Domain-specific tools and graph integration](Product_Requirements.md#domain-specific-tools-and-graph-integration) | [Research/Candidates.md](Research/Candidates.md) |
| [Synthesis-feasibility acceptance](Product_Requirements.md#synthesis-feasibility-acceptance) | [Research/Candidates.md](Research/Candidates.md) |
| [Lab-In-The-Loop Optimization](Product_Requirements.md#lab-in-the-loop-optimization) | [Research/Experiments.md](Research/Experiments.md) |
| [Experimental evidence contract](Product_Requirements.md#experimental-evidence-contract) | [Research/Experiments.md](Research/Experiments.md) |
| [Two explicit feedback paths](Product_Requirements.md#two-explicit-feedback-paths) | [Research/Experiments.md](Research/Experiments.md) |
| [Asynchronous operation and acceptance](Product_Requirements.md#asynchronous-operation-and-acceptance) | [Research/Experiments.md](Research/Experiments.md) |
| [Evolutionary Candidate Campaigns](Product_Requirements.md#evolutionary-candidate-campaigns) | [Campaigns/Search.md](Campaigns/Search.md) |
| [Intelligence, Reasoning, and Optimization](Product_Requirements.md#intelligence-reasoning-and-optimization) | [Knowledge/README.md](Knowledge/Knowledge_Architecture.md) |
| [Biological and Cross-Domain Research](Product_Requirements.md#biological-and-cross-domain-research) | [Research/Candidates.md](Research/Candidates.md) |
| [Representations and scientific context](Product_Requirements.md#representations-and-scientific-context) | [Research/Candidates.md](Research/Candidates.md) |
| [Composable execution and evidence](Product_Requirements.md#composable-execution-and-evidence) | [Research/Candidates.md](Research/Candidates.md) |
| [Biological-support acceptance](Product_Requirements.md#biological-support-acceptance) | [Research/Candidates.md](Research/Candidates.md) |
| [LLM Prompt Integration](Product_Requirements.md#llm-prompt-integration) | [Agents/Planning.md](Agents/Planning.md) |
| [Neuro-Symbolic Reasoning and Evolutionary Search](Product_Requirements.md#neuro-symbolic-reasoning-and-evolutionary-search) | [Knowledge/Reasoning.md](Knowledge/Reasoning.md) |
| [Neuro-symbolic uses](Product_Requirements.md#neuro-symbolic-uses) | [Knowledge/Reasoning.md](Knowledge/Reasoning.md) |
| [Genetic and evolutionary uses](Product_Requirements.md#genetic-and-evolutionary-uses) | [Campaigns/Search.md](Campaigns/Search.md) |
| [Required interaction boundary](Product_Requirements.md#required-interaction-boundary) | [Knowledge/Reasoning.md](Knowledge/Reasoning.md) |
| [Cross-project learning and reusable experience](Product_Requirements.md#cross-project-learning-and-reusable-experience) | [Data/Learning.md](Data/Learning.md) |
| [Knowledge and Data Platform](Product_Requirements.md#knowledge-and-data-platform) | [Data/README.md](Data/Data_Architecture.md) |
| [Data Sources and Campaign Acquisition](Product_Requirements.md#data-sources-and-campaign-acquisition) | [Data/Acquisition.md](Data/Acquisition.md) |
| [Knowledge Refinery](Product_Requirements.md#knowledge-refinery) | [Knowledge/Reasoning.md](Knowledge/Reasoning.md) |
| [Scientific Library](Product_Requirements.md#scientific-library) | [Data/Acquisition.md](Data/Acquisition.md) |
| [Embedding and Representation Layer](Product_Requirements.md#embedding-and-representation-layer) | [Data/Representations.md](Data/Representations.md) |
| [Versioned representation profiles and compatibility](Product_Requirements.md#versioned-representation-profiles-and-compatibility) | [Data/Representations.md](Data/Representations.md) |
| [Identity, provenance and shared reuse](Product_Requirements.md#identity-provenance-and-shared-reuse) | [Data/Representations.md](Data/Representations.md) |
| [Index lifecycle, changes and access controls](Product_Requirements.md#index-lifecycle-changes-and-access-controls) | [Data/Representations.md](Data/Representations.md) |
| [Representation quality and acceptance](Product_Requirements.md#representation-quality-and-acceptance) | [Data/Representations.md](Data/Representations.md) |
| [Scientific Tools in the Execution Graph](Product_Requirements.md#scientific-tools-in-the-execution-graph) | [Capabilities/Execution.md](Capabilities/Execution.md) |
| [Tool, node, and runtime boundaries](Product_Requirements.md#tool-node-and-runtime-boundaries) | [Capabilities/Execution.md](Capabilities/Execution.md) |
| [Domain-specific science under shared execution contracts](Product_Requirements.md#domain-specific-science-under-shared-execution-contracts) | [Capabilities/Execution.md](Capabilities/Execution.md) |
| [Knowledge and LLM feedback](Product_Requirements.md#knowledge-and-llm-feedback) | [Campaigns/Runtime.md](Campaigns/Runtime.md) |
| [Tool delivery and acceptance](Product_Requirements.md#tool-delivery-and-acceptance) | [Capabilities/Execution.md](Capabilities/Execution.md) |
| [Extensible Capability-Node Platform](Product_Requirements.md#extensible-capability-node-platform) | [Capabilities/README.md](Capabilities/Capability_Architecture.md) |
| [Node concepts](Product_Requirements.md#node-concepts) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Node definition contract](Product_Requirements.md#node-definition-contract) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Semantic module capability index](Product_Requirements.md#semantic-module-capability-index) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Project-to-node matching](Product_Requirements.md#project-to-node-matching) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Capability-gap and node-build workflow](Product_Requirements.md#capability-gap-and-node-build-workflow) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Node developer experience](Product_Requirements.md#node-developer-experience) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Registry, composition, and dependency resolution](Product_Requirements.md#registry-composition-and-dependency-resolution) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Node lifecycle and authority](Product_Requirements.md#node-lifecycle-and-authority) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Domain packs and reuse](Product_Requirements.md#domain-packs-and-reuse) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Capability-node acceptance posture](Product_Requirements.md#capability-node-acceptance-posture) | [Capabilities/Catalog.md](Capabilities/Catalog.md) |
| [Enterprise Platform Requirements](Product_Requirements.md#enterprise-platform-requirements) | [Platform/README.md](Platform/Platform_Architecture.md) |
| [Enterprise identity and access management](Product_Requirements.md#enterprise-identity-and-access-management) | [Platform/Security.md](Platform/Security.md) |
| [API and integration platform](Product_Requirements.md#api-and-integration-platform) | [Platform/Operations.md](Platform/Operations.md) |
| [Quantitative non-functional requirements](Product_Requirements.md#quantitative-non-functional-requirements) | [Platform/Operations.md](Platform/Operations.md) |
| [Supported deployment models](Product_Requirements.md#supported-deployment-models) | [Platform/Operations.md](Platform/Operations.md) |
| [Security assurance and software supply chain](Product_Requirements.md#security-assurance-and-software-supply-chain) | [Platform/Security.md](Platform/Security.md) |
| [Business continuity and service management](Product_Requirements.md#business-continuity-and-service-management) | [Platform/Operations.md](Platform/Operations.md) |
| [Commercial entitlements, metering, and cost governance](Product_Requirements.md#commercial-entitlements-metering-and-cost-governance) | [Platform/Operations.md](Platform/Operations.md) |
| [Configuration, customization, and change management](Product_Requirements.md#configuration-customization-and-change-management) | [Platform/Operations.md](Platform/Operations.md) |
| [Accessibility, localization, and adoption](Product_Requirements.md#accessibility-localization-and-adoption) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Enterprise platform acceptance posture](Product_Requirements.md#enterprise-platform-acceptance-posture) | [Platform/README.md](Platform/Platform_Architecture.md) |
| [User Experience and Role Workspaces](Product_Requirements.md#user-experience-and-role-workspaces) | [Experience/README.md](Experience/Experience_Architecture.md) |
| [Human Graph Studio](Product_Requirements.md#human-graph-studio) | [Experience/Studio.md](Experience/Studio.md) |
| [Operator and DevOps Slice](Product_Requirements.md#operator-and-devops-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [External Customer Slice](Product_Requirements.md#external-customer-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Internal Data Scientist Slice](Product_Requirements.md#internal-data-scientist-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Agent Management Slice](Product_Requirements.md#agent-management-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Customer Slice](Product_Requirements.md#customer-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Experiment Slice](Product_Requirements.md#experiment-slice) | [Experience/Workspaces.md](Experience/Workspaces.md) |
| [Cross-Domain UI and Functional Auditability](Product_Requirements.md#cross-domain-ui-and-functional-auditability) | [Platform/Audit.md](Platform/Audit.md) |
| [Common audit event contract](Product_Requirements.md#common-audit-event-contract) | [Platform/Audit.md](Platform/Audit.md) |
| [Domain-object history and state reconstruction](Product_Requirements.md#domain-object-history-and-state-reconstruction) | [Platform/Audit.md](Platform/Audit.md) |
| [Decision and calculation auditability](Product_Requirements.md#decision-and-calculation-auditability) | [Platform/Audit.md](Platform/Audit.md) |
| [Evidence and scientific-claim auditability](Product_Requirements.md#evidence-and-scientific-claim-auditability) | [Platform/Audit.md](Platform/Audit.md) |
| [UI audit experience](Product_Requirements.md#ui-audit-experience) | [Platform/Audit.md](Platform/Audit.md) |
| [Search, reporting, and audit packages](Product_Requirements.md#search-reporting-and-audit-packages) | [Platform/Audit.md](Platform/Audit.md) |
| [Security, privacy, and tenant boundaries](Product_Requirements.md#security-privacy-and-tenant-boundaries) | [Platform/Audit.md](Platform/Audit.md) |
| [Reliability and failure posture](Product_Requirements.md#reliability-and-failure-posture) | [Platform/Audit.md](Platform/Audit.md) |
| [Auditability acceptance posture](Product_Requirements.md#auditability-acceptance-posture) | [Platform/Audit.md](Platform/Audit.md) |
| [Fully Agent-Orchestrated and Supported Environment](Product_Requirements.md#fully-agent-orchestrated-and-supported-environment) | [Agents/Work.md](Agents/Work.md) |
| [Agent roles and responsibilities](Product_Requirements.md#agent-roles-and-responsibilities) | [Agents/Work.md](Agents/Work.md) |
| [Orchestration model](Product_Requirements.md#orchestration-model) | [Agents/Work.md](Agents/Work.md) |
| [Human control and approval](Product_Requirements.md#human-control-and-approval) | [Platform/Security.md](Platform/Security.md) |
| [Tools, credentials, and execution safety](Product_Requirements.md#tools-credentials-and-execution-safety) | [Platform/Security.md](Platform/Security.md) |
| [Observability, provenance, and support](Product_Requirements.md#observability-provenance-and-support) | [Agents/Work.md](Agents/Work.md) |
| [Agent quality and lifecycle](Product_Requirements.md#agent-quality-and-lifecycle) | [Agents/Work.md](Agents/Work.md) |
| [Agent-orchestration acceptance posture](Product_Requirements.md#agent-orchestration-acceptance-posture) | [Agents/Work.md](Agents/Work.md) |
| [Non-Goals](Product_Requirements.md#non-goals) | [../../Architecture.md](../../Architecture.md) |
| [Acceptance Posture](Product_Requirements.md#acceptance-posture) | [../../Architecture.md](../../Architecture.md) |
