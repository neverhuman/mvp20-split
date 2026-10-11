import type { CampaignOrigin, OriginDraft } from "../../contracts/campaign_origin.js";
import { AuthoringFailure } from "../../transport/authoring.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";
import { immutable } from "../explore/context.js";
import { RequestLane } from "../request_lane.js";
import type { OriginReader } from "./reader.js";
import type { OriginCriteria, OriginResearchReader } from "./research.js";

type Phase = "idle" | "loading" | "ready" | "not_recorded" | "denied" | "failed";
interface OriginView {
  phase: Phase; origin: CampaignOrigin | null; reason: string | null;
  detail: { phase: "idle" | "loading" | "ready" | "denied" | "failed"; index: number | null; value: OriginCriteria | null; reason: string | null };
}
const emptyDetail = () => ({ phase: "idle" as const, index: null, value: null, reason: null });

/** One request owner per provenance region; no campaign mutations or scientific promotion. */
export class CampaignOriginModel {
  private readonly lane = new RequestLane();
  private readonly detailLane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private disposed = false;
  private view: Readonly<OriginView> = immutable({ phase: "idle", origin: null, reason: null, detail: emptyDetail() });
  constructor(private readonly source: Pick<OriginReader, "read">, private readonly research: Pick<OriginResearchReader, "read">) {}
  get snapshot() { return this.view; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  dispose() { this.disposed = true; this.lane.cancel(); this.detailLane.cancel(); this.listeners.clear(); }
  private patch(fields: Partial<OriginView>) {
    if (this.disposed) return;
    this.view = immutable({ ...this.view, ...fields }); for (const listener of this.listeners) listener();
  }
  async load(selection: OriginDraft) {
    if (this.disposed) return;
    const request = this.lane.begin(); this.detailLane.cancel();
    this.patch({ phase: "loading", origin: null, reason: null, detail: emptyDetail() });
    try {
      const origin = await this.source.read(immutable(selection), request.signal);
      if (request.current()) this.patch({ phase: origin ? "ready" : "not_recorded", origin });
    } catch (error) {
      if (!request.current()) return;
      const kind = failure(error);
      this.patch({ phase: kind === "denied" ? "denied" : "failed", origin: null, reason: kind });
    }
  }
  async inspect(index: number) {
    if (this.disposed || this.view.phase !== "ready" || !this.view.origin) return;
    const request = this.detailLane.begin(), origin = this.view.origin;
    this.patch({ detail: { phase: "loading", index, value: null, reason: null } });
    try {
      const value = await this.research.read(origin.origin, index, request.signal);
      if (request.current() && this.view.origin?.origin_sha256 === origin.origin_sha256) this.patch({ detail: { phase: "ready", index, value, reason: null } });
    } catch (error) {
      if (!request.current()) return;
      const kind = failure(error);
      this.patch({ detail: { phase: kind === "denied" ? "denied" : "failed", index, value: null, reason: kind } });
    }
  }
}
function failure(error: unknown) {
  return error instanceof ScientificReadFailure || error instanceof AuthoringFailure ? error.kind : "invalid_response";
}
