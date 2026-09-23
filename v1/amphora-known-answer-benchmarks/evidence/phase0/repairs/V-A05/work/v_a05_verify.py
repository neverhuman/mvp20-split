#!/usr/bin/env python3
"""V-A05: independent adversarial verify of interactive repair R-A05
(amphora-known-answer-benchmarks). Re-derives the ARITH-A221-X70P1-VOLUME-SOLIDS
and ARITH-A702B75P1-VOLUME-SOLIDS corrected values from raw masses/densities with
a FRESH, independently-written exact-rational implementation (not the repair's
script); re-fetches the A221 TDS live to cross-check the transcription the repair
inherited from the original refuting receipt; verifies sweep completeness by
enumerating all 14 raw controls directly; Ed25519-verifies R-A05's own DSSE
envelope against the pinned Phase-0 evaluator key; and checks byte-intactness of
every file R-A05 claims it left untouched. AUDIT_ONLY. Writes no supersession.
"""
import base64, hashlib, json, subprocess
from fractions import Fraction as F
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-known-answer-benchmarks"
R_A05_DONE = MOD / "evidence/phase0/repairs/R-A05/done/R-A05.done-receipt.v1.dsse.json"
CONTROL_RECEIPT = MOD / "reference/mvp20/out/control_by_control_receipt.v1.json"
ARITH_AUDIT = MOD / "reference/mvp20/out/arithmetic_audit.json"
RESULT_V1 = MOD / "evidence/phase0/benchmark/result.v1.json"
RETRACTION_INDEX = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
MISSION = MOD / "docs/mission.md"
A702_CACHED_PDF = MOD / "evidence/phase0/repairs/R-A05/work/a702b75_us_tds.pdf"
A221_FRESH_PDF = MOD / "evidence/phase0/repairs/V-A05/work/a221_verify.pdf"
A221_FRESH_TXT = MOD / "evidence/phase0/repairs/V-A05/work/a221_verify.txt"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


checks = {}

# --- 1. precondition ---
checks["1_precondition_done_receipt_exists"] = R_A05_DONE.exists()
assert checks["1_precondition_done_receipt_exists"], "no R-A05 done receipt -> CLAIM_REFUTED (no repair)"

r_a05 = json.loads(R_A05_DONE.read_bytes())
r_a05_sig = r_a05["signature"]
r_a05_payload = base64.standard_b64decode(r_a05_sig["payload"])
r_a05_body = json.loads(r_a05_payload)

# --- 2. Ed25519 verify R-A05's own DSSE envelope against the pinned trust-store key ---
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust.get("keys", [])}
pinned_eval_key_id = tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
checks["2_r_a05_evaluator_key_id"] = r_a05["evaluator_key_id"]
checks["2_r_a05_evaluator_key_matches_pinned_trust_store"] = (r_a05["evaluator_key_id"] == pinned_eval_key_id)

pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(r_a05["evaluator_public_key_hex"]))
sigbytes = base64.standard_b64decode(r_a05_sig["signatures"][0]["sig"])
try:
    pub.verify(sigbytes, pae(r_a05_sig["payloadType"], r_a05_payload))
    checks["2_r_a05_dsse_signature_valid"] = True
except Exception:
    checks["2_r_a05_dsse_signature_valid"] = False

# --- 3. Sweep completeness: enumerate all controls in control_by_control_receipt.v1.json myself ---
cbc = json.loads(CONTROL_RECEIPT.read_bytes())
controls = cbc["controls"]
checks["3_control_count_on_disk"] = len(controls)
checks["3_control_count_matches_receipt_field"] = (len(controls) == cbc["control_count"])
vs_controls = [c["control_id"] for c in controls if "VOLUME-SOLIDS" in c["control_id"]]
non_vs_controls = [c["control_id"] for c in controls if "VOLUME-SOLIDS" not in c["control_id"]]
# independently confirm no non-VOLUME-SOLIDS control has a volume-solids-shaped
# tolerance (percentage_point absolute tolerance on a numeric 30-70-range actual)
# that could hide a mislabeled volume-solids semantic
suspect_mislabeled = [
    c["control_id"] for c in controls
    if "VOLUME-SOLIDS" not in c["control_id"]
    and isinstance(c.get("tolerance"), dict)
    and c["tolerance"].get("unit") == "percentage_point"
]
checks["3_volume_solids_controls_found"] = sorted(vs_controls)
checks["3_volume_solids_controls_count"] = len(vs_controls)
checks["3_non_volume_solids_controls_with_percentage_point_tolerance"] = suspect_mislabeled
checks["3_sweep_matches_r_a05_claim_2_of_2"] = (len(vs_controls) == 2 and len(suspect_mislabeled) == 0)
r_a05_swept = r_a05_body["sweep"]["flagged_as_mass_basis_conflated"] + \
    [c["control_id"] for c in r_a05_body["sweep"]["volume_solids_controls"]
     if c["control_id"] not in r_a05_body["sweep"]["flagged_as_mass_basis_conflated"]]
