# NOMAD Feature Foundry v2 operations

These five JSON runbooks are declarative gates consumed by the isolated
`nomad_feature_hunt.v2` controller. Every feature input and generated artifact
is staged below the selected v2 run inbox. Jailgun is optional; its identity
probe can only add compact FamilyCards and cannot block the Jnoccio campaign.

The controller entry point is:

```bash
python -m nomad_feature_hunt.v2 preflight --run-id <run_id>
python -m nomad_feature_hunt.v2 run --run-id <run_id>
python -m nomad_feature_hunt.v2 resume --run-id <run_id>
python -m nomad_feature_hunt.v2 status --run-id <run_id>
python -m nomad_feature_hunt.v2 verify --run-id <run_id>
```

Internal phase commands use the same entry point and the phase name. Discovery
and confirmation produce and validate controller-private GPU score artifacts;
adaptive agents receive only `adaptive_feedback.json`, which contains
categorical values and no rows or exact scores.
