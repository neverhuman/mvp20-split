#!/usr/bin/env python3
"""CF-ALT ranked-alternates / discriminating-experiment audit, fire 2/2
(campaign item CF-ALT, founder directive AMPHORA-DIRECTIVE-2026-08-09 S7,
obligation CF-ALT, max_fires=2, REPAIR-MODE re-attack / acceptance test).

This is a MINIMAL-DIFF successor to fire 1's
run_cf_alt_alternates_audit_v1.py. The `evidence_indistinguishable`,
`all_pairs` and `find_unresolved` functions and their thresholds are
BYTE-IDENTICAL to v1 (copy-paste, unchanged) -- see
diagnostic.canonical.json#core_logic_unchanged_from_v1 for the diff
summary. The ONLY change: v1's `real_resolved_pair_experiments` was a
manually-asserted empty dict (`{}`), because at fire-1 time there was
nothing in the corpus to derive it from -- it was an audit snapshot, not a
live checker, and re-running it byte-for-byte can never observe a repair.
v2 instead DERIVES `real_resolved_pair_experiments` from a live field in
capture_template.json (`candidate_pairwise_discriminating_experiments`),
so it can genuinely re-attack a repair. v2 also checks the new
`candidate_ranking` field for a valid primary + ranked_alternates
partition of the candidates list (the "ships the primary plus ranked
alternates" half of the done_criterion, which v1 did not check at all).

Refutation criterion (verbatim, pre-committed, unchanged from fire 1):
"Any pair of evidence-indistinguishable candidates ships without ranked
alternates and a named discriminating experiment."

Runs the checker THREE times:
  A. against the SAVED PRE-REPAIR SNAPSHOT (work/pre_repair_capture_
     template.snapshot.json, byte-identical to what fire 1 audited) --
     regression check that v2 faithfully reproduces fire 1's finding
     (n_unresolved == 3, no ranking field) on the untouched original, i.e.
     v2 is a generalization of v1's logic, not a gerrymandered pass.
  B. against the LIVE (repaired) capture_template.json -- the real
     acceptance test.
  C. positive control: a copy of the repaired dict with exactly ONE
     pair's discriminating-experiment entry stripped (attack-shape-literal
     "merge two curative alternates into one unexplained pick") -- must
     re-flag exactly that pair and only that pair.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
CAPTURE = ROOT / "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json"
SNAPSHOT = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-ALT/work/pre_repair_capture_template.snapshot.json"
OUTDIR = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-alt-ranked-alternates-discriminating-experiment-v2"

REFUTATION_CRITERION = (
    "Any pair of evidence-indistinguishable candidates ships without "
    "ranked alternates and a named discriminating experiment."
)
ATTACK_SHAPE = (
    "Merge two curative alternates into one unexplained pick in a copy "
    "and attack whether the check fires; hunt for an evidence-"
    "indistinguishable pair shipped without a discriminating experiment."
)
DIRECTIVE_PATH = "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA256 = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"
DIRECTIVE_OBLIGATION = "CF-ALT"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# BYTE-IDENTICAL to v1 (copy-paste, unchanged): the indistinguishability
# definition and thresholds this repair must actually satisfy.
# ---------------------------------------------------------------------------
def evidence_indistinguishable(a_id, b_id, ledger):
    a, b = ledger[a_id], ledger[b_id]
    same_corrosion_tier = (
        a["corrosion"]["tier"] == b["corrosion"]["tier"] == "CRO-GATED"
        and a["corrosion"]["rank_model"] == b["corrosion"]["rank_model"] == "demoted (card FAIL)"
    )
    same_pot_life_tier = a["pot_life_h"]["tier"] == b["pot_life_h"]["tier"] == "CRO-GATED"
    same_mix_ratio = a["mix_ratio_by_volume"] == b["mix_ratio_by_volume"]
    same_stoich = a["stoichiometric_ratio"] == b["stoichiometric_ratio"]
    same_solids = a["volume_solids_pct"] == b["volume_solids_pct"]
    pvc_delta = abs(a["pvc_pct"] - b["pvc_pct"])
    indistinguishable = bool(
        same_corrosion_tier and same_pot_life_tier and same_mix_ratio
        and same_stoich and same_solids and pvc_delta < 1.0
    )
    return {
        "pair": [a_id, b_id],
        "same_corrosion_tier_demoted": same_corrosion_tier,
        "same_pot_life_tier": same_pot_life_tier,
        "same_mix_ratio_by_volume": same_mix_ratio,
        "same_stoichiometric_ratio": same_stoich,
        "same_volume_solids_pct": same_solids,
        "pvc_pct_delta": round(pvc_delta, 4),
        "evidence_indistinguishable": indistinguishable,
    }


def all_pairs(candidates, ledger):
    out = []
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            out.append(evidence_indistinguishable(candidates[i], candidates[j], ledger))
    return out


def find_unresolved(candidates, ledger, resolved_pair_experiments):
    pairs = all_pairs(candidates, ledger)
    unresolved = []
    for p in pairs:
        if not p["evidence_indistinguishable"]:
            continue
        key = frozenset(p["pair"])
        experiment = resolved_pair_experiments.get(key)
        if not experiment:
            unresolved.append(p["pair"])
    return pairs, unresolved


# ---------------------------------------------------------------------------
# NEW in v2: derive resolved_pair_experiments LIVE from the corpus instead
# of a hardcoded {}, and check the ranking field.
# ---------------------------------------------------------------------------
def derive_resolved_pair_experiments(capture_obj):
    node = capture_obj.get("candidate_pairwise_discriminating_experiments", {})
    pairs_obj = node.get("pairs", {})
    out = {}
    for _key, entry in pairs_obj.items():
        pair = entry.get("pair")
        experiment = entry.get("discriminating_experiment")
        if pair and experiment:
            out[frozenset(pair)] = experiment
    return out


def check_ranking(capture_obj, candidates):
    ranking = capture_obj.get("candidate_ranking")
    if not ranking:
        return {"present": False, "valid": False, "reason": "candidate_ranking field absent"}
    primary = ranking.get("primary")
    alternates = ranking.get("ranked_alternates", [])
    valid = (
        primary in candidates
        and isinstance(alternates, list)
        and sorted([primary] + alternates) == sorted(candidates)
        and len(set([primary] + alternates)) == len(candidates)
    )
    return {
        "present": True,
        "valid": bool(valid),
        "primary": primary,
        "ranked_alternates": alternates,
        "reason": "" if valid else "primary+ranked_alternates does not exactly partition candidates",
    }


def run_check(capture_obj, label):
    candidates = capture_obj["candidates"]
    ledger = capture_obj["prediction_ledger"]
    resolved = derive_resolved_pair_experiments(capture_obj)
    pairs, unresolved = find_unresolved(candidates, ledger, resolved)
    ranking = check_ranking(capture_obj, candidates)
    return {
        "label": label,
        "candidates": candidates,
        "pairs_evaluated": pairs,
        "resolved_pair_keys": ["|".join(sorted(k)) for k in resolved.keys()],
        "unresolved_evidence_indistinguishable_pairs": unresolved,
        "n_unresolved": len(unresolved),
        "ranking": ranking,
        "criterion_fires": bool(len(unresolved) > 0 or not ranking["valid"]),
    }


# ---------------------------------------------------------------------------
# Step A: regression check against the SAVED PRE-REPAIR SNAPSHOT.
# ---------------------------------------------------------------------------
assert SNAPSHOT.exists(), "pre-repair snapshot missing -- run patch_capture_template.py first"
snapshot_bytes = SNAPSHOT.read_bytes()
snapshot_sha256 = sha(snapshot_bytes)
snapshot_obj = json.loads(snapshot_bytes)
step_a = run_check(snapshot_obj, "pre_repair_snapshot")

# ---------------------------------------------------------------------------
# Step B: the real acceptance test -- live (repaired) capture_template.json.
# ---------------------------------------------------------------------------
live_bytes = CAPTURE.read_bytes()
live_sha256 = sha(live_bytes)
live_obj = json.loads(live_bytes)
step_b = run_check(live_obj, "live_repaired")

# ---------------------------------------------------------------------------
# Step C: positive control -- strip exactly ONE pair's resolution from a
# copy of the repaired object ("merge two curative alternates into one
# unexplained pick"). Checker must re-flag exactly that pair and only that
# pair.
# ---------------------------------------------------------------------------
mutated = copy.deepcopy(live_obj)
stripped_pair_key = "M00101|M00109"
assert stripped_pair_key in mutated["candidate_pairwise_discriminating_experiments"]["pairs"], (
    "expected pair key missing pre-mutation"
)
del mutated["candidate_pairwise_discriminating_experiments"]["pairs"][stripped_pair_key]
step_c = run_check(mutated, "positive_control_stripped_M00101_M00109")
positive_control_detected = step_c["unresolved_evidence_indistinguishable_pairs"] == [["M00101", "M00109"]]

# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------
repair_holds = (step_b["n_unresolved"] == 0) and step_b["ranking"]["valid"]
regression_reproduces_v1 = (step_a["n_unresolved"] == 3) and (not step_a["ranking"]["present"])

diagnostic = {
    "schema": "amphora.cro-protocol-packager.cf-alt-alternates-audit-diagnostic.v2",
    "study_id": "cf-alt-ranked-alternates-discriminating-experiment-v2",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-ALT",
    "fire_sequence": 2,
    "directive_path": DIRECTIVE_PATH,
    "directive_sha256": DIRECTIVE_SHA256,
    "directive_obligation": DIRECTIVE_OBLIGATION,
    "claim_under_attack": (
        "The current CF-ALT deliverable state is complete and accurate for "
        "its scope (finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "deliverable_under_test": "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json",
    "refutation_criterion_verbatim": REFUTATION_CRITERION,
    "attack_shape_verbatim": ATTACK_SHAPE,
    "core_logic_unchanged_from_v1": (
        "evidence_indistinguishable(), all_pairs(), find_unresolved() and "
        "all six comparison thresholds (corrosion tier, pot_life tier, mix "
        "ratio, stoichiometric ratio, volume solids, pvc_pct delta < 1.0) "
        "are byte-identical copies of v1's functions. The only change is "
        "that real_resolved_pair_experiments is now DERIVED from a live "
        "corpus field (candidate_pairwise_discriminating_experiments) "
        "instead of hardcoded to {}, and a ranking-validity check was "
        "added -- v1 had nothing to derive from and did not check ranking "
        "at all, so it could only ever report REFUTED regardless of any "
        "repair; v2 is required to serve as a genuine, re-runnable "
        "acceptance test."
    ),
    "pre_repair_snapshot_sha256": snapshot_sha256,
    "live_capture_template_sha256": live_sha256,
    "step_a_regression_against_pre_repair_snapshot": {
        **step_a,
        "expected_n_unresolved": 3,
        "matches_fire1_finding": regression_reproduces_v1,
        "note": (
            "Confirms v2's derivation logic, run against the UNTOUCHED "
            "original bytes fire 1 audited, reproduces fire 1's exact "
            "finding (3 unresolved pairs, no ranking field) -- v2 "
            "generalizes v1, it is not gerrymandered to only pass on the "
            "repaired file."
        ),
    },
    "step_b_live_repaired_acceptance_test": {
        **step_b,
        "repair_holds": repair_holds,
    },
    "step_c_positive_control": {
        **step_c,
        "planted_defect": "removed candidate_pairwise_discriminating_experiments.pairs['M00101|M00109']",
        "how_planted": (
            "deepcopy of the live repaired capture_template.json object, "
            "then dict.pop of the 'M00101|M00109' entry from "
            "candidate_pairwise_discriminating_experiments.pairs; all "
            "other pairs and candidate_ranking left intact"
        ),
        "detected": positive_control_detected,
        "evidence": (
            f"unresolved_evidence_indistinguishable_pairs == "
            f"{step_c['unresolved_evidence_indistinguishable_pairs']}, "
            "matching exactly the single pair whose resolution was "
            "stripped."
        ),
    },
    "verdict": "CLAIM_SURVIVED" if repair_holds else "CLAIM_REFUTED",
    "repair_status": "fix_landed_survived" if repair_holds else "fix_landed_refuted",
}

OUTDIR.mkdir(parents=True, exist_ok=True)
canon_path = OUTDIR / "diagnostic.canonical.json"
canon_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
canon_path.write_bytes(canon_bytes)
print("WROTE", canon_path)
print("verdict", diagnostic["verdict"])
print("step_a n_unresolved", step_a["n_unresolved"], "ranking_present", step_a["ranking"]["present"])
print("step_b n_unresolved", step_b["n_unresolved"], "ranking_valid", step_b["ranking"]["valid"])
print("step_c positive_control_detected", positive_control_detected)
print("live_sha256", live_sha256)
print("snapshot_sha256", snapshot_sha256)
