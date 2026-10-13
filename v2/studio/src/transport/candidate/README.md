# Candidate owner reads

Read-only adapter for existing Research `/v1/candidates/read` and Runtime
`/v1/runs/{run}/completions/{completion}/producer`. Uses generated published
serialization validators, same-origin session transport, bounded responses and
sanitized failures. Verifies requested candidate or run/completion identity.
No retries, writes, secrets, content cache or direct database/service imports.
DataProvenanceClient separately verifies current Artifact access and exact bytes;
candidate_inspector owns cross-record interpretation. Tests live in
`tests/transport/candidate/`; replacement must preserve route and identity bounds.
