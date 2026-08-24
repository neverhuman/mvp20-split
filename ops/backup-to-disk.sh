#!/usr/bin/env bash
# Back this host up to a locally-mounted disk.
#
# xbabe1 is the only place Amphora exists. It holds the 473-commit canonical history, the
# only evaluator signing seed, the 6.20 GB dataset inventory and the 40 GB NOMAD corpus,
# and none of it is on any remote. This script puts a verified copy on a second disk.
#
#   ops/backup-to-disk.sh --list                     # what would be copied, and how big
#   ops/backup-to-disk.sh /mnt/amphora-backup        # dry run against a real destination
#   ops/backup-to-disk.sh /mnt/amphora-backup --apply
#
# What this does and does not buy you: a second disk in the same chassis protects against
# disk failure and against an accidental deletion. It does NOT protect against losing the
# machine -- theft, fire, a dead motherboard. Getting a copy onto separate hardware is
# still worth doing, and ops/push-datasets-to.sh is the tool for seeding that host.
#
# FILESYSTEM MATTERS. The tree relies on Unix permissions (ops/amphora-controller is mode
# 0555) and on symlinks, and it contains a git object store. exFAT and FAT preserve none of
# those. On such a filesystem this script refuses to rsync and writes tar archives instead,
# which carry modes and symlinks inside the archive. ext4 gets a plain mirrored tree.
set -Eeuo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
DEST=""
APPLY=0
LIST=0

while [ $# -gt 0 ]; do
    case "$1" in
        --apply)   APPLY=1 ;;
        --list)    LIST=1 ;;
        -h|--help) sed -n '2,21p' "$0"; exit 0 ;;
        -*)        echo "unknown argument: $1" >&2; exit 2 ;;
        *)         DEST="$1" ;;
    esac
    shift
done

# What gets copied. Each entry is "label:absolute-source". Everything here is either
# irreplaceable or expensive to regenerate; nothing here is on a remote.
ITEMS=(
    # canonical-history.git is inside legacy/, but it gets its own entry so the verify step
    # can open it as a repository. legacy-archive excludes it to avoid writing 188 MB twice.
    "canonical-history:$ROOT/legacy/canonical-history.git"
    "legacy-archive:$ROOT/legacy"
    "datasets-and-state:$ROOT/state"
    "control-plane:$ROOT/.amphora"
    "seeds-and-rdkit:/home/ubuntu/.local/share/amphora"
    "host-config:/home/ubuntu/.config/amphora"
)
# feedback/ and artifacts/ are the DATASETS.local.json payloads; they live in the repo tree.
for d in feedback artifacts; do
    [ -d "$ROOT/$d" ] && ITEMS+=("datasets-$d:$ROOT/$d")
done

if [ "$LIST" = 1 ] || [ -z "$DEST" ]; then
    echo "would back up:"
    total=0
    for e in "${ITEMS[@]}"; do
        label=${e%%:*}; src=${e#*:}
        if [ -e "$src" ]; then
            sz=$(du -sm "$src" 2>/dev/null | cut -f1)
            total=$((total + sz))
            printf "  %-20s %8s MB  %s\n" "$label" "$sz" "$src"
        else
            printf "  %-20s %8s      %s\n" "$label" "absent" "$src"
        fi
    done
    echo "  ----"
    printf "  %-20s %8s MB\n" "total" "$total"
    [ -z "$DEST" ] && { echo; echo "name a destination to go further, e.g. $0 /mnt/amphora-backup"; exit 0; }
fi

[ -d "$DEST" ] || { echo "ERROR: destination is not a mounted directory: $DEST" >&2; exit 2; }

# Detect the destination filesystem. exFAT/FAT cannot hold modes, symlinks or hardlinks,
# so a plain rsync there would silently produce an unrestorable copy.
FSTYPE=$(df --output=fstype "$DEST" 2>/dev/null | tail -1 | tr -d ' ')
case "$FSTYPE" in
    exfat|vfat|msdos|ntfs) MODE="tar" ;;
    *)                     MODE="tree" ;;
esac
echo "destination: $DEST  (fstype=$FSTYPE -> $MODE)"
[ "$MODE" = "tar" ] && echo "note:    $FSTYPE cannot store Unix permissions or symlinks; writing tar archives instead."

