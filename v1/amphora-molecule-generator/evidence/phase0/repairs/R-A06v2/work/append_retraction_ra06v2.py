#!/usr/bin/env python3
"""Append the R-A06v2 section to amphora-molecule-generator's RETRACTION-INDEX.md.
Strictly append-only: never rewrites or removes pre-existing content. Idempotent."""
import hashlib
from pathlib import Path

MOD = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-molecule-generator")
IDX = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
MARK = "## R-A06v2"
REL = "amphora-molecule-generator"

NEW = f"""{MARK} -- 2026-08-04 (repair_mode: interactive-2026-08-04)

Superseding receipt:
`{REL}/evidence/phase0/repairs/R-A06v2/done/molgen-r-a06v2-functionality-convention-repair-receipt.v1.dsse.json`
sha256 `985d4aeb3effd6f9c8ffbc04b647b4ff8e283b785346e355e59741739a306f2f`

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `R-A06`: "29/38 valid-unique-**DIFUNCTIONAL**-feasible hardener proposals", where the gate used was `amine_sites == 2` (a count of nitrogen ATOMS). **Corrected: 0 of 38 are difunctional under the active-hydrogen functionality convention (`active_NH == 2`), and 29 of 38 have exactly 2 amine CENTRES (they are primary,primary diamines) with `active_NH == 4`, i.e. TETRAfunctional.** The arithmetic R-A06 published is not disputed -- the independent verify reproduced it exactly -- only the word "difunctional". Structures unchanged. | `{REL}/evidence/phase0/repairs/V-A06/done/v-a06-molecule-generator-repair-verify-receipt.v1.dsse.json` (verdict CLAIM_REFUTED; measured `n_amine_sites2_but_active_nh_ne_2` = 29 of 29 and `n_true_difunctional_active_h_eq_2_among_all_38` = 0) | `{REL}/evidence/phase0/repairs/R-A06v2/done/molgen-r-a06v2-functionality-convention-repair-receipt.v1.dsse.json` | 2026-08-04 |

Portfolio convention fixed by this repair: the word **"difunctional"** means `active_NH == 2`
(active-hydrogen count), never `amine_sites == 2` (nitrogen-atom count). The active-hydrogen
count is what AHEW is defined as (`AHEW = M / n_activeH`, Lee & Neville 1967), what the mix
ratio is computed from (`phr = 100 * AHEW / EEW`) and what Flory-Stockmayer takes as the
network functionality `f`; the nitrogen-atom count enters only the ASTM D2074 amine value and
sets no stoichiometry. For a primary,primary diamine the two differ by exactly 2x, so
confusing them doubles the hardener mix ratio. The 2-amine-centre subset should be called
**"diamines"**, never "difunctional".

Instrument validated before any count was asserted, against this module's own in-tree ground
truth `{REL}/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json`
(sha256 `b1a08e856cab233c69c09673ed0d96a40c38346753afae4ad415b5948edaa9a8`, cites Lee & Neville
1967): 8/8 `known_answer_amines` reproduced on BOTH conventions (`expected_active_nh` and
`expected_basic_n`), 6/6 `fail_closed_decoys` reproduced. Two mutually-independent RDKit
implementations (explicit per-atom rule loop; SMARTS query) agree on all 38 proposals and on
the whole ground-truth set.

Not superseded, carried forward re-derived: R-A06's exact Clopper-Pearson feasible-fraction
interval [0.9075, 1.0000] and its family-resolved IntDiv_1 diversity table -- V-A06
reproduced both exactly and R-A06v2 reproduces them again.

Superseded original (verified byte-intact, NOT deleted or modified):

- `{REL}/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json`
  sha256 `89fc28d21f7224743a6e0a1d2a0750055058e6167e038eee7a65b90145ea4b52`

Scope: AUDIT_ONLY, ceiling EVIDENCE_ONLY. No authority promoted, no scientific_readiness
flipped, no manifest, ledger, mission front-matter, or locked dataset touched. The 38 accepted
structures are unchanged -- this is a label/convention correction. All 38 remain valid, unique,
SA-feasible and network-forming (`active_NH >= 3`).

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
