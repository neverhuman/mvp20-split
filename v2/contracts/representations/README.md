# Representation contracts

Version 0.1.0; wire version 1. [Architecture](../../docs/Architecture/Data/Representations.md), [owning plan](../../docs/Build%20Plans/BP-06/BP-06.05%20Representation%20reuse%20and%20retrieval.md).

This independently packaged public boundary serializes complete encoding profiles, scoped profile references, exact source-span encoding requests, retained vector documents, attributable source bindings and pending/published status. It depends only on Pydantic and public Core/Evidence contracts. Import the package root; private source modules are not a consumer API.

Profiles expose every result-affecting encoder/input/pipeline/space choice plus applicability, limitations and determinism. Registry identity adds scope, id/version and a Data-verified complete-profile digest. Equal dimensions do not establish compatibility. Source requests cannot supply vectors, cache-hit claims, source rights or scientific authority.

Vector Artifact documents retain profile/input/context identity and bounded lowercase hexadecimal binary32 payloads. Schema validation checks shape only: Data validates exact byte length, finiteness, canonical zero, digest, registry scope/profile and context consistency. `representation_vector_schema()` returns the exact generated validation-schema digest used by Artifact publication. Vector payload digest alone is not a full representation identity.

Bindings retain their own scoped identity, profile, source span and derived Artifact. Independent sources never gain rights from shared content hashes. The discriminated status outcome prevents pending results from exposing a binding and requires a binding for published results. Data must still verify actor, source/span, all cross-field references, attribution and publication before returning that state.

There is no encoder, database, API, cache, permission policy or backend here. Schemas grant no scientific validity, executable authority or provenance trust. Initial Data support is a bounded synthetic fixture; contextual/general scientific profiles are descriptors, not evidence of supported providers. Generation/retrieval contracts remain B2 work.

`examples/` contains synthetic wire fixtures, not retained owner records. The example binding digest is a placeholder for later owner verification. Profile/runtime references are fixed example identities rather than a claim about every consumer's machine. `tests/` checks examples against both published schema modes, rejects malformed or authority-injecting inputs and verifies exact schema identity. Run `dev/run_tests.py --module representations`; Data's mapping tests are separately owned under `--module data-artifacts --area representations`.

Compatibility is additive: seven new roots publish fourteen input/output schemas under `representations.*`; the preceding 406 schema files must remain byte-identical. No existing public schema, command bytes or Data migration changes. A replacement must preserve wire names, bounds, discriminated outcomes, schema identities and owner rejection of semantically inconsistent documents.
