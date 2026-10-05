# Runtime supervisor capture reader

- Implemented: Runtime0.27.0; reviewed `2026-10-05 15:53:34` (America/Chicago).
- Owner: Campaign Runtime; BP-07.04/B1.04b.ii.

CaptureReader(endpoint, token, seconds=10).fetch(ArtifactRef|None) returns exact bytes or no content for a no-Artifact diagnostic. It reads configured Data metadata followed by /processing-content. The complete original ArtifactRef must match, then length and SHA256 must match the original reference. This module never uses /content, private peer storage or another service's implementation. Data owns processing authorization; a local cached reference cannot grant it.

Only explicitly configured http://127.0.0.1:port endpoints, no credentials/path/query/fragment in URLs. Bearer tokens are printable ASCII32..512 characters, retained only in memory; no logs. Two GETs maximum,10s total,5s maximum socket wait,327680 combined response bytes; metadata262144 and capture65536. A socket shutdown timer bounds trickled responses across the whole window. Duplicate/nonfinite/malformed metadata, compressed content, redirects, denied/missing sources, changed identities, truncated/altered or oversized bytes fail explicitly. No retry, proxy, redirect following or model-selected endpoint. Zero-length Artifact content still requires owner metadata/processing reads; None makes no network call.

No SQL, request authorization, provider call, graph decision or retained cache. The HTTP recording adapter must validate the original request/actor/scope and recover stored receipts before calling this fresh-processing reader. B1.04b.iii owns that ordering. Exact returned bytes are retained by ResponseJournal; future history recovery does not refetch Data.

Replacement must preserve these bounds, byte equality and owner authorization. tests/supervision_capture uses a real local HTTP peer for success, status failures, altered metadata/content, size limits and slow bodies.22 cases; combined reader/cancellation/journal/persistence96 cases24.31s;12 boundary cases11.38s. Capture reader117 statements20 branches93%; untaken timing/error cleanup branches, explicit already-expired-window and nonfinite-metadata branch remain gaps. Cancellation module87 statements10 branches100%. No actual Data installation or independent replacement claim here; B1.04d supplies actual-owner integration.
