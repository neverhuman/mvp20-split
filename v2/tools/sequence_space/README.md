# Synthetic sequence space

- Owner: BP-08.03/B1.02; release0.2.0 adds public adapters; pure0.1.0 behavior unchanged, adapter/CLI verification passed.
- Design: [Representation and fitness](../../docs/Architecture/Campaigns/Representation_Fitness.md).

This independent package owns legality and one proposed move for the synthetic sequence encoding. Domain objects validate complete inputs, preserve scope/profile and retain a hash of the exact canonical source. Public DTOs serialize results; no SQL, I/O, service/private sibling imports, global RNG, scheduler, scientific eligibility or hidden loop belongs here. Pure domain dependencies are public candidate_spaces/Core; adapters additionally use public Tools and Tool Protocol0.2. No source copied from v1.

Profile and operator pins hash deterministic owned semantic documents. Canonical bytes use sorted compact UTF-8 JSON, no trailing newline; array order is preserved here. Exact profiles and operators must match; schema shape alone cannot establish legality. No chemical, biological, synthesis or measured-property claim follows from synthetic validity. Representation equivalence/cache policy is B2; standalone adapters/actual owner ingress is B1.03; image/independent replacement is V1.

Tests belong in tests/legality. Replacement must retain profile digests, exact source/result attribution, failure distinctions and legal moves, or version the changed boundary. Validity never authorizes registration or promotion.

SequenceSpace reconstructs the full DTO and requires the exact DNA profile. Alphabet A/C/G/T, uppercase, length1..4096. A zero-based substitution must be within source length and use the pinned operator/source. All other fields and source bytes remain unchanged; same-base substitution is an attributable no-op. This validates a synthetic string, not a biological function.

Verified 2026-10-06 13:06:00:59 combined owner/boundary checks12.07s;172 statements and42 branches covered100% across the three packages. Independently specified moves, unknown metadata, connected cycles, invalid sites/bonds, explicit constraints and source/operator mismatch are covered. Worker/HTTP/image evidence remains B1.03/V1; tests do not establish science.


The configured adapter requires a descriptor/image binding before compute and rejects rebinding. `python -m amphora_sequence_space` exposes compute/describe (explicit --image-sha256), schema (--direction input/output), profiles (exact semantic pins), and worker (--config). One worker process handles one claimed invocation. PureToolWorker supplies existing public Runtime/Data clients, claim/lease fences, immutable publication and completion. Output is the exact canonical proposed-change JSON with no newline; neither CLI image arguments nor profile pins prove an image was deployed.

Input/output cap262144 bytes. Invalid payloads return a closed safe code without values. Dockerfile is an offline-wheel nonroot recipe, not yet image evidence. tests/capability checks schema bytes, descriptors, immutable binding, capacity, safe errors and public CLI parity. Actual worker HTTP/Research ingress and image replacement retain their later gates.

Verified 2026-10-06 13:10:07:80 combined operator/capability/boundary checks24.46s. Capability schemas100% measured coverage; adapters94% with defensive output-capacity branch unexercised. Pure domain remains100%. CLI subprocess compute/profiles/error paths pass but are not attributed to parent coverage; aggregate451statements/120branches69%. Configured worker HTTP remains the actual-owner gate.
