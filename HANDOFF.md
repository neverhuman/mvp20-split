# Amphora MVP20 handoff

This repository is a source-only handoff derived from the frozen Amphora
operational tree. It is intentionally not a clone of that tree's operational
history.

## Provenance

- Canonical host and path: `xbabe2:/home/ubuntu/amphora/build/mvp20-split`
- Frozen source commit: `f5b2238720999cc765a751928942ad67d8e419d8`
- Capture time: `2026-08-22T09:22:29+00:00`
- Source history at capture: 443 commits on `main`
- Handoff history: one root commit on `main`; no tags or other branches

The operational repository, its history, its external demo worktree, and all
local data remain unchanged on xbabe2. This handoff contains no GitHub Actions
workflows and requires no Git LFS objects.

## Deliberate exclusions

The handoff excludes `.amphora/` (including its private Ed25519 signing key),
runtime logs and state, feedback trees, generated artifacts and report/archive
binaries, caches, local environments, build output, compiled code, raw and
derived dataset payloads, model/archive formats, synthetic private signing
seeds embedded in T-12 diagnostic outputs, one scanner-ambiguous W-D-ROLE
evidence payload, evidence or data payloads at least 1 MiB, and every remaining
file at least 10 MiB.

`DATASETS.local.json` is the deterministic inventory for omitted non-cache
datasets and artifacts. Every entry records its xbabe2-relative path, byte
size, SHA-256, and category. Restore data only from the canonical xbabe2 path
and verify its hash before use; do not commit restored bytes. The rights-clean
OpenPoly CSV needed by benchkit is the sole local dataset copied into the
handoff, under `benchkit/tests/fixtures/openpoly/`.

## Portable maintained paths

Rust packet probes derive the workspace from `CARGO_MANIFEST_DIR`. Maintained
Python red-team and benchkit paths derive from their file location. The local
launcher derives the repository root from its script location. Set
`AMPHORA_ROOT` to override the inferred root for Python or the launcher.

The red-team ledger regression uses a minimal sanitized fixture containing the
two malformed timestamps and small clean ordering controls; it no longer reads
the operational log. Data-heavy benchkit tests skip only when their required
input is absent and listed in `DATASETS.local.json`.

Exactly 831 historical evidence, benchmark, and report reproduction source
files that contain the canonical xbabe2 checkout path are retained
byte-for-byte. They are provenance records, not maintained portable entry
points, and still expect `/home/ubuntu/amphora/build/mvp20-split` when replayed.

## Validation and baseline

The publication gate runs:

```text
cargo test --workspace --locked --no-run
cargo test --workspace --locked -- --skip cf_packet_blueprint_citation_binding_probe
pytest tests/crystal360
pytest amphora-redteam-audit/tests/test_ledger_ts.py
pytest benchkit/tests
```

The frozen xbabe2 baseline is 395 passing Rust tests with the stale
`cf_packet_blueprint_citation_binding_probe` adversarial gap-reproduction probe
filtered, a passing Crystal360 suite, 6 passing portable red-team ledger tests,
and 21 passing benchkit tests when xbabe2-only data is available. In the
source-only handoff, benchkit reports explicit manifest-backed skips for the
intentionally omitted Purformance dataset.

Publication additionally requires a clean `git fsck`, policy checks over both
the staged tree and a fresh clone, validation of every manifest entry against
xbabe2, and redacted Gitleaks and TruffleHog scans. Any secret finding other
than a narrowly verified public DSSE key identifier blocks publication.

The staged publication scan has zero TruffleHog findings. Gitleaks reports
1,408 public DSSE identifier matches: 1,397 key identifiers whose SHA-256
suffixes derive from retained Ed25519 public keys, plus 11 explicitly checked
legacy identifiers or public identifier prefixes. Its committed allowlist is
limited to exact, non-credential domain labels used by evidence oracles.
