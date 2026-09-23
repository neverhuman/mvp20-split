#!/usr/bin/env bash
# WV-1 dry-run sweep: `portfolio phase0 re-evaluate --dry-run` for every module
# whose shipped benchmark result is unbound from its signed evaluation receipt.
# Writes nothing to the repository (the dry run is wrapped in prove_read_only).
set -u
ROOT=/home/ubuntu/amphora/build/mvp20-split
# Outputs land OUTSIDE the repository: a dry run proves it changed nothing, and
# redirecting its own report into the worktree would break that proof.
WORK=/home/ubuntu/wv1-dryrun-out
BIN="$ROOT/target/debug/amphora-tui"
KEY=/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed
REVIEWS=/home/ubuntu/wv1-dryrun-reviews
P=/home/ubuntu/.local/share/amphora/rdkit-2026.03.2
export LD_LIBRARY_PATH=$P/lib
AS_OF=2026-08-04T00:00:00Z
REASON="WV-1 governed re-evaluation: the shipped evidence/phase0/benchmark/result.v1.json no longer hashes to metrics.benchmark_result_sha256 in this module's own signed Phase-0 evaluation receipt (repair B2 collateral damage); the evaluated bytes are unrecoverable."

MODULES="amphora-cro-protocol-packager amphora-evidence-intake-validator amphora-known-answer-benchmarks amphora-molecule-design-gate amphora-molecule-property amphora-optimizer-orchestrator amphora-redteam-audit amphora-report-packager amphora-source-ledger"

mkdir -p "$WORK/dry-run"
for M in $MODULES; do
  REVIEW="$REVIEWS/$M.review.v1.dsse.json"
  if [ ! -f "$REVIEW" ]; then
    # amphora-molecule-property has no independent-review receipt at all. Supply
    # another module's review so the refusal is recorded verbatim rather than
    # fabricating a review claim.
    REVIEW="$REVIEWS/amphora-source-ledger.review.v1.dsse.json"
  fi
  echo "### $M (review=$REVIEW)"
  cd "$ROOT" || exit 1
  "$BIN" portfolio phase0 re-evaluate \
      --module "$M" --reason "$REASON" --as-of "$AS_OF" \
      --evaluation-key "$KEY" --review "$REVIEW" --dry-run \
      > "$WORK/dry-run/$M.json" 2> "$WORK/dry-run/$M.err"
  echo "exit=$?"
  head -c 400 "$WORK/dry-run/$M.err"
  echo
done

# Also record one negative control: a module with an INTACT binding must be refused.
cd "$ROOT" || exit 1
"$BIN" portfolio phase0 re-evaluate \
    --module amphora-solvency-score --reason "$REASON" --as-of "$AS_OF" \
    --evaluation-key "$KEY" --review "$REVIEWS/amphora-source-ledger.review.v1.dsse.json" --dry-run \
    > "$WORK/dry-run/NEGATIVE-CONTROL-amphora-solvency-score.json" \
    2> "$WORK/dry-run/NEGATIVE-CONTROL-amphora-solvency-score.err"
echo "negative control exit=$?"
cat "$WORK/dry-run/NEGATIVE-CONTROL-amphora-solvency-score.err"

# And a repository-local key must be refused even for a repairable module.
# A dummy 32-byte file is enough: load_signing_key refuses the path before it
# ever reads the bytes, so no real private key is placed inside the repository.
head -c 32 /dev/zero > "$ROOT/.wv1-repo-local-key.seed" && chmod 600 "$ROOT/.wv1-repo-local-key.seed"
"$BIN" portfolio phase0 re-evaluate \
    --module amphora-source-ledger --reason "$REASON" --as-of "$AS_OF" \
    --evaluation-key "$ROOT/.wv1-repo-local-key.seed" \
    --review "$REVIEWS/amphora-source-ledger.review.v1.dsse.json" --dry-run \
    > "$WORK/dry-run/NEGATIVE-CONTROL-repo-local-key.json" \
    2> "$WORK/dry-run/NEGATIVE-CONTROL-repo-local-key.err"
echo "repo-local-key control exit=$?"
cat "$WORK/dry-run/NEGATIVE-CONTROL-repo-local-key.err"
rm -f "$ROOT/.wv1-repo-local-key.seed"
echo DRY_RUN_SWEEP_DONE
