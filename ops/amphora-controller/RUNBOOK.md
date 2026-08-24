# Amphora operator runbook

## Safety model

The fleet has four structural lane locks on xbabe1 and module leases in mutable
state. A `HARD_STOP` prevents fires.

> **This host is standalone.** Amphora was removed from xbabe2 on 2026-08-24 and
> `AMPHORA_TARGET_HOST` is empty. Anything below describing a second host — deploying a guard,
> provisioning lateral SSH, diffing a remote crontab — describes a topology that no longer
> exists. It is kept only where it explains why a control is shaped the way it is.

The autocommit guard that ran on xbabe2 created an `AUTOCOMMIT_DRAIN` marker, waited for every
lane and fleet lock to drain, then staged only policy-approved files; rejected schema-flip
bytes were preserved in `/home/ubuntu/.local/state/amphora/schema-flip-quarantine`, and it
never pushed. There is no host to deploy it to now.

The controller tree is hash-inventoried and installed without write bits. The
operator CLI refuses a foreign hard stop and resume requires the exact owned
tag. Cron mutation replaces only the Amphora job lines — two of them on this host.

## Status and diagnosis

Run on xbabe1:

```bash
cd /home/ubuntu/mvp20-split
ops/amphora-controller/bin/amphora status
ops/amphora-controller/bin/amphora doctor
ops/amphora-controller/bin/amphora test
```

`status` prints the hard stop, local jobs and process count, then
`standalone: no target host configured; remote cron check skipped`, and **exits 0**. `doctor`
reports `standalone: local signing seed present (32 bytes, 0600)` and
`OK doctor: controller hashes verified`, and **exits 0**. Neither is degraded: with no target
configured, having no remote to check is the correct result, not a fault.

`doctor` checks required programs, controller hashes and permissions, config mode, and the
**local** signing seed's existence and length — never its contents. The seed is at
`~/.local/share/amphora/phase0/keys/evaluator.ed25519.seed`, mode 0600, and it is the only copy
in existence. Claude authentication is deliberately a separate gate.

## Pause and drain

Choose a unique uppercase tag and preview first:

```bash
TAG=AMPHORA-INCIDENT-YYYYMMDDTHHMMSSZ-OPERATOR
ops/amphora-controller/bin/amphora pause --tag "$TAG"
ops/amphora-controller/bin/amphora pause --tag "$TAG" --apply
ops/amphora-controller/bin/amphora drain --timeout 180
```

Pause atomically creates the stop before disabling the hourly launcher and the
10-minute mirror. It exits without overwriting any existing
foreign stop. Record before/after crontabs and hashes for every manual incident.

For this handoff, use the existing tag
`AMPHORA-HANDOFF-20260823T025604Z-CODEX-7F3A92`; do not replace it.

## Authentication

Authentication is allowed only after explicit activation approval. Log in as
`ubuntu` on xbabe1 and use the installed Claude CLI's interactive authentication
flow. Never authenticate as root, copy session material into the repository, or
store credentials in the environment files. Re-run `doctor` and sandbox tests
after authentication; do not remove the stop yet.

## Installation and update

The dedicated GitHub deploy key on xbabe1 is read-only. Preview installation:

```bash
ops/amphora-controller/bin/amphora install
ops/amphora-controller/bin/amphora install --apply
```

`install --apply` creates a mode-0600 config if absent, seeds only missing
mutable bootstrap files, installs both cron entries disabled, and mechanically
protects the controller tree. With no target host it deploys no remote guard.
It never overwrites existing mutable campaign or queue state.

For a reviewed fast-forward update: pause and drain, restore owner write permission
with `bin/amphora unprotect --apply`, fetch with the read-only key, verify the
intended commit, use `git merge --ff-only`, rerun tests and manifest verification,
then `bin/amphora protect --apply` (or `install --apply`) to reprotect it. Never
reset the checkout or force-update it.

Applied install/pause/resume run entirely on this host. They no longer require lateral SSH,
because there is no second host to reach.

## State restoration

