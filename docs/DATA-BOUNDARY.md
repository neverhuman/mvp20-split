# Git and data boundary

This private repository is **source-only by operational policy, not literally data-free**.
It intentionally retains small frozen evidence, fixtures, receipts, and public/reference
tables needed to audit past claims. Some have unresolved redistribution rights, so private
repository access is not permission to republish them. Read the root `LICENSE` before sharing
any artifact.

## Excluded from every reachable published ref

- 1,344 path-addressed payloads (6,196,631,575 logical bytes) inventoried by path, size,
  and SHA-256 in
  `DATASETS.local.json`;
- the canonical `.amphora/` control plane, runtime logs/state, credentials, signing seeds,
  Claude/account state, and host SSH material;
- model weights, archives, compiled binaries, build output, Git LFS objects, and GitHub
  Actions workflows;
- the 40 GB NOMAD input corpus described in `EXTERNAL_INPUTS.md`.

The publication policy reads the staged Git blobs (not merely worktree copies), checks the
complete tracked tree, denies every inventoried payload plus nested raw/derived/object/split/
quarantine payload locations, blocks common secret/model/archive formats, and hash-pins the
five intentional binary evidence files. The reviewed snapshot then scans the staged index,
the complete tree, and full reachable history.

### The inventory does not cover logs

`DATASETS.local.json` holds 1,344 entries and **none of them is a `.log` file** -- the
generator selects data payloads (`.json`, `.gz`, `.csv`, `.parquet`, ...), so run logs sitting
beside inventoried data are invisible to it. That is a real gap, not a theoretical one: the
2026-08-24 move to xbabe1 found `feedback/v1/external_data/point2_metadata/raw/Tg_run.log`
present on the old host and absent here, even though the two CSVs it describes were both
inventoried and restored. It was copied by hand.

`ops/restore-datasets.sh` reporting "every selected path is present and hash-verified" means
every *selected* path. If you move this tree to another machine, copy the directories wholesale
rather than trusting the manifest to enumerate them.

This boundary is path-addressed, not a claim that every omitted byte sequence is unique.
Small retained fixtures and frozen audit metadata intentionally duplicate some bytes found at
omitted canonical paths (including the 178,587-byte OpenPoly fixture). That does not restore
the excluded corpus layout or make the retained material rights-clean.

## Intentionally retained

The filtered handoff still carries approximately 55.7 MB under evidence trees and 6.0 MB
under reference trees. The evidence inventory identifies 103 paths (about 3.22 MB) whose
rights status is `UNRESOLVED`: 56 dataset-class artifacts, 37 outputs, and 10 fixtures.
These are frozen audit context, not a rights-clean training corpus and not a redistribution
bundle. Removing them from only the current tree would neither purge history nor preserve
their signed evidence bindings; a true removal requires a separately reviewed history
rewrite.

## Burned-key/history incident

The original `demo/founder-showcase` ancestry and the separate
`neverhuman/mvp20-split-history` repository briefly exposed a local-development Ed25519 key
and an unsanitized canonical history. The demo branch was rebuilt directly on the filtered
handoff. On 2026-08-23 every branch/tag ref in the history repository was replaced with the
sanitized handoff `main`, its unsafe demo ref was deleted, and the repository was archived.

GitHub may retain unreachable objects after a force rewrite in **both** repositories.
Complete server-side erasure therefore requires GitHub Support to purge the original demo
objects and an owner token with `delete_repo` scope (or Support) to delete
`neverhuman/mvp20-split-history`; the available publication token has only `repo`, `read:org`,
and `gist`. Until deletion, keep the latter archived and private. The local canonical
repository on xbabe2 remains unchanged and is the recovery source. The writable filtered
publication clone was separately reflog-expired and garbage-collected, so it retains no
unreachable object from the unsafe demo ancestry.

## xbabe1 meaning of "full Git"

`xbabe1:/home/ubuntu/mvp20-split` is a complete, non-shallow, non-partial clone of the
**filtered published repository**, including all published branch and tag refs. It
deliberately is not a copy of the unsafe 462-commit canonical history.

As of 2026-08-24 that host was consolidated to a single directory and made self-sufficient.
Alongside the tracked tree it now carries, all gitignored: the **complete** 1,344-file
`DATASETS.local.json` inventory (hash-verified on arrival), its own `.amphora/` run state,
the controller's mutable `state/` (formerly `~/amphora-cron`), `legacy/` provenance archives
(formerly `~/amphora-archive`), and build output.

Two things follow that this document previously stated otherwise:

- The host holds the **complete** inventory, not a 385 MB subset.
- The **evaluator signing seed is present on xbabe1**, at
  `~/.local/share/amphora/phase0/keys/`, mode 0600. Signing seeds remain excluded from the
  *repository* — that invariant is unchanged — but they are no longer xbabe2-only. This was
  a deliberate handoff decision so the verification backlog and the outstanding
  `source-lock.v1.json` repair are actionable. Whoever holds xbabe1 can sign as
  `phase0-evaluator-3ef6b35cdbbfea74`.

`git clean -xdf` on that host would delete all of the above. Since 2026-08-24 none of it is
recoverable at all: Amphora was removed from xbabe2, so xbabe1 holds the only copy of the
473-commit canonical history (`legacy/canonical-history.git`), the dataset inventory, and the
signing seeds.

## Operator checks## Operator checks

```bash
python3 ops/amphora-controller/policy/staged_file_policy.py \
  --repo . --profile publication --source staged
python3 ops/amphora-controller/policy/staged_file_policy.py \
  --repo . --profile publication --source tracked
gitleaks git . --staged --config .gitleaks.toml --redact --no-banner --exit-code 1
gitleaks git . --config .gitleaks.toml --redact --no-banner --exit-code 1
```

Never interpret Git-clean as data-clean: ignored local datasets remain invisible to
`git status` unless requested explicitly.
