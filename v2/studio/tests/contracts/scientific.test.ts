import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { decodeKnowledge } from "../../src/contracts/scientific/knowledge.js";
import { decodeResearch } from "../../src/contracts/scientific/research.js";
import knowledge from "../fixtures/scientific/knowledge.json" with { type: "json" };
import research from "../fixtures/scientific/research.json" with { type: "json" };
import knowledgeManifest from "../../src/contracts/generated/knowledge/manifest.json" with { type: "json" };
import researchManifest from "../../src/contracts/generated/research/manifest.json" with { type: "json" };

test("scientific schema derivatives pin every owner-published byte", async () => {
  for (const manifest of [knowledgeManifest, researchManifest]) for (const entry of Object.values(manifest)) {
    assert.equal(createHash("sha256").update(await readFile("../" + entry.source)).digest("hex"), entry.sha256);
  }
});

test("all scientific roots decode without coercion or data mutation", () => {
  const k = { search_request: knowledge.search_request, search_page: knowledge.search_page,
    neighborhood_request: knowledge.neighborhood_request, neighborhood_page: knowledge.neighborhood_page,
    object_request: knowledge.object_request, object_detail: knowledge.object_detail, catalog: knowledge.catalog };
  for (const name of Object.keys(k) as (keyof typeof k)[]) assert.deepEqual(decodeKnowledge(name, k[name]), k[name]);
  const r = { specimen_request: research.specimen_request, specimen_page: research.specimen_page,
    property_request: research.property_request, property_page: research.property_page,
    series_request: research.series_request, series_page: research.series_page, catalog: research.catalog };
  for (const name of Object.keys(r) as (keyof typeof r)[]) assert.deepEqual(decodeResearch(name, r[name]), r[name]);
  assert.throws(() => decodeKnowledge("search_request", { ...knowledge.search_request, limit: "1" }));
  assert.throws(() => decodeResearch("property_request", { ...research.property_request, limit: true }));
  assert.throws(() => decodeResearch("property_page", { ...research.property_page, authority: "scientifically_accepted" }));
  assert.throws(() => decodeKnowledge("catalog", { ...knowledge.catalog, executable_route: "https://external.invalid" }));
});
