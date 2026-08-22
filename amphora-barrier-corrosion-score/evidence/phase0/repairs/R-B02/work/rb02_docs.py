#!/usr/bin/env python3
"""R-B02 doc updates: RETRACTION-INDEX.md append + mission.md prose line.
Front-matter is verified byte-identical before/after; only prose changes."""
import hashlib
from pathlib import Path

MOD = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-barrier-corrosion-score")
RIDX = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
MISSION = MOD / "docs/mission.md"
RECEIPT_REL = "evidence/phase0/repairs/R-B02/done/barrier-index-repair-receipt.v1.dsse.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------- RETRACTION-INDEX.md ---
section = (
    "\n## R-B02 — barrier_index structural unevaluability (repaired 2026-08-03)\n\n"
    "| claim | refuted-by receipt path | superseded-by | date |\n"
    "|---|---|---|---|\n"
    "| `EisPredictionV1.barrier_index` / `metrics.barrier_index` is unconditionally "
    "`None` on every code path in `src/lib.rs`, so the locked primary KPI (blinded "
    "Kendall tau at `metrics.barrier_index`) is structurally unevaluable | "
    "`benchmarks/three-series-barrier-ranking-v1/three-series-barrier-ranking-receipt.v1.dsse.json` | "
    f"`{RECEIPT_REL}` (structural finding only; W1's statistical-infeasibility "
    "findings — all 3 in-class series below FEASIBILITY_FLOOR=6 — remain in force) | "
    "2026-08-03 |\n"
)
if RIDX.exists():
    prior = RIDX.read_text()
    print("retraction_index_existed sha_before", sha(prior.encode()))
    RIDX.write_text(prior.rstrip("\n") + "\n" + section)
else:
    RIDX.write_text(
        "# amphora-barrier-corrosion-score — retraction / supersession index\n\n"
        "Each row records a refuted claim, the signed receipt that refuted it, and "
        "the signed repair receipt that supersedes the refuted element. Superseded "
        "artifacts are never modified or deleted.\n" + section)
    print("retraction_index_created")
print("retraction_index_sha_after", sha(RIDX.read_bytes()))

# --------------------------------------------------------------- mission.md --
raw = MISSION.read_text()
sha_before = sha(raw.encode())
lines = raw.split("\n")
assert lines[0] == "---" and lines[2] == "---", "front-matter fences moved"
front_matter_before = "\n".join(lines[0:3])

anchor = ("No checked result promotes this module. The locked independent benchmark "
          "remains `NOT_PASSED` until a qualifying receipt meets the KPI gate.")
assert raw.count(anchor) == 1, "anchor paragraph not unique"
new_line = (f"barrier_index implemented 2026-08-03, receipt `{RECEIPT_REL}`; "
            "feasibility floor still unmet.")
assert new_line not in raw, "mission.md already carries the R-B02 line"
updated = raw.replace(anchor, anchor + "\n\n" + new_line)
MISSION.write_text(updated)

after = MISSION.read_text()
after_lines = after.split("\n")
assert "\n".join(after_lines[0:3]) == front_matter_before, "FRONT-MATTER CHANGED"
assert new_line in after
print("mission_sha_before", sha_before)
print("mission_sha_after", sha(after.encode()))
print("front_matter_unchanged", True)
