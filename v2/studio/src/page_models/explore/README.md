# Explore page state

Implemented boundary: Studio0.7, BP-06.06. Internal researchers inspect exact domain/scientific context through independently owned public Knowledge, Research and Data clients. Host owns explicit context selection, model lifetime and disposal. Code here owns view state and relationships; no database, owner credential, scientific mutation or result-cache authority.

`ExploreContext` validates graph-only, laboratory-only or combined same-project pins. `ExploreProjection` freezes render snapshots. `ExploreModel` owns eleven independently loaded lanes: search, neighborhood, detail, specimens, properties, series, source, artifact, trace, derivation and material. The optional Research record client supplies full material states; absent support returns unavailable. Transport owns strict schema/identity/hash checking.

Binding, hiding, disposal and authority/query conflicts cancel requests and clear protected data. Generation checks reject late uncancellable replies. Reentrant subscribers cannot start work in a removed context. Pages replace rather than accumulate. Inactive modes suspend their loaders. `clearInspection` resets all inspector lanes to idle; a new graph detail, prepared-state selection or replacement Artifact clears the previous selection. Material reads use exact references and current owner rights. Series reads require a selected observation.

`scene.ts` draws only exact returned assertion endpoints and preserves missing-context counts. `measurement.ts` retains lexical values, uncertainty units, censor bounds, missing reasons and original series order. No unreported time, zero fitness or converted units are synthesized.

## Scientific comparison

`comparison.ts` consumes one bounded specimen page and one property page from the same pinned experiment. It joins exact sample revisions; omitted, unbound and conflicting specimen context stay explicit. Selected rows preserve measurement DTOs, source, quality and order. Scope, duplicate and selected-observation checks prevent identity collapse. Full preparation comes from the independent material read.

`ScientificPair` reports identity relationships for sample, candidate, prepared state, method, applicability, readout, units, experiment and role. Matching nominal candidate identity cannot erase state differences. Identical versus distinct evidence is separate from context identity. Every reuse decision remains owner-policy-required; this display classification is not an eligibility verdict or implemented cache.

Tests belong to `tests/page_models/explore.test.ts`, `explore_projection.test.ts` and `scientific_comparison.test.ts`. They cover exact pins, context/identity rejection, immutable selection, bounded replacement, races, hidden/disposed/reentrant lifecycles, material loader absence and late responses, and unchanged missing/censored/quality semantics. Transport tests own wire/hash/deadline checks. Actual-owner and browser proof are separate tiers; see [presentation](../../presentation/explore/README.md) and BP-06 evidence for measured coverage/checkpoints. Replacement must preserve these failure/context semantics before cutover.
