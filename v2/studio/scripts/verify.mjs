/** Public entrypoint shared by npm and the repository's owned-suite dispatcher. */
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
for (const args of [["scripts/generate-contracts.mjs", "--check"], ["scripts/scientific-validators.mjs", "--check"],
  ["node_modules/typescript/bin/tsc", "-p", "tsconfig.json"], ["scripts/test.mjs", ...process.argv.slice(2)]]) {
  const result = spawnSync(process.execPath, args, { cwd: root, stdio: "inherit", windowsHide: true });
  if (result.status !== 0) process.exit(result.status ?? 1);
}
