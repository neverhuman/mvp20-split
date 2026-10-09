import { decodeAuthoring } from "../../contracts/authoring.js";
import type { DraftPage } from "../../contracts/authoring.js";
import { decodeLaunch } from "../../contracts/launch.js";
import type { LaunchProfileCatalog } from "../../contracts/launch.js";
import type { AuthoringClient } from "../../transport/authoring.js";
import type { LaunchClient } from "../../transport/launch/client.js";
import { same } from "../../transport/scientific/identity.js";
import { RequestLane } from "../request_lane.js";
import { DraftSession } from "../design/draft_session.js";
import { DraftCommands } from "../design/draft_commands.js";
import type { LaunchContext } from "./journal.js";
import type { CampaignLaunch } from "./model.js";

interface PreparationView {
  phase: "idle" | "loading" | "ready" | "denied" | "failed";
  drafts: DraftPage | null;
  profiles: LaunchProfileCatalog | null;
  selected: string | null;
  validating: boolean;
  canRun: boolean;
  message: string | null;
}
/** Bounded saved-draft selection. Only self-contained drafts can launch in this first UI. */
export class LaunchPreparation {
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private commands: DraftCommands | undefined;
  private subscriptions: (() => void)[] = [];
  private disposed = false;
  private view: Readonly<PreparationView> = Object.freeze({ phase: "idle", drafts: null, profiles: null, selected: null, validating: false, canRun: false, message: null });
  constructor(private readonly context: LaunchContext, private readonly authoring: Pick<AuthoringClient, "drafts" | "draft" | "submit" | "receipt" | "validation">,
    private readonly launcher: Pick<LaunchClient, "profiles">) {}
  get snapshot() { return this.view; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private patch(fields: Partial<PreparationView>) {
    if (this.disposed) return;
    this.view = Object.freeze({ ...this.view, ...fields }); for (const listener of this.listeners) listener();
  }
  async load() {
    if (this.disposed || this.view.phase === "denied" || this.commands?.session.snapshot.pending) return;
    const request = this.lane.begin(); this.patch({ phase: "loading", canRun: false, message: null });
    try {
      const [drafts, profiles] = await Promise.all([this.authoring.drafts(undefined, request.signal), this.launcher.profiles(request.signal)]);
      if (!request.current()) return;
      decodeAuthoring("page", drafts); decodeLaunch("catalog", profiles);
      if (!same(drafts.scope, this.context.scope) || !same(profiles.scope, this.context.scope) ||
        profiles.profiles.some(profile => !same(profile.scope, this.context.scope)) ||
        new Set(drafts.drafts.map(draft => draft.draft_id)).size !== drafts.drafts.length) throw Error("scope");
      this.closeCommands(); this.patch({ phase: "ready", drafts, profiles, selected: null });
    } catch (error) { if (request.current()) this.fail(error); }
  }
  async select(id: string) {
    if (this.disposed || this.view.phase !== "ready" || this.commands?.session.snapshot.pending) return;
    const head = this.view.drafts?.drafts.find(draft => draft.draft_id === id);
    if (!head) throw Error("unknown_draft");
    const request = this.lane.begin(); this.patch({ phase: "loading", canRun: false, message: null });
    try {
      const record = decodeAuthoring("draft", await this.authoring.draft(id, head.revision, request.signal));
      if (!request.current()) return;
      if (!same(record.scope, this.context.scope) || !same(record.head, head)) throw Error("draft_changed");
      this.closeCommands();
      this.commands = new DraftCommands(new DraftSession(this.context.actor_id, this.context.scope, id,
        { title: record.head.title, definition: record.definition }, record), this.authoring);
      this.subscriptions = [this.commands.subscribe(() => this.sync())];
      this.patch({ phase: "ready", selected: id }); this.sync();
    } catch (error) { if (request.current()) this.fail(error); }
  }
  private sync() {
    const draft = this.commands?.session.snapshot;
    if (!draft) return;
    const unbound = (draft.local.definition.body.inputs?.length ?? 0) > 0;
    const pending = !!draft.pending;
    const valid = !draft.denied && !pending && draft.validationMatchesDraft && !!draft.validation?.structurally_valid;
    this.patch({ validating: pending, canRun: valid && !unbound && this.view.profiles?.profiles.length === 1,
      message: draft.denied ? "Draft access denied." : unbound ? "This draft needs input bindings. Choose a prepared draft with pinned inputs for this demo."
      : pending ? "Checking this exact saved revision. A pending check keeps its original request."
      : valid ? "Saved revision checked. Installed tools and capacity will be checked again at launch."
      : "Check this saved revision before running it." });
  }
  async validate(id: string) {
    if (!this.commands || this.view.phase !== "ready") throw Error("draft_required");
    if (this.commands.session.snapshot.pending) await this.commands.reconcile();
    else await this.commands.validate(id);
    this.sync();
  }
  run(id: string, launch: CampaignLaunch) {
    if (!this.view.canRun || !this.commands || !launch.canRequest) throw Error("launch_not_available");
    const profile = this.view.profiles!.profiles[0]!;
    const admission = this.commands.session.admission(id, { inputs: [],
      budget: { limit: profile.maximum_invocations, max_attempts_per_activation: 2 },
      limits: { max_activations: 10000, deadline_seconds: profile.maximum_deadline_seconds } });
    return launch.requestLaunch(admission, profile.reference);
  }
  private fail(error: unknown) {
    const denied = (error as { kind?: string }).kind === "denied";
    this.closeCommands(); this.patch({ phase: denied ? "denied" : "failed", drafts: null, profiles: null, selected: null,
      canRun: false, validating: false, message: denied ? "Launch preparation access denied." : "Campaign launch preparation is unavailable. Existing runs are unchanged." });
  }
  private closeCommands() { for (const unsubscribe of this.subscriptions) unsubscribe(); this.subscriptions = []; this.commands?.dispose(); this.commands = undefined; }
  dispose() { this.disposed = true; this.lane.cancel(); this.closeCommands(); this.listeners.clear(); }
}
