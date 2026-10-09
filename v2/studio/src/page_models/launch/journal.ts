import type { LaunchReceipt, LaunchRequest } from "../../contracts/launch.js";
import { LaunchSubmission } from "../../transport/launch/submission.js";

export interface LaunchContext { actor_id: string; scope: LaunchRequest["identity"]["scope"] }
export interface LaunchStorage { getItem(key: string): string | null; setItem(key: string, value: string): void }
export interface SavedLaunch { command: LaunchSubmission; receipt?: LaunchReceipt }

/** Browser recovery hints are untrusted; a live receipt must reestablish the selected run. */
export class LaunchJournal {
  private readonly key: string;
  constructor(readonly context: LaunchContext, private readonly storage: LaunchStorage) {
    this.key = "amphora.launch.v1:" + JSON.stringify([context.scope.tenant_id, context.scope.project_id, context.actor_id]);
  }
  private authorize(command: LaunchSubmission) {
    const identity = command.request.identity;
    if (identity.actor_id !== this.context.actor_id || identity.scope.tenant_id !== this.context.scope.tenant_id ||
      identity.scope.project_id !== this.context.scope.project_id) throw new Error("launch_scope_mismatch");
  }
  load(): SavedLaunch | undefined {
    const raw = this.storage.getItem(this.key);
    if (raw === null) return undefined;
    if (raw.length > 600_000) throw new Error("launch_storage_invalid");
    const value = JSON.parse(raw);
    if (!value || value.version !== 1 || typeof value.body !== "string" ||
      Object.keys(value).some(key => !["version", "body", "receipt"].includes(key))) throw new Error("launch_storage_invalid");
    const command = LaunchSubmission.restore(value.body); this.authorize(command);
    return { command, ...(value.receipt ? { receipt: command.verify(value.receipt) } : {}) };
  }
  save(command: LaunchSubmission, receipt?: LaunchReceipt) {
    this.authorize(command);
    const old = this.load();
    if (old && old.command.body !== command.body && !["released", "rejected"].includes(old.receipt?.phase ?? ""))
      throw new Error("launch_storage_pending");
    if (receipt) command.verify(receipt, old?.command.body === command.body ? old.receipt : undefined);
    const raw = JSON.stringify({ version: 1, body: command.body, ...(receipt ? { receipt } : {}) });
    this.storage.setItem(this.key, raw);
    if (this.storage.getItem(this.key) !== raw) throw new Error("launch_storage_changed");
  }
}
