#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export PYTHONDONTWRITEBYTECODE=1

while IFS= read -r script; do bash -n "$script"; done < <(find "$ROOT" -type f -name '*.sh' -print | sort)
if command -v shellcheck >/dev/null; then
    shellcheck "$ROOT/claude-hourly-loop.sh" "$ROOT/mirror-log.sh" \
      "$ROOT/autocommit-guard.sh" "$ROOT/reviewed-snapshot.sh"
fi
python3 "$ROOT/tests/ast_check.py" "$ROOT"
python3 "$ROOT/tools/check_unbound.py" "$ROOT/claude-hourly-loop.sh"
python3 "$ROOT/tools/campaign_invariants.py" "$ROOT/bootstrap/campaign.json" --json >/dev/null
python3 "$ROOT/tools/directive_coverage.py" --quiet
python3 "$ROOT/tools/recon_invariants.py" --self-test
python3 -m unittest -v "$ROOT/tests/test_ops.py"
bash "$ROOT/tools/tests/run-all.sh"
