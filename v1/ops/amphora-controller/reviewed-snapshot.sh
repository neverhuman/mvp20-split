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

SCRIPT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=${AMPHORA_SNAPSHOT_REPO:-$(git -C "$SCRIPT_ROOT" rev-parse --show-toplevel)}
CONTROLLER_ROOT="$REPO/ops/amphora-controller"
CONTROLLER_HOST=${AMPHORA_CONTROLLER_HOST:-xbabe1}
CONTROLLER_CLI=${AMPHORA_CONTROLLER_CLI:-/home/ubuntu/mvp20-split/ops/amphora-controller/bin/amphora}
read -r -a CONTROL_SSH <<< "${AMPHORA_CONTROL_SSH_COMMAND:-ssh -o ConnectTimeout=15 -o BatchMode=yes}"
read -r -a CONTROL_SCP <<< "${AMPHORA_CONTROL_SCP_COMMAND:-scp -o ConnectTimeout=15 -o BatchMode=yes}"
STATE_ROOT=${AMPHORA_STATE_ROOT:-/home/ubuntu/amphora-cron}
SOURCE_ROOT=${AMPHORA_TARGET_ROOT:-/home/ubuntu/amphora/build/mvp20-split}

run_controller() {
    if [ "$(hostname -s)" = "$CONTROLLER_HOST" ]; then
        "$CONTROLLER_CLI" "$@"
    else
        "${CONTROL_SSH[@]}" "$CONTROLLER_HOST" "$CONTROLLER_CLI" "$@"
    fi
}

copy_controller_file() {
    local source=$1 destination=$2
    if [ "$(hostname -s)" = "$CONTROLLER_HOST" ]; then
        install -m 600 "$source" "$destination"
    else
        "${CONTROL_SCP[@]}" -q "$CONTROLLER_HOST:$source" "$destination"
        chmod 600 "$destination"
    fi
}

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

run_controller pause --tag "$TAG" --apply
run_controller drain --timeout 180
if ! git -C "$REPO" diff --quiet || ! git -C "$REPO" diff --cached --quiet; then
    echo 'snapshot repository was dirty before export' >&2
    exit 70
fi

copy_controller_file "$STATE_ROOT/campaign.json" "$REPO/ops/amphora-controller/bootstrap/campaign.json"
copy_controller_file "$STATE_ROOT/data-acquisition-queue.jsonl" "$REPO/ops/amphora-controller/bootstrap/data-acquisition-queue.jsonl"
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
git -C "$REPO" diff --quiet || {
    echo 'snapshot left unstaged worktree changes after export' >&2
    exit 73
}
python3 "$CONTROLLER_ROOT/policy/staged_file_policy.py" --repo "$REPO" --profile publication --source staged
python3 "$CONTROLLER_ROOT/policy/staged_file_policy.py" --repo "$REPO" --profile publication --source tracked

# Both scanners are required for an applied publication. Guarding them with a bare
# `command -v` meant this gate could exit 0 having scanned nothing at all -- the most
# expensive kind of false confidence, since a green publication run is exactly what a
# reviewer trusts. Neither is installed on xbabe1, so run applied publications from a
# host that has them.
MISSING_SCANNERS=""
command -v gitleaks   >/dev/null || MISSING_SCANNERS="$MISSING_SCANNERS gitleaks"
command -v trufflehog >/dev/null || MISSING_SCANNERS="$MISSING_SCANNERS trufflehog"
if [ -n "$MISSING_SCANNERS" ]; then
    echo "ERROR: secret scanners missing:$MISSING_SCANNERS" >&2
    echo "       An applied snapshot must not publish unscanned bytes. Install them, or" >&2
    echo "       run the dry form (no --apply) which does not publish." >&2
    [ "$APPLY" = "1" ] && exit 1
    echo "       (dry run: continuing without a secret scan)" >&2
fi
command -v gitleaks >/dev/null && \
  gitleaks git "$REPO" --staged --config "$REPO/.gitleaks.toml" --redact --no-banner --exit-code 1
command -v gitleaks >/dev/null && \
  gitleaks git "$REPO" --config "$REPO/.gitleaks.toml" --redact --no-banner --exit-code 1
if command -v trufflehog >/dev/null; then
    SCAN_TREE=$(mktemp -d)
    trap 'rm -rf -- "$SCAN_TREE"' EXIT
    git -C "$REPO" checkout-index --all --prefix="$SCAN_TREE/"
    # Scan the exact staged index as a one-commit repository. The filesystem source's
    # content decoder misclassifies four long UTF-8 citation extracts as Brotli and emits
    # read errors while still exiting zero; the Git source scans those same raw blobs fully.
    git -C "$SCAN_TREE" init -q
    git -C "$SCAN_TREE" add -f -A
    git -C "$SCAN_TREE" -c user.name='Amphora Scan' -c user.email='scan@amphora.invalid' \
      commit -qm staged-index
    trufflehog git "file://$SCAN_TREE" --no-update --fail --fail-on-scan-errors
    trufflehog git "file://$REPO" --no-update --fail --fail-on-scan-errors
    rm -rf -- "$SCAN_TREE"
    trap - EXIT
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
if [ "$PUSH" -eq 1 ]; then
    [ "$(git -C "$REPO" branch --show-current)" = main ] || {
        echo '--push requires the reviewed commit to be on local main' >&2
        exit 72
    }
    git -C "$REPO" push origin HEAD:main
fi
