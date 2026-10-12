import type { ValidateFunction } from "ajv";
import compiled from "./generated/campaign_curation/validators.js";
import type { CurationView } from "./generated/campaign_curation/curation.js";
import type { CapabilityRequestView } from "./generated/campaign_curation/capability.js";

export type { CurationView, CapabilityRequestView };
export type CurationRef = CurationView["receipt"]["reference"];
export type CapabilityRef = CapabilityRequestView["reference"];
const validators = compiled as Record<string, ValidateFunction>;
export function decodeCuration(value: unknown): CurationView {
  if (!validators.curation!(value)) throw Error("invalid_curation_response");
  return value as CurationView;
}
export function decodeCapability(value: unknown): CapabilityRequestView {
  if (!validators.capability!(value)) throw Error("invalid_capability_response");
  return value as CapabilityRequestView;
}
