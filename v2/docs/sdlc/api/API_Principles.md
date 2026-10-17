# API and contract development

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.

The architectural validation/acceptance pipeline and version bindings remain in [Contract Architecture](../../Architecture/System/Contract_Architecture.md). This document owns the engineering steps used to implement them; it introduces no routes or new authority.


## Purpose and handoff

| Element | Meaning |
|---|---|
| Why it exists | Make independently changing producers and consumers exchange bounded, unambiguous data. |
| Inputs | Operation purpose, semantic owner, callers, authority and compatibility obligations. |
| Output | Public request/response/error contracts, mappings and consumer/negative-case evidence. |
| Completion test | Consumers can interpret success, rejection and replay under the declared version; required compatibility gates pass. |

## Validation and safe failures

Use strict validation at internal command and invocation boundaries, reject unexpected fields in closed command contracts and define any extensible metadata explicitly. Normalize source-specific data in acquisition adapters, preserving raw input, conversion identity and provenance. Never silently repair scientific units or representations merely to pass validation. [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) reduces coercion but differs between Python and JSON inputs, so both boundary paths need fixtures.

Structural validity checks required fields, tags, ranges and formats. Semantic validity checks units, representation compatibility, port meaning, graph dependencies and scientific applicability. Transactional acceptance checks live authority, expected revision, budget and attempt fencing. A structurally valid molecule is not necessarily synthesizable; a well-shaped knowledge assertion is not accepted evidence.

Return stable reason codes, safe field paths and the validation stage. Do not expose raw private payloads through validation errors or logs. Bound input size, graph depth, collection length and error output before accepting a contract as safe to process.

## Schema and consumer workflow

Name the semantic owner and exact contract/version before adding a route. Use public contracts and explicit domain mappers; handlers must not access peer-private tables or implementation modules.

Publish reproducible input/output schemas and semantic valid/invalid fixtures; generate transport types from that surface. Do not edit generated files to conceal a contract mismatch. Local policy/semantic checks remain authoritative even when provider schemas omit unsupported keywords.

Check producer/consumer compatibility explicitly, including unknown fields, omitted versus null, numeric fidelity, canonical bytes and error bounds. Preserve predecessor schema bytes unless an intentional, reviewed version change requires otherwise.

Exercise authentication/scope rejection, malformed and oversized input, revision/idempotency collisions, unsupported versions and relevant concurrency/restart paths. A read endpoint must preserve scoped read authority without acquiring mutation rights. Endpoint-specific cache, pagination and snapshot guarantees belong in its public contract.

Record affected consumers, migrations, replay obligations and replacement proof in the owning plan and module README. See [build and release](../delivery/Build_and_Release.md).
