import type { ValidateFunction } from "ajv";
import compiled from "./generated/authoring/validators.js";
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

const validators = compiled as Record<string, ValidateFunction>;

export function decodeAuthoring<K extends keyof AuthoringWire>(kind: K, value: unknown): AuthoringWire[K] {
  const validate = validators[kind] as ValidateFunction<AuthoringWire[K]>;
  if (!validate(value)) throw new Error("invalid_authoring_response");
  return value;
}
