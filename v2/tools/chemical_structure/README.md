# Chemical structure tool

UI-02/P1.2 verified:32 independent copied tests, fresh-process determinism, exact schema bytes and dependency isolation. Independent package0.1.0; no Research/Runtime service imports,
SQL, external chemistry calls, model calls or persistent state. Design:
[approved chemical boundary](../../docs/Build%20Plans/UI-02.01%20Chemical%20structure%20boundary%20decision.md).

Public CLI: compute (bounded JSON stdin), schema --kind input/output, describe
--image-sha256 <measured image digest>, worker --config <public SDK configuration>.
Capability chemistry.chemical-structure consumes the public request and emits result
through Tool Protocol0.2.0. Descriptor authority ceiling evidence_proposal does not
certify scientific applicability; Runtime alone accepts execution. No ranking,
generation, synthesizability or biological efficacy claim.

DerivationProfile pins exact semantic bytes and locked RDKit/numpy/Pillow versions;
ParsedMolecule owns supported feature/size checks and canonical atom graph;
DisplayBundle derives formula and inert PNG from that same normalized molecule;
Derivation binds the original request bytes and candidate to success or failure.
RDKit2025.9.6 is private to this tool. Atom-index order is canonical-SMILES parse
order. Explicit H atoms/isotopes, formal charge and supported stereo are retained.
No tautomer/protonation correction. Missing stereo remains unspecified with a warning.
Unrepresentable features and invalid structures produce explicit failure outcomes.
Malformed envelope/oversized input fails the SDK invocation with a safe code.

PNG800x600, maximum131072bytes; JSON maximum262144bytes. No SVG/HTML, fetching or
embedded molecule metadata. Request hashes are attribution claims until matched
against exact Data input bytes and accepted Runtime producer. Current rights and
registration remain consumer responsibilities. Profile/environment hashes are
byte-pinned; image digest is supplied externally, never guessed from source.

Owned tests: tests/kernel. Replacement must preserve goldens for isotope/charge/H,
stereo distinction, formula/graph/image consistency, source identity, failure modes,
public schema bytes and SDK transport. Same pinned environment must be deterministic;
other toolkit/platform releases need separate qualification. Source tests do not
prove independent installation or actual graph/Research acceptance (P1.4).
Reference APIs: https://www.rdkit.org/docs/GettingStartedInPython.html and
https://www.rdkit.org/docs/source/rdkit.Chem.rdMolDescriptors.html.
