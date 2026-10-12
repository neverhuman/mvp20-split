import type { ValidateFunction } from "ajv";
import compiled from "./generated/campaign_curation/validators.js";
import type { CurationView } from "./generated/campaign_curation/curation.js";
import type { CapabilityRequestView } from "./generated/campaign_curation/capability.js";
import type { CurationRequest } from './generated/campaign_curation/request.js';
import type { CurationReceipt } from './generated/campaign_curation/receipt.js';

export type { CurationView, CapabilityRequestView, CurationRequest, CurationReceipt };
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
export function decodeCurationRequest(value: unknown): CurationRequest {
  if (!validators.request!(value)) throw Error('invalid_curation_request');
  return value as CurationRequest;
}
export function decodeCurationReceipt(value: unknown): CurationReceipt {
  if (!validators.receipt!(value)) throw Error('invalid_curation_receipt');
  return value as CurationReceipt;
}
