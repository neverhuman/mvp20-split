import { test } from "node:test";
import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import { dirname, relative, resolve } from "node:path";
import { parse } from "@babel/parser";

test("browser modules import only local boundaries and declared public packages", async () => {
  const root = resolve("src");
  const manifest = JSON.parse(await readFile("package.json", "utf8")) as { dependencies: Record<string, string> };
  async function visit(folder: string) {
    for (const entry of await readdir(folder, { withFileTypes: true })) {
      const path = resolve(folder, entry.name);
      if (entry.isDirectory()) { if (entry.name !== "generated") await visit(path); continue; }
      if (!path.endsWith(".ts")) continue;
      const tree = parse(await readFile(path, "utf8"), { sourceType: "module", plugins: ["typescript"] });
      function record(value: unknown): Record<string, unknown> {
        return value !== null && typeof value === "object" ? value as Record<string, unknown> : {};
      }
      function inspect(value: unknown) {
        if (Array.isArray(value)) { for (const child of value) inspect(child); return; }
        const node = record(value);
        if (node.type === "ImportDeclaration" && typeof record(node.source).value === "string") {
          const value = record(node.source).value as string;
          if (value.startsWith(".")) assert.ok(!relative(root, resolve(dirname(path), value)).startsWith(".."), path);
          else {
            const owner = value.startsWith("@") ? value.split("/").slice(0, 2).join("/") : value.split("/")[0]!;
            assert.ok(owner in manifest.dependencies, `${path}: undeclared/private import ${value}`);
          }
        }
        assert.notEqual(node.type, "ImportExpression", "Dynamic import requires an explicit boundary review");
        if (node.type === "CallExpression") {
          const callee = record(node.callee);
          assert.notEqual(callee.type, "Import", "Dynamic import requires an explicit boundary review");
          if (callee.type === "Identifier") {
            assert.notEqual(callee.name, "require", "Browser source cannot bypass ESM boundary declarations");
            if (callee.name === "fetch") assert.ok(path.includes("transport"), "Only transport owns network requests");
          }
        }
        for (const child of Object.values(node)) if (typeof child === "object" && child !== null) inspect(child);
      }
      inspect(tree);
    }
  }
  await visit(root);
});
