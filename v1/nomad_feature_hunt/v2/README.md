# NOMAD Feature Foundry v2

V2 is isolated from the original feature-hunt controller. It stages Atlas and
all public structure inputs below a NOMAD-owned run inbox, builds an immutable
180-role roster, and treats agent output only as compact `FamilyCard` and
`FeatureSpec` data. The controller owns IDs, compilation, matrix creation,
invariance checks, scoring gates, receipts, and promotion.

The main commands are `preflight`, `run`, `resume`, `status`, and `verify`:

```bash
python -m nomad_feature_hunt.v2 preflight --run-id campaign-001
```

The internal phase commands are `evidence`, `design`, `compilation`,
`execution`, `discovery`, `adaptive`, `confirmation`, and `judging`. Discovery
and confirmation folds are separate: adaptive generation cannot read or
trigger confirmation until its frozen marker exists. The controller runs the
two-GPU CatBoost screen itself, publishes only categorical feedback, freezes
up to eight views per target, and then opens the five confirmation folds once.
Custom plugins are statically checked and execute both complete matrices and
their reruns in a networkless, read-only container before scalar quarantine.

`verify` is fail-closed. It promotes only a campaign that proves all feature,
domain, family, evidence, provenance, sandbox, scoring, storage, timing, and
budget gates. It never writes to `nomad_crystal360`.

`run` is the paid campaign entry point: it can dispatch up to 360 conservatively
accounted Jnoccio attempts. `preflight`, `status`, and `verify` do not dispatch
roles.

## ZYAL v2.1 ten-epoch campaign

The final ten-epoch campaign is a separate interface so the v2.0 controller and
its 180-role state remain compatible:

```bash
python -m nomad_feature_hunt.v2.zyal_epochs preflight --run-id final-001
python -m nomad_feature_hunt.v2.zyal_epochs run       --run-id final-001
python -m nomad_feature_hunt.v2.zyal_epochs resume    --run-id final-001
python -m nomad_feature_hunt.v2.zyal_epochs verify    --run-id final-001
```

It owns exactly 360 roles across ten epochs, dynamically caps each ready wave
to Fusion's eligible slots, permits one retry per role, and conservatively
debits at least $2.50 per attempt under a $2,000 ceiling. Its artifacts are
isolated below `v2/inbox/zyal10-final-<run_id>/`; successful output is delivered
only through the promotion inbox.

## Full-space sweep

The post-campaign full-union importance and genetic search is also isolated:

```bash
python -m nomad_feature_hunt.v2.full_space_sweep prepare 20260719-r1
python -m nomad_feature_hunt.v2.full_space_sweep run     20260719-r1
python -m nomad_feature_hunt.v2.full_space_sweep status  20260719-r1
python -m nomad_feature_hunt.v2.full_space_sweep resume  20260719-r1
python -m nomad_feature_hunt.v2.full_space_sweep verify  20260719-r1
```

Artifacts are written below `v2/inbox/fullspace-sweep-<run_id>/`. Preparation
hash-binds the 10,800-column baseline, the 6,234 accepted `20260719-r3`
columns, and 577 positional Hyperion columns. Model fits are resumable through
content-addressed cache entries. The local RTX 3090 starts first; a remote RTX
3090 or 4090 is staged and attached only after it reports idle.

## Full-space joint distillation

The verified sweep can be distilled without modifying its artifact tree:

```bash
python -m nomad_feature_hunt.v2.full_space_distill prepare 20260720-r1 \
  --parent-run 20260719-r1
python -m nomad_feature_hunt.v2.full_space_distill run 20260720-r1 \
  --parent-run 20260719-r1
python -m nomad_feature_hunt.v2.full_space_distill verify 20260720-r1 \
  --parent-run 20260719-r1 --scq-terminal-receipt /path/to/scq-terminal.json
```

This controller searches paired target masks and minimizes both confirmed mean
RMSLE and their unique extraction union. It runs as a foreground, one-GPU SCQ
assignment in the `xhyp3` project, resumes from content-addressed fit caches, derives two
new confirmation seeds from the frozen parent identity, and emits a
`DistilledFeatureSet.v1`, ordered target masks, a membership-flagged union CSV,
the complete Pareto curve, and the fold ledger. Final verification requires the
post-controller SCQ terminal receipt and fails closed on parent drift or any
test-label path.
