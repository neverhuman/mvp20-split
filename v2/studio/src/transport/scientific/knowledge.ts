import { decodeKnowledge } from "../../contracts/scientific/knowledge.js";
import type { DomainRevisionRef, GraphEntitySearchRequest, GraphNeighborhoodRequest, GraphObjectRequest } from "../../contracts/scientific/knowledge.js";
import manifest from "../../contracts/generated/knowledge/manifest.json" with { type: "json" };
import { ScientificHTTP } from "./http.js";
import { checkPage, checkWindow, normalized, queryDigest, requireReply, same } from "./identity.js";

const base = "/api/knowledge/v1/graph-explore/";
const format = "knowledge.explore-query.v1";

export class KnowledgeClient {
  private readonly http: ScientificHTTP;
  constructor(fetcher: typeof fetch = fetch, timeoutMs = 15_000) { this.http = new ScientificHTTP(fetcher, timeoutMs); }

  async catalog(revision: DomainRevisionRef, signal: AbortSignal) {
    const checked = normalized({ wire_version: "1" as const, revision }, {}, value => decodeKnowledge("search_request", value)).revision;
    const result = await this.http.post(base + "catalog", checked, value => decodeKnowledge("catalog", value), signal);
    requireReply(same(result.revision, checked));
    const expected = { entity_search: ["knowledge.entity-search-page", manifest.search_page.sha256],
      neighborhood: ["knowledge.neighborhood-page", manifest.neighborhood_page.sha256],
      object_detail: ["knowledge.object-detail", manifest.object_detail.sha256] };
    requireReply(new Set(result.views.map(v => v.view_id)).size === 3);
    for (const view of result.views) requireReply(view.result_schema.schema_id === expected[view.view_id][0] && view.result_schema.sha256 === expected[view.view_id][1]);
    return result;
  }

  async search(request: GraphEntitySearchRequest, signal: AbortSignal) {
    const query = normalized(request, { text: "", entity_type: null, history: "current", limit: 50, position: null }, value => decodeKnowledge("search_request", value));
    const digest = await queryDigest(format, "entity_search", query);
    const page = await this.http.post(base + "entities", query, value => decodeKnowledge("search_page", value), signal);
    checkPage(page, query, digest);
    requireReply((query.position?.assertion_offset ?? 0) === 0 && (page.next_position?.assertion_offset ?? 0) === 0);
    checkWindow(query.position?.entity_offset ?? 0, page.entities.length, query.limit!, page.total, page.next_position?.entity_offset ?? null);
    for (const row of page.entities) {
      requireReply(same(row.reference.graph, query.revision.graph));
      requireReply(row.alias_target === null || same(row.alias_target.graph, query.revision.graph));
    }
    return page;
  }

  async neighborhood(request: GraphNeighborhoodRequest, signal: AbortSignal) {
    const query = normalized(request, { radius: 1, history: "current", entity_limit: 64, assertion_limit: 128, position: null }, value => decodeKnowledge("neighborhood_request", value));
    const digest = await queryDigest(format, "neighborhood", query);
    const page = await this.http.post(base + "neighborhood", query, value => decodeKnowledge("neighborhood_page", value), signal);
    checkPage(page, query, digest);
    const left = query.position?.entity_offset ?? 0, right = query.position?.assertion_offset ?? 0;
    const entityEnd = left + page.entities.length, assertionEnd = right + page.assertions.length;
    requireReply(page.entities.length === Math.min(query.entity_limit!, page.entity_total - left));
    requireReply(page.assertions.length === Math.min(query.assertion_limit!, page.assertion_total - right));
    const finished = entityEnd === page.entity_total && assertionEnd === page.assertion_total;
    requireReply(finished ? page.next_position === null : page.next_position?.entity_offset === entityEnd && page.next_position?.assertion_offset === assertionEnd);
    const references = [...page.entities.flatMap(row => row.alias_target ? [row.reference, row.alias_target] : [row.reference]), ...page.assertions.flatMap(row => [row.subject, row.object]), ...page.unresolved_entities];
    for (const ref of references) requireReply(same(ref.graph, query.revision.graph));
    for (const row of page.assertions) requireReply(same(row.reference.graph, query.revision.graph));
    return page;
  }

  async detail(request: GraphObjectRequest, signal: AbortSignal) {
    const query = normalized(request, {}, value => decodeKnowledge("object_request", value));
    const result = await this.http.post(base + "object", query, value => decodeKnowledge("object_detail", value), signal);
    requireReply(same(result.request, query) && result.detail.kind === query.selection.kind && same(result.detail.record.reference, query.selection.reference));
    requireReply(same(result.detail.record.reference.graph, query.revision.graph));
    return result;
  }
}
