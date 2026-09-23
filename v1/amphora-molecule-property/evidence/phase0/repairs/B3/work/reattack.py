#!/usr/bin/env python3
"""B3 re-attack: prove zero occurrences of every stale string, and prove the
mission.md front-matter is byte-identical before vs after the repair."""
import hashlib
import json
import sys

MISSION = "/home/ubuntu/amphora/build/mvp20-split/amphora-molecule-property/docs/mission.md"
BEFORE = "/tmp/b3_mission.before.md"

STALE = [
    "REAL POSITIVE lift, n=295",
    "Directly delivers the coating IP prediction capability for POLYMER DIELECTRIC",
    "can now offer polymer\ndielectric constant prediction with a defended MAE ~0.40",
    "Directly applicable to coating chemistry decisions for\nelectrical-insulation applications.",
    "1. **REAL predictive capability**",
    "**MAJOR POSITIVE FINDING**",
    "Combined with Push #23 (dielectric R² +0.66)",
    "The 24-group STRUCTURE is CONFIRMED CORRECT at scale**:",
    "2. **The prior \"under-determination\" hypothesis is RESOLVED**",
    "4. **Fitted Y_gi values are chemistry-plausible**",
    "this receipt proves that a 24-group Van Krevelen calibration",
    "2. **Portfolio priority**: For coating Tg prediction on experimental targets",
    "ML strictly dominates the frozen physics-Ridge inference",
    "3. **Positive R² on rigorous LOSO-CV** confirms cross-scaffold generalization.",
    "- Confirms Push #20's Ridge Y_gi calibration has real generalization value.",
    "confirms the 24-group structure captures ordinal Tg signal",
    "RESOLVES the Push #20 Phase-1 hypothesis about applicability domain.",
    "Applicability domain restricted to the openpoly scaffold distribution. Phase-1",
    "**Portfolio implication**: `amphora-molecule-property` can now offer polymer",
    "**Portfolio implication**: For Phase-1, this receipt proves",
    "reaching Bicerano-level accuracy.",
]


def frontmatter(text):
    end = text.index("\n---\n", 3)
    return text[: end + len("\n---\n")]


after = open(MISSION, encoding="utf-8").read()
before = open(BEFORE, encoding="utf-8").read()

rows = []
fail = 0
for s in STALE:
    nb = before.count(s)
    na = after.count(s)
    rows.append({"stale_string": s, "count_before": nb, "count_after": na})
    if na != 0:
        fail += 1
        sys.stderr.write("STILL PRESENT (%d): %r\n" % (na, s))
    if nb == 0:
        sys.stderr.write("WARNING: stale string was not present BEFORE either: %r\n" % s)

fm_b = frontmatter(before)
fm_a = frontmatter(after)
res = {
    "stale_string_sweep": rows,
    "stale_strings_checked": len(STALE),
    "stale_occurrences_after": sum(r["count_after"] for r in rows),
    "frontmatter_sha256_before": hashlib.sha256(fm_b.encode()).hexdigest(),
    "frontmatter_sha256_after": hashlib.sha256(fm_a.encode()).hexdigest(),
    "frontmatter_byte_identical": fm_b == fm_a,
    "frontmatter_json_parse_equal": json.loads(fm_b.split("\n")[1]) == json.loads(fm_a.split("\n")[1]),
    "mission_sha256_before": hashlib.sha256(before.encode()).hexdigest(),
    "mission_sha256_after": hashlib.sha256(after.encode()).hexdigest(),
    "lines_before": before.count("\n"),
    "lines_after": after.count("\n"),
}
print(json.dumps(res, indent=1, sort_keys=True))
if fail or not res["frontmatter_byte_identical"]:
    sys.exit(1)
print("RE-ATTACK PASSED: 0 stale occurrences, front-matter byte-identical")
