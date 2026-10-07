# Offline backup inventory boundary

- Owner: Deployment, BP-09.04/B1.1; Deployment0.12 implemented; actual capture/restore remains B1.2/B2.
- Architecture: [Runtime topology](../../../../../docs/Architecture/System/Runtime_Topology.md).

`BackupManifest.from_bytes` parses closed local-offline-backup-v1 records into immutable
owner snapshots, file inventory and offline-cut references. The record binds all six
owner release/schema/checkpoint identities, exactly one PostgreSQL snapshot, one Qdrant
snapshot, one cut-evidence file, installation files and zero or more artifact files.
Empty artifact sets are legitimate; capture must independently prove inventory completeness.
Unknown/duplicate fields, nonportable/ambiguous paths and missing roles reject safely.
Timestamp is absolute America/Chicago local time with seconds; identity is the backup ID.

`verify_inventory` reads only named local files and checks exact size/SHA256 against a
manifest whose SHA256 is supplied from a separately trusted capture journal. It requires
exact caller-selected owner release/schema compatibility and a different target identity.
Only `inventory_verified_not_restore_ready` is returned. This does not establish that
caller compatibility choices are correct, owner exports are semantically complete,
the cut was actually drained or restored references are valid. B1.2/B2 must prove these.

No database access, export/restore, credential loading, network, migrations, process
control, deletion or provider calls. No scanning/reading arbitrary unlisted files.
No change to existing installation/profile/journal formats. Path checks reject links
and junctions within the bundle; the caller owns exclusive offline filesystem access.
This is not a sandbox against concurrent malicious filesystem mutation or aliased parent
directories. Target-resource allocation must additionally reject original volumes/paths.

Rebuild boundary: preserve canonical manifest bytes, strict rejection codes, immutable
identities and read-only verification; never promote inventory validity to service health.
Owned tests: deploy/local/tests/backup_restore. Coverage and installed evidence are
recorded after verification; actual snapshot and corruption drills remain later gates.

Verified 2026-10-07 08:25:20:98 backup/preflight tests pass5.43s; backup module159/159 statements and14/14 branches measured (100%). Deep JSON tests permit parser-depth or shape rejection; explicit short test IDs avoid oversized pytest paths, and backup-specific fixture names preserve granular/combined suite isolation. Filesystem link checks use injected link/junction observations; actual capture/restore and concurrent mutation are not covered by these unit cases.
