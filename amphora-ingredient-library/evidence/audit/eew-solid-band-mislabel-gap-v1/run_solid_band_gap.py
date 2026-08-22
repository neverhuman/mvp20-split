#!/usr/bin/env python3
"""
amphora-ingredient-library : eew-solid-band-mislabel-gap-v1  (AUDIT_ONLY)

Attacks constant-crosscheck-v1's Check-1 claim for the solid-epoxy EEW
sub-check: that the admissibility band is "structure-derived" and that
"fail-closed mutation tests confirm gross-error detection".

Falsification criterion (pre-registered)
-----------------------------------------
constant-crosscheck-v1's own script (run_crosscheck.py) computes, for any
catalog key NOT starting with "resin.dgeba_" (i.e. resin.solid_cut_1001x75.
eew_on_nv), an admissibility test:
    n = (FUNC*eew - M0) / MREP
    admissible <=> 1.5 <= n <= 3.5
    band_g_per_eq = [ (M0+1.5*MREP)/FUNC , (M0+3.5*MREP)/FUNC ] = [383.5, 667.8]
The [1.5, 3.5] window is NOT taken from a cited table (Ellis 1993 / Lee &
Neville 1967 do not tabulate a "Type 1 = n in [1.5,3.5]" class); the script's
own inline comment justifies it only as "n ~ 2 expected (Epon 1001 class EEW
450-550)". But facts.json's OWN single_source_waiver note for this exact key
already records the real manufacturer-published range: "Hexion HCD-4022
direct read (450-550 on nonvolatiles)".

REFUTED if: the true manufacturer TDS band (parsed from facts.json's own
note field for resin.solid_cut_1001x75.eew_on_nv) is strictly narrower than
constant-crosscheck-v1's self-computed admissibility band, AND at least one
physically-real EEW value that lies inside the self-computed band but
OUTSIDE the true manufacturer band is NOT flagged by replaying
constant-crosscheck-v1's own admissibility predicate.
SURVIVED if: the self-computed band is <= the true manufacturer band width,
or no such gap value exists.
"""
import base64, hashlib, json, re, sys

FACTS_REL = "reference/mvp20/data/facts.json"
FACTS = "/home/ubuntu/amphora/build/mvp20-split/amphora-ingredient-library/" + FACTS_REL
KEY = "resin.solid_cut_1001x75.eew_on_nv"

# ---- constant-crosscheck-v1's own Check-1 constants/logic, replayed verbatim ----
M0   = 340.42
MREP = 284.35
FUNC = 2
N_LO, N_HI = 1.5, 3.5

def eew_to_n(eew):
    return (FUNC * eew - M0) / MREP

def cc_v1_admissible(eew):
    n = eew_to_n(eew)
    return (N_LO - 1e-9) <= n <= (N_HI + 1e-9)

CC_BAND = [round((M0 + N_LO*MREP)/FUNC, 1), round((M0 + N_HI*MREP)/FUNC, 1)]

TRUE_BAND_NOTE_RE = re.compile(r"(\d+)\s*-\s*(\d+)\s*(?:on nonvolatiles)?")

