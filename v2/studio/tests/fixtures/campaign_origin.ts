import raw from "./campaign_origin/record.json" with { type: "json" };
import { decodeCampaignOrigin } from "../../src/contracts/campaign_origin.js";
import { decodeAuthoring } from "../../src/contracts/authoring.js";
import { decodeProvenance } from "../../src/contracts/scientific/provenance.js";

/** Python-owned synthetic compiler fixture; no actual Runtime/scientific acceptance claim. */
export function originScenario() {
  const value = structuredClone(raw);
  return { origin: decodeCampaignOrigin(value.origin), draft: decodeAuthoring("draft", value.draft),
    question: decodeProvenance("question", value.research[0]), need: decodeProvenance("need", value.research[1]) };
}
