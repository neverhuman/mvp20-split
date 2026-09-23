#!/usr/bin/env python3
"""CF-ALT repair (fire 2/2): add a structured, machine-checkable ranking
(primary + ranked alternates) and pair-keyed named discriminating
experiment for every evidence-indistinguishable pair among this module's
own carried candidates (M00097/M00101/M00109), directly in the M00-series
id namespace this module's own capture_template.json already uses --
sidestepping the separate, still-open, cross-module M00-id <-> track-name
crosswalk question (Envelope-65/Enhanced-65/Lineage-60) that fire 1 also
flagged but which is NOT required by the CF-ALT refutation criterion.

Before editing, snapshot the pre-repair bytes so fire 2's acceptance-test
script can regression-check itself against the untouched original.
"""
import json
import shutil
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
CAPTURE = ROOT / "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json"
WORK = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-ALT/work"
WORK.mkdir(parents=True, exist_ok=True)
SNAPSHOT = WORK / "pre_repair_capture_template.snapshot.json"

if not SNAPSHOT.exists():
    shutil.copyfile(CAPTURE, SNAPSHOT)
    print("SNAPSHOTTED pre-repair bytes to", SNAPSHOT)
else:
    print("snapshot already present, not overwriting:", SNAPSHOT)

capture = json.loads(CAPTURE.read_text())
candidates = capture["candidates"]
assert candidates == ["M00097", "M00101", "M00109"], candidates
ledger = capture["prediction_ledger"]

# Ranking rule: primary = M00097 (blueprint.md's own prose ties M00097 to
# the "Lead" designation -- the one candidate with an explicit, if only
# prose, track-name tie, per fire 1's finding). Ranked alternates ordered
# by ascending |pvc_pct - primary.pvc_pct| -- an objective, reproducible
# distance-from-lead metric already present in this file's own data, not a
# fabricated chemistry judgement.
primary = "M00097"
primary_pvc = ledger[primary]["pvc_pct"]
alternates = sorted(
    (c for c in candidates if c != primary),
    key=lambda c: abs(ledger[c]["pvc_pct"] - primary_pvc),
)

capture["candidate_ranking"] = {
    "schema": "amphora.cro-protocol-packager.candidate-ranking.v1",
    "primary": primary,
    "ranked_alternates": alternates,
    "ranking_rule": (
        "primary = M00097 (blueprint.md's own prose ties M00097 to the "
        "'Lead' designation -- see amphora-cro-protocol-packager CF-ALT "
        "fire 1 finding, evidence/phase0/repairs/CF-ALT/attempts/"
        "cf-alt-ranked-alternates-discriminating-experiment-audit-receipt."
        "v1.dsse.json); ranked_alternates ordered by ascending "
        "abs(pvc_pct - primary.pvc_pct), ties broken by candidate id "
        "ascending. This is a reproducible bookkeeping ranking only -- it "
        "asserts NO corrosion-performance ordering, since all three carry "
        "identical CRO-GATED / 'demoted (card FAIL)' corrosion tier and "
        "cannot be ranked on evidence."
    ),
    "note": (
        "All three candidates are evidence-indistinguishable on the "
        "corpus's own tier labels (see candidate_pairwise_discriminating_"
        "experiments below); this ranking exists so a downstream reader "
        "has a stated default order plus the named experiment required to "
        "override it, not because the evidence supports ranking them."
    ),
}

pairwise = {}
for i in range(len(candidates)):
    for j in range(i + 1, len(candidates)):
        a, b = candidates[i], candidates[j]
        key = "|".join(sorted((a, b)))
        pairwise[key] = {
            "pair": sorted((a, b)),
            "discriminating_experiment": (
                "the side-by-side CRO decision experiment already defined "
                "in this file (decision_experiment.minimum_design: all "
                "tracks built, applied, randomized and exposed under one "
                "protocol with raw data returned; early_kill_gates and "
                "acceptance_gates unchanged) extended to carry "
                f"{a} and {b} as explicit arms alongside the existing "
                "named tracks"
            ),
            "decision_rule_source": (
                "statistical_decision_rules.minimum_detectable_effect."
                "eis_log10_abs_z_0p01hz (>=1.0 log10 |Z|@0.01Hz gap, "
                "greater than replicate scatter) + statistical_decision_"
                "rules.tie_rule + statistical_decision_rules."
                "replicate_scatter_threshold"
            ),
            "protocol_source": (
                "decision_experiment.minimum_design + early_kill_gates + "
                "acceptance_gates (this file, unchanged by this repair)"
            ),
            "inconclusive_rule_source": "inconclusive_handling (this file, unchanged)",
            "status": (
                "NAMED, not yet executed -- both candidates remain "
                "CRO-GATED; commissioning this pairwise arm is future CRO "
                "work (external dependency per docs/mission.md), not a "
                "promotion or a claimed result"
            ),
        }

capture["candidate_pairwise_discriminating_experiments"] = {
    "schema": "amphora.cro-protocol-packager.candidate-pairwise-discriminating-experiments.v1",
    "scope_note": (
        "Named directly in the M00-series id namespace this module's own "
        "candidates/prediction_ledger use. This intentionally sidesteps "
        "the separate, still-open cross-module question of whether/how "
        "M00101 and M00109 map onto the Lineage-60/Envelope-65/"
        "Enhanced-65/CRO-Robust-65 track-name namespace used elsewhere in "
        "this file's statistical_decision_rules and by amphora-report-"
        "packager's blueprint.md -- CF-ALT's refutation criterion requires "
        "a named discriminating experiment per evidence-indistinguishable "
        "pair, not resolution of that separate crosswalk question."
    ),
    "pairs": pairwise,
}

CAPTURE.write_text(json.dumps(capture, indent=2) + "\n")
print("PATCHED", CAPTURE)
print("candidate_ranking", capture["candidate_ranking"]["primary"], capture["candidate_ranking"]["ranked_alternates"])
print("pairwise_keys", sorted(pairwise.keys()))
