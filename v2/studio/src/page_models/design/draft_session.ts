import { decodeAuthoring } from "../../contracts/authoring.js";
import type { AuthoringWire, CommandIdentity, DraftCommandReceipt, DraftRevision, DraftValidation, SaveDraft } from "../../contracts/authoring.js";
import { Submission } from "../../transport/submission.js";

type Scope = CommandIdentity["scope"];
type LocalDraft = Pick<SaveDraft, "title" | "definition">;
type Pending = { command: Submission<"save"> | Submission<"validate">; editVersion: number; binding?: string; terminal?: string };
const sameScope = (left: Scope, right: Scope) => left.tenant_id === right.tenant_id && left.project_id === right.project_id;

function comparable(value: unknown): string {
  if (Array.isArray(value)) return "[" + value.map(comparable).join(",") + "]";
  if (value && typeof value === "object") return "{" + Object.entries(value).sort(([a], [b]) => a.localeCompare(b))
    .map(([key, item]) => JSON.stringify(key) + ":" + comparable(item)).join(",") + "}";
  return JSON.stringify(value) ?? "null";
}

export class DraftSession {
  private readonly context: string;
  private base: DraftRevision | undefined;
  private local: LocalDraft;
  private pending: Pending | undefined;
  private validation: DraftValidation | undefined;
  private editVersion = 0;
  private denied = false;
  private selected: string | undefined;
  private reason: string | undefined;

  constructor(actor: string, scope: Scope, readonly draftId: string, initial: LocalDraft, base?: DraftRevision) {
    // This validates identity/definition bounds without issuing or registering a command.
    this.context = JSON.stringify({ actor_id: actor, scope });
    this.local = structuredClone(initial);
    this.makeSubmission("shape-check", "save", { ...initial, draft_id: draftId, expected_revision: base?.head.revision ?? 0 });
    if (base) {
      decodeAuthoring("draft", base);
      this.requireRevision(base);
      if (comparable(initial) !== comparable({ title: base.head.title, definition: base.definition })) throw new Error("initial_base_mismatch");
      this.base = structuredClone(base);
    }
  }

  get snapshot() {
    return structuredClone({ draftId: this.draftId, local: this.local, base: this.base, selected: this.selected,
      dirty: this.dirty, denied: this.denied, reason: this.reason, validation: this.validation,
      validationMatchesDraft: !this.denied && !this.dirty && !!this.base && !!this.validation &&
        this.validation.revision === this.base.head.revision && this.validation.content_sha256 === this.base.head.content_sha256,
      pending: this.pending ? { action: this.pending.command.action, identity: this.pending.command.identity } : undefined });
  }

  get unresolvedCommand() { return this.pending?.command; }
  get dirty() { return !this.base || comparable(this.local) !== comparable({ title: this.base.head.title, definition: this.base.definition }); }

  edit(next: LocalDraft) {
    if (this.denied) throw new Error("session_denied");
    if (next.definition.campaign_id !== this.local.definition.campaign_id) throw new Error("campaign_identity_changed");
    this.makeSubmission("shape-check", "save", { ...next, draft_id: this.draftId, expected_revision: this.base?.head.revision ?? 0 });
    this.local = structuredClone(next);
    this.editVersion++;
  }

  select(node: string | undefined) { this.selected = node; }

  beginSave(commandId: string): Submission<"save"> {
    this.requireAvailable();
    const command = this.makeSubmission(commandId, "save", { ...this.local, draft_id: this.draftId, expected_revision: this.base?.head.revision ?? 0 });
    this.pending = { command, editVersion: this.editVersion }; this.reason = undefined;
    return command;
  }

  beginValidation(commandId: string): Submission<"validate"> {
    this.requireAvailable();
    if (!this.base || this.dirty) throw new Error("save_before_validation");
    const command = this.makeSubmission(commandId, "validate", { draft_id: this.draftId, revision: this.base.head.revision, content_sha256: this.base.head.content_sha256 });
    this.pending = { command, editVersion: this.editVersion }; this.reason = undefined;
    return command;
  }

