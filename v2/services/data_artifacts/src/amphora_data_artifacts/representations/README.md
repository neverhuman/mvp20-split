# Representation domain

Design: [Data representations](../../../../../docs/Architecture/Data/Representations.md). Delivery: BP-06.05/B1.01-.02.

The pure domain files own immutable encoding profiles, exact input/work identities, canonical vector bytes, a deterministic synthetic encoder and explicit public wire mappings. They perform no I/O. The separately bounded [storage module](storage/README.md) adds private registry/cache persistence under B1.03. There is no hosted representation API, source-binding publication or retrieval implementation yet.

`RepresentationProfile` groups encoder identity, input contract, pipeline, vector space, applicability, limitations and determinism. Every descriptor field participates in its canonical sorted UTF-8 JSON digest. References use wire version 1; the runtime descriptor digest includes the interpreter version, build and platform. Compatibility requires the exact same profile and explicit shared query/document role. Equal dimensions grant no compatibility. Unsupported fixture profiles fail without fallback.

`EncodingInput` preserves 1..65536 strict UTF-8 bytes and an optional context digest. `EncodingWorkIdentity.prepare` requires declared context presence to match the input and includes scope, complete profile, exact input digest and context digest. This identity authorizes nothing. Future source bindings must retain separate source provenance and enforce current rights even when computation is reused.

`Float32Vector` retains 1..4096 finite IEEE754 binary32 values in little-endian bytes. Conversion explicitly rounds and canonicalizes zero; raw nonfinite values, negative zero and incorrect payload lengths fail. Normalization is the encoder's responsibility, not inferred from the vector's declared space.

`FixtureEncoder` counts each original UTF-8 byte in its byte-modulo-16 bin, optionally divides by the L2 norm, then converts to binary32. It uses Dot as its declared metric. There is no tokenization, preprocessing, truncation, hidden prompt or contextual encoding. Its profile pins the algorithm and runtime. This is a software fixture with no semantic or scientific similarity claim and no cross-provider reproducibility guarantee.

Failures use `RepresentationError` with bounded stable codes. Frozen objects and validated nested public core references protect the normal construction boundary; callers must not bypass Python constructors. Descriptor dictionaries are fresh projections. Dependencies are the standard library, public core contracts and Pydantic validation; no peer implementation is imported.

B1.02 adds `EncodedRepresentation`, which groups complete profile, input/context digests and the exact vector. `mapping` revalidates public DTOs (including copied/forged model instances), maps full profiles and checks retained vector scope/profile, dimensions/dtype, canonical bytes and digest. Public `contracts/representations` is the added dependency. Mapping a document establishes its internal interpretation only; Artifact authentication, source attribution and current rights remain mandatory future owner fences. The wire profile does not replace this module's behavior-owning objects. Source/status projections are public shapes awaiting their B1.03/B1.04 owner implementation.

Replacement acceptance belongs to `tests/representations/`: literal byte histograms, explicit binary32 bytes and normalization, original-byte preservation, every profile component changing identity, scope/context separation, incompatible pairing, unsupported encoders, malformed references and numeric/input bounds. Run the owner selector with `--module data-artifacts --area representations`; this does not prove storage single-flight, HTTP compatibility, rights enforcement or scientific relevance.

B1.04a adds the separately scoped [binding identity/publication document/receipt checks](bindings/README.md). These pure objects do not publish or authorize source use; later workflow tasks own durable effects.
