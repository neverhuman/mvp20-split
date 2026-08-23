#!/usr/bin/env bash
# Export a reviewed frozen state. Default is a no-write plan.
set -Eeuo pipefail

APPLY=0; REVIEW=0; COMMIT=0; PUSH=0; TAG=""; REVIEWED_SHA=""
while [ "$#" -gt 0 ]; do
    case "$1" in
      --apply) APPLY=1 ;;
      --review) REVIEW=1 ;;
      --commit) COMMIT=1 ;;
      --push) PUSH=1 ;;
      --tag) TAG=${2:?}; shift ;;
      --reviewed-diff-sha256) REVIEWED_SHA=${2:?}; shift ;;
      *) printf 'unknown argument: %s\n' "$1" >&2; exit 64 ;;
    esac
    shift
done

CONTROLLER_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=${AMPHORA_SNAPSHOT_REPO:-$(git -C "$CONTROLLER_ROOT" rev-parse --show-toplevel)}
CLI="$CONTROLLER_ROOT/bin/amphora"
STATE_ROOT=${AMPHORA_STATE_ROOT:-/home/ubuntu/amphora-cron}
SOURCE_ROOT=${AMPHORA_TARGET_ROOT:-/home/ubuntu/amphora/build/mvp20-split}

if [ "$APPLY" -eq 0 ]; then
    printf '%s\n' 'DRY-RUN reviewed snapshot:' \
      '  1. create/verify the owned hard stop and drain all lanes' \
      '  2. export campaign, acquisition queue, and chain checkpoint' \
      '  3. regenerate DATASETS.local.json and OPERATIONS.local.json' \
      '  4. apply staged-file and secret-scan policies' \
      '  5. print the exact diff hash for human review' \
      '  6. commit only with --commit and push only with --push'
    exit 0
fi
[ -n "$TAG" ] || { echo '--apply requires --tag' >&2; exit 64; }
[ "$REVIEW" -eq 1 ] || { echo '--apply requires --review' >&2; exit 64; }
[ "$COMMIT" -eq 1 ] || [ "$PUSH" -eq 0 ] || { echo '--push requires --commit' >&2; exit 64; }

"$CLI" pause --tag "$TAG" --apply
"$CLI" drain --timeout 180
if ! git -C "$REPO" diff --quiet || ! git -C "$REPO" diff --cached --quiet; then
    echo 'snapshot repository was dirty before export' >&2
    exit 70
fi

install -m 600 "$STATE_ROOT/campaign.json" "$REPO/ops/amphora-controller/bootstrap/campaign.json"
install -m 600 "$STATE_ROOT/data-acquisition-queue.jsonl" "$REPO/ops/amphora-controller/bootstrap/data-acquisition-queue.jsonl"
SOURCE_SHA=$(git -C "$SOURCE_ROOT" rev-parse HEAD)
SOURCE_HISTORY_COMMITS=$(git -C "$SOURCE_ROOT" rev-list --count HEAD)
CAPTURED_AT=$(date -Iseconds)
python3 "$CONTROLLER_ROOT/tools/regenerate_datasets_manifest.py" \
  --manifest "$REPO/DATASETS.local.json" --source-root "$SOURCE_ROOT" \
  --source-sha "$SOURCE_SHA" --captured-at "$CAPTURED_AT"
python3 "$CONTROLLER_ROOT/tools/regenerate_operations_manifest.py" \
  --repo "$REPO" --source-sha "$SOURCE_SHA" \
  --source-history-commits "$SOURCE_HISTORY_COMMITS" --captured-at "$CAPTURED_AT" \
  --legacy-archive /home/ubuntu/amphora-archive/cron-legacy-20260823T031711Z
python3 "$CONTROLLER_ROOT/tools/controller_tree_manifest.py" generate --root "$CONTROLLER_ROOT"

git -C "$REPO" add -- DATASETS.local.json OPERATIONS.local.json ops/amphora-controller/bootstrap \
  ops/amphora-controller/controller-tree.sha256
python3 "$CONTROLLER_ROOT/policy/staged_file_policy.py" --repo "$REPO" --profile publication --source staged

if command -v gitleaks >/dev/null; then
    gitleaks git "$REPO" --redact --no-banner --exit-code 1
fi
if command -v trufflehog >/dev/null; then
    trufflehog git "file://$REPO" --no-update --fail --only-verified
fi

git -C "$REPO" diff --cached --stat
DIFF_SHA=$(git -C "$REPO" diff --cached --binary | sha256sum | cut -d' ' -f1)
printf 'review_diff_sha256=%s\n' "$DIFF_SHA"
if [ "$COMMIT" -eq 0 ]; then
    printf '%s\n' 'review complete; nothing committed or pushed'
    exit 0
fi
[ "$REVIEWED_SHA" = "$DIFF_SHA" ] || { echo 'reviewed diff hash mismatch or absent' >&2; exit 71; }
git -C "$REPO" -c user.name='Amphora Ops' -c user.email='techie@amphora.bio' \
  commit -m "Reviewed Amphora state snapshot $CAPTURED_AT"
[ "$PUSH" -eq 1 ] && git -C "$REPO" push origin main
