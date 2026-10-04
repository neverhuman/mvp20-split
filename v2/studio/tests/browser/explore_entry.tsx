import { createRoot } from "react-dom/client";
import { KnowledgeClient } from "../../src/transport/scientific/knowledge.js";
import { ResearchClient } from "../../src/transport/scientific/research.js";
import { DataProvenanceClient } from "../../src/transport/provenance/data.js";
import { ExploreModel } from "../../src/page_models/explore/model.js";
import { ExploreWorkspace } from "../../src/presentation/explore/workspace.js";
import { decodeKnowledge } from "../../src/contracts/scientific/knowledge.js";
import { decodeResearch } from "../../src/contracts/scientific/research.js";
import fixture from "../fixtures/scientific/explore.json" with { type: "json" };
const graph = decodeKnowledge("search_request", { wire_version: "1", revision: fixture.revision }).revision;
const science = decodeResearch("property_request", fixture.research.property_request);
const model = new ExploreModel({ knowledge: new KnowledgeClient(), research: new ResearchClient(), data: new DataProvenanceClient() });
model.bind({ graph, experiment: science.experiment, observations: science.observations });
declare global { interface Window { exploreHarness: { model: ExploreModel } } }
window.exploreHarness = { model };
createRoot(document.getElementById("root")!).render(<ExploreWorkspace model={model} synthetic />);
window.addEventListener("pagehide", () => model.dispose());
