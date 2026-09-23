#!/usr/bin/env bash
# Guarded forensic commit on xbabe2. It never pushes.
set -Eeuo pipefail

CONFIG_FILE=${AMPHORA_AUTOCOMMIT_CONFIG_FILE:-/home/ubuntu/.config/amphora/mvp20-autocommit.env}
if [ -r "$CONFIG_FILE" ]; then
    while IFS='=' read -r config_key config_value; do
        config_key=${config_key%%[[:space:]]*}
        case "$config_key" in
            AMPHORA_SOURCE_REPO|AMPHORA_CONTROLLER_HOST|AMPHORA_CONTROLLER_STATE_ROOT|AMPHORA_AUTOCOMMIT_POLICY|AMPHORA_AUTOCOMMIT_QUARANTINE|AMPHORA_AUTOCOMMIT_LOG)
                if [ -n "$config_key" ] && [ -z "${!config_key+x}" ]; then
                    config_value=${config_value%$'\r'}
                    config_value=${config_value#\"}; config_value=${config_value%\"}
                    config_value=${config_value#\'}; config_value=${config_value%\'}
                    printf -v "$config_key" '%s' "$config_value"
                fi
                ;;
        esac
    done < "$CONFIG_FILE"
fi

REPO=${AMPHORA_SOURCE_REPO:-/home/ubuntu/amphora/build/mvp20-split}
CONTROLLER_HOST=${AMPHORA_CONTROLLER_HOST:-xbabe1}
CONTROLLER_STATE=${AMPHORA_CONTROLLER_STATE_ROOT:-/home/ubuntu/amphora-cron}
POLICY=${AMPHORA_AUTOCOMMIT_POLICY:-/home/ubuntu/.local/libexec/amphora-staged-file-policy.py}
QUARANTINE=${AMPHORA_AUTOCOMMIT_QUARANTINE:-/home/ubuntu/.local/state/amphora/schema-flip-quarantine}
GUARD_LOG=${AMPHORA_AUTOCOMMIT_LOG:-$REPO/logs/autocommit-guard.log}
DRAIN_FILE="$CONTROLLER_STATE/state/AUTOCOMMIT_DRAIN"
TAG="AUTOCOMMIT-$(date -u +%Y%m%dT%H%M%SZ)-$$"

log() { printf '%s %s\n' "$(date -Iseconds)" "$*" >> "$GUARD_LOG"; }

release_drain() {
    ssh -o BatchMode=yes -o ConnectTimeout=15 "$CONTROLLER_HOST" \
        "bash -s -- '$DRAIN_FILE' '$TAG'" <<'REMOTE' >/dev/null 2>&1 || true
set -u
path=$1; tag=$2
if [ -f "$path" ] && [ "$(head -1 "$path")" = "$tag" ]; then
    rm -f -- "$path"
fi
REMOTE
}
trap release_drain EXIT

cd "$REPO"
git diff --cached --quiet || { log "REFUSED pre-existing staged changes"; exit 70; }
[ -x "$POLICY" ] || { log "REFUSED policy missing or not executable: $POLICY"; exit 71; }

# The marker makes every new launcher exit. Existing lanes must then drain and
# every fleet lock must be simultaneously acquirable before local Git mutation.
ssh -o BatchMode=yes -o ConnectTimeout=15 "$CONTROLLER_HOST" \
    "bash -s -- '$DRAIN_FILE' '$TAG'" <<'REMOTE'
set -Eeuo pipefail
path=$1; tag=$2
umask 077
mkdir -p "$(dirname "$path")"
[ ! -e "$path" ] || { printf 'foreign drain exists: %s\n' "$(head -1 "$path")" >&2; exit 73; }
set -C
printf '%s\n' "$tag" > "$path"
REMOTE

drained=0
for _ in $(seq 1 120); do
    if ssh -o BatchMode=yes -o ConnectTimeout=15 "$CONTROLLER_HOST" \
        "bash -s -- '$CONTROLLER_STATE'" <<'REMOTE' >/dev/null 2>&1
set -Eeuo pipefail
root=$1
! pgrep -x claude >/dev/null
! pgrep -f '[/]home/ubuntu/.*/claude-hourly-loop.sh' >/dev/null
for lock in "$root"/state/locks/lane-{1,2,3,4}.lock "$root"/state/locks/fleet.lock "$root"/state/locks/campaign.lock "$root"/state/locks/state.lock; do
    mkdir -p "$(dirname "$lock")"
    exec {fd}>>"$lock"
    flock -n "$fd" || exit 1
done
REMOTE
    then
        drained=1
        break
    fi
    sleep 1
done
[ "$drained" -eq 1 ] || { log "REFUSED fleet did not drain"; exit 74; }

stamp=$(date -u +%Y%m%dT%H%M%SZ)
while IFS= read -r f; do
    git show "HEAD:$f" 2>/dev/null | grep -q execution_passed || continue
    grep -q execution_passed "$f" 2>/dev/null && continue
    destination="$QUARANTINE/$stamp/$f"
    install -D -m 600 "$f" "$destination"
    replacement=$(mktemp)
    git show "HEAD:$f" > "$replacement"
    install -m 600 "$replacement" "$f"
    rm -f -- "$replacement"
    log "QUARANTINED_SCHEMA_FLIP $f -> $destination"
done < <(git ls-files '*/evidence/phase0/benchmark/result.v1.json')

report=$(mktemp)
trap 'rm -f -- "$report"; release_drain' EXIT
if ! "$POLICY" --repo "$REPO" --profile autocommit --source worktree --json > "$report"; then
    log "REFUSED staged-file policy: $(tr '\n' ' ' < "$report")"
    exit 75
fi
"$POLICY" --repo "$REPO" --profile autocommit --source worktree --stage-approved >/dev/null
"$POLICY" --repo "$REPO" --profile autocommit --source staged >/dev/null

if ! git diff --cached --quiet; then
    git -c user.name='Amphora Ops' -c user.email='techie@amphora.bio' \
        commit -qm "autocommit $(date -Iseconds)"
    log "COMMITTED $(git rev-parse HEAD) (never pushed)"
fi
