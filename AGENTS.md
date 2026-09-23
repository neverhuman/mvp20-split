# Repository Boundaries

- The repository root contains shared Git configuration and navigation only.
- `v1/` is the frozen, read-only implementation baseline. Do not edit, regenerate, format, build in place, or run operational automation there. Reuse reviewed code by copying/adapting it into `v2/`, retaining provenance. Changes to the baseline require explicit user authorization.
- `v2/` is the active development workspace. Read [v2/AGENTS.md](v2/AGENTS.md), then [v2/Restore.md](v2/Restore.md) before starting work.
- Requirements: [v2/docs/Architecture/Product_Requirements.md](v2/docs/Architecture/Product_Requirements.md). Architecture: [v2/Architecture.md](v2/Architecture.md).
- Verify the frozen tracked baseline with `py -3 v1/tools/verify_v1_baseline.py` from the repository root. Do not regenerate its checksum manifest to hide a modification.
- `v1/HANDOFF.md` describes historical operations. Relocation does not authorize fleet activity, publication, remote access or removing hard stops. Historical absolute paths are reference material, not instructions to access another workspace.
- Keep credentials and local datasets excluded from Git. Root `.gitignore` and the preserved `v1/.gitignore` protect both layouts.
