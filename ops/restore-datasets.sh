#!/usr/bin/env bash
# Restore the datasets omitted from this repository, from the canonical xbabe2 tree.
#
# DATASETS.local.json is the inventory: 1,344 paths with size, sha256, and category,
# captured from xbabe2 at git sha 7d85419. Nothing in the repo restored them until now,
# so every runnable CLI command failed on a fresh clone.
#
#   ops/restore-datasets.sh                 # dry run: report what is missing
#   ops/restore-datasets.sh --apply         # fetch, then verify every sha256
#   ops/restore-datasets.sh --apply --only feedback/    # restore one prefix
#
# Requires ssh access to the canonical host and rsync. Verifies every restored file
# against its recorded digest and exits non-zero on any mismatch.
set -Eeuo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
MANIFEST="$REPO_ROOT/DATASETS.local.json"
APPLY=0
ONLY=""

while [ $# -gt 0 ]; do
    case "$1" in
        --apply) APPLY=1 ;;
        --only)  ONLY="${2:-}"; shift ;;
        -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

[ -f "$MANIFEST" ] || { echo "ERROR: $MANIFEST is absent" >&2; exit 1; }

SRC_HOST=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['source']['host'])" "$MANIFEST")
SRC_PATH=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['source']['path'])" "$MANIFEST")
SRC_SHA=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['source']['git_sha'])" "$MANIFEST")

echo "source:  $SRC_HOST:$SRC_PATH  (captured at $SRC_SHA)"

# The capture host may no longer exist. Say so plainly rather than letting a fetch fail
# with a bare ssh error, and point at the archive that replaced it.
if grep -q '"superseded"' "$MANIFEST"; then
    echo "note:    that capture host no longer holds the data -- see source.superseded in"
    echo "         DATASETS.local.json. This run can VERIFY what is present locally but"
    echo "         cannot fetch anything."
fi
echo "target:  $REPO_ROOT"
[ -n "$ONLY" ] && echo "filter:  $ONLY"

# Which inventoried paths are absent locally?
mapfile -t MISSING < <(
    python3 - "$MANIFEST" "$REPO_ROOT" "$ONLY" <<'PY'
import json, os, sys
manifest, root, only = sys.argv[1], sys.argv[2], sys.argv[3]
for row in json.load(open(manifest))["omitted"]:
    p = row["path"]
    if only and not p.startswith(only):
        continue
    if not os.path.exists(os.path.join(root, p)):
        print(p)
PY
)

# Never equate "present" with "verified". This check runs even when there is nothing
# to fetch, and streams large payloads instead of reading multi-gigabyte files at once.
python3 - "$MANIFEST" "$REPO_ROOT" "$ONLY" <<'PY'
import hashlib, json, os, sys
manifest, root, only = sys.argv[1], sys.argv[2], sys.argv[3]
ok = bad = 0
for row in json.load(open(manifest))["omitted"]:
    p = row["path"]
    if only and not p.startswith(only):
        continue
    full = os.path.join(root, p)
    if not os.path.isfile(full):
        continue
    digest = hashlib.sha256()
    with open(full, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    if digest.hexdigest() == row["sha256"]:
        ok += 1
    else:
        bad += 1
        print(f"  MISMATCH {p}\n    expected {row['sha256']}\n    observed {digest.hexdigest()}")
print(f"verified {ok} already-present files, {bad} mismatched")
sys.exit(1 if bad else 0)
PY

if [ "${#MISSING[@]}" -eq 0 ]; then
    echo "nothing to restore: every selected path is present and hash-verified"
    exit 0
fi
echo "missing: ${#MISSING[@]} files"

if [ "$APPLY" != "1" ]; then
    printf '  %s\n' "${MISSING[@]:0:10}"
    [ "${#MISSING[@]}" -gt 10 ] && echo "  ... and $(( ${#MISSING[@]} - 10 )) more"
    echo
    echo "DRY RUN. Re-run with --apply to fetch them."
    exit 0
fi

# Confirm the alias actually resolves to the canonical host before pulling 6 GB from it.
# On xbabe2 itself, `ssh xbabe2` resolves via ~/.ssh/config to an unrelated machine --
# so a bare alias is not enough evidence that we are talking to the right tree.
echo "confirming $SRC_HOST is the canonical host ..."
# The canonical tree is identified by its git HEAD, which DATASETS.local.json records.
# (It has no DATASETS.local.json of its own -- that file is produced by packaging.)
REMOTE_SHA=$(ssh -o BatchMode=yes -o ConnectTimeout=15 "$SRC_HOST" \
    "git -C '$SRC_PATH' rev-parse HEAD 2>/dev/null" 2>/dev/null || echo unreachable)
if [ "$REMOTE_SHA" != "$SRC_SHA" ]; then
    echo "ERROR: $SRC_HOST:$SRC_PATH is not the tree this manifest was captured from." >&2
    echo "       expected HEAD $SRC_SHA" >&2
    echo "       observed      $REMOTE_SHA" >&2
    echo "       If 'observed' is empty or 'unreachable', the '$SRC_HOST' ssh alias is not" >&2
    echo "       resolving to the canonical host -- run from a host with explicitly" >&2
    echo "       provisioned xbabe2 access. Decommissioned xbabe1 intentionally lacks it." >&2
    echo "       If it is a different sha, the canonical tree has moved on; the digests in" >&2
    echo "       DATASETS.local.json may no longer match. Regenerate the manifest first." >&2
    exit 1
fi
echo "  HEAD $REMOTE_SHA matches the manifest"

echo "fetching from $SRC_HOST ..."
printf '%s\n' "${MISSING[@]}" \
  | rsync -a --files-from=- "$SRC_HOST:$SRC_PATH/" "$REPO_ROOT/"

echo "verifying digests ..."
python3 - "$MANIFEST" "$REPO_ROOT" "$ONLY" <<'PY'
import hashlib, json, os, sys
manifest, root, only = sys.argv[1], sys.argv[2], sys.argv[3]
ok = bad = absent = 0
for row in json.load(open(manifest))["omitted"]:
    p = row["path"]
    if only and not p.startswith(only):
        continue
    full = os.path.join(root, p)
    if not os.path.exists(full):
        absent += 1
        print(f"  ABSENT   {p}")
        continue
    digest_state = hashlib.sha256()
    with open(full, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest_state.update(chunk)
    digest = digest_state.hexdigest()
    if digest == row["sha256"]:
        ok += 1
    else:
        bad += 1
        print(f"  MISMATCH {p}\n    expected {row['sha256']}\n    observed {digest}")
print(f"verified {ok} ok, {bad} mismatched, {absent} still absent")
sys.exit(1 if (bad or absent) else 0)
PY

echo "restore complete. The CLI commands in BUILD.md will now run."
