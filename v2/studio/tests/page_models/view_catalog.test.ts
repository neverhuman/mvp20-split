import { test } from "node:test";
import assert from "node:assert/strict";
import { ViewCatalog, scientificViews } from "../../src/page_models/view_catalog.js";
import { catalog, lineage } from "../fixtures/navigation.js";
import { id } from "../fixtures/observations.js";

test("VIEW-01 named views reject unknown, mistyped and out-of-scope queries", () => {
  const page = catalog(), views = ViewCatalog.open(page.cut, page);
  assert.deepEqual(views.resolve("execution_topology", { scope_key: id(100) }).filters, { scope_key: id(100), radius: 1 });
  for (const filters of [{}, { scope_key: "wrong" }, { scope_key: id(100), radius: "1" },
    { scope_key: id(100), radius: 3 }, { scope_key: id(100), sql: "select" }])
    assert.throws(() => views.resolve("execution_topology", filters));
  assert.throws(() => views.resolve("unknown", {}));
  assert.throws(() => views.resolve("successor_lineage", { radius: 1 }));
  assert.deepEqual(views.acceptLineage(lineage()), lineage());
  assert.throws(() => views.acceptLineage({ ...lineage(), scope: { tenant_id: "other", project_id: "other" } }));
  assert.throws(() => views.acceptLineage({ ...lineage(), plan_sha256: id(700) }));
});

test("VIEW-04 scientific views stay unavailable without their owning producers", () => {
  const page = catalog(), views = ViewCatalog.open(page.cut, page);
  for (const view of scientificViews) {
    assert.equal(views.available(view.id), false);
    assert.throws(() => views.resolve(view.id, {}));
  }
  assert.throws(() => ViewCatalog.open({ ...page.cut, revision: 2 }, page));
  assert.throws(() => ViewCatalog.open(page.cut, { ...page, views: [page.views[0]!, page.views[0]!] }));
  assert.throws(() => ViewCatalog.open(page.cut, { ...page, views: [{ ...page.views[0]!, result_bound: 1 }] }));
});
