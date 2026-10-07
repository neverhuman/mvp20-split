# Catalog recovery integrity

- Owner: Data/artifacts, BP-09.04/B2.1; Data0.31 implemented; integrated restore acceptance remains separately gated.
- Scope: read-only finalized catalog/byte integrity for an offline recovery cut.

`CatalogAudit` alone enumerates this owner's finalized catalog through the artifact_service
role in a read-only repeatable-read transaction. Each immutable ArtifactRef, storage key,
actual byte count and SHA256 is checked through the owner's link-rejecting local storage.
No provisional upload is promoted, no table/file is changed, no peer is queried and no
scientific or source-use authority is inferred. Integrity preservation is local maintenance;
this command grants no interactive content download or processing rights.

`python -m amphora_data_artifacts.recovery --config ... --output ...` is an explicit
local operator command using existing environment credentials and owner configuration.
It is not a browser/API route. Optional `--inventory-output` writes local JSONL references,
storage keys and closed result codes, never payload bytes or credential values. Outputs
are create-once; retain partial output on failure and never treat it as success.
Exit0 means every selected catalog item passed;3 means counted integrity failures;
2 means incomplete/configuration/operation failure. Failed/incomplete never means ready.

Summary includes checked/verified counts, verified bytes, closed failure counts and an
ordered catalog fingerprint independent of file health. Pending protective reservation count is reported separately; verified bytes do not clear a pending hold or authorize traffic. Default300s/100000 entries bounds
the audit; exceeding either aborts, without a completeness claim. The caller must keep
workers/owners drained and prevent filesystem mutation. This is not online consistency
or protection against an administrator racing the filesystem. Missing/changed bytes do
not authorize deleting references, replacing hashes or resetting receipts.

Rebuild acceptance preserves strict service-role admission, read-only SQL, deterministic
inventory identity, streaming checks and safe failures. Tests belong under tests/recovery;
actual restored-catalog checks remain separate from unit and isolated PostgreSQL evidence.

Verified2026-10-07 09:08:00:7 scoped tests including actual PostgreSQL pass3.56s;114/115statements and23/26branches97% combined. Remaining branches are module-entry and unscoped inventory/count paths, exercised separately by installed CLI probes rather than attributed to this coverage. Deadline propagation, incomplete output, wrong serving role, source-scope selection, corruption/missing files, unchanged catalog identity and bounded enumeration are covered. Initial stale fixture port was repaired only in ignored connection metadata; no data reset.
