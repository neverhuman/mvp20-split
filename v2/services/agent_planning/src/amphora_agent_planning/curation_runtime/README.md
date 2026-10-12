# Curation Runtime context

UI-01.08/P2.3b.2. Architecture: ../../../../../docs/Architecture/Agents/Planning.md.
Read the exact selected saved draft and predecessor run through existing Runtime
public GET APIs. One15second metadata window, two calls,4MiB per response. No
owner SQL/imports, graph mutations, validation, admission or retry. Metadata route
catalog adds exact /v1/definition-drafts/{id}?revision={positive-safe-integer};
mutable latest reads, extra/duplicate parameters and arbitrary routes reject.

CurationRuntimeContext revalidates public DTOs, exact scope/draft ID/revision/content
hash using the published authored-order amphora-draft-content-v1 digest, and exact
predecessor run/plan/revision. Running/blocked predecessors reject the between-
campaign workflow. The original authored graph goes into a required untrusted
slice; one-node execution summary is explicitly partial, not the execution graph.
Selected draft is not claimed to be the predecessor's original source without
separate lineage evidence. Runtime still decides successor compatibility/admission.

Byte-owned replay validates original intent and all pins again. Wrong digest,
changed revision, active predecessor or denied source is a technical preparation
failure; no substitute graph/model call is generated. Model packet limits can
reject an oversized original graph. Public-peer deployed qualification, complete
context assembly and durable worker linkage remain next. Tests: tests/curation_runtime.
