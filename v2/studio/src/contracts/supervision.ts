import { Ajv2020 } from "ajv/dist/2020.js";
import type { ValidateFunction } from "ajv";
import addFormats from "ajv-formats";
import schemas from "./generated/supervision/schemas.json" with { type: "json" };
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
const ajv = new Ajv2020({ strict: true, coerceTypes: false, useDefaults: false, removeAdditional: false });
ajv.addKeyword({ keyword: "discriminator", schemaType: "object", valid: true });
addFormats.default(ajv);
const validators = new Map<string, ValidateFunction>(Object.entries(schemas).map(([key, schema]) => [key, ajv.compile(schema)]));
export function decodeSupervision<K extends keyof SupervisionWire>(kind: K, value: unknown): SupervisionWire[K] {
  const validate = validators.get(kind) as ValidateFunction<SupervisionWire[K]>;
  if (!validate(value)) throw new Error("invalid_supervision_response");
  return value;
}
