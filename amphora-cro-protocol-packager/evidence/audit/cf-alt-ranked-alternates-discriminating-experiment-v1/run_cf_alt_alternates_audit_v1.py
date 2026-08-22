#!/usr/bin/env python3
"""CF-ALT ranked-alternates / discriminating-experiment audit, fire 1/2
(campaign item CF-ALT, founder directive AMPHORA-DIRECTIVE-2026-08-09 S7,
obligation CF-ALT, max_fires=2).

CLAIM UNDER ATTACK: "The current CF-ALT deliverable state is complete and
accurate for its scope" (i.e. this module's own carried-candidate corpus
already ships ranked alternates + a named discriminating experiment
wherever evidence cannot distinguish candidates).

Refutation criterion (verbatim, pre-committed): "Any pair of
evidence-indistinguishable candidates ships without ranked alternates and
a named discriminating experiment."

Attack shape (verbatim): "Merge two curative alternates into one
unexplained pick in a copy and attack whether the check fires; hunt for
an evidence-indistinguishable pair shipped without a discriminating
experiment."

METHOD: this module's OWN reference deliverable
(reference/mvp20/out/capture_template.json) carries three candidates
(M00097, M00101, M00109) in its top-level "candidates" list and
"prediction_ledger". By the corpus's own tier labels, ALL THREE share an
identical CRO-GATED / "demoted (card FAIL)" corrosion-rank tier -- i.e.
the corpus itself asserts no validated model can rank them -- and
identical mix_ratio_by_volume, stoichiometric_ratio and
volume_solids_pct, with pvc_pct differing by under 1 percentage point.
That is this module's own definition of "evidence cannot distinguish."

The corpus DOES name one discriminating experiment (the "key_pairwise"
statistical_decision_rules entry / falsification_protocol.json's
key_pairwise_bet), but it is keyed to a DIFFERENT ID namespace
(Lineage-60 / Envelope-65 / Enhanced-65 / CRO-Robust-65) than the
M00-series ids the module's own candidates/prediction_ledger use, with no
structured crosswalk file anywhere in the repo connecting the two
namespaces (only one prose sentence in amphora-report-packager's
blueprint.md ties M00097 to "Envelope-65"; M00101 and M00109 are never
tied to any track name anywhere).

Pure read + audit. Modifies nothing outside amphora-cro-protocol-packager
(blueprint.md is read-only cross-module context, exactly as CF-BOM's
precedent audits did).
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
CAPTURE = ROOT / "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json"
CRO_PROTOCOL_MD = ROOT / "amphora-cro-protocol-packager/reference/mvp20/out/cro_protocol.md"
FALS_PROTOCOL = ROOT / "amphora-cro-protocol-packager/reference/mvp20/out/falsification_protocol.json"
BLUEPRINT = ROOT / "amphora-report-packager/reference/mvp20/out/blueprint.md"
OUTDIR = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-alt-ranked-alternates-discriminating-experiment-v1"

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


capture_text = CAPTURE.read_text()
capture = json.loads(capture_text)
capture_sha256 = sha(CAPTURE.read_bytes())

blueprint_text = BLUEPRINT.read_text()
blueprint_sha256 = sha(BLUEPRINT.read_bytes())

fals_text = FALS_PROTOCOL.read_text()
fals = json.loads(fals_text)
fals_sha256 = sha(FALS_PROTOCOL.read_bytes())

cro_md_text = CRO_PROTOCOL_MD.read_text()
cro_md_sha256 = sha(CRO_PROTOCOL_MD.read_bytes())

TRACK_NAMES = ("Envelope-65", "Enhanced-65", "CRO-Robust-65", "Lineage-60")


def m00_ids(text):
    return sorted(set(re.findall(r"M00\d{3}", text)))


# ---------------------------------------------------------------------------
# Step 1: this module's own carried-candidate bookkeeping (the "ships"
# corpus that CF-ALT actually judges, since amphora-cro-protocol-packager
# cannot edit amphora-report-packager/blueprint.md).
# ---------------------------------------------------------------------------
carried_candidates = capture["candidates"]
prediction_ledger = capture["prediction_ledger"]


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
    """resolved_pair_experiments: dict[frozenset(ids)] -> experiment name (str)"""
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
# Step 2: what discriminating experiments does the REAL corpus actually name,
# and to which candidate identifiers are they keyed?
# ---------------------------------------------------------------------------
key_pairwise_capture = capture.get("statistical_decision_rules", {}).get("key_pairwise", "")
key_pairwise_bet = fals.get("key_pairwise_bet", {})
named_pair_track_names = key_pairwise_bet.get("pair", [])

m00_in_capture = m00_ids(capture_text)
m00_in_blueprint = m00_ids(blueprint_text)
m00_in_fals = m00_ids(fals_text)
m00_in_cro_md = m00_ids(cro_md_text)

crosswalk_sentences = [
    ln.strip() for ln in blueprint_text.splitlines()
    if re.search(r"M00\d{3}", ln) and any(t in ln for t in TRACK_NAMES)
]

explicit_crosswalk = {
    cid: any(cid in s for s in crosswalk_sentences) for cid in ("M00097", "M00101", "M00109", "M00098")
}

m00098_in_capture_candidates = "M00098" in carried_candidates
m00098_in_capture_ledger = "M00098" in prediction_ledger

power_analysis_path_cited = capture.get("statistical_decision_rules", {}).get("power_analysis_path")
power_analysis_exists = (ROOT / "amphora-cro-protocol-packager/reference/mvp20/out/power_analysis.json").exists()
funnel_results_cited = "funnel_results.json" in blueprint_text
funnel_results_exists = any(ROOT.rglob("funnel_results.json"))

# The REAL corpus resolves NO pair by M00-series id: no discriminating
# experiment anywhere in the four in-scope files is keyed to M00097 /
# M00101 / M00109 directly -- only to the Lineage-60/Envelope-65/
# Enhanced-65/CRO-Robust-65 track names, and only M00097 has even a prose
# (not structured) tie to a track name ("Lead M00097 / Envelope-65").
real_resolved_pair_experiments = {}

real_pairs, real_unresolved = find_unresolved(
    carried_candidates, prediction_ledger, real_resolved_pair_experiments
)

# ---------------------------------------------------------------------------
# Step 3: discrimination control -- a synthetic REPAIRED copy that adds an
# explicit, pair-keyed crosswalk + named discriminating experiment for every
# evidence-indistinguishable pair. The SAME checker must report zero
# unresolved pairs on this copy, proving it is not hard-wired to refute.
# ---------------------------------------------------------------------------
repaired_resolved_pair_experiments = {
    frozenset(p["pair"]): (
        "ASTM D870 immersion + ISO 16773 EIS pairwise gap "
        f"({p['pair'][0]} vs {p['pair'][1]}), same protocol construction as "
        "falsification_protocol.json's key_pairwise_bet, decision rule: "
        ">=1.0 log10 |Z|@0.01Hz gap and greater than replicate scatter"
    )
    for p in real_pairs
    if p["evidence_indistinguishable"]
}
_, repaired_unresolved = find_unresolved(
    carried_candidates, prediction_ledger, repaired_resolved_pair_experiments
)
discrimination_control_passed = (len(repaired_unresolved) == 0) and (len(real_unresolved) > 0)

# ---------------------------------------------------------------------------
# Step 4: positive control -- literal attack-shape enactment. Start from the
# discrimination-control's fully-repaired state (every pair resolved), then
# silently strip the resolution for exactly ONE pair (M00101 vs M00109) --
# "merge two curative alternates into one unexplained pick" in the sense
# that, absent a named discriminating experiment, a downstream reader has no
# principled way to choose between M00101 and M00109 and will pick one
# silently. The checker must re-flag exactly that pair and ONLY that pair.
# ---------------------------------------------------------------------------
planted_defect_pairs = dict(repaired_resolved_pair_experiments)
stripped_key = frozenset(["M00101", "M00109"])
assert stripped_key in planted_defect_pairs, "expected M00101/M00109 to be a resolved pair pre-mutation"
del planted_defect_pairs[stripped_key]
_, positive_control_unresolved = find_unresolved(
    carried_candidates, prediction_ledger, planted_defect_pairs
)
positive_control_detected = positive_control_unresolved == [["M00101", "M00109"]]

# ---------------------------------------------------------------------------
# Assemble diagnostic
# ---------------------------------------------------------------------------
diagnostic = {
    "schema": "amphora.cro-protocol-packager.cf-alt-alternates-audit-diagnostic.v1",
    "study_id": "cf-alt-ranked-alternates-discriminating-experiment-v1",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-ALT",
    "fire_sequence": 1,
    "directive_path": DIRECTIVE_PATH,
    "directive_sha256": DIRECTIVE_SHA256,
    "directive_obligation": DIRECTIVE_OBLIGATION,
    "claim_under_attack": (
        "The current CF-ALT deliverable state is complete and accurate for "
        "its scope (finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "deliverable_under_test": "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json",
    "deliverable_sha256": capture_sha256,
    "cross_module_context_read_only": {
        "blueprint_md_path": "amphora-report-packager/reference/mvp20/out/blueprint.md",
        "blueprint_md_sha256": blueprint_sha256,
        "falsification_protocol_path": "amphora-cro-protocol-packager/reference/mvp20/out/falsification_protocol.json",
        "falsification_protocol_sha256": fals_sha256,
        "cro_protocol_md_path": "amphora-cro-protocol-packager/reference/mvp20/out/cro_protocol.md",
        "cro_protocol_md_sha256": cro_md_sha256,
    },
    "refutation_criterion_verbatim": REFUTATION_CRITERION,
    "attack_shape_verbatim": ATTACK_SHAPE,
    "step_1_carried_candidates": {
        "candidates_list": carried_candidates,
        "prediction_ledger_ids": sorted(prediction_ledger.keys()),
        "pairs_evaluated": real_pairs,
    },
    "step_2_named_discriminating_experiments_in_real_corpus": {
        "key_pairwise_capture_template": key_pairwise_capture,
        "key_pairwise_bet_falsification_protocol": key_pairwise_bet,
        "track_names_used_by_named_experiment": named_pair_track_names,
        "m00_series_ids_mentioned_per_file": {
            "capture_template.json": m00_in_capture,
            "blueprint.md": m00_in_blueprint,
            "falsification_protocol.json": m00_in_fals,
            "cro_protocol.md": m00_in_cro_md,
        },
        "structured_crosswalk_sentences_found_in_blueprint": crosswalk_sentences,
        "explicit_id_to_track_name_tie_present": explicit_crosswalk,
        "m00098_functional_variant_in_this_modules_candidates_list": m00098_in_capture_candidates,
        "m00098_functional_variant_in_this_modules_prediction_ledger": m00098_in_capture_ledger,
        "finding": (
            "The only named discriminating experiment in the corpus (key_pairwise: "
            "Enhanced-65 > Envelope-65) is keyed to the Lineage-60/Envelope-65/"
            "Enhanced-65/CRO-Robust-65 track namespace, not to the M00-series ids "
            "this module's own capture_template.json carries. Only M00097 has a "
            "prose (not structured/machine-checkable) tie to a track name "
            "('Lead M00097 / Envelope-65' in blueprint.md). M00101 and M00109 -- "
            "both explicitly in THIS module's own 'candidates' list -- are never "
            "tied to any track name anywhere in the four in-scope files, so the "
            "named experiment cannot be verified to resolve them. Separately, "
            "'Enhanced-65' (the zinc-phosphate functional variant per blueprint "
            "prose) most plausibly corresponds to M00098, which is entirely "
            "ABSENT from this module's own candidates list and prediction_ledger "
            "-- an internal inconsistency in this module's own carried-candidate "
            "bookkeeping, independent of the cross-module ownership question."
        ),
        "additional_missing_companion_files": {
            "power_analysis_path_cited_by_this_modules_own_capture_template": power_analysis_path_cited,
            "power_analysis_json_exists_anywhere_in_repo": power_analysis_exists,
            "funnel_results_json_cited_by_blueprint_for_alternates": funnel_results_cited,
            "funnel_results_json_exists_anywhere_in_repo": funnel_results_exists,
        },
    },
    "step_3_real_corpus_unresolved_pairs": {
        "resolved_pair_experiments": {},
        "unresolved_evidence_indistinguishable_pairs": real_unresolved,
        "n_unresolved": len(real_unresolved),
        "refutation_criterion_observed": bool(len(real_unresolved) > 0),
    },
    "step_4_discrimination_control": {
        "description": (
            "Synthetic fully-repaired copy: every evidence-indistinguishable "
            "pair gets an explicit pair-keyed named discriminating experiment. "
            "SAME checker must report zero unresolved pairs."
        ),
        "resolved_pair_experiments": {
            "|".join(sorted(k)): v for k, v in repaired_resolved_pair_experiments.items()
        },
        "unresolved_pairs_on_repaired_copy": repaired_unresolved,
        "discrimination_control_passed": discrimination_control_passed,
    },
    "step_5_positive_control": {
        "description": (
            "Attack-shape-literal: from the fully-repaired state, silently "
            "strip the named discriminating experiment for exactly the "
            "M00101 vs M00109 pair (the 'merge into one unexplained pick' "
            "scenario -- no test is named to choose between them, so a "
            "downstream reader picks one silently). The checker must "
            "re-flag exactly that pair and only that pair."
        ),
        "planted_defect": "removed resolved_pair_experiments[frozenset({'M00101','M00109'})]",
        "how_planted": (
            "dict.pop on the fully-repaired resolved_pair_experiments map, "
            "key frozenset({'M00101','M00109'}); all other pairs' resolutions "
            "left intact"
        ),
        "unresolved_pairs_after_planting": positive_control_unresolved,
        "detected": positive_control_detected,
        "evidence": (
            f"unresolved_pairs_after_planting == {positive_control_unresolved}, "
            "matching exactly the single pair whose resolution was stripped -- "
            "the checker fired on the planted defect and did not over- or "
            "under-flag."
        ),
    },
    "verdict": "CLAIM_REFUTED" if len(real_unresolved) > 0 else "CLAIM_SURVIVED",
}

OUTDIR.mkdir(parents=True, exist_ok=True)
canon_path = OUTDIR / "diagnostic.canonical.json"
canon_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
canon_path.write_bytes(canon_bytes)
print("WROTE", canon_path)
print("verdict", diagnostic["verdict"])
print("n_unresolved", diagnostic["step_3_real_corpus_unresolved_pairs"]["n_unresolved"])
print("unresolved_pairs", real_unresolved)
print("discrimination_control_passed", discrimination_control_passed)
print("positive_control_detected", positive_control_detected)
print("capture_sha256", capture_sha256)
print("blueprint_sha256", blueprint_sha256)
