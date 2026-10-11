import { createRoot } from "react-dom/client";
import { CampaignOriginClient } from "../../src/transport/campaign_origin/client.js";
import { AuthoringClient } from "../../src/transport/authoring.js";
import { ResearchRecordClient } from "../../src/transport/provenance/research.js";
import { OriginReader } from "../../src/page_models/campaign_origin/reader.js";
import { OriginResearchReader } from "../../src/page_models/campaign_origin/research.js";
import { CampaignOriginModel } from "../../src/page_models/campaign_origin/model.js";
import { CampaignOriginPanel } from "../../src/presentation/campaign_origin/panel.js";
import "../../src/presentation/style.css";

const binding = await fetch("/binding").then(response => response.json());
const model = new CampaignOriginModel(new OriginReader(new CampaignOriginClient(), new AuthoringClient()),
  new OriginResearchReader(new ResearchRecordClient()));
createRoot(document.getElementById("root")!).render(<main style={{ maxWidth: "1100px", padding: "24px", margin: "auto" }}>
  <h1>Inspect a campaign's origin</h1><p>Synthetic public-contract browser fixture; actual-owner qualification is separate.</p>
  <CampaignOriginPanel model={model} selection={binding} openKnowledge={() => { throw Error("No graph selected in this fixture"); }} />
</main>);
window.addEventListener("pagehide", () => model.dispose());
