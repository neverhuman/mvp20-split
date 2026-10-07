import type { ValidateFunction } from "ajv";
import compiled from "./generated/supervision/validators.js";
import type { CheckpointInspectionPage } from "./generated/supervision/checkpoints.js";
import type { CheckpointRequestPage } from "./generated/supervision/requests.js";
import type { CheckpointContextPage } from "./generated/supervision/context.js";
import type { CheckpointResponsePage } from "./generated/supervision/responses.js";
import type { CheckpointDecision } from "./generated/supervision/decision.js";
export interface SupervisionWire {
  checkpoints: CheckpointInspectionPage; requests: CheckpointRequestPage;
  context: CheckpointContextPage; responses: CheckpointResponsePage; decision: CheckpointDecision;
}
export type Checkpoint = CheckpointInspectionPage["items"][number];
export type CheckpointRequest = CheckpointRequestPage["items"][number];
export type InspectionSnapshot = CheckpointInspectionPage["snapshot"];
const validators = compiled as Record<string, ValidateFunction>;

export function decodeSupervision<K extends keyof SupervisionWire>(kind: K, value: unknown): SupervisionWire[K] {
  const validate = validators[kind] as ValidateFunction<SupervisionWire[K]>;
  if (!validate(value)) throw new Error("invalid_supervision_response");
  return value;
}
