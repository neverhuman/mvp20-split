# Owned local PostgreSQL and Qdrant

Owner BP-09.02/B1.02. Explicit provisioning creates dedicated, labeled resources
for a persisted random deployment identity. It never discovers/reuses test fixture
volumes, deletes data, resets schemas or runs owner migrations. Provisioning is
serialized with a Windows byte-range lock and journals progress through atomic
file replacement. Failure retains credentials and data for explicit resume.

The host vault is current-user DPAPI. Docker receives password/key values through
its child environment, never command arguments. Docker administrators can inspect
runtime container configuration; this is not an isolation boundary against host
administrators. Raw Docker inspection, SQL input and credential-bearing diagnostics
must not enter logs. Persisted stores.json contains resource identities and ports,
never passwords. Missing credentials with existing resources fail closed.

PostgreSQL and Qdrant use digest-pinned images and separate named volumes. Only
127.0.0.1 ports are published. Existing resources must match deployment labels,
images, exact data-volume mounts and loopback scope before any start operation.
PostgreSQL readiness uses TCP to avoid the image's temporary initialization server.
Bootstrap creates only role/schema boundaries and its own admin marker in one
transaction. Each primary service retains separate migrator and restricted service
roles; database/public-schema privileges are revoked from PUBLIC. Subsequent DDL
belongs exclusively to each owner's migration CLI under its migration credential.

Readiness here means stores accept connections/authentication. It does not mean
service schemas are migrated, owner APIs are running, Qdrant collections exist,
tool eligibility is established, or backup/power-loss guarantees are proven.
Tests live under deploy/local/tests/persistence; actual local provisioning and
role/authentication/restart evidence are separate from mocked adapter cases.

Verified 2026-10-06 22:07:00: dedicated local stores, all12role authentication/schema boundaries, serving DDL denial, Qdrant missing/wrong-key denial and repeated provisioning preserving credentials/identity. Driver dev/verify_local_stores.py stores only nonsecret evidence. Unit coverage is partial (Docker35%,bootstrap26%,stores30%,state94% statements); real provisioning is separate evidence. Container restart, interrupted provisioning, dependency loss and power-loss remain unproven.

B2.01 migrations.py invokes each independently installed owner migration CLI explicitly, serially and only while service/control ports are stopped and the deployment operation lease is held. It grants only that owner migrator URL through the child environment, suppresses raw diagnostics and journals named outcomes. Different migration-release manifests require a forward plan; service startup never migrates. Actual six-owner initial and repeat migrations succeeded against the dedicated deployment. No legacy fixture migration/reset occurred.

Fixed-port correction verified 2026-10-06 23:29:25: Docker dynamic bindings changed PostgreSQL60687 to51130 on restart. ensure_store now persists an explicit loopback host port before creation and rejects dynamic or changed bindings. port_repair.repair is an explicit forward repair for exactly owned/digest-pinned/mount-verified dedicated containers while service/control ports are stopped. It retains the same volume, image, credentials and original routing; original containers are renamed -dynamic-baseline and remain stopped. Never start a baseline alongside the replacement on its shared volume. No deletion, reset or owner migration occurs. Failed repairs remain journaled for explicit forward repair. Actual database outage now recovers readiness and byte-identical registered synthetic receipt, followed by seven successful cooperative drains.
