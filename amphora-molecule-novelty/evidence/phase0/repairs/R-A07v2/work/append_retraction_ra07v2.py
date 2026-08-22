#!/usr/bin/env python3
"""Append the R-A07v2 section to amphora-molecule-novelty's RETRACTION-INDEX.md.
Strictly append-only: never rewrites or removes pre-existing content. Idempotent."""
import hashlib
from pathlib import Path

MOD = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-molecule-novelty")
IDX = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
MARK = "## R-A07v2"

NEW = f"""{MARK} -- 2026-08-04 (repair_mode: interactive-2026-08-04)

Superseding receipt:
`evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json`
sha256 `45b75c2a1a534d6ec0667e55e5ad130ecaa66bdaa60bb5cd12088a1af694328e`

| Claim | Refuted-by receipt path | Superseded-by | Date |
|---|---|---|---|
| `R-A07`: `corrected_family_alpha_table_deduped_350` is "recomputed ... under both corrections". **False for three of the four fingerprint families**: the IPDA structural correction (C9H20N2 to real isophorone diamine C10H22N2) was applied only inside a separate `morgan_r2_2048`-only side table, so the `maccs_166` / `atompair_2048` / `toptorsion_2048` IPDA cells of the shipped table were still computed on the refuted structure. **Corrected: the complete four-family table is republished with the corrected structure in every family, and the one undisclosed flip it surfaces -- `atompair_2048 / IPDA / alpha=0.01`, conformal p 0.011396 to 0.008547, NOVEL false to true -- is disclosed.** | `evidence/phase0/repairs/V-A07/done/v-a07-independent-verify-of-r-a07-receipt.v1.dsse.json` (verdict CLAIM_REFUTED; 11/11 self-tests passed and R-A07's 5 declared flip cells reproduced before the defect was found) | `evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json` | 2026-08-04 |

**The top-level 5/5-NOVEL headline STANDS.** All 5 candidates remain below the 0.40
Bajusz-Racz-Heberger Morgan(r2,2048) Tanimoto cutoff on the deduplicated 350-distinct corpus
with the corrected structure (NN range 0.1579-0.3929), and the IPDA structural fix leaves the
Morgan nearest-neighbour similarity numerically unchanged at 0.16666666666666666 -- the
headline never depended on any defective cell.

Complete flip disclosure published in the v2 receipt (four difference sets, so no flip can
hide in a comparison that was never made):

- **A** dedup effect, old structure (R-A07's declared set, reproduced exactly): **5** cells --
  `maccs_166/DDS/a0.05`, `maccs_166/IPDA/a0.01`, `atompair_2048/DDS/a0.2`,
  `atompair_2048/IPDA/a0.01`, `atompair_2048/m-XDA/a0.01`.
- **B** structural effect, undisclosed by R-A07, found by V-A07: **1** cell --
  `atompair_2048/IPDA/a0.01` (NOVEL false to true).
- **C** net, originally-signed to fully-corrected: **4** cells. `atompair_2048/IPDA/a0.01`
  appears in both A and B and therefore cancels in the net view -- two independent errors
  offset -- so it is disclosed in A and B regardless.
- **D** dedup effect isolated under correct chemistry: **4** cells.

Constructive reproduction of V-A07's diagnosis: all 20 cells of R-A07's shipped four-family
table reproduce exactly when the OLD, refuted C9H20N2 string is used in every family.
Isophorone diamine was re-derived a third independent way (`NCC1(C)CC(N)CC(C)(C)C1`, written
from the exocyclic aminomethyl carbon) and pinned to the in-tree ground truth
`amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json`
(sha256 `b1a08e856cab233c69c09673ed0d96a40c38346753afae4ad415b5948edaa9a8`).

Not superseded, carried forward reproduced exactly: the 443 to 350 canonical deduplication
(36 duplicate groups / 129 duplicate rows, dedup-set sha256
`74513e30071335d097ee83315f5b21249da86ea6a5d61e98a27d07b631593dce`), R-A07's 5 declared flip
cells, its DDS cross-family count 0/4 at alpha=0.05, and its top-level 5/5-NOVEL result.

Superseded original (verified byte-intact, NOT deleted or modified):

- `evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json`
  sha256 `72496a149815075618fd22b4e6fc60cae4953d81f7100a67b394b01b59583198`

Scope: AUDIT_ONLY, ceiling EVIDENCE_ONLY. No authority promoted, no scientific_readiness
flipped, no manifest, ledger, mission front-matter, or locked dataset touched.

"""

prior = IDX.read_text()
if MARK in prior:
    print("ALREADY_PRESENT -- no append performed")
else:
    with IDX.open("a", encoding="utf-8") as fh:
        if not prior.endswith("\n"):
            fh.write("\n")
        fh.write(NEW)
    print("APPENDED")

txt = IDX.read_text()
assert prior in txt, "PRIOR CONTENT LOST -- append was not append-only"
print("prior_content_preserved", True)
print("index_path", IDX)
print("index_sha256", hashlib.sha256(IDX.read_bytes()).hexdigest())
