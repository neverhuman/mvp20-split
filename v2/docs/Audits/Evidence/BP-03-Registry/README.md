# Registry Acceptance Evidence

These credential-free manifests preserve the BP-03.02 closeout matrix. Each wraps canonical compact/sorted JSON evidence with its SHA-256. Source-process manifests record exact scopes, descriptor/source hashes, process IDs, barrier times, command/operation identities and observations. The installed replacement manifest records exact wheel hashes, original/replacement observations and retained revisions. No database URLs, credentials or tokens are included.

- `REG-01-same.json`, `REG-01-distinct.json`: concurrent duplicate registration with same/distinct command identities, one immutable release, changed-byte conflict and public read preservation.
- `REG-02-prepared.json`: kill while actual owner transaction is uncommitted; restart rolls back abandoned work and commits one release/receipt/audit.
- `REG-02-committed.json`: kill after commit before receipt delivery; restart replays the exact original operation.
- `REG-03-drain.json`, `REG-03-revoke.json`: actual PostgreSQL advisory-lock waits while lifecycle changes are held; later heartbeat/resolution are denied.
- `replacement.json`: separately installed original/replacement registry hosts preserve discovery, immutable releases/deployments, original registration/heartbeat/resolution receipts and replica revision; subsequent drain preserves pins.

Source-process cases use the explicit owner-only test entrypoint, not deployed HTTP transport. Replacement uses actual loopback HTTP, independent wheels and separate owner migration/service environments. Existing runtime/artifact REC-01..09 remain separate evidence. Neither tier claims scientific validity, Kubernetes or host power-loss durability.
