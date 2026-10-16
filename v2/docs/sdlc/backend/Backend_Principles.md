# Backend implementation principles

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.

Keep transport handlers focused on decoding, authentication, dispatch and safe responses. Application handlers own use-case orchestration and transaction boundaries; domain objects own invariants; adapters implement declared ports. The architectural ownership and dependency graph remain in [Interfaces and Code Boundaries](../../Architecture/System/Interfaces_and_Code_Boundaries.md). Historical broad rules that every scientific tool is stateless are not imported: tools retain their declared state/effect contracts.

## Objects and domain behavior

- Pydantic schemas and frontend API types are boundary DTOs. They are valid for validation, serialization, route contracts, and UI transport, but they are not a substitute for domain objects that own behavior.
- Do not add new wide schema/DTO constructors as the primary implementation shape. If constructing a record needs many loosely related fields, first look for the missing domain object, value object, projection object, policy object, or builder/factory method that should group the behavior and defaults.
- Group behavior with the data that owns its failure modes. Counts, latest-item selection, evidence status, policy recommendations, privacy/disclosure decisions, replay fingerprints, and lane-specific defaults should live behind focused objects or policy classes when they have nontrivial rules.
- Schema records should generally be produced from domain/projection objects through explicit conversion methods or mappers. Accept direct schema construction only for small boundary responses, tests, or simple pass-through records where no behavior is hiding in the call site.
- When touching existing wide constructor patterns, prefer incremental repair: introduce a focused value object or factory for the behavior being changed, add direct tests for that behavior, and keep the outward API schema stable.

## Dependency direction

Domain logic cannot import the web framework or provider SDK as its primary behavior model. DTOs validate/serialize the boundary; domain objects enforce invariants. Infrastructure returns explicit failure/uncertainty states rather than exceptions that secretly alter scientific disposition. Query projections may denormalize for performance but cannot become command authority.