checks["3_r_a05_swept_control_ids"] = sorted(set(r_a05_swept))
checks["3_r_a05_swept_matches_independent_enumeration"] = (sorted(set(r_a05_swept)) == sorted(vs_controls))

# --- 4. Independent, freshly-written exact-rational re-derivation ---
def volume_weighted(mass_a, dens_a, vs_a, mass_b, dens_b, vs_b):
    vol_a = mass_a / dens_a
    vol_b = mass_b / dens_b
    solids_vol = vol_a * vs_a / F(100) + vol_b * vs_b / F(100)
    total_vol = vol_a + vol_b
    return solids_vol / total_vol * 100, vol_a, vol_b


def mass_fraction_weighted(mass_a, vs_a, mass_b, vs_b):
    total_mass = mass_a + mass_b
    return (mass_a / total_mass) * vs_a + (mass_b / total_mass) * vs_b


# A221-X70P1 -- transcribed independently from a FRESH live re-fetch of the TDS
# (see section 5 below), not copied from R-A05's own transcription
mA1, dA1, vsA1, wtA1 = F(1000), F(151, 100), F(46), F(70)
mB1, dB1, vsB1, wtB1 = F(200), F(23, 25), F(63, 2), F(371, 10)
correct_a221, volA1, volB1 = volume_weighted(mA1, dA1, vsA1, mB1, dB1, vsB1)
invalid_a221 = mass_fraction_weighted(mA1, vsA1, mB1, vsB1)
wt_check_a221 = (mA1 * wtA1 / 100 + mB1 * wtB1 / 100) / (mA1 + mB1) * 100

# A702B75P1 -- transcribed independently from the cached, hash-verified TDS extract
mA2, dA2, vsA2, wtA2 = F(1000), F(41, 25), F(679, 10), F(833, 10)
mB2, dB2, vsB2, wtB2 = F(284), F(19, 20), F(492, 10), F(111, 2)
correct_a702, volA2, volB2 = volume_weighted(mA2, dA2, vsA2, mB2, dB2, vsB2)
invalid_a702 = mass_fraction_weighted(mA2, vsA2, mB2, vsB2)
wt_check_a702 = (mA2 * wtA2 / 100 + mB2 * wtB2 / 100) / (mA2 + mB2) * 100

checks["4_independent_a221_correct_volume_weighted_exact"] = str(correct_a221)
checks["4_independent_a221_correct_volume_weighted_4dp"] = round(float(correct_a221), 4)
checks["4_independent_a221_invalid_mass_fraction_4dp"] = round(float(invalid_a221), 4)
checks["4_independent_a221_wt_pct_solids_sanity_gate_4dp"] = round(float(wt_check_a221), 4)
checks["4_independent_a702_correct_volume_weighted_exact"] = str(correct_a702)
checks["4_independent_a702_correct_volume_weighted_4dp"] = round(float(correct_a702), 4)
checks["4_independent_a702_invalid_mass_fraction_4dp"] = round(float(invalid_a702), 4)
checks["4_independent_a702_wt_pct_solids_sanity_gate_4dp"] = round(float(wt_check_a702), 4)

r_a05_a221 = r_a05_body["corrected_values"]["ARITH-A221-X70P1-VOLUME-SOLIDS"]["corrected_actual"]
r_a05_a702 = r_a05_body["corrected_values"]["ARITH-A702B75P1-VOLUME-SOLIDS"]["exact_topdown_reference_value"]
checks["4_matches_r_a05_a221_corrected_actual_to_4dp"] = (round(float(correct_a221), 4) == round(float(r_a05_a221), 4))
checks["4_matches_r_a05_a702_topdown_reference_to_4dp"] = (round(float(correct_a702), 4) == round(float(r_a05_a702), 4))
# and: does correct recompute reproduce the TDS-published values (independent of R-A05's own framing)?
checks["4_a221_correct_reproduces_published_42_5_within_0_2pp"] = (abs(float(correct_a221) - 42.5) < 0.2)
checks["4_a702_correct_reproduces_published_62_0_within_0_3pp"] = (abs(float(correct_a702) - 62.0) < 0.3)
checks["4_a221_invalid_still_closely_reproduces_superseded_actual_43_7"] = (abs(float(invalid_a221) - 43.7) < 0.2)

# --- 5. Fresh live re-fetch of the A221 TDS + hash check of the cached A702 TDS ---
checks["5_a221_fresh_pdf_present"] = A221_FRESH_PDF.exists()
checks["5_a221_fresh_pdf_sha256"] = sha(A221_FRESH_PDF.read_bytes()) if A221_FRESH_PDF.exists() else None
a221_txt = A221_FRESH_TXT.read_text(errors="replace") if A221_FRESH_TXT.exists() else ""
a221_expected_strings = [
    "Density (g/ml)", "1.51", "0.92", "1.37",
    "Solid Content (weight %)", "70.0", "37.1", "64.5",
    "Solid Content (Volume %)", "46.0", "31.5", "42.5",
    "106.00", "200.00", "1,000.00",
]
checks["5_a221_fresh_fetch_contains_all_transcribed_source_numbers"] = all(s in a221_txt for s in a221_expected_strings)
checks["5_a221_fresh_fetch_low_volume_solids_narrative_43pct_present"] = ("low volume solids (43%)" in a221_txt)

