# amine-class-active-nh-robustness-v1 (AUDIT_ONLY)

Second-signal for amphora-molecule-property. Independent RDKit-2026.03.2 reference
implementation of the module rule EEW=M/n_epoxide, AHEW=M/n_active_amine_NH
(2x1deg + 1x2deg + 0x3deg; amide/imine/nitrile/nitro/aromatic-ring N and -OH
excluded).

- Reproduces shipped Phase-0 anchors: 3/3 exact (max abs err 0.0338 g/eq, bar 0.5),
  6/6 monodisperse within 6.0 g/eq.
- Extends the falsifiable hypothesis from 3 fitted points to a 13-hardener grid
  (DETA/TETA/TEPA/EDA/IPDA/HMDA/mXDA/piperazine/AEP/DACH/aniline/MDA/DDS):
  100% correct active-N-H integer, theoretical AHEW within 0.3% of published refs.
- 7/7 non-amine controls fail-closed to 0; ethanolamine -OH-exclusion probe correct.
- IUPAC-2021 atomic-weight uncertainty <=0.011 g/eq => bar carries >=47x headroom.

Sources: Lee & Neville 1967; May 1988 (ISBN 0-8247-7690-9); Ellis 1993
(ISBN 0-7514-0095-0); ASTM D1652; Prohaska et al. Pure Appl. Chem. 94(5):573 (2022)
doi:10.1515/pac-2019-0603.

Files: compute_amine_class.py (deterministic), diagnostic.canonical.json +
diagnostic.runB.json (byte-identical two-replay), sign_amine_class.py,
amine_class_active_nh_robustness_receipt.v1.json (DSSE Ed25519, local audit key
local-9028773f..., NOT trust-anchored). Promotes nothing; manifest untouched 66/11.
