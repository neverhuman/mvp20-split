import type { ValidateFunction } from "ajv";
import compiled from "./generated/launch/validators.js";
import type { LaunchRequest } from "./generated/launch/request.js";
import type { LaunchReceipt } from "./generated/launch/receipt.js";
import type { LaunchProfileCatalog } from "./generated/launch/catalog.js";

export type { LaunchRequest, LaunchReceipt, LaunchProfileCatalog };
export interface LaunchWire { request: LaunchRequest; receipt: LaunchReceipt; catalog: LaunchProfileCatalog }
const validators = compiled as Record<string, ValidateFunction>;
export function decodeLaunch<K extends keyof LaunchWire>(kind: K, value: unknown): LaunchWire[K] {
  const validate = validators[kind] as ValidateFunction<LaunchWire[K]>;
  if (!validate(value)) throw new Error("invalid_launch_response");
  return value;
}
