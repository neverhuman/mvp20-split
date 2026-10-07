# Retained follow-up transport

SQ-01/B3/P1 implemented. This source reads the exact Runtime response selected by
the checkpoint inspection, binds its request/attempt/capture/digest, and separately
checks Data Artifact metadata and current content permission. No content is returned
to presentation until both owners' bindings and raw bytes are verified. One bounded
capture is read on selection; no graph-wide scan, credential, storage or mutation.

Python-published serialization DTOs and exact validation profile hashes select the
new follow-up or old checkpoint/campaign parser. Unknown profiles remain unavailable.
Old profiles expose need-level intent, never invented criterion targeting. Owner
response body limit262144 and capture limit65536 apply. Source errors are sanitized.
Cancellation and late replies are fenced again by the page model. Exact Research
record/evidence reads use existing clients through CriterionClient: exact question,
need membership and selected assessment status SHA are required. No head discovery
or repinning. Tests under tests/transport/followup cover permission denial, changed
bytes, profile mismatch, foreign requests, membership and changed status digest.
