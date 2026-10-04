import { decodeResearch } from "../../contracts/scientific/research.js";
import type { ExperimentRevisionRef, SpecimenViewRequest, PropertyViewRequest, ObservationSeriesRequest } from "../../contracts/scientific/research.js";
import manifest from "../../contracts/generated/research/manifest.json" with { type: "json" };
import { ScientificHTTP } from "./http.js";
import { canonical, checkPage, checkWindow, normalized, queryDigest, requireReply, same } from "./identity.js";
import { ScientificReadFailure } from "./failure.js";

const base = "/api/research/v1/research-explore/";
const format = "research.view-query.v1";

export class ResearchClient {
  private readonly http: ScientificHTTP;
  constructor(fetcher: typeof fetch = fetch, timeoutMs = 15_000) { this.http = new ScientificHTTP(fetcher, timeoutMs); }

  async catalog(experiment: ExperimentRevisionRef, signal: AbortSignal) {
    const checked = normalized({ wire_version: "1" as const, experiment }, {}, value => decodeResearch("specimen_request", value)).experiment;
    const result = await this.http.post(base + "catalog", checked, value => decodeResearch("catalog", value), signal);
    requireReply(same(result.experiment, checked));
    const expected = { specimens: ["research-views.specimen-view-page", manifest.specimen_page.sha256],
      properties: ["research-views.property-view-page", manifest.property_page.sha256],
      observation_series: ["research-views.observation-series-page", manifest.series_page.sha256] };
    requireReply(new Set(result.views.map(v => v.view_id)).size === 3);
    for (const view of result.views) requireReply(view.result_schema.schema_id === expected[view.view_id][0] && view.result_schema.sha256 === expected[view.view_id][1]);
    return result;
  }

  async specimens(request: SpecimenViewRequest, signal: AbortSignal) {
    const query = normalized(request, { limit: 16, position: null }, value => decodeResearch("specimen_request", value));
    const digest = await queryDigest(format, "specimens", query);
    const page = await this.http.post(base + "specimens", query, value => decodeResearch("specimen_page", value), signal);
    checkPage(page, query, digest);
    checkWindow(query.position?.offset ?? 0, page.rows.length, query.limit!, page.total, page.next_position?.offset ?? null);
    for (const row of page.rows) {
      requireReply(same(row.sample.reference.scope, query.experiment.scope) && same(row.sample.candidate.scope, query.experiment.scope));
      if (row.material) requireReply(same(row.material.reference, row.sample.material_state) && same(row.material.candidate, row.sample.candidate));
    }
    return page;
  }

  async properties(request: PropertyViewRequest, signal: AbortSignal) {
    const query = normalized(request, { limit: 16, position: null }, value => decodeResearch("property_request", value));
    if (query.observations.some(ref => !same(ref.scope, query.experiment.scope)) || new Set(query.observations.map(canonical)).size !== query.observations.length)
      throw new ScientificReadFailure("invalid_request");
    const digest = await queryDigest(format, "properties", query);
    const page = await this.http.post(base + "properties", query, value => decodeResearch("property_page", value), signal);
    checkPage(page, query, digest);
    requireReply(page.total === query.observations.length);
    const offset = query.position?.offset ?? 0;
    checkWindow(offset, page.rows.length, query.limit!, page.total, page.next_position?.offset ?? null);
    requireReply(same(page.protocol.applicability.scope, query.experiment.scope) && same(page.protocol.source.scope, query.experiment.scope));
    page.rows.forEach((row, index) => {
      requireReply(same(row.reference, query.observations[offset + index]) && same(row.source.scope, query.experiment.scope));
      if (row.expectation) requireReply(same(row.expectation.sample.scope, query.experiment.scope));
      // Binding is reported evidence, including mismatched/foreign claims; it is not an access grant.
    });
    return page;
  }

  async series(request: ObservationSeriesRequest, signal: AbortSignal) {
    const query = normalized(request, { limit: 256, position: null }, value => decodeResearch("series_request", value));
    const digest = await queryDigest(format, "observation_series", query);
    const page = await this.http.post(base + "observation-series", query, value => decodeResearch("series_page", value), signal);
    checkPage(page, query, digest);
    checkWindow(query.position?.offset ?? 0, page.points.length, query.limit!, page.total, page.next_position?.offset ?? null);
    requireReply(same(page.source.scope, query.observation.scope));
    return page;
  }
}
