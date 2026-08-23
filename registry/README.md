# registry/

The succession chain for `module-manifest.json` — the runtime policy registry.

- `succession.v1.json`, `succession-chain.v1.json` — the chain head and its history.
  `succession-chain.v1.json`'s `head_manifest_sha256` must equal the SHA-256 of the current
  root `module-manifest.json`; that binding is what makes the manifest authoritative.
- `succession/<sha>.json` — one record per succession event.
- `archive/<sha>/module-manifest.json` — the manifest as it stood at each prior head. Each
  directory name is the SHA-256 of the manifest it contains.

**Generated, not hand-edited.** Written by `cargo run -p xtask -- snapshot-registry`.
