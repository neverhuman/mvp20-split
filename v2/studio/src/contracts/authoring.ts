import { Ajv2020 } from "ajv/dist/2020.js";
import type { ValidateFunction } from "ajv";
import addFormats from "ajv-formats";
import schemas from "./generated/authoring/schemas.json" with { type: "json" };
import type { SaveDraft } from "./generated/authoring/save.js";
import type { ValidateDraft } from "./generated/authoring/validate.js";
import type { DraftRevision } from "./generated/authoring/draft.js";
import type { DraftPage } from "./generated/authoring/page.js";
import type { DraftValidation } from "./generated/authoring/validation.js";
import type { DraftCommandReceipt } from "./generated/authoring/receipt.js";
import type { AdmitDraft } from "./generated/authoring/admit.js";
import type { DefinitionUniverse } from "./generated/authoring/universe.js";
import type { DefinitionSchema } from "./generated/authoring/schema.js";
import type { ReleasePage } from "./generated/authoring/releases.js";
import type { ReleaseSnapshot } from "./generated/authoring/release.js";
import type { CancelRun } from "./generated/authoring/cancel.js";
import type { CommandReceipt } from "./generated/authoring/execution_receipt.js";
import type { CommandIdentity } from "./generated/authoring/identity.js";

export type { SaveDraft, ValidateDraft, DraftRevision, DraftPage, DraftValidation, DraftCommandReceipt, AdmitDraft, DefinitionUniverse, DefinitionSchema, ReleasePage, ReleaseSnapshot, CancelRun, CommandReceipt, CommandIdentity };
export interface AuthoringWire {
  save: SaveDraft;
  validate: ValidateDraft;
  draft: DraftRevision;
  page: DraftPage;
  validation: DraftValidation;
  receipt: DraftCommandReceipt;
  admit: AdmitDraft;
  universe: DefinitionUniverse;
  schema: DefinitionSchema;
  releases: ReleasePage;
  release: ReleaseSnapshot;
  cancel: CancelRun;
  execution_receipt: CommandReceipt;
  identity: CommandIdentity;
}

const ajv = new Ajv2020({ strict: true, allErrors: false, coerceTypes: false, useDefaults: false, removeAdditional: false });
ajv.addKeyword({ keyword: "discriminator", schemaType: "object", valid: true });
addFormats.default(ajv);
const validators = {
  save: ajv.compile<SaveDraft>(schemas.save),
  validate: ajv.compile<ValidateDraft>(schemas.validate),
  draft: ajv.compile<DraftRevision>(schemas.draft),
  page: ajv.compile<DraftPage>(schemas.page),
  validation: ajv.compile<DraftValidation>(schemas.validation),
  receipt: ajv.compile<DraftCommandReceipt>(schemas.receipt),
  admit: ajv.compile<AdmitDraft>(schemas.admit),
  universe: ajv.compile<DefinitionUniverse>(schemas.universe),
  schema: ajv.compile<DefinitionSchema>(schemas.schema),
  releases: ajv.compile<ReleasePage>(schemas.releases),
  release: ajv.compile<ReleaseSnapshot>(schemas.release),
  cancel: ajv.compile<CancelRun>(schemas.cancel),
  execution_receipt: ajv.compile<CommandReceipt>(schemas.execution_receipt),
  identity: ajv.compile<CommandIdentity>(schemas.identity),
};

export function decodeAuthoring<K extends keyof AuthoringWire>(kind: K, value: unknown): AuthoringWire[K] {
  const validate = validators[kind] as ValidateFunction<AuthoringWire[K]>;
  if (!validate(value)) throw new Error("invalid_authoring_response");
  return value;
}
