# dgeba-oligomer-eew-series-v1 (AUDIT_ONLY)

Second-signal for amphora-molecule-property. Independent RDKit-2026.03.2 reference
implementation extending the module's canonical EEW structure rule (EEW = M / n_epoxide)
from the pure n=0 DGEBA monomer to the linear difunctional DGEBA **oligomer series**.

- **G1 monomer anchor** reproduces the shipped Phase-0 expected EEW 170.2 g/eq
  (abs err 0.01, bar 0.5).
- **G2 oligomer additivity + difunctionality**: four independently RDKit-built oligomers
  n=0..3 (C21H24O4, C39H44O7, C57H64O10, C75H84O13) each carry EXACTLY 2 terminal epoxides;
  the bisphenol-A / 2-hydroxypropylene repeat mass is a byte-exact constant **284.355 g/mol**
  across all three adjacent pairs (spread 0.0, additivity deviation 0.0), so
  **EEW(n) = 170.21 + 142.18·n** exactly.
- **G3 commercial-band consistency**: the mole-weighted number-average EEW_bar = 170.21 +
  142.18·n_bar maps every published commercial DGEBA EEW band (liquid Epon 828/DER 331,
  near-monomer DER 332, semisolid Epon 1001F, solid Epon 1004F) to a non-negative n_bar that
  overlaps the independently published number-average degree of polymerization — mechanistically
  explaining why commercial grades read EEW > 170.2. This is CORROBORATIVE ONLY: the exact EEW
  of a polydisperse mixture requires MEASURED composition, so it does NOT overturn the module's
  `commercial_product_claim_locked=true` lock.
- **G4 fail-closed**: bisphenol-A (0 epoxide), phenyl glycidyl ether (1), mono-hydrolyzed DGEBA
  (1), fully advanced DGEBA-diol (0) all correctly excluded as non-difunctional exact anchors.
- IUPAC-2021 atomic-weight uncertainty <= 0.0085 g/eq on EEW(n=0) => 0.5 bar carries ~59x headroom.

Sources: Lee & Neville 1967 (Handbook of Epoxy Resins); May 1988 (ISBN 0-8247-7690-9);
Ellis 1993 (ISBN 0-7514-0095-0); ASTM D1652; Prohaska et al. Pure Appl. Chem. 94(5):573 (2022)
doi:10.1515/pac-2019-0603.

Files: compute_dgeba_oligomer.py (deterministic), diagnostic.canonical.json +
diagnostic.runB.json (byte-identical two-replay, sha256 15b33c0d…), sign_dgeba_oligomer.py,
dgeba_oligomer_eew_series_receipt.v1.json (DSSE Ed25519, local audit key local-9028773f…,
NOT trust-anchored). Promotes nothing; manifest untouched 66/11.