  /** Caller follows accepted receipts to exact public records before releasing the pending command. */
  reconcile(command: Submission, receipt: DraftCommandReceipt, record?: DraftRevision | DraftValidation): boolean {
    if (!this.observeReceipt(command, receipt) || !this.pending) return false;
    const outcome = receipt.outcome;
    if (outcome.status === "pending") return false;
    if (outcome.status === "rejected") { this.reason = outcome.reason_code; this.pending = undefined; return true; }
    const commit = outcome.committed;
    if (command.action === "save") {
      const revision = decodeAuthoring("draft", record);
      this.requireRevision(revision);
      const submitted = (JSON.parse(command.body) as { payload: SaveDraft }).payload;
      if (commit.kind !== "draft_revision" || commit.object_id !== this.draftId || commit.revision !== revision.head.revision ||
        commit.content_sha256 !== revision.head.content_sha256 || revision.head.revision !== submitted.expected_revision + 1 ||
        revision.parent_revision !== submitted.expected_revision || revision.head.title !== submitted.title)
        throw new Error("save_record_mismatch");
      this.base = structuredClone(revision);
      if (this.pending.editVersion === this.editVersion) this.local = { title: revision.head.title, definition: structuredClone(revision.definition) };
    } else {
      const validation = decodeAuthoring("validation", record);
      if (!this.base || !sameScope(validation.scope, this.base.scope) || validation.draft_id !== this.draftId ||
        validation.revision !== this.base.head.revision || validation.content_sha256 !== this.base.head.content_sha256 ||
        commit.kind !== "draft_validation" || commit.object_id !== validation.validation_id || commit.revision !== validation.revision ||
        commit.content_sha256 !== validation.content_sha256 || validation.structurally_valid !== (validation.plan_sha256 !== null))
        throw new Error("validation_record_mismatch");
      this.validation = structuredClone(validation);
    }
    this.pending = undefined; this.reason = undefined;
    return true;
  }

  observeReceipt(command: Submission, receipt: DraftCommandReceipt): boolean {
    if (this.denied || this.pending?.command !== command) return false;
    command.verify(receipt);
    const outcome = receipt.outcome;
    const binding = JSON.stringify([outcome.binding.operation_id, outcome.binding.request_sha256]);
    if (this.pending.binding !== undefined && this.pending.binding !== binding) throw new Error("receipt_binding_changed");
    const terminal = comparable(outcome);
    if (this.pending.terminal !== undefined && this.pending.terminal !== terminal) throw new Error("terminal_receipt_changed");
    this.pending.binding = binding;
    if (outcome.status !== "pending") this.pending.terminal = terminal;
    return true;
  }

  deny() {
    this.denied = true; this.base = undefined; this.validation = undefined; this.selected = undefined;
    this.reason = "session_denied";
    // Preserve local draft and original unresolved identity; never transmit from this session again.
  }

  private requireAvailable() { if (this.denied) throw new Error("session_denied"); if (this.pending) throw new Error("command_unresolved"); }
  private requireRevision(revision: DraftRevision) {
    const { scope } = JSON.parse(this.context) as { scope: Scope };
    if (!sameScope(revision.scope, scope) || !sameScope(revision.definition.scope, scope) || revision.head.draft_id !== this.draftId ||
      revision.definition.campaign_id !== this.local.definition.campaign_id || revision.parent_revision !== revision.head.revision - 1)
      throw new Error("draft_record_mismatch");
  }
  private makeSubmission<A extends "save" | "validate">(id: string, action: A, payload: AuthoringWire[A]): Submission<A> {
    const context = JSON.parse(this.context) as Pick<CommandIdentity, "actor_id" | "scope">;
    return new Submission(action, { ...context, command_id: id, command_family: action === "save" ? "definition.save" : "definition.validate" }, payload);
  }
}
