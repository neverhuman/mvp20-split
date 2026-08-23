#!/usr/bin/env bash
# Mirror the loop's evidence trail to xbabe2. xbabe1 is the source of truth;
# xbabe2 holds a derived copy.
#
# v2 (lanes): LOCKLESS, deliberately. The old version gated a whole-file rsync
# on flocking the launcher's own lock -- "runs only when no fire is running".
# Under four lanes that lock path goes unheld (rsync would clobber mid-fire
# appends while reading "idle") or, gated on the fleet lock instead, starves
# (*/15 cadence leaves almost no all-idle gaps). Neither is needed: per-lane
# logs are single-writer append-only, whole-file rsync of an append-only file
# is idempotent, and a torn tail self-heals on the next pass. The launcher no
# longer pushes per-fire slices (a shared-window slice duplicated sibling bytes
# up to 4x), so this job is the one log mirror and runs every 10 minutes.
set -Eeuo pipefail

CONFIG_FILE=${AMPHORA_CONFIG_FILE:-/home/ubuntu/.config/amphora/mvp20-cron.env}
if [ -r "$CONFIG_FILE" ]; then
    while IFS='=' read -r config_key config_value; do
        config_key=${config_key%%[[:space:]]*}
        case "$config_key" in
            AMPHORA_STATE_ROOT|AMPHORA_TARGET_HOST|AMPHORA_TARGET_ROOT)
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

STATE_ROOT=${AMPHORA_STATE_ROOT:-/home/ubuntu/amphora-cron}
TARGET_HOST=${AMPHORA_TARGET_HOST:-xbabe2}
TARGET_ROOT=${AMPHORA_TARGET_ROOT:-/home/ubuntu/amphora/build/mvp20-split}
SRC="$STATE_ROOT/logs"
DST="$TARGET_ROOT/logs"
FILES=("$SRC"/./lane-*/claude-hourly-loop.log
       "$SRC"/./fire-summary.jsonl
       "$SRC"/./heartbeat.jsonl)
# The pre-lane combined log is deliberately NOT mirrored: its remote path is
# where mirror_line() APPENDS every live ALERT, and rsyncing the frozen local
# copy over it would erase each alert on the next pass (review finding). The
# frozen local file stays on xbabe1 as history; the remote copy is now the
# alert channel.
rsync -qR --timeout=60 "${FILES[@]}" "$TARGET_HOST:$DST/" 2>/dev/null
exit 0
