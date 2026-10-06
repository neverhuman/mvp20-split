# Synthetic polymer space

- Owner: BP-08.03/B1.02; release0.1.0, pure domain verification passed.
- Design: [Representation and fitness](../../docs/Architecture/Campaigns/Representation_Fitness.md).

This independent package owns legality and one proposed move for the synthetic polymer encoding. Domain objects validate complete inputs, preserve scope/profile and retain a hash of the exact canonical source. Public DTOs serialize results; no SQL, I/O, service/private sibling imports, global RNG, scheduler, scientific eligibility or hidden loop belongs here. Dependencies are only public candidate_spaces/Core. No source copied from v1.

Profile and operator pins hash deterministic owned semantic documents. Canonical bytes use sorted compact UTF-8 JSON, no trailing newline; array order is preserved here. Exact profiles and operators must match; schema shape alone cannot establish legality. No chemical, biological, synthesis or measured-property claim follows from synthetic validity. Representation equivalence/cache policy is B2; standalone adapters/actual owner ingress is B1.03; image/independent replacement is V1.

Tests belong in tests/legality. Replacement must retain profile digests, exact source/result attribution, failure distinctions and legal moves, or version the changed boundary. Validity never authorizes registration or promotion.

PolymerSpace owns unique labeled units/sites, a connected acyclic undirected tree, declared unit references and no duplicate/self edges. Explicit branching must agree with degrees; explicitly alternating neighbors must differ. End groups name distinct terminal sites. Known composition covers all declared units and matches blueprint site fractions within1e-12; changing a site recomputes those fractions only when composition was known. Blueprint fractions and DP metadata are synthetic descriptors, not measured material composition. Known number/weight averages require ordered values and any known dispersity must match their ratio (1e-9 relative tolerance); missing fields stay missing. Replacing a label with opaque BigSMILES present rejects unless it is a no-op: an independent encoding provider must recompute it. Tacticity, nominal DP and other descriptive metadata are retained, not scientifically verified.

Verified 2026-10-06 13:06:00:59 combined owner/boundary checks12.07s;172 statements and42 branches covered100% across the three packages. Independently specified moves, unknown metadata, connected cycles, invalid sites/bonds, explicit constraints and source/operator mismatch are covered. Worker/HTTP/image evidence remains B1.03/V1; tests do not establish science.
