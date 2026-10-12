import {checkJSON,numericJSON} from "./command_wire.js";
import { decodeAuthoring } from "../contracts/authoring.js";
import type { AuthoringWire, CommandIdentity, CommandReceipt, DraftCommandReceipt } from "../contracts/authoring.js";

type Action = "save" | "validate" | "admit" | "cancel";
const families = { save: "definition.save", validate: "definition.validate", admit: "graph.admit_draft", cancel: "runtime.cancel" } as const;
const paths = { save: "definition-drafts/save", validate: "definition-drafts/validate", admit: "graph-runs/drafts", cancel: "runs/cancel" } as const;

function sameIdentity(left: CommandIdentity, right: CommandIdentity): boolean {
  return left.actor_id === right.actor_id && left.command_family === right.command_family && left.command_id === right.command_id &&
    left.scope.tenant_id === right.scope.tenant_id && left.scope.project_id === right.scope.project_id;
}

/** Retains submitted bytes, never the caller's mutable editor objects. No network retry policy. */
export class Submission<A extends Action = Action> {
  readonly body: string;
  readonly path: string;
  readonly receiptPath: string;
  readonly receiptKind: "receipt" | "execution_receipt";
  private readonly originalIdentity: string;

  constructor(readonly action: A, identity: CommandIdentity, payload: AuthoringWire[A]) {
    const numeric = action === "save" || action === "admit";
    const envelope = numeric ? { encoding: "amphora-command-v2", identity, payload } : { identity, payload };
    checkJSON(envelope, numeric);
    decodeAuthoring("identity", identity);
    decodeAuthoring(action, payload);
    if (identity.command_family !== families[action]) throw new Error("command_family_mismatch");
    if (action === "save") {
      const scope = (payload as AuthoringWire["save"]).definition.scope;
      if (scope.tenant_id !== identity.scope.tenant_id || scope.project_id !== identity.scope.project_id) throw new Error("command_scope_mismatch");
    }
    if (action === "cancel" && (payload as AuthoringWire["cancel"]).expected_run_revision == null) throw new Error("cancel_revision_required");
    this.body = numeric ? numericJSON(envelope) : JSON.stringify(envelope);
    if (new TextEncoder().encode(this.body).byteLength > 262_144) throw new Error("command_too_large");
    this.originalIdentity = JSON.stringify(identity);
    this.path = paths[action];
    this.receiptKind = action === "save" || action === "validate" ? "receipt" : "execution_receipt";
    this.receiptPath = (this.receiptKind === "receipt" ? "definition-commands/" : "commands/") +
      encodeURIComponent(identity.command_family) + "/" + encodeURIComponent(identity.command_id);
    Object.freeze(this);
  }

  get identity(): CommandIdentity { return JSON.parse(this.originalIdentity) as CommandIdentity; }

  verify(receipt: DraftCommandReceipt | CommandReceipt): void {
    decodeAuthoring(this.receiptKind, receipt);
    if (!sameIdentity(this.identity, receipt.outcome.binding.identity)) throw new Error("receipt_identity_mismatch");
  }
}
