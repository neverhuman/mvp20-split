# Planning source access boundary

Planning0.12, BP-07.02/B1.04b. This owner-local consumer reads only public Data
contracts and routes; no peer implementation imports, peer SQL, source mutation,
provider egress, graph acceptance or persistent rights cache. Data0.29 or later
is required for explicit processing-content reads. Missing that route is not
permission to fall back to ordinary content.

DataReader uses a configured explicit loopback HTTP endpoint and credential,
not model-selected URLs. It performs GET on a closed catalog of Artifact
metadata, processing-content, source revision and conversion-trace routes.
There are no redirects, proxies or implicit retries. A per-review ReadBudget
bounds elapsed time20s, calls512 and response bytes32MiB; metadata256KiB,
Artifact bytes4MiB. Configuration may narrow these limits. The socket inactivity
timeout is at most5s, and a whole-review deadline shuts down the active socket
to interrupt trickling headers/bodies. Strict JSON rejects duplicate keys,
nonfinite values, malformed UTF-8 and invalid public records. Denied/missing
references have safe ValueError codes; network/protocol/operational failure is
SourceUnavailable, requiring explicit orchestration reconciliation. Peer bodies
and credentials are never included in error codes.

SourceReviewer revalidates task/request identity before reading. Every selected
context Artifact plus objective/prompt/policy/model configuration is included in
consumed ancestry, even if a candidate omits it from citations. Artifact identity,
scope, SHA-256 and exact byte count must match. Per-review caching prevents
duplicate reads but is never shared across reviews. At most128 distinct inputs
are consumed, matching the public derived declaration limit; no silent omission
or fallback upload is allowed. Sources retain exact revision and completeness;
the raw profile requires utf8_document and text/plain. Conversion traces must
match pinned canonical digests, source/target schemas, output identity and all
source byte-span hashes. SourceBundle retains its4MiB aggregate raw limit.
PromptTemplate verifies the actual reviewed prompt bytes.

ReviewedSources owns immutable task/source bundle/prompt bytes and canonical
consumed Artifact, SourceRevision and ConversionTrace documents. Its input order
is stable by Artifact ID. It is an observation of verified public responses,
not a durable access grant or a claim that science is correct. Partial sources,
unresolved/quarantined conversions and inferred fields remain explicit; no
global quality veto is introduced. Publication must recheck current process
rights on complete ancestry, and a future live adapter needs separate egress
and provider authorization.

Tests/source_access owns scripted record adversaries and real loopback scripted
HTTP.55 focused cases cover scope/identity/digest/trace/span conflicts, input
bounds, no cross-review caching, explicit process route, safe failures, strict
metadata, no redirects/retries, deadlines and configuration.194/196 statements
and28/28 branches covered; only defensive OSError suppression when shutting down
an already-closed socket is uncovered. Actual Data service compatibility and
publication recovery are B1.04d, separately from these client-boundary tests.
Replacement must preserve limits, exact original references, full consumed
ancestry, explicit evidence posture and the read/process distinction.

ArtifactReview in artifacts.py owns the shared exact metadata/body, scope,
identity, byte-count and SHA guards. SourceReviewer and repair preparation reuse
it with per-operation caches only. ReadBudget.remaining_total exposes the whole
deadline so sequential Data, Knowledge and Research reads cannot each restart
an elapsed-time allowance; remaining still caps socket inactivity at5s.
