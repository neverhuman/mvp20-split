# Replica Integration Evidence

Reviewed: `2026-09-28 17:04:34` (America/Chicago).

[B1 manifest](b1.json) records actual registry-to-runtime selection, two concurrently leased distinct invocations, independently published artifacts, lost-completion receipt recovery and canonical outputs/budget. Exact package/image digests and public receipts are preserved; the companion hash protects bytes. Scope f303014dbbc44baa870a8bf5c01095a7.

Actual workers/owners are independent Windows wheel processes; Linux image goldens/isolation are separate prior evidence with matching internal wheels. Advertised registry resources are the image profile, not measured host capacity or container attestation. No scientific/Kubernetes/target-host claim.

[B2 process evidence](b2.json) and [replacement images](images-b2.json), verified 2026-09-28 17:12:18: real worker death/expiry/reclaim with stale rejection, 0.2.0/0.3.0 sequence cutover and unchanged prior records. Scope cf1cde5566ec445b97829458da776604. New output representation is statistics; payload schemas and golden behavior remain unchanged. Numeric image identity is unchanged.
