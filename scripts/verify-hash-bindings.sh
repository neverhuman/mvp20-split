#!/usr/bin/env bash
# Verify that every SHA-256 recorded in the tree still resolves to a file with that hash.
#
# `xtask audit` checks the DECLARED inventory (config/module-evidence-inventory.json).
# Nothing checked the thousands of digests embedded across evidence, benchmark, and report
# artifacts -- fields like `frozen_*_script_sha256`, `observed_sha256`, `declared_sha256`,
# and bundle artifact maps. A one-word edit to a comment in a pinned script silently breaks
# such a binding, which is exactly what happened on 2026-08-23 to
# analyze_st19168_preregistered.py. This is the gate that would have caught it.
#
#   scripts/verify-hash-bindings.sh            # report and exit non-zero on any break
#   scripts/verify-hash-bindings.sh --quiet    # summary only
set -Eeuo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUIET=0
[ "${1:-}" = "--quiet" ] && QUIET=1

python3 - "$QUIET" <<'PY'
import hashlib, json, os, re, subprocess, sys

quiet = sys.argv[1] == "1"
tracked = set(subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split())

# Fields whose value is a sha256 of a file named by a sibling field, or of a path key.
PATH_HASH_FIELDS = ("sha256", "observed_sha256", "declared_sha256", "sha256sum")
digest_re = re.compile(r"^[0-9a-f]{64}$")
cache = {}

def file_hash(path):
    if path not in cache:
        try:
            with open(path, "rb") as fh:
                cache[path] = hashlib.sha256(fh.read()).hexdigest()
        except OSError:
            cache[path] = None
    return cache[path]

checked = ok = broken = skipped = 0
breaks = []

def check(path_value, digest, source, field):
    global checked, ok, broken, skipped
    if not isinstance(path_value, str) or not isinstance(digest, str):
        return
    if not digest_re.match(digest):
        return
    # resolve relative to repo root, then to the source file's module root
    for cand in (path_value, os.path.join(source.split("/")[0], path_value)):
        if os.path.isfile(cand):
            checked += 1
            actual = file_hash(cand)
            if actual == digest:
                ok += 1
            else:
                broken += 1
                breaks.append((source, field, cand, digest, actual))
            return
    skipped += 1   # target absent (omitted dataset, or path not resolvable) -- not a break

def walk(node, source, parent_path=None):
    if isinstance(node, dict):
        # {"path": ..., "sha256": ...} shape
        p = node.get("path") or node.get("module_relative_path") or node.get("file")
        for f in PATH_HASH_FIELDS:
            if p and f in node:
                check(p, node[f], source, f)
        # {"<path>": "<sha256>"} map shape, e.g. bundle artifact maps
        for k, v in node.items():
            if isinstance(v, str) and digest_re.match(v) and ("/" in k or k.endswith(".json")):
                check(k, v, source, k)
            walk(v, source, k)
    elif isinstance(node, list):
        for v in node:
            walk(v, source, parent_path)

for path in sorted(tracked):
    if not path.endswith(".json"):
        continue
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except Exception:
        continue
    walk(doc, path)

if breaks and not quiet:
    for source, field, target, declared, actual in breaks:
        print(f"BROKEN  {target}")
        print(f"        recorded in {source} ({field})")
        print(f"        declared {declared}")
        print(f"        actual   {actual}")
print(f"hash bindings: {ok} ok, {broken} broken, {skipped} unresolvable/absent "
      f"({checked} resolved of {ok + broken + skipped} candidates)")

# A ratchet, not a zero target. Many recorded digests live in DATED point-in-time
# snapshots (reports/founder-readiness-brief-2026-07-19/evidence-snapshot.json and
# similar) which are SUPPOSED to diverge as the live docs move on -- the project even
# runs audits named mission-hash-provenance-staleness-v1 tracking exactly that. What
# must never happen is the count going UP, which is what an accidental edit to a frozen
# artifact looks like.
# Raising this is legitimate ONLY when a reviewed source change makes a point-in-time
# record legitimately stale -- e.g. landing a fix to amphora-engine/src/lib.rs moves its
# hash, and older evidence/audit/*/diagnostic.*.json recorded the pre-fix value. Those
# are historical records of what was audited THEN; rewriting them would be evidence
# tampering. Raising it to paper over an accidental edit to a frozen artifact is not
# legitimate -- revert instead.
#
#   452  after the 2026-08-23 handoff preparation (down from 558; six deleted evidence
#        snapshots restored and four wrongly-edited frozen artifacts reverted)
#   458  after landing R1 (T-01B) on amphora-engine/src/lib.rs and amphora-core/src/lib.rs.
#        The six are those two files' pre-fix hashes inside the frozen
#        eight-vector-facts-injection-v1 and normalized-molecule-consumer-sweep-v1 audit
#        diagnostics, which recorded the engine as it was when those probes ran.
BASELINE = 458
if broken > BASELINE:
    print(f"REGRESSION: {broken - BASELINE} new broken binding(s) above the {BASELINE} baseline.",
          file=sys.stderr)
    print("Something edited a pinned file. Revert it -- do not raise the baseline unless a",
          file=sys.stderr)
    print("reviewed source change legitimately staled a point-in-time record (see above).",
          file=sys.stderr)
    sys.exit(1)
if broken < BASELINE:
    print(f"improved: {BASELINE - broken} fewer than the {BASELINE} baseline -- "
          f"lower the BASELINE in this script to lock the gain in.")
sys.exit(0)
PY
