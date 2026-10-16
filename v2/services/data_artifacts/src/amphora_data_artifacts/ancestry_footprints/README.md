# Artifact ancestry footprints

Data owns POP-01.08's GET `/v1/artifacts/{id}/ancestry-footprint`. Existing scoped
read permission suffices; no retention action is granted. One repeatable-read,
read-only transaction reads the root and reuses authoritative conversion/derivation
discovery (128 parents,4096 identities including root, cycles rejected). A focused
value object computes checked distinct content bytes and the unchanged protected
closure digest. Missing root is404; incomplete/invalid/oversized ancestry is409;
existing authentication/grant/storage errors remain401/403/503. Responses are bounded
to262144 bytes and no-store. No payload storage, external network, writes, command
ledger, reservation, processing-rights grant or migration is involved. Later catalog
registration can change the observation; it is not a durable snapshot or lease.
Tests belong under Data tests/ancestry_footprints; independent HTTP/restart
qualification is required before Search relies on this response in preflight.