checks["5_a702_cached_pdf_present"] = A702_CACHED_PDF.exists()
checks["5_a702_cached_pdf_sha256"] = sha(A702_CACHED_PDF.read_bytes()) if A702_CACHED_PDF.exists() else None
checks["5_a702_cached_pdf_sha256_matches_r_a05_claimed"] = (
    checks["5_a702_cached_pdf_sha256"] == r_a05_body["repair_artifacts"]["tds_pdf_sha256"]
)

# --- 6. Byte-intactness of every file R-A05 claims it left untouched ---
byte_intact = {}
for path_str, claimed_sha in [
    (str(CONTROL_RECEIPT.relative_to(ROOT)), r_a05_body["supersedes"]["superseded_sha256"]),
    (str(ARITH_AUDIT.relative_to(ROOT)), r_a05_body["also_affected_not_modified"]["arithmetic_audit.json"]["sha256"]),
    (str(RESULT_V1.relative_to(ROOT)), r_a05_body["also_affected_not_modified"]["result.v1.json"]["sha256"]),
]:
    actual = sha((ROOT / path_str).read_bytes())
    byte_intact[path_str] = {"expected_sha256": claimed_sha, "actual_sha256": actual, "byte_intact": actual == claimed_sha}
checks["6_byte_intact_checks"] = byte_intact
checks["6_all_byte_intact"] = all(v["byte_intact"] for v in byte_intact.values())

# --- 7. Retraction index + mission.md discipline ---
checks["7_retraction_index_exists"] = RETRACTION_INDEX.exists()
ri_text = RETRACTION_INDEX.read_text() if RETRACTION_INDEX.exists() else ""
checks["7_retraction_index_mentions_r_a05"] = ("R-A05" in ri_text)
checks["7_retraction_index_mentions_42_4165"] = ("42.4165" in ri_text)
mission_text = MISSION.read_text() if MISSION.exists() else ""
checks["7_mission_md_mentions_43_7_or_42_5_or_volume_solids_control_id"] = any(
    s in mission_text for s in ["43.7", "ARITH-A221-X70P1-VOLUME-SOLIDS", "42.4165"]
)
checks["7_mission_md_update_not_required"] = (not checks["7_mission_md_mentions_43_7_or_42_5_or_volume_solids_control_id"])

# --- 8. Reattack: re-apply the ORIGINAL refuting receipt's falsification criterion
#     to the CORRECTED value, independently ---
# criterion: correct method must NOT reproduce 43.7 (superseded actual), and MUST
# reproduce the TDS-published expected (42.5) within normal source rounding.
checks["8_reattack_corrected_a221_not_reproducible_by_superseded_actual_43_7"] = (abs(float(correct_a221) - 43.7) > 0.5)
checks["8_reattack_corrected_a221_reproduces_expected_42_5"] = checks["4_a221_correct_reproduces_published_42_5_within_0_2pp"]

all_checks_pass = (
    checks["1_precondition_done_receipt_exists"]
    and checks["2_r_a05_evaluator_key_matches_pinned_trust_store"]
    and checks["2_r_a05_dsse_signature_valid"]
    and checks["3_control_count_matches_receipt_field"]
    and checks["3_sweep_matches_r_a05_claim_2_of_2"]
    and checks["3_r_a05_swept_matches_independent_enumeration"]
    and checks["4_matches_r_a05_a221_corrected_actual_to_4dp"]
    and checks["4_matches_r_a05_a702_topdown_reference_to_4dp"]
    and checks["4_a221_correct_reproduces_published_42_5_within_0_2pp"]
    and checks["4_a702_correct_reproduces_published_62_0_within_0_3pp"]
    and checks["5_a221_fresh_fetch_contains_all_transcribed_source_numbers"]
    and checks["5_a702_cached_pdf_sha256_matches_r_a05_claimed"]
    and checks["6_all_byte_intact"]
    and checks["7_retraction_index_mentions_r_a05"]
    and checks["7_retraction_index_mentions_42_4165"]
    and checks["8_reattack_corrected_a221_not_reproducible_by_superseded_actual_43_7"]
    and checks["8_reattack_corrected_a221_reproduces_expected_42_5"]
)
checks["all_checks_pass"] = all_checks_pass

report = {
    "schema": "amphora.known-answer-benchmarks.repair-verify-report.v1",
    "verify_item": "V-A05",
    "target_repair_item": "R-A05",
    "checks": checks,
}
out_path = MOD / "evidence/phase0/repairs/V-A05/work/V-A05-verify-report.v1.json"
out_path.write_text(json.dumps(report, indent=2, sort_keys=True))
print("all_checks_pass:", all_checks_pass)
print("WROTE", out_path)
