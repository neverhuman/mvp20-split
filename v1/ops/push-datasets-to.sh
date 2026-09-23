#!/usr/bin/env bash
# Push the omitted datasets from the canonical tree to a target host.
#
# The companion to ops/restore-datasets.sh. That script PULLS, which requires the target
# to be able to reach the canonical host. A decommissioned handoff host deliberately
# cannot, so the transfer has to be driven from the canonical side instead.
#
# Both scripts read the same DATASETS.local.json inventory, so push and pull cannot
# disagree about where the data boundary is.
#
#   ops/push-datasets-to.sh xbabe1                      # dry run: what would transfer
#   ops/push-datasets-to.sh xbabe1 --apply              # transfer, then verify every sha256
#   ops/push-datasets-to.sh xbabe1 --apply --only feedback/
#
# Run this ON the canonical host. Verifies every digest on the RECEIVING side after
# transfer and exits non-zero on any mismatch.
#
# DO NOT also copy `.amphora/`. Its run archives carry provenance hashes computed against
# the canonical tree's content. Transplanted onto the filtered handoff tree they fail the
# integrity check and the engine refuses to run at all:
#     Error: run archive integrity error: provenance hash mismatch
# That is the engine working correctly. A handoff host builds its own `.amphora/` from its
# own runs; the canonical receipts stay on the canonical host.
set -Eeuo pipefail

CANONICAL_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TARGET_HOST=""
TARGET_ROOT="/home/ubuntu/mvp20-split"
APPLY=0
ONLY=""

while [ $# -gt 0 ]; do
    case "$1" in
        --apply)       APPLY=1 ;;
        --only)        ONLY="${2:-}"; shift ;;
        --target-root) TARGET_ROOT="${2:-}"; shift ;;
        -h|--help)     sed -n '2,17p' "$0"; exit 0 ;;
        -*)            echo "unknown argument: $1" >&2; exit 2 ;;
        *)             TARGET_HOST="$1" ;;
    esac
    shift
done

[ -n "$TARGET_HOST" ] || { echo "ERROR: name a target host, e.g. $0 xbabe1" >&2; exit 2; }

# The manifest lives in the published repo, not the canonical tree. Find it.
MANIFEST=""
for c in "$CANONICAL_ROOT/DATASETS.local.json" \
         "/home/ubuntu/amphora/build/mvp20-split-github/DATASETS.local.json"; do
    [ -f "$c" ] && { MANIFEST="$c"; break; }
done
[ -n "$MANIFEST" ] || { echo "ERROR: DATASETS.local.json not found" >&2; exit 1; }

SRC_PATH=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['source']['path'])" "$MANIFEST")
SRC_SHA=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['source']['git_sha'])" "$MANIFEST")

echo "manifest: $MANIFEST"
echo "source:   $SRC_PATH (local, must be at $SRC_SHA)"
echo "target:   $TARGET_HOST:$TARGET_ROOT"
[ -n "$ONLY" ] && echo "filter:   $ONLY"

# Refuse to ship bytes from a tree that is not the one the manifest describes.
LOCAL_SHA=$(git -C "$SRC_PATH" rev-parse HEAD 2>/dev/null || echo unknown)
if [ "$LOCAL_SHA" != "$SRC_SHA" ]; then
    echo "ERROR: $SRC_PATH is at $LOCAL_SHA, manifest was captured at $SRC_SHA." >&2
    echo "       The digests in the manifest may no longer describe this tree." >&2
    exit 1
fi
echo "  canonical HEAD matches the manifest"

# What the target is missing. Ask the target, not ourselves.
mapfile -t WANT < <(
    python3 - "$MANIFEST" "$ONLY" <<'PY'
import json, sys
manifest, only = sys.argv[1], sys.argv[2]
for row in json.load(open(manifest))["omitted"]:
    p = row["path"]
    if only and not p.startswith(only):
        continue
    print(p)
PY
)
echo "  inventory selects ${#WANT[@]} files"

if [ "$APPLY" != "1" ]; then
    printf '%s\n' "${WANT[@]:0:8}" | sed 's/^/    /'
    [ "${#WANT[@]}" -gt 8 ] && echo "    ... and $(( ${#WANT[@]} - 8 )) more"
    echo
    echo "DRY RUN. Re-run with --apply to transfer."
    exit 0
fi

echo "transferring ..."
printf '%s\n' "${WANT[@]}" \
  | rsync -a --info=progress2 --files-from=- "$SRC_PATH/" "$TARGET_HOST:$TARGET_ROOT/"

echo "verifying digests on $TARGET_HOST ..."
python3 - "$MANIFEST" "$ONLY" > /tmp/.push-expect.$$ <<'PY'
import json, sys
manifest, only = sys.argv[1], sys.argv[2]
for row in json.load(open(manifest))["omitted"]:
    p = row["path"]
    if only and not p.startswith(only):
        continue
    print(f"{row['sha256']}  {p}")
PY
scp -q /tmp/.push-expect.$$ "$TARGET_HOST:/tmp/.push-expect.$$"
rm -f /tmp/.push-expect.$$

ssh "$TARGET_HOST" "TARGET_ROOT='$TARGET_ROOT' EXPECT='/tmp/.push-expect.$$' python3 - " <<'PY'
import hashlib, os, sys
root = os.environ["TARGET_ROOT"]
expect = os.environ["EXPECT"]
ok = bad = absent = 0
for line in open(expect):
    digest, path = line.rstrip("\n").split("  ", 1)
    full = os.path.join(root, path)
    if not os.path.isfile(full):
        absent += 1
        print(f"  ABSENT   {path}")
        continue
    h = hashlib.sha256()
    with open(full, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() == digest:
        ok += 1
    else:
        bad += 1
        print(f"  MISMATCH {path}\n    expected {digest}\n    observed {h.hexdigest()}")
print(f"verified {ok} ok, {bad} mismatched, {absent} absent")
sys.exit(1 if (bad or absent) else 0)
PY
rc=$?
ssh "$TARGET_HOST" "rm -f '/tmp/.push-expect.$$'" 2>/dev/null || true
[ "$rc" -eq 0 ] || { echo "ERROR: verification failed on $TARGET_HOST" >&2; exit 1; }
echo "push complete and verified."
