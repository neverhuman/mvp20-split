# Repository Layout and Baseline

- Status: v1/v2 separation; v2 implementation not started
- Last refreshed: `2026-09-22 13:43:28`
- Scope: filesystem relocation preserving pre-existing working-tree changes
- Baseline: existing local implementation at relocation time, not a claim that the working tree equalled a committed release
- Next step: define the bounded v2 implementation plan from the product requirements

## Placement

All implementation crates, Python modules, scripts, tests, schemas, registry, configuration, evidence, reports and historical operational files moved under `v1/`. Their contents are preserved. The old root README and HANDOFF remain there as historical references. License and shared Git configuration remain at the root; the legacy ignore rules are also copied into `v1/.gitignore` so anchored exclusions keep their original scope.

`AGENTS.md`, `Architecture.md` and `Restore.md` moved to `v2/`. The `docs/Architecture`, `docs/Artifacts`, `docs/Presentations` and `docs/Build Plans` directories moved to `v2/docs/`. Architecture includes historical domain-specific requirements and assessments as references; Product Requirements and Graph-Native Research Engine remain the active direction. PDF exports may predate Markdown updates and are not the authoritative requirements.

Legacy `docs` files, directives and moonshots remain under `v1/docs`. Local credentials remain excluded under `v1/docs/Keys`; they are not active v2 assets. Existing ignored root IDE state and presentation preview files were left in place. No source artifacts or pre-existing uncommitted work were intentionally discarded, and no commit or push is part of this relocation.

## Frozen Baseline

The baseline verifier and its manifest now reside in `v1/tools/`, alongside the preserved legacy tooling. Invoke the verifier from the repository root. The verifier, its manifest and this relocation record are maintenance metadata explicitly excluded from newly tracked implementation-addition checks; the original 6,022 baseline hashes remain unchanged.

`v1` is read-only by repository policy. A checksum manifest in `v1/tools/v1-baseline.sha256.json` records the relocated tracked files and copied ignore file. `py -3 v1/tools/verify_v1_baseline.py` detects missing or modified baseline files and newly tracked additions under v1. Local ignored credentials/data are excluded from the portable manifest. This is an integrity check, not an OS access-control boundary or a Git server enforcement rule.

Legacy scripts may assume the old repository root, `.git` location or historical absolute paths. Their contents are deliberately preserved rather than rewritten. Do not run legacy build, publication or operations scripts in place as if relocation established compatibility. Future extraction should run from a separate working copy or adapt reviewed components into v2.

Before editing active documentation, all relocated files are compared against their pre-move SHA-256 hashes. Active links to implementation files are then repaired to point into v1. The baseline verifier is the ongoing check; no runtime tests or remote fleet actions are needed for this directory-only change.
