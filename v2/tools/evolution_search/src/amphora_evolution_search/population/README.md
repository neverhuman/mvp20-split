# Population domain

Owner: POP-01.01/E1. This module owns intrinsic population behavior beside the
existing numeric search, without changing old search entry points. Its first
delivery is OriginalPopulation, not an activated worker or accepted campaign.

OriginalPopulation validates independent original pins, unique methods/node paths,
required objective dependencies, variables/units, minimum parent policy, scope and
consistent Artifact identities. It revalidates DTOs at entry and owns the canonical
specification fingerprint. No Artifact existence/access, Registry eligibility,
admitted graph binding or expanded-work feasibility follows from this check.

`population-json-v1` is the complete validated DTO with defaults/nulls included,
sorted JSON keys, compact separators, finite numbers, UTF-8/non-ASCII preserved,
no trailing newline. Python JSON float spelling is part of this profile; it is
not RFC8785. Specification identity hashes ASCII
`amphora.population/specification-v1`, one zero byte, then canonical bytes.
Original-spec binding requires an independent original object, not a checkpoint
asserting its own authorization. Any changed pin starts a new specification.

GenerationMembership owns canonical sorted/unique membership, predecessor presence,
cohort/union bounds, representation/scope and deterministic page packing. It verifies
an explicitly supplied complete manifest/page byte closure, including counts,
schema/hash/size and canonical partitioning. It does not fetch files, prove birth
identity/content, authorize access or accept predecessors. Source-generation checks
keep seeds separate from successor parents/offspring. No page is a selection batch.

Tests belong to `tools/evolution_search/tests/population/specification` and
`membership`. Evaluation coverage, selection and successor rules are subsequent E1 deliveries.
Current adapters do not expose this module; no peer-private imports or I/O allowed.