def build():
    facts = json.load(open(FACTS))
    ent = facts["entries"]
    facts_sha = hashlib.sha256(open(FACTS, "rb").read()).hexdigest()

    fact = ent[KEY]
    catalog_value = float(fact["value"])
    waiver_note = fact.get("single_source_waiver") or ""
    m = TRUE_BAND_NOTE_RE.search(waiver_note)
    true_lo, true_hi = float(m.group(1)), float(m.group(2))
    true_band = [true_lo, true_hi]

    cc_n_of_true_lo = round(eew_to_n(true_lo), 4)
    cc_n_of_true_hi = round(eew_to_n(true_hi), 4)

    cc_width = round(CC_BAND[1] - CC_BAND[0], 2)
    true_width = round(true_band[1] - true_band[0], 2)
    band_ratio = round(cc_width / true_width, 4)

    catalog_within_cc_band = cc_v1_admissible(catalog_value)
    catalog_within_true_band = true_lo <= catalog_value <= true_hi

    # gap zones: admitted by constant-crosscheck-v1's own predicate, but
    # outside the manufacturer band already cited by facts.json for this key
    gap_lo_zone = [CC_BAND[0], true_lo]
    gap_hi_zone = [true_hi, CC_BAND[1]]

    # mutation replay: physically-real EEW values (not digit-corruption
    # noise -- genuine numbers a mislabeled/wrong-grade product could carry)
    # probed inside the two gap zones, tested against constant-crosscheck-v1's
    # OWN admissibility predicate exactly as implemented in run_crosscheck.py
    probe_values = [420.0, 400.0, 600.0, 650.0]
    mutation_results = []
    for v in probe_values:
        n = round(eew_to_n(v), 4)
        cc_flag = not cc_v1_admissible(v)          # would constant-crosscheck-v1 flag it?
        in_gap = (gap_lo_zone[0] <= v < gap_lo_zone[1]) or (gap_hi_zone[0] < v <= gap_hi_zone[1])
        outside_true_band = not (true_lo <= v <= true_hi)
        mutation_results.append({
            "probe_eew_g_per_eq": v,
            "implied_n": n,
            "in_selfcomputed_cc_v1_band": cc_v1_admissible(v),
            "flagged_by_cc_v1_predicate": bool(cc_flag),
            "outside_true_manufacturer_band": bool(outside_true_band),
            "in_undetected_gap_zone": bool(in_gap),
            "demonstrates_missed_detection": bool(in_gap and not cc_flag and outside_true_band),
        })

    n_missed = sum(1 for r in mutation_results if r["demonstrates_missed_detection"])
    band_gap_confirmed = bool(cc_width > true_width) and n_missed > 0

    diag = {
        "schema": "amphora.ingredient-library.eew-solid-band-mislabel-gap.v1",
        "module": "amphora-ingredient-library",
        "run_type": "AUDIT_ONLY",
        "authority": "AUDIT_ONLY",
        "purpose": "Falsification attack on constant-crosscheck-v1 Check-1's claim that the "
                   "solid-epoxy EEW admissibility band is structure-derived and that its "
                   "fail-closed mutation tests confirm gross-error detection, by comparing "
                   "constant-crosscheck-v1's self-computed band against the manufacturer TDS "
                   "band already recorded in facts.json's own single_source_waiver note for "
                   "the identical fact.",
        "hypothesis": "constant-crosscheck-v1's solid_type1_epoxy admissibility band "
                      "([1.5<=n<=3.5], EEW [383.5,667.8]) is claimed structure-derived and "
                      "fail-closed. If the manufacturer-published TDS band already cited "
                      "in-repo for this exact fact (Hexion HCD-4022, 450-550 g/eq NV) is "
                      "strictly narrower, and physically-real EEW values exist that fall "
                      "inside constant-crosscheck-v1's band but outside the true TDS band "
                      "without being flagged, the fail-closed gross-error-detection claim is "
                      "refuted for this constant family.",
        "attacked_claim": {
            "receipt": "amphora-ingredient-library/evidence/audit/constant-crosscheck-v1/constant-crosscheck-receipt.v1.dsse.json",
            "sub_check": "check1_dgeba_eew_admissibility, resin_class=solid_type1_epoxy",
            "constant": KEY,
            "quoted_headline": "All 4 catalog EEW constants fall inside the structure-derived "
                                "epoxy-oligomer admissibility band ... fail-closed mutation "
                                "tests confirm gross-error detection.",
        },
        "inputs": {
            "facts_json_rel": FACTS_REL,
            "facts_json_sha256": facts_sha,
            "fact_key": KEY,
            "fact_note_field_used": "single_source_waiver",
            "fact_note_raw": waiver_note,
        },
        "checkA_band_width_comparison": {
            "cc_v1_selfcomputed_band_g_per_eq": CC_BAND,
            "cc_v1_selfcomputed_n_window": [N_LO, N_HI],
            "cc_v1_band_width_g_per_eq": cc_width,
            "true_manufacturer_tds_band_g_per_eq": true_band,
            "true_manufacturer_tds_source": "Hexion HCD-4022 (as transcribed in facts.json's "
                                             "own single_source_waiver note for " + KEY + "); "
                                             "independent of run_crosscheck.py's invented n-window.",
            "true_manufacturer_band_width_g_per_eq": true_width,
            "true_band_implied_n_window": [cc_n_of_true_lo, cc_n_of_true_hi],
            "cc_v1_band_is_wider_by_ratio": band_ratio,
            "cc_v1_band_strictly_wider_than_true_band": bool(cc_width > true_width),
        },
        "checkB_catalog_value_status": {
            "catalog_value_g_per_eq": catalog_value,
            "within_cc_v1_selfcomputed_band": bool(catalog_within_cc_band),
            "within_true_manufacturer_band": bool(catalog_within_true_band),
            "note": "The catalog value itself (500.0) is a safe midpoint of the true TDS band "
                    "and so passes under either band; this check targets the BAND's own claimed "
                    "provenance and detection power, not this single value.",
        },
        "checkC_undetected_gap_zones": {
            "gap_lo_zone_g_per_eq": gap_lo_zone,
            "gap_hi_zone_g_per_eq": gap_hi_zone,
            "gap_zones_nonempty": bool(gap_lo_zone[1] > gap_lo_zone[0] or gap_hi_zone[1] > gap_hi_zone[0]),
        },
        "checkD_mutation_replay_against_cc_v1_own_predicate": {
            "method": "Each probe value is tested with constant-crosscheck-v1's OWN admissibility "
                      "predicate (eew_to_n + 1.5<=n<=3.5), replayed verbatim from run_crosscheck.py.",
            "probe_values": mutation_results,
            "n_probes_demonstrating_missed_detection": n_missed,
        },
        "verdict": {
            "band_gap_confirmed": band_gap_confirmed,
            "explanation": (
                "constant-crosscheck-v1's solid_type1_epoxy admissibility band is %.1f g/eq wide "
                "(%.2fx wider than the %.0f g/eq manufacturer TDS band already cited in-repo for "
                "the same fact). %d of %d physically-real probe EEW values fall inside "
                "constant-crosscheck-v1's own admissible band, outside the true manufacturer "
                "band, and are NOT flagged by constant-crosscheck-v1's own predicate -- directly "
                "contradicting its headline claim that 'fail-closed mutation tests confirm "
                "gross-error detection' for this constant family. The band's [1.5,3.5] n-window "
                "is not sourced from the cited literature (Ellis 1993 / Lee & Neville 1967 "
                "tabulate no such range); it is wider than the manufacturer spec its own inline "
                "comment cites as justification."
                % (cc_width, band_ratio, true_width, n_missed, len(mutation_results))
            ),
        },
        "closes": [
            "Demonstrates that constant-crosscheck-v1's solid-resin EEW admissibility band is "
            "looser than the manufacturer TDS band already recorded in-repo for the identical "
            "fact, and that this gap is not merely theoretical: constant-crosscheck-v1's own "
            "predicate fails to flag realistic wrong-grade EEW values inside the gap.",
        ],
        "does_not_close": [
            "Does not show the catalog VALUE (500.0) is wrong -- it is well inside both bands.",
            "Does not affect the liquid-DGEBA sub-check (3/4 constants), whose n in [0,0.2] band "
            "is tight and literature-anchored.",
            "Does not modify facts.json, the module manifest, or any locked dataset.",
            "Gap probe values are illustrative EEW numbers, not verified transcriptions of a "
            "real competing product's TDS; they demonstrate the admissibility predicate's "
            "detection power, not an actual catalog error.",
        ],
        "modifies_locked_dataset": False,
        "modifies_manifest": False,
        "modifies_module_manifest": False,
        "modifies_signed_phase0_kpi": False,
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "non_circularity": "The true manufacturer TDS band used for comparison is read from "
                           "facts.json's own single_source_waiver note field (populated at "
                           "catalog-authoring time from the Hexion HCD-4022 TDS), which is a "
                           "different provenance channel than run_crosscheck.py's hardcoded "
                           "[1.5,3.5] n-window (invented at audit-authoring time); comparing the "
                           "two is a genuine in-repo cross-check, not a self-referential re-read "
                           "of the audit script's own constants.",
        "theory_reference": {
            "eew_oligomer_series": "Ellis 1993 (ISBN 978-0-7514-0095-6); Lee & Neville 1967, "
                                    "Handbook of Epoxy Resins -- cited by constant-crosscheck-v1 "
                                    "as the basis for its band, but does not tabulate the "
                                    "[1.5,3.5] n-window used for the solid-resin class.",
            "manufacturer_tds_band": "Hexion HCD-4022 EPON Resin 1001-X-75, EEW 450-550 g/eq on "
                                      "nonvolatiles (as transcribed into facts.json's "
                                      "single_source_waiver note at catalog-authoring time).",
        },
        "headline": None,
    }
    diag["headline"] = (
        "constant-crosscheck-v1's solid-resin EEW admissibility band [%s] is %.2fx wider than "
        "the manufacturer TDS band [%s] already cited in-repo for the identical fact (%s); "
        "%d/%d realistic gap-zone probe values are admitted by constant-crosscheck-v1's own "
        "predicate without being flagged, refuting its fail-closed gross-error-detection claim "
        "for the solid-resin EEW sub-check."
        % (CC_BAND, band_ratio, true_band, KEY, n_missed, len(mutation_results))
    )
    return diag

def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()

if __name__ == "__main__":
    d1 = build(); b1 = canon(d1); h1 = hashlib.sha256(b1).hexdigest()
    d2 = build(); b2 = canon(d2); h2 = hashlib.sha256(b2).hexdigest()
    assert b1 == b2, "two-replay byte MISMATCH"
    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        open("diagnostic.canonical.json", "wb").write(b1)
        open("diagnostic.runB.json", "wb").write(b2)
    print("replay_sha256:", h1, "| byte_stable:", h1 == h2)
    print("band_gap_confirmed:", d1["verdict"]["band_gap_confirmed"])
    print("headline:", d1["headline"])
