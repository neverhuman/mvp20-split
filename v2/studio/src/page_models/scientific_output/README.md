# Scientific output projection

Owner: Studio / UI-01.03 E3. Selected Runtime output ArtifactRefs provide identity;
Data remains content authority. DataProvenanceClient.jsonArtifact verifies exact
metadata, bounded media/size, current content permission and SHA-256 before JSON
parsing. This model additionally pins the exact published tool output schema hash
and validates against its public JSON schema before rendering any scientific values.
Schema snapshots in schemas.ts come from tools' published schemas, not private code.

Only Hansen solvency0.1 and Arrhenius viscosity0.1 outputs are supported. New hashes
require an explicit adapter update. Candidate identity must match retained input
identity. The projection owns named quantities/units; it never recomputes scores,
infers applicability or promotes unvalidated_screen to measured/proven science.
All parameters, intermediate values, procedures and limitations are tool records.

RequestLane fences late responses. Rebind clears results; denial/failure clears
protected values; hiding/disposal cancels reads. No owner commands, model calls,
scientific ranking or parameter estimation. Owned tests cover exact schema pins,
identity mismatch, late responses, denial and malformed content. Actual served
scientific run and browser qualification are separate integration evidence.

Schemas are exact local copies of the two published public output files. scripts/scientific-validators.mjs generates hashes and standalone validators at build time; npm test checks reproducibility. Runtime schema compilation is prohibited by CSP. Owned tests run without tool source trees. Public snapshot equality is independently checked during integration review.
