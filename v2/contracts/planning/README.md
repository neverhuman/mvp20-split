# Planning public contracts

Version0.1.0, BP-07.01/B1.01. These DTOs describe scoped context, reviewed model/configuration pins, logical requests, physical attempt identity and observed usage. Dependencies are public core and graph-runtime contracts plus Pydantic. No provider SDK, persistence, credential, endpoint, domain policy or execution acceptance belongs here.

Request collections are bounded immutable tuples; strict scalar validation, forbidden extras and schema_version1 apply. Usage fields may be null: unknown is not zero. JSON Schema publication uses dev/export_schemas.py; additive planning roots preserve predecessor bytes. Context relationships and immutable fingerprints belong to Agent Planning's context domain. A DTO does not authorize source reads, provider egress, spend, acceptance or real science.

Owned tests: tests/test_wire.py and literal fixture. Rebuild acceptance preserves validation/serialization schemas, exact public exports and strict negative cases; downstream domain tests verify relationships separately. Changes to existing published fields require deliberate version/compatibility evidence. Provider outcomes/proposal envelopes are subsequent B1.02 scope.
