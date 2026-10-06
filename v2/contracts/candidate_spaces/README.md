# Synthetic candidate-space contracts

- Owner: BP-08.03/B1.01; release0.1.0, shape/publication verification passed.
- Design: [Representation and fitness](../../docs/Architecture/Campaigns/Representation_Fitness.md).

This package owns immutable, extra-forbidden transport for three distinct synthetic candidate encodings, their typed single moves and proposed change output. It depends only on public Core and Pydantic. Vector embedding contracts/representations and existing numerical search/checkpoint schemas remain unchanged.

Numeric coordinates retain bounds, units and values. Polymer blueprints retain labeled repeat units, sites/bonds, optional composition and explicit nullable arrangement/tacticity/degree/distribution/branching/end groups/BigSMILES. These are toy labeled sites, not atoms or chemically validated molecules. Missing metadata cannot silently become random/atactic. Preparation and morphology remain separate Research material-state records. DNA encoding accepts uppercase A/C/G/T under its declared alphabet; it has no polymer fields.

Required nullable fields must be present as null when unknown. DTO shape checks do not enforce graph connectivity, unique identifiers, coordinate bounds relative to one another, distribution coherence, profile authenticity, operator legality or equivalence. Focused tool domain objects own these behaviors. Schema success is not candidate registration, scientific validity, synthesis feasibility, accepted Runtime completion or authorization to use evidence. Source_sha256 records canonical source bytes but grants no access.

Seven exported root models cover three designs, three requests and a proposed change. Module-owned tests compare Python and JSON Schema validation, explicit unknown preservation, distinct kinds and bounded input failures. New versions must preserve old schema bytes or explicitly version incompatible boundaries. Domain legality, actual worker/Research integration and independent replacement remain named BP-08.03 gates.

Verified 2026-10-06 12:59:00: 36 contract/publication/boundary checks passed25.91s; 584 schemas, all570 predecessors unchanged. All99 declaration statements executed, zero branches; this is transport import coverage, not domain legality. Invalid alphabet, foreign fields/moves, missing nullable metadata and trailing newline reject in Python and JSON Schema.
