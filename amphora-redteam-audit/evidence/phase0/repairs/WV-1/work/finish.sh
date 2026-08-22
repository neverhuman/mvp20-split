#!/usr/bin/env bash
# WV-1 finish: canonical acceptance, then publish the log.
# The log is written OUTSIDE the repository: phase0::tests::
# source_ledger_historical_movement_and_status_are_read_only hashes the whole
# worktree, so a log growing inside it would fail that test by its own presence.
set -u
ROOT=/home/ubuntu/amphora/build/mvp20-split
WORK="$ROOT/amphora-redteam-audit/evidence/phase0/repairs/WV-1/work"
LOG=/home/ubuntu/wv1-acceptance-2026-08-04.log
P=/home/ubuntu/.local/share/amphora/rdkit-2026.03.2
export RDKIT_INCLUDE_DIR=$P/include/rdkit RDKIT_LIB_DIR=$P/lib BOOST_INCLUDE_DIR=$P/include LD_LIBRARY_PATH=$P/lib
cd "$ROOT"
rm -f "$WORK/acceptance-2026-08-04.log"

echo "== canonical acceptance =="
flock -w 300 .cron.lock ~/.cargo/bin/cargo test --workspace --locked --features rdkit > "$LOG" 2>&1
RC=$?
echo "acceptance exit=$RC"
cp "$LOG" "$WORK/acceptance-2026-08-04.log"
python3 "$WORK/summarize_acceptance.py" "$WORK/acceptance-2026-08-04.log" "$RC" \
    > "$WORK/acceptance-summary.json"
cat "$WORK/acceptance-summary.json"

echo "== git status on the shipped benchmark results =="
git status --porcelain -- '*/evidence/phase0/benchmark/result.v1.json' > "$WORK/git-status-results.txt"
echo "result_pathspec_lines=$(wc -l < "$WORK/git-status-results.txt")"

echo "FINISH_DONE rc=$RC"
