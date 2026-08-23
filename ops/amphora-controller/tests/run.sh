#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export PYTHONDONTWRITEBYTECODE=1

while IFS= read -r script; do bash -n "$script"; done < <(find "$ROOT" -type f -name '*.sh' -print | sort)
# shellcheck is required, not optional. Skipping it silently meant this suite printed
# ALL SUITES PASSED having linted none of the ~82 KB of shell it is meant to cover,
# including the 73 KB launcher. Set AMPHORA_ALLOW_MISSING_SHELLCHECK=1 to override
# deliberately; the skip is then announced rather than invisible.
if command -v shellcheck >/dev/null; then
    shellcheck "$ROOT/claude-hourly-loop.sh" "$ROOT/mirror-log.sh" \
      "$ROOT/autocommit-guard.sh" "$ROOT/reviewed-snapshot.sh"
elif [ "${AMPHORA_ALLOW_MISSING_SHELLCHECK:-0}" = "1" ]; then
    echo "WARNING: shellcheck absent; 4 shell scripts were NOT linted (override in effect)" >&2
else
    echo "ERROR: shellcheck is required by this suite but is not installed." >&2
    echo "       Install it (apt install shellcheck), or re-run with" >&2
    echo "       AMPHORA_ALLOW_MISSING_SHELLCHECK=1 to accept an unlinted run." >&2
    exit 1
fi
python3 "$ROOT/tests/ast_check.py" "$ROOT"
python3 "$ROOT/tools/check_unbound.py" "$ROOT/claude-hourly-loop.sh"
python3 "$ROOT/tools/campaign_invariants.py" "$ROOT/bootstrap/campaign.json" --json >/dev/null
python3 "$ROOT/tools/directive_coverage.py" --quiet
python3 "$ROOT/tools/recon_invariants.py" --self-test
python3 -m unittest -v "$ROOT/tests/test_ops.py"
bash "$ROOT/tools/tests/run-all.sh"
