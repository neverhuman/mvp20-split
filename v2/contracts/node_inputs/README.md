# Retained node input contract

Owner: Runtime; approved POP-01.07, POP-01.01/E2.2. Public import root
`amphora_contracts_node_inputs`, version0.1. Depends only on public Core/Runtime
and Pydantic. Immutable closed DTOs; no service, database, scheduling or SDK logic.

NodeInputObservation exposes exact scope/run/node/scope-key identities, observed
revision, at most64 original scope-input summaries and optional PreparedInvocation.
Scalars/collections reveal counts only; Artifact input reveals its immutable ref.
PreparedInvocation is historical input/tool/checkpoint metadata, without lease or
grant credentials. Scope, duplicate ports, singleton counts, activation identity
and262144 serialized UTF-8 byte ceiling reject inconsistent records.

Null invocation does not prove failure or skipped execution. Revision is correlation
only; callers use existing graph/history APIs for execution state and successful
producer proofs for accepted outputs. No mutation or scientific validity implied.

Owned tests cover strict decoding, scope/identity/count/bound failures and absence
of credential fields. Replacement must preserve published schema bytes or version
the contract explicitly. Independent wheel and Runtime HTTP acceptance are separate.
