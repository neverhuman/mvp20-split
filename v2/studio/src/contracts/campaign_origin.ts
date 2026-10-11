import type { ValidateFunction } from "ajv";
import compiled from "./generated/campaign_origin/validators.js";
import type { CampaignOriginV2 as CampaignOrigin } from "./generated/campaign_origin/origin.js";

export type { CampaignOrigin };
export type OriginBody = CampaignOrigin["origin"];
export type OriginDraft = OriginBody["draft"];
export type OriginResearchRecord = OriginBody["research"]["records"][number];
const validate = (compiled as Record<string, ValidateFunction>)["origin"]!;
export function decodeCampaignOrigin(value: unknown): CampaignOrigin {
  if (!validate(value)) throw Error("invalid_campaign_origin_response");
  return value as CampaignOrigin;
}