FREE_MB=$(df -Pm "$DEST" | tail -1 | awk '{print $4}')
NEED_MB=0
for e in "${ITEMS[@]}"; do
    label=${e%%:*}; src=${e#*:}
    [ -e "$src" ] || continue
    if [ "$label" = "legacy-archive" ]; then
        NEED_MB=$((NEED_MB + $(du -sm --exclude=canonical-history.git "$src" 2>/dev/null | cut -f1)))
    else
        NEED_MB=$((NEED_MB + $(du -sm "$src" 2>/dev/null | cut -f1)))
    fi
done
echo "space:       need ~${NEED_MB} MB, have ${FREE_MB} MB free"
[ "$FREE_MB" -gt "$NEED_MB" ] || { echo "ERROR: not enough free space on $DEST" >&2; exit 1; }

if [ "$APPLY" != 1 ]; then
    echo
    echo "DRY RUN. Re-run with --apply to write."
    exit 0
fi

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$DEST/amphora-backup-$STAMP"
mkdir -p "$OUT"
echo "writing to $OUT"

fail=0
for e in "${ITEMS[@]}"; do
    label=${e%%:*}; src=${e#*:}
    [ -e "$src" ] || { echo "  skip     $label (absent)"; continue; }
    if [ "$MODE" = "tar" ]; then
        # -p keeps modes, and tar records symlinks as symlinks regardless of the destination fs.
        ex=()
        [ "$label" = "legacy-archive" ] && ex=(--exclude canonical-history.git)
        if tar -cf "$OUT/$label.tar" "${ex[@]}" -C "$(dirname "$src")" "$(basename "$src")" 2>/dev/null; then
            echo "  wrote    $label.tar"
        else
            echo "  FAILED   $label"; fail=1
        fi
    else
        mkdir -p "$OUT/$label"
        ex=()
        [ "$label" = "legacy-archive" ] && ex=(--exclude canonical-history.git)
        if rsync -aHAX --numeric-ids --delete "${ex[@]}" "$src/" "$OUT/$label/" >/dev/null 2>&1; then
            echo "  copied   $label"
        else
            echo "  FAILED   $label"; fail=1
        fi
    fi
done
[ "$fail" -eq 0 ] || { echo "ERROR: at least one item failed to copy; backup is INCOMPLETE" >&2; exit 1; }

# Verification. A backup nobody has restored from is a hypothesis, so check the thing that
# matters most -- that the canonical history is readable and complete at the destination.
echo
echo "verifying:"
if [ "$MODE" = "tree" ] && [ -d "$OUT/canonical-history" ]; then
    n=$(git -C "$OUT/canonical-history" rev-list --count --all 2>/dev/null || echo 0)
    m=$(git -C "$ROOT/legacy/canonical-history.git" rev-list --count --all 2>/dev/null || echo 0)
    if [ "$n" -gt 0 ] && [ "$n" = "$m" ]; then
        echo "  history  $n commits, matches source"
    else
        echo "  HISTORY MISMATCH: backup=$n source=$m" >&2; exit 1
    fi
    if git -C "$OUT/canonical-history" fsck --connectivity-only >/dev/null 2>&1; then
        echo "  fsck     clean"
    else
        echo "  FSCK FAILED" >&2; exit 1
    fi
else
    # "The tar lists" is not the same as "the history survived". Extract it and open it as a
    # repository, which is the only check that would have caught a truncated object store.
    TMP=$(mktemp -d)
    trap 'rm -rf "$TMP"' EXIT
    if ! tar -xf "$OUT/canonical-history.tar" -C "$TMP" 2>/dev/null; then
        echo "  ARCHIVE UNREADABLE" >&2; exit 1
    fi
    n=$(git -C "$TMP/canonical-history.git" rev-list --count --all 2>/dev/null || echo 0)
    m=$(git -C "$ROOT/legacy/canonical-history.git" rev-list --count --all 2>/dev/null || echo 0)
    if [ "$n" -gt 0 ] && [ "$n" = "$m" ]; then
        echo "  history  $n commits restored from the archive, matches source"
    else
        echo "  HISTORY MISMATCH: backup=$n source=$m" >&2; exit 1
    fi
    if git -C "$TMP/canonical-history.git" fsck --connectivity-only >/dev/null 2>&1; then
        echo "  fsck     clean"
    else
        echo "  FSCK FAILED" >&2; exit 1
    fi
    rm -rf "$TMP"; trap - EXIT
fi

# Hash a sample of the dataset payloads against the manifest they were inventoried with.
if [ -f "$ROOT/DATASETS.local.json" ]; then
    python3 - "$ROOT" "$OUT" "$MODE" <<'PY'
import hashlib, json, os, subprocess, sys
root, out, mode = sys.argv[1], sys.argv[2], sys.argv[3]
inv = json.load(open(os.path.join(root, "DATASETS.local.json")))["omitted"]

def digest_tree(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def digest_tar(archive, member):
    # Stream the member out of the archive rather than extracting it. A backup that is
    # never read back is a hypothesis; this reads it back.
    r = subprocess.run(["tar", "-xOf", archive, member], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        return None
    return hashlib.sha256(r.stdout).hexdigest()

checked = bad = 0
for e in inv:
    p = e.get("path") or ""
    top = p.split("/", 1)[0]
    if mode == "tree":
        dst = os.path.join(out, "datasets-" + top, p.split("/", 1)[1] if "/" in p else p)
        if not os.path.exists(dst):
            continue
        got = digest_tree(dst)
    else:
        archive = os.path.join(out, "datasets-" + top + ".tar")
        if not os.path.exists(archive):
            continue
        got = digest_tar(archive, p)
        if got is None:
            continue
    checked += 1
    if got != e.get("sha256"):
        bad += 1
        print("  MISMATCH", p)
    if checked >= 12:
        break
print(f"  datasets {checked} sampled from the backup, {bad} mismatched")
raise SystemExit(1 if bad else 0)
PY
fi

echo
echo "backup complete: $OUT"
echo "This protects against disk failure and accidental deletion on this machine."
echo "It does NOT protect against losing the machine. Get a copy onto separate hardware."
