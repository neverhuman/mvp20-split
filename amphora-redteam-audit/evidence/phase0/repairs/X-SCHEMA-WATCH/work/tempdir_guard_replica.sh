#!/bin/bash
# Verbatim logic of /home/ubuntu/amphora-autocommit-guard.sh, cd retargeted to
# the tempdir simulation repo instead of the real mvp20-split tree.
cd /tmp/schema-watch-sim || exit 1
GUARD_LOG=logs/autocommit-guard.log
for f in $(git ls-files "*/evidence/phase0/benchmark/result.v1.json" 2>/dev/null); do
  git show "HEAD:$f" 2>/dev/null | grep -q execution_passed || continue   # HEAD is runtime-shape?
  grep -q execution_passed "$f" 2>/dev/null && continue                    # worktree still runtime-shape?
  git checkout -- "$f" && echo "$(date -Iseconds) RESTORED_SCHEMA_FLIP $f" >> "$GUARD_LOG"
done
git add -A
git diff --cached --quiet || git commit -qm "autocommit $(date -Iseconds)"
