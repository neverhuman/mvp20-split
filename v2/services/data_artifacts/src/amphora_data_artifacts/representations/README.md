# Representation domain

Design: [Data representations](../../../../../docs/Architecture/Data/Representations.md). Delivery: BP-06.05/B1.01-.02.

The pure domain files own immutable encoding profiles, exact input/work identities, canonical vector bytes, a deterministic synthetic encoder and explicit public wire mappings. They perform no I/O. The separately bounded [storage module](storage/README.md) adds private registry/cache persistence under B1.03. The [bindings module](bindings/README.md) adds source preflight, durable state and bounded Artifact publication. Optional authenticated representation APIs are implemented under B1.05; independent installed HTTP proof and retrieval remain subsequent milestones.

`RepresentationProfile` groups encoder identity, input contract, pipeline, vector space, applicability, limitations and determinism. Every descriptor field participates in its canonical sorted UTF-8 JSON digest. References use wire version 1; the runtime descriptor digest includes the interpreter version, build and platform. Compatibility requires the exact same profile and explicit shared query/document role. Equal dimensions grant no compatibility. Unsupported fixture profiles fail without fallback.

`EncodingInput` preserves 1..65536 strict UTF-8 bytes and an optional context digest. `EncodingWorkIdentity.prepare` requires declared context presence to match the input and includes scope, complete profile, exact input digest and context digest. This identity authorizes nothing. Future source bindings must retain separate source provenance and enforce current rights even when computation is reused.

`Float32Vector` retains 1..4096 finite IEEE754 binary32 values in little-endian bytes. Conversion explicitly rounds and canonicalizes zero; raw nonfinite values, negative zero and incorrect payload lengths fail. Normalization is the encoder's responsibility, not inferred from the vector's declared space.

`FixtureEncoder` counts each original UTF-8 byte in its byte-modulo-16 bin, optionally divides by the L2 norm, then converts to binary32. It uses Dot as its declared metric. There is no tokenization, preprocessing, truncation, hidden prompt or contextual encoding. Its profile pins the algorithm and runtime. This is a software fixture with no semantic or scientific similarity claim and no cross-provider reproducibility guarantee.

Failures use `RepresentationError` with bounded stable codes. Frozen objects and validated nested public core references protect the normal construction boundary; callers must not bypass Python constructors. Descriptor dictionaries are fresh projections. Dependencies are the standard library, public core contracts and Pydantic validation; no peer implementation is imported.

B1.02 adds `EncodedRepresentation`, which groups complete profile, input/context digests and the exact vector. `mapping` revalidates public DTOs (including copied/forged model instances), maps full profiles and checks retained vector scope/profile, dimensions/dtype, canonical bytes and digest. Public `contracts/representations` is the added dependency. Mapping a document establishes its internal interpretation only; Artifact authentication, source attribution and current rights remain mandatory future owner fences. The wire profile does not replace this module's behavior-owning objects. Source/status projections are public shapes awaiting their B1.03/B1.04 owner implementation.

Replacement acceptance belongs to `tests/representations/`: literal byte histograms, explicit binary32 bytes and normalization, original-byte preservation, every profile component changing identity, scope/context separation, incompatible pairing, unsupported encoders, malformed references and numeric/input bounds. Run the owner selector with `--module data-artifacts --area representations`; this does not prove storage single-flight, HTTP compatibility, rights enforcement or scientific relevance.

B1.04a adds the separately scoped [binding identity/publication document/receipt checks](bindings/README.md). These pure objects do not publish or authorize source use; later workflow tasks own durable effects.


## Authenticated service boundary

`service.RepresentationService` groups profile registry, encoding workflow and current binding views. `api.representation_router` is attached only when explicitly configured. `hosting.content_policy/probe` owns the vector validator and representation-table readiness checks; it neither migrates nor registers records. The main Host exposes a strict boolean `representations` flag, false by default, independently of acquisition routes for previously retained sources. Enabling it allows representation_manage/read/encode grants; encoding additionally needs read, source_history, upload and finalize. Credentials determine scope and actor, never request payloads.

| Route under /v1/representations | Authority and result |
|---|---|
| GET /available-profiles | representation_read; runtime-pinned reviewed synthetic profile descriptors, not registry writes |
| POST /profiles | representation_manage; EncodingProfile -> immutable scoped EncodingProfileRef |
| GET /profiles/{profile_id}/{version}?sha256=... | representation_read; exact scoped/digest-qualified EncodingProfile |
| POST /encodings | representation_encode plus named dependencies; EncodeSourceRequest ->202 pending or200 published EncodingStatus |
| GET /encodings/{encoding_id} | representation_read; actor-specific original status, with no execution side effects |
| GET /bindings/{binding_id} | representation_read/read; current ancestry rights checked before binding metadata leaves Data |

Registration is inert metadata: it cannot install encoder code, override an existing profile or confer scientific validity. The current available list contains only the reviewed fixture for the running interpreter. Runtime/profile changes must be explicitly versioned; conflicts never overwrite history. A status GET does not advance pending work; retry the original POST for bounded recovery. Existing Artifact content routes remain the only payload read interface and enforce current rights separately. Binding metadata can be shared by permitted actors in scope; original request history remains actor-specific.

Authentication/grants precede body parsing. JSON bodies are bounded to65536 bytes and5s and reject duplicate keys, nonfinite values and excessive nesting. DTO shape errors422, wrong content type415, body limit413, incomplete body408, immutable/source conflicts409, missing identities404 and current rights403 remain explicit. Owner database/filesystem failures use the existing safe503 handler. Successful responses are no-store. Public DTO versions/schema bytes are unchanged.

Tests: `tests/representations/test_api.py` runs actual Data/PG through TestClient, including scoped/digest-qualified profiles, malformed/unprivileged requests, pending status versus POST advancement, inert unreviewed profiles, source-span conflict, a real parser deadline, permitted cross-actor binding access and revoked binding versus immutable historical status. `test_host.py` proves enabled/disabled/ill-typed configuration, required-table readiness and no hidden profile registration. These are B1.05 transport/configuration tests; B1.06 owns real independently installed HTTP processes.

B1.05 verification:185 source/452 independent installed cases and14 dev checks pass. The four new boundary modules cover all126 statements/14 branches; aggregate representation coverage1247/1250 statements and122/126 branches retains the prior B3 gaps. Package0.18.0, public schemas andartifact_0009 remain compatible.
