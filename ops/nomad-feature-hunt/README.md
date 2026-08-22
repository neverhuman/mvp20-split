# NOMAD theoretical feature foundry

This ops-only campaign runs 70 stable Jnoccio roles in dependency-ordered waves through a hard
20-worker pool, alongside one guarded ten-tab Jailgun batch. It never modifies
`nomad_crystal360`, reads a test-label source, or promotes an uncomputed idea as a feature.

The controller stores each run under
`/home/ubuntu/nomad/artifacts/nomad_theory_feature_hunt/inbox/<run_id>/`. Override
`--inbox-root` only with another path below `--nomad-root`; paths outside that storage boundary are
rejected. Agent runtime temporary files, Jailgun downloads, GPU work arrays, and every persistent
feature artifact also remain below `/home/ubuntu/nomad/`. The public commands are resumable:

```bash
python3 -m nomad_feature_hunt.controller preflight --run-id hunt-20260718
python3 -m nomad_feature_hunt.controller run       --run-id hunt-20260718
python3 -m nomad_feature_hunt.controller resume    --run-id hunt-20260718
python3 -m nomad_feature_hunt.controller status    --run-id hunt-20260718
python3 -m nomad_feature_hunt.controller verify    --run-id hunt-20260718
```

`run` performs a visible exact-model probe before either paid branch starts. After that gate passes,
Jnoccio and Jailgun launch concurrently. Failure to prove `GPT-5.6`, ten ready tab slots, or ten
fresh post-run conversation IDs stops the campaign. An invalid archive gets at most one new
Jailgun batch; a Jnoccio answer is never accepted as tab evidence.

Build and record the sandbox image before a live run:

```bash
docker build -t nomad-feature-sandbox:2026-07-18 ops/nomad-feature-hunt
docker image inspect --format '{{.Id}}' nomad-feature-sandbox:2026-07-18
```

Generated Python is rejected by static import/AST policy before it reaches Docker. Docker runs as
UID 65532 with a read-only root, no network, no capabilities, no new privileges, and only four
mount classes: the generator, trusted harness, stripped public CSV/geometry inputs, and a fresh
output directory. The trusted harness executes a deterministic rerun and independently checks
translation, rotation, atom permutation, wrapping, and equivalent-cell invariance on a toy and a
fixed real structure.

The trusted scorer joins training targets by the frozen Atlas row IDs outside the container. It
uses the frozen two selection folds, three seeds, 150-tree GPU screens, then shuffled five-fold
400-tree confirmation for the best five nonoverlapping batches and their positive-lift union. CPU
fallback is prohibited. Screening pairs are dispatched concurrently to the local RTX 3090 and the
`xbabe1` RTX 4090, with one CatBoost subprocess locked to each GPU. Remote inputs and the hashed
worker are staged over SSH because the hosts do not share project paths. A failed fit is retried
once on the other GPU and never on CPU; preflight runs a real two-host fit and records both GPU
identities. The score table compares each target against both the Atlas target winner (mean
`0.05053309`) and existing-809 control (mean `0.05162068`).

`verify` is deliberately fail-closed. It reports incomplete unless it can prove all 70/10/500
receipts, 1,500 attempts, 1,000 validated executable novel columns, at least 50 validated columns
per domain, generator/environment/matrix/experiment/judgment hashes, both target score/lift rows,
and the no-test-label boundary. Nothing is padded or automatically merged.

The isolated ten-epoch successor is declared in
`01-jnoccio-research-generation-v2.zyal` and invokes
`python3 -m nomad_feature_hunt.v2.zyal_epochs`. The original ZYAL runbook is
retained unchanged for reproducibility. V2.1 receipt schemas live under
`schemas/v2.1/`.
