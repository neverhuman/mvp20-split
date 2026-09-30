import { decodeAuthoring } from "../../contracts/authoring.js";
import type { DefinitionSchema, DefinitionUniverse } from "../../contracts/authoring.js";
import { reviewedSchema } from "../../contracts/reviewed_schema.js";
import { AuthoringFailure } from "../../transport/authoring.js";
import type { AuthoringClient } from "../../transport/authoring.js";
import { RequestLane } from "../request_lane.js";
import { ToolChoices } from "./tool_choices.js";

type Source = Pick<AuthoringClient, "universe" | "releases" | "schema">;
type Reference = DefinitionSchema["reference"];
interface CatalogView {
  phase: "idle" | "loading" | "ready" | "stale" | "denied";
  universe: DefinitionUniverse | undefined;
  choices: ToolChoices | undefined;
  nextAfter: string | undefined;
  error: string | undefined;
  schemaPhase: "idle" | "loading" | "ready" | "unavailable";
  schema: { reference: Reference; document: Readonly<Record<string, unknown>> } | undefined;
}

/** One bounded discovery page and one lazy schema selection; no catalog-wide schema download. */
export class EditorCatalog {
  private readonly catalogLane = new RequestLane();
  private readonly schemaLane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private readonly expectedScope: DefinitionUniverse["scope"];
  private disposed = false;
  private view: CatalogView = { phase: "idle", universe: undefined, choices: undefined, nextAfter: undefined,
    error: undefined, schemaPhase: "idle", schema: undefined };

  constructor(scope: DefinitionUniverse["scope"], private readonly source: Source) { this.expectedScope = structuredClone(scope); }
  get snapshot() {
    return { ...structuredClone({ ...this.view, choices: undefined }), choices: this.view.choices?.snapshot };
  }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private patch(fields: Partial<CatalogView>) {
    if (this.disposed) return;
    this.view = { ...this.view, ...fields };
    for (const listener of this.listeners) listener();
  }

  async refresh(after?: string) {
    if (this.disposed || this.view.phase === "denied") return;
    const request = this.catalogLane.begin(); this.schemaLane.cancel();
    this.patch({ phase: "loading", error: undefined, schema: undefined, schemaPhase: "idle" });
    try {
      const protect = <T>(promise: Promise<T>) => promise.catch((error: unknown) => {
        // Either owner can revoke access, including after its sibling request already failed.
        if (request.current() && error instanceof AuthoringFailure && error.kind === "denied") this.deny();
        throw error;
      });
      const [rawUniverse, rawPage] = await Promise.all([protect(this.source.universe(request.signal)), protect(this.source.releases(after, request.signal))]);
      if (!request.current()) return;
      const universe = decodeAuthoring("universe", rawUniverse), page = decodeAuthoring("releases", rawPage);
      if (universe.scope.tenant_id !== this.expectedScope.tenant_id || universe.scope.project_id !== this.expectedScope.project_id)
        throw new Error("catalog_scope_mismatch");
      const choices = new ToolChoices(universe, page.items);
      this.patch({ phase: "ready", universe: structuredClone(universe), choices, nextAfter: page.next_after ?? undefined });
    } catch (error) {
      if (!request.current()) return;
      if (error instanceof AuthoringFailure && error.kind === "denied") { this.deny(); return; }
      this.patch({ phase: "stale", error: error instanceof AuthoringFailure ? error.kind : "invalid_response" });
    }
  }

  select(descriptor: string) {
    if (this.disposed || this.view.phase !== "ready" || !this.view.choices) throw new Error("catalog_not_ready");
    return this.view.choices.select(descriptor);
  }

  async inspectSchema(reference: Reference) {
    if (this.disposed || this.view.phase !== "ready" || !this.view.universe) throw new Error("catalog_not_ready");
    const universe = structuredClone(this.view.universe), selected = structuredClone(reference);
    if (!universe.schemas.some(item => item.schema_id === selected.schema_id && item.version === selected.version && item.sha256 === selected.sha256))
      throw new Error("schema_not_reviewed");
    const request = this.schemaLane.begin();
    this.patch({ schemaPhase: "loading", schema: undefined, error: undefined });
    try {
      const raw = await this.source.schema(selected, universe.universe_sha256, request.signal);
      if (!request.current()) return;
      const document = await reviewedSchema(raw, universe, selected);
      if (!request.current()) return;
      this.patch({ schemaPhase: "ready", schema: { reference: selected, document } });
    } catch (error) {
      if (!request.current()) return;
      if (error instanceof AuthoringFailure && error.kind === "denied") { this.deny(); return; }
      this.patch({ schemaPhase: "unavailable", error: error instanceof AuthoringFailure ? error.kind : "invalid_response",
        ...(error instanceof AuthoringFailure && error.kind === "stale" ? { phase: "stale" as const } : {}) });
    }
  }

  deny() {
    this.catalogLane.cancel(); this.schemaLane.cancel();
    this.patch({ phase: "denied", universe: undefined, choices: undefined, nextAfter: undefined, schema: undefined,
      schemaPhase: "idle", error: "denied" });
  }
  dispose() { this.disposed = true; this.catalogLane.cancel(); this.schemaLane.cancel(); this.listeners.clear(); }
}
