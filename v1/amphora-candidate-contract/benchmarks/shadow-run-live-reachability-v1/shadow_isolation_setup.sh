#!/bin/sh
# Reproduction script for amphora-candidate-contract shadow-run-live-reachability-v1.
# Builds an isolated, symlink-based copy of the workspace so that `amphora-tui shadow run`
# can be executed end-to-end (including its real Ed25519 sign + persist_receipt() path)
# WITHOUT writing anything to the shared production root/.amphora/ state.
#
# workspace_root() in amphora-cli/src/main.rs is `env!("CARGO_MANIFEST_DIR").parent()`,
# baked in at COMPILE time. To point it at an isolated root, amphora-cli must be rebuilt
# with its own Cargo.toml/src living inside a REAL (non-symlinked) directory under the
# isolated root; every other crate/dir can be a plain symlink back to the real tree
# (read-only, zero copy). `.amphora` is deliberately NOT symlinked so all writes
# (local dev identity keygen, receipt persistence) land only inside the isolated root.
set -e
REAL=/home/ubuntu/amphora/build/mvp20-split
ISO="$1"
[ -n "$ISO" ] || { echo "usage: $0 <isolated_root>"; exit 1; }
rm -rf "$ISO"
mkdir -p "$ISO"
for entry in "$REAL"/*; do
  base=$(basename "$entry")
  case "$base" in .amphora|target) continue ;; esac
  ln -s "$entry" "$ISO/$base"
done
for entry in "$REAL"/.[a-zA-Z]*; do
  base=$(basename "$entry")
  case "$base" in .amphora) continue ;; esac
  ln -s "$entry" "$ISO/$base" 2>/dev/null || true
done
rm -f "$ISO/amphora-cli"
mkdir -p "$ISO/amphora-cli"
ln -s "$REAL/amphora-cli/Cargo.toml" "$ISO/amphora-cli/Cargo.toml"
ln -s "$REAL/amphora-cli/src" "$ISO/amphora-cli/src"
export PATH="$HOME/.cargo/bin:$PATH"
CARGO_TARGET_DIR="$ISO/target" cargo build --bin amphora-tui --manifest-path "$ISO/amphora-cli/Cargo.toml"
echo "Built $ISO/target/debug/amphora-tui (workspace_root will resolve to $ISO)"
