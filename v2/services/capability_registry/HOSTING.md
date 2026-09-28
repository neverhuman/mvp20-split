# Registry Hosting and Replacement

The registry is an independent Python wheel. Install only its declared public contracts and locked dependencies. It requires its own PostgreSQL schema, service role and environment-referenced credentials; it does not need runtime/artifact implementations, peer database credentials, scientific libraries or a shared backend.

An operator provisions schema `registry` owned by `registry_migrator` and grants the ordinary `registry_service` role schema usage. Run explicit owner migrations with `AMPHORA_REGISTRY_MIGRATION_URL` using `python -m amphora_capability_registry.persistence.migrate`. Migrations grant only named table/column permissions. Never supply the migration credential to the ordinary host; startup refuses a different database role and performs readiness reads, never DDL.

Supply a bounded JSON configuration file:

```json
{
  "database_url_env": "REGISTRY_DATABASE_URL",
  "principals": [{
    "actor_id": "catalog-operator",
    "scope": {"tenant_id": "internal", "project_id": "synthetic"},
    "token_env": "REGISTRY_OPERATOR_TOKEN",
    "actions": ["register", "activate", "deploy", "read", "resolve", "drain", "revoke"]
  }],
  "resources": {
    "architecture": "x86_64",
    "operating_system": "windows",
    "cpu_millicores": 2000,
    "memory_mib": 1024,
    "gpu_count": 0,
    "timeout_seconds": 300,
    "max_parallel_invocations": 8,
    "max_batch_size": 128
  },
  "allowed_egress_hosts": []
}
```

This is a synthetic local test profile, not an assertion about the eventual DGX/Threadripper host. Configure resources for the selected environment. Separately configured workers receive only heartbeat permission and their own tokens, and must appear in a deployment's worker list. Tokens are opaque ASCII values of 32–512 characters; inline secrets/URLs, unknown configuration fields, wildcard actions, duplicate principals and test fault switches are rejected. Configuration names environment variables, never embeds their values.

Run `python -m amphora_capability_registry check --config <path>` before `python -m amphora_capability_registry serve --config <path> --port 8082`. The initial host binds loopback and disables access logs. Remote deployment/TLS/cluster policy remains a selected-environment gate. The API's [catalog boundary](src/amphora_capability_registry/catalog/README.md) defines authentication, operations, reason codes, original-receipt replay and exact-version resolution.

Replace implementation between campaigns: preserve database/configuration and published contract/canonical versions; stop the old host; independently install the replacement wheel; run any explicit forward migration with only its owner migration credential; start the replacement with only service credentials. Verify immutable release/lock identity, deployment definition/revision, original registration/heartbeat/resolve receipts and current lifecycle. A replayed capacity receipt is historical: issue a fresh heartbeat/resolve command to obtain a new observation. Registry replacement never changes admitted runtime pins or takes over runtime claim/fence authority.

`tests/acceptance/service_probe.py` is the installed original/replacement HTTP acceptance gate. It uses fresh wheel environments, explicit owner migration subprocesses, minimal service environments and actual PostgreSQL. It retains original release/deployment/replica/command state across process replacement, verifies scoped reads and later drain behavior, and writes a credential-free hashed evidence manifest. `owner_process.py` is a separate explicit test-only transaction barrier harness; production hosting does not expose those hooks. Process replacement evidence does not establish target-host power-loss or backup durability.
