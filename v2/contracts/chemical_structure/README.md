# Chemical structure contracts

Owner: UI-02/P1.1. Public package0.1.0. Transport validation only; no RDKit,
chemical inference, database, ranking or candidate admission policy.
Design: [approved boundary](../../docs/Build%20Plans/UI-02.01%20Chemical%20structure%20boundary%20decision.md).

StructureRequest binds supplied SMILES to exact CandidateRevisionRef/scope and
semantic profile. StructureResult binds that identity and exact request byte digest
to either a derived bundle or a safe invalid/unsupported/error code. Failure cannot
contain a formula, depiction or structural authority. A successful bundle contains
canonical isomeric SMILES, indexed atom/bond graph, isotope-aware formula, explicit
net charge, method/environment pins and a bounded base64 PNG. Formula/depiction
share one retained result; neither is a property prediction or recommendation.

Public schema roots: chemical-structure.request/result under contracts/schemas/v1.
Semantic profile: profiles/finite-smiles-2d-v1.json (exact bytes SHA-256). This
profile rejects features the normalized graph cannot preserve. Unspecified stereo
is preserved as unspecified and visibly warned; it is never completed. Supplied
finite oligomers must include exact end groups. Repeat units/distributions/mixtures
remain unsupported. Candidate registration is separately opt-in in Research.

DTO validation enforces wire types, bounds, closed vocabulary and equal scopes.
Consumers still enforce exact JSON byte limits, pinned profiles, graph topology,
chemistry, base64 decoded size/PNG structure/hash and source attribution. DTO success
alone is not chemical validation or accepted producer authority. Runtime accepted
execution plus current Data rights/bytes is required to attribute the derivation.
No result-internal hash authenticates itself. Tool owns chemical behavior; Research
owns admission; Studio owns safe rights-aware display. No new owner storage.

Replacement gates: owned wire tests plus dev/schema_publication compatibility pins
for every predecessor schema. Existing synthetic schemas/authority are unchanged.
Tool, Research integration and browser acceptance remain UI-02/P1.2-P4 work.
