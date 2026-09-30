/** Portable module-local Node tests; no shell glob assumptions. */
import { readdir } from "node:fs/promises";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const area = args.find((arg) => arg.startsWith("--area="))?.slice(7);
if (area && !["contracts", "transport", "page_models"].includes(area)) throw new Error("Unknown Studio test area");
const files = [];
async function collect(folder) {
  for (const entry of await readdir(folder, { withFileTypes: true })) {
    const path = resolve(folder, entry.name);
    if (entry.isDirectory()) await collect(path);
    else if (entry.name.endsWith(".test.js")) files.push(path);
  }
}
await collect(resolve(root, "dist/tests", area ?? ""));
if (!files.length) throw new Error("No owned Studio tests found");
const flags = args.includes("--coverage") ? ["--experimental-test-coverage", "--test-coverage-include=**/dist/src/**/*.js"] : [];
const result = spawnSync(process.execPath, ["--test", ...flags, ...files.sort()], { cwd: root, stdio: "inherit", windowsHide: true });
process.exit(result.status ?? 1);
