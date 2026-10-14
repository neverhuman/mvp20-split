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

NumericBirth reuses NumericBox/CounterRandom and the unchanged BoxVariation kernel.
Seed ordinal fixes the draw interval independently of batching. Birth ID hashes the
compact JSON array `[numeric-population-birth-v1, original digest, generation,
ordinal, operator, float.hex genes, ordered unique parents, draw start, draw end]`.
Disposition/reason/duplicate links do not change the birth ID. Supplied variation
records require verify_parent_pool against the separately retained ordered pool;
constructor checks alone do not establish ancestry or cross-birth duplicate claims.
No member's representation Artifact bytes are inferred from its genotype.

BoundEvaluation ties a named method/occurrence to the exact frozen membership,
candidate material and original release/conditions/objective policy. Its digest
uses ASCII `amphora.population/evaluation-v1`, zero, canonical EvaluationKey bytes.
Attempts are observations under the key, not new scientific identities. A terminal
result must match that key, producer run, scoped outputs and exactly one primary
method-result schema. Duplicate output ports and conflicting Artifact aliases reject.
Actual input compatibility, node/attempt/producer authenticity, evidence access and
accepted history still require Runtime/Data/Registry checks.

FrozenEvaluations rejects missing required candidate-method coverage and mixed
memberships; it permits explicit repeated occurrences within frozen limits. Its
identity binds generation/role/member IDs and sorted evaluation digests even for
empty sets. Terminal collection must cover exactly the frozen keys once, in stable
digest order; failure stays explicit. It does not decide fitness, authorize a new
occurrence from an outcome, or accept post-close updates. Coverage/identity checks
are not a scheduler, budget authority or scientific calibration.

FitnessEvidence/BoundFitness bind complete terminal method evidence to an assembly
release/policy and ordered objective units/dependencies. Missing required method
fitness cannot become a score. Weak-but-present values, including zero, stay eligible;
uncertainty labels do not independently exclude them. These checks do not reproduce
or authorize a scientific assembly model's numerical claims.

PopulationSelection requires exactly the full declared union and original pins.
Parent fitness can come from an earlier same-run/same-spec generation with exact
birth/representation references; selected-parent eligibility still requires the
separate accepted predecessor. Current offspring/seed fitness binds the current
generation. Selection calls the explicit2000-member entry of the unchanged numerical
kernel; the original256-member entry rejects larger pools. All ranks/exclusions
survive. Below minimum parents stops, below requested but at least minimum continues
with fewer parents, and infeasible members remain ranked without surviving.

RecordPages packs at64rows/131072bytes, checks8192-byte rows and64MiB/512-page closure,
and verifies schema/scope/hash/count/ordering/partitioning. RetainedEvaluations and
RetainedFitness decode supplied canonical Artifact bytes, reconstruct required key
coverage and exact observation cuts, and rerun intrinsic fitness/selection binding.
They perform no Data fetch, access check, retention, producer authentication or
accepted-predecessor lookup. A hash-valid locator is never an accepted execution.

PopulationDecision creates a source-bound selection receipt with exact recomputed
rank pages. verify_receipt compares it against independently supplied source pins
and the computed whole-pool decision. Tampered survivors/stop policy/cut/rank bytes
reject. Observation-cut hashes bind canonical retained observations including
producer attempts; semantic cross-run comparisons must separately omit operational
identities rather than pretend those byte fingerprints match.

Tests belong to `tools/evolution_search/tests/population/{specification,membership,
birth,evaluations,fitness,pages}`. Successor/process lineage, graph-step/admission,
generation acceptance and full recovery/scale remain open E1/E2-E4 deliveries.
Current adapters do not expose this module; no peer-private imports or I/O allowed.

SelectedGeneration verifies exact checkpoint/selection bytes against recomputed global
selection and selected birth Artifacts, RNG position and completed evaluation/work
counters. SuccessorContinuity replays each birth from the retained selected parents,
checks contiguous RNG, dispositions, full parent/offspring union, birth pages and
frozen evaluation membership/budgets. All population slots retain a birth disposition.
Rejected evaluation-budget births require remaining capacity below the required-method
floor; complex per-candidate allocation still belongs to the admitted graph policy.
Runtime must authenticate predecessor acceptance, counters, producer identity and
resource limits. These pure records grant no execution or budget authority. Process
material lineage/mapping lives in the independent process_mapping package.
