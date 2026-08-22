#!/usr/bin/env python3
"""Append the R-A06 section to the module RETRACTION-INDEX.md (create if absent).
Strictly append-only: never rewrites or removes pre-existing content.
Idempotent: refuses to append twice."""
import hashlib
from pathlib import Path

MOD = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-molecule-generator")
IDX = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
MARK = "## R-A06"

HEADER = """# RETRACTION INDEX -- amphora-molecule-generator

Append-only record of published claims that were refuted by a signed falsification
receipt and subsequently superseded by a signed corrected receipt. Superseded
artifacts are NEVER deleted or modified; they remain byte-intact on disk and are
listed here with the receipt that refutes them and the receipt that replaces them.

"""

REL = "amphora-molecule-generator"
NEW = f"""{MARK} -- 2026-08-03 (repair_mode: interactive-2026-08-03)

Superseding receipt (all three rows):
`{REL}/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json`

| claim | refuted-by receipt path | superseded-by | date |
|---|---|---|---|
| `molgen-deterministic-grammar-yield-v1`: feasible_fraction bootstrap 95% CI = [1.0000, 1.0000] at k=n=38. **Corrected to exact Clopper-Pearson [0.9075, 1.0000]** (percentile bootstrap is degenerate at the all-success boundary; 0.0925 lower-bound gap exceeds the a-priori 0.02 admissibility threshold). | `{REL}/evidence/audit/molgen-grammar-yield-bootstrap-ci-inadmissibility-v1/molgen-grammar-yield-ci-inadmissibility-receipt.v1.dsse.json` | `{REL}/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json` | 2026-08-03 |
| `molgen-deterministic-grammar-yield-v1`: "38 valid-unique-difunctional-feasible hardener proposals" (yield 38/38). **Corrected to 29/38** -- 9 proposals flagged `difunctional_hardener=true` carry 3-9 amine sites (homopiperazine-N,N' 3, piperazine-bis(aminoethyl)/AEP 3, DETA 3, TETA 4, TEPA 5, PEHA 6, ethyleneamine-k6 7, -k7 8, -k8 9); the gate did not implement its own stated definition `amine_sites==2`. Structures unchanged. | `{REL}/evidence/audit/molgen-hardener-functionality-mislabel-v1/molgen-hardener-functionality-mislabel-receipt.v1.dsse.json` | `{REL}/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json` | 2026-08-03 |
| `molgen-scaffold-diversity-v1`: hypothesis_evaluation verdict CORROBORATED_IN_AUDIT_INSTRUMENT on aggregate IntDiv_1 = 0.7681 ("not trivially inflated variants of a single scaffold"). **Corrected to family-resolved: cross-family diversity is real (homolog-bloc vs ring mean Tanimoto 0.1054), but within-family homolog series are near-degenerate** -- F1_polyethyleneamine IntDiv_1 = 0.1851 and F2_alpha_omega_diamine IntDiv_1 = 0.0870 over 47.4% of the accepted set, with 12/16 chain-adjacent pairs saturated at Tanimoto >= 0.99. | `{REL}/evidence/audit/molgen-scaffold-diversity-homolog-fingerprint-saturation-v1/molgen-scaffold-diversity-homolog-fingerprint-saturation-receipt.v1.dsse.json` | `{REL}/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json` | 2026-08-03 |

Superseded originals (verified byte-intact, NOT deleted or modified):

- `{REL}/evidence/audit/molgen-deterministic-grammar-yield-v1/molgen-deterministic-grammar-yield-receipt.v1.dsse.json`
  sha256 `a7bedf57ece42bee60fabb4a1b7069a205b1297735356f21cc4e71dc64c98b0a`
- `{REL}/evidence/audit/molgen-scaffold-diversity-v1/molgen-scaffold-diversity-receipt.v1.dsse.json`
  sha256 `f74b5bcc37eb4306109984178e305d3aa84b4d4f24527d5a984f32125cff9fb7`

Scope: AUDIT_ONLY. No authority promoted, no scientific_readiness flipped, no manifest,
ledger, mission front-matter, or locked dataset touched. The 38 accepted structures
themselves are unchanged -- these are interval, label, and resolution corrections.

"""

IDX.parent.mkdir(parents=True, exist_ok=True)
existed = IDX.exists()
prior = IDX.read_text() if existed else ""
if MARK in prior:
    print("ALREADY_PRESENT -- no append performed")
else:
    with IDX.open("a", encoding="utf-8") as fh:
        if not existed:
            fh.write(HEADER)
        elif not prior.endswith("\n"):
            fh.write("\n")
        fh.write(NEW)
    print("APPENDED (created)" if not existed else "APPENDED (existing file)")

txt = IDX.read_text()
assert prior in txt, "PRIOR CONTENT LOST -- append was not append-only"
print("prior_content_preserved", True)
print("index_path", IDX)
print("index_sha256", hashlib.sha256(IDX.read_bytes()).hexdigest())