Restoration is a paused operation. Archive the current mutable state first.
Verify the hashes in `bootstrap/campaign-chain-checkpoint.json`, then restore
`campaign.json` and `data-acquisition-queue.jsonl` only under
`state/locks/campaign.lock`. Append an `operator_restore` chain event containing
pre/post hashes. Never restore runtime counters, live leases, or lock-file
contents from the frozen bootstrap. Keep the hard stop throughout and run all
invariants before considering activation.

The frozen campaign is intentionally exhausted and carries a complete,
unique 30-module weighted fallback rotation. This is `EXHAUSTED_ROTATION`, not
a backlog defect. Three historical campaign deviations and 21 append-only
reconnaissance deviations are exact, hash-bound baselines; any additional
violation fails the gate.

## Reviewed snapshot and publication

The **dry run works here** and mutates nothing:

```bash
cd /home/ubuntu/mvp20-split
ops/amphora-controller/reviewed-snapshot.sh      # prints the 6-step plan, exits 0
```

An **applied** snapshot is different: it needs a clone that can push, and none exists any more.
The writable one lived on xbabe2 and was deleted with everything else on 2026-08-24; xbabe1
holds no GitHub credential at all. Until someone is added as a collaborator and clones with
their own identity, the dry form is the only form. `AMPHORA_SNAPSHOT_REPO` is only for an
equivalent writable clone on the same publishing host. See `BUILD.md`.

An applied snapshot requires `--apply --review --tag TAG`. It pauses and drains,
exports the bootstrap state from xbabe1, regenerates both local manifests against the local
canonical source, runs required staged/full-tree/full-history policy and secret scanners,
stages the exact diff, and prints
`review_diff_sha256`. Commit requires `--commit --reviewed-diff-sha256 HASH`;
push additionally requires `--push`. Push only `main`, then verify privacy,
branches, tags, workflows, and a fresh clone.

## Incidents

- **Foreign hard stop:** leave it untouched, identify its owner, and stop.
- **Held lane or fleet lock:** identify the holder with `lslocks`; do not delete
  lock files. Terminate only a positively identified abandoned controller after
  recording its PID and logs.
- **Controller hash mismatch:** keep paused, compare with GitHub `main`, and
  redeploy through the installer. Do not bless the changed bytes in place.
- **Schema flip:** inspect the quarantined rejected bytes and HEAD version;
  never discard quarantine during incident response.
- **Campaign-chain alert:** keep paused; compare the last claim's post-hash to
  the current campaign and append a reviewed rebase/restore event under lock.
- **Secret/policy finding:** unstage and quarantine the file locally. Do not
  weaken a rule to make publication pass.
- **Partial cron change:** restore the saved before crontab, retain the hard
  stop, and rerun pause after diagnosing connectivity.

## Rollback

Rollback begins with pause and drain. Preserve the current checkout and mutable
state as a timestamped archive. Deploy the previously reviewed commit into a
new checkout or use a verified fast-forward-capable replacement; do not hard
reset or erase the current copy. Restore mutable state only by the procedure
above. Run `doctor`, controller tests, repository suites, policy scans, and a
no-write preflight. Leave all jobs disabled until a separate activation review.

## Eventual activation (separate approval)

1. Obtain explicit user approval for activation.
2. Reauthenticate Claude interactively on xbabe1.
3. Run `doctor`, all sandbox and repository tests, and a no-write preflight.
4. Confirm the stop content exactly matches the approved tag.
5. Preview `resume --tag TAG`; then run `resume --tag TAG --apply`. This enables the two
   reviewed entries — hourly launcher and 10-minute mirror — then removes only the matching
   stop. Expect two lines, not three; the third was the remote guard.
6. Observe the first fire through claim, lease release, DSSE verification, and mirror.

An earlier version of this list had a step between 1 and 2: provision and verify a reviewed
xbabe1→xbabe2 host key and a dedicated activation credential. There is no such host, so that
step is gone rather than merely unsatisfiable. Nothing lateral needs provisioning.

Until step 1 is satisfied, do none of these activation actions.
