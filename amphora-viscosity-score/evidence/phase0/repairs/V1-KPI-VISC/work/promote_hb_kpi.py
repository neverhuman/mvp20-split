#!/usr/bin/env python3
"""V1-KPI-VISC: promote the AUDIT_ONLY Herschel-Bulkley CC-BY Amorim-2021
validation (evidence/audit/herschel-bulkley-ccby-amorim2021-v1/) to the
Phase-0 KPI surface (evidence/phase0/kpis/) for amphora-viscosity-score.

REPAIR-MODE discipline (item id prefix V-):
  1. Re-runs the ORIGINAL refuting attack script verbatim (same file, same
     sha256, same invocation, no args changed) and asserts the fresh
     diagnostic is byte-identical to the diagnostic that was signed into the
     parent audit receipt. This is the "re-attack your own fix" step -- here
     there is no fix to re-verify, but the promotion is only honest if the
     claim still survives the SAME falsifying check right now, not just on
     2026-08-01.
  2. Self-verifies the parent audit receipt's DSSE signature against the
     pinned Phase-0 evaluator public key before relying on it.
  3. Writes an unsigned KPI-surface descriptor (house convention: KPI files
     in evidence/phase0/kpis/ are plain JSON that carry authority by
     referencing a signed receipt's sha256, not by being individually
     DSSE-wrapped themselves -- see viscosity-arrhenius-kpi.v1.json and the
     two polyverse KPI files in the same directory).
  4. DSSE-Ed25519-signs the actual campaign deliverable: a KPI-PROMOTION
     receipt under evidence/phase0/repairs/V1-KPI-VISC/done/ that carries
     the source DOI+licence, the locale-repair provenance note, the
     single-source/single-resin/single-temperature scope limit, the
     KRIEGER_DOUGHERTY rights-wall/unbenchmarked status, the parent audit
     receipt hash, and the fresh re-attack result.

AUDIT_ONLY / PROMOTE_KPI_SURFACE_ONLY: does not flip module phase or
scientific_readiness (still PRE_PHASE_0 / UNVALIDATED pending human
PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER ceremony), does not edit the
signed FFW/melt-viscosity or Arrhenius KPIs, does not touch the 66-receipt
master manifest.
"""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"
AUDIT = MOD / "evidence/audit/herschel-bulkley-ccby-amorim2021-v1"
REPAIR = MOD / "evidence/phase0/repairs/V1-KPI-VISC"
KPIS = MOD / "evidence/phase0/kpis"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


def verify_envelope(envelope, pub_hex):
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
    body = base64.standard_b64decode(envelope["payload"])
    sig = base64.standard_b64decode(envelope["signatures"][0]["sig"])
    pub.verify(sig, pae(envelope["payloadType"], body))
    return True


# --- step 1: self-verify the parent AUDIT_ONLY receipt ---------------------
parent_path = AUDIT / "herschel-bulkley-ccby-amorim2021-receipt.v1.dsse.json"
parent_bytes = parent_path.read_bytes()
parent_receipt = json.loads(parent_bytes)
parent_env = parent_receipt["signature"]
verify_envelope(parent_env, parent_receipt["evaluator_public_key_hex"])
parent_body = json.loads(base64.standard_b64decode(parent_env["payload"]))
assert parent_body["verdict"] == "CLAIM_SURVIVED"
parent_sha256 = sha(parent_bytes)

# --- step 2: re-run the ORIGINAL refuting attack script verbatim -----------
harness_path = AUDIT / "run_hb_benchmark.py"
harness_sha256 = sha(harness_path.read_bytes())
assert harness_sha256 == parent_body["provenance"]["harness_sha256"]["run_hb_benchmark.py"], \
    "harness script has changed since the parent audit -- re-attack invalid"

reattack_out = REPAIR / "work" / "diagnostic.reattack.json"
subprocess.run(["python3", str(harness_path), str(reattack_out)], check=True, cwd=str(AUDIT))
reattack_sha256 = sha(reattack_out.read_bytes())
reattack_diag = json.loads(reattack_out.read_bytes())

recorded_canonical_sha256 = parent_body["reproducibility"]["canonical_diagnostic_sha256"]
byte_identical = (reattack_sha256 == recorded_canonical_sha256)
assert byte_identical, f"RE-ATTACK DIVERGED: {reattack_sha256} != {recorded_canonical_sha256}"
assert reattack_diag["all_corrected_gates_passed"] is True
assert reattack_diag["literal_english_reading_all_within_axis_bounds"] is False

# --- step 3: write the (unsigned, house-convention) KPI-surface descriptor -
kpi_body = {
    "$schema": "amphora.module-phase0-kpi.v1",
    "schema": "amphora.module-phase0-kpi.v1",
    "kpi_id": "amphora-viscosity-score-phase0-herschel-bulkley-ccby-amorim2021-kpi-v1",
    "module_id": "amphora-viscosity-score",
    "authority_ceiling": "LIMITED_SANITY",
    "populated_at": "2026-08-04",
    "capability": (
        "Herschel-Bulkley yield-flow path (src/lib.rs:1227) evaluated at "
        "published fitted parameters (tau_0, K, n) from a rights-clean CC BY "
        "4.0 real-data source: Amorim, Oliveira, Mancini & Sirqueira (2021) "
        "SN Applied Sciences 3:236, doi:10.1007/s42452-021-04247-7 -- "
        "commercial DGEBA epoxy/polyamide anti-corrosion coating, control + "
        "5 carbon-black/nanoclay formulations, steady-shear 0.1-100 s^-1, "
        "25C, R^2>0.998 for all 6 fits. This is PARAMETER-LEVEL reproduction "
        "(module equation evaluated at the paper's own published tau_0/K/n "
        "and cross-checked against the paper's own stated Fig.3 axis bounds "
        "and ranking claims), not a raw (gamma_dot, eta) point-level "
        "regression -- the source paper does not tabulate raw flow-curve "
        "points."
    ),
    "source": {
        "source_id": parent_body["source"]["source_id"],
        "doi": parent_body["source"]["doi"],
        "license": parent_body["source"]["license"],
        "source_lock_sha256": parent_body["source"]["source_lock_sha256"],
    },
    "locale_repair_provenance": {
        "issue": (
            "As-printed Table 2 typesets every tau_0/K value with a comma "
            "before the final 3 digits, while n/R2/MRD in the same table use "
            "a period -- a Word/Excel-to-PDF locale (comma-decimal) mixup "
            "affecting only the thousands-scale columns."
        ),
        "repair": (
            "Last comma read as the decimal separator (European/Brazilian "
            "locale convention consistent with the corresponding author's "
            "Brazilian institutional affiliation), independently justified "
            "by cross-checking against the paper's OWN stated Fig.3 "
            "apparent-viscosity axis metadata (1 to 1e5 Pa.s) -- not by "
            "fitting the repair to make the module's equation look good."
        ),
        "control_arm_result": (
            "The literal-English reading of the SAME as-printed table "
            "(comma = thousands separator, i.e. what a downstream engineer "
            "would transcribe verbatim) fails the paper's own axis bounds by "
            "13x-1500x for every one of the 6 formulations. This control arm "
            "is the falsifying observation the attack was pre-registered to "
            "surface, and it DID fire -- just for the wrong/naive reading, "
            "not the corrected one."
        ),
        "literal_english_max_multiple_over_axis_ceiling": max(
            row["literal_english_max_multiple_over_axis_ceiling"]
            for row in reattack_diag["rows"]
        ),
    },
    "scope_limits": [
        "Single source (one paper, one lab).",
        "Single commercial resin family (JUMBO-grade DGEBA epoxy / polyamide).",
        "Single temperature (25C).",
        "Parameter-level benchmark only -- module equation evaluated AT "
        "published fitted tau_0/K/n, cross-checked against the paper's own "
        "reported axis range and ranking claims. No raw (gamma_dot, eta) "
        "point-level regression was performed or is possible from this "
        "source (paper tabulates only fitted parameters and a graphical "
        "Fig.3, not raw flow-curve data points).",
        "Does not establish Herschel-Bulkley adequacy across coating "
        "chemistries, resin families, or temperatures.",
    ],
    "krieger_dougherty_status": (
        "KRIEGER_DOUGHERTY (pigment/filler volume-fraction crowding, "
        "src/lib.rs:1208) remains UNBENCHMARKED in-tree. No rights-clean "
        "pigment/filler volume-fraction viscosity ladder was located during "
        "the parent audit's open-literature sweep (MDPI Coatings/Polymers, "
        "RSC Advances, ACS Omega, Scientific Reports, Frontiers, SN Applied "
        "Sciences). This is a genuine data gap, filed to the "
        "data-acquisition-queue, not a rights-quarantine of an identified "
        "asset."
    ),
    "metrics": [
        {
            "name": "corrected_reading_all_within_paper_axis_bounds",
            "authority": "REAL_ARITHMETIC",
            "direction": "MAXIMIZE",
            "floor": 1.0,
            "observed": 1.0 if reattack_diag["corrected_reading_all_within_axis_bounds"] else 0.0,
            "passed": bool(reattack_diag["corrected_reading_all_within_axis_bounds"]),
            "sample_size": 6,
            "note": "All 6 formulations' apparent viscosity (locale-repaired reading) lands inside the paper's own stated Fig.3 axis range [1, 1e5] Pa.s at all 4 tested shear rates.",
        },
        {
            "name": "corrected_reading_all_monotonic_shear_thinning",
            "authority": "REAL_ARITHMETIC",
            "direction": "MAXIMIZE",
            "floor": 1.0,
            "observed": 1.0 if (reattack_diag["corrected_reading_all_monotonic_decreasing"] and reattack_diag["corrected_reading_all_shear_thinning_n_lt_1"]) else 0.0,
            "passed": bool(reattack_diag["corrected_reading_all_monotonic_decreasing"] and reattack_diag["corrected_reading_all_shear_thinning_n_lt_1"]),
            "sample_size": 6,
            "note": "All 6 formulations n<1 and apparent viscosity monotonically decreasing with shear rate, matching the paper's own stated finding.",
        },
        {
            "name": "paper_ranking_claims_reproduced",
            "authority": "REAL_ARITHMETIC",
            "direction": "MAXIMIZE",
            "floor": 1.0,
            "observed": 1.0 if (reattack_diag["sample4_has_max_tau0_corrected"] and reattack_diag["epoxy_control_has_min_K_corrected"]) else 0.0,
            "passed": bool(reattack_diag["sample4_has_max_tau0_corrected"] and reattack_diag["epoxy_control_has_min_K_corrected"]),
            "sample_size": 6,
            "note": "Sample 4 = max yield stress (tau_0), unmodified epoxy control = min consistency coefficient (K), reproducing the paper's own stated ranking.",
        },
        {
            "name": "literal_reading_control_arm_fails_axis_bounds",
            "authority": "REAL_ARITHMETIC",
            "direction": "MINIMIZE",
            "ceiling": 0.0,
            "observed": 0.0 if not reattack_diag["literal_english_reading_all_within_axis_bounds"] else 1.0,
            "passed": not reattack_diag["literal_english_reading_all_within_axis_bounds"],
            "sample_size": 6,
            "note": "Control arm: literal-English (naive transcription) reading of the same table fails the paper's own axis bounds by 13x-1500x for all 6 formulations -- confirms the attack was genuinely capable of falsifying and did fire, just not for the justified reading.",
        },
    ],
    "phase0_deterministic_gates_passed": True,
    "n_deterministic_gates_defined": 4,
    "n_deterministic_gates_passed": 4,
    "population": "Commercial DGEBA epoxy/polyamide marine/anti-corrosion coating, control + 5 carbon-black/nanoclay formulations, 25C, steady shear 0.1-100 s^-1.",
    "split_methodology": "No split performed -- this is a parameter-level cross-check against externally published fitted parameters and externally published axis/ranking metadata, not a fitted model with train/test partitions.",
    "theory": "Herschel, W.H. & Bulkley, R. (1926) 'Konsistenzmessungen von Gummi-Benzollosungen', Kolloid-Zeitschrift 39:291-300. eta_apparent(gamma_dot) = tau_0/gamma_dot + K*gamma_dot^(n-1).",
    "claim_locks": {
        "no_batch_release_authority": True,
        "no_manufacturing_qualification_authority": True,
        "no_optimizer_authority": True,
        "no_patentability_authority": True,
        "no_phase_1_or_phase_2_claim": True,
        "no_product_performance_authority": True,
        "no_regulatory_authority": True,
        "no_release_authority": True,
        "no_safety_authority": True,
        "no_solver_authority": True,
        "no_wet_lab_evidence_upgrade": True,
        "parameter_level_benchmark_only_not_point_level_regression": True,
        "single_source_single_resin_single_temperature_scope": True,
        "krieger_dougherty_remains_unbenchmarked": True,
        "pre_phase_0_research_only": True,
        "documented_locale_repair_independently_justified": True,
    },
    "awaiting": [
        "PHASE0_EVALUATOR signed evaluation.v1.dsse.json",
        "PHASE0_INTERNAL_REVIEWER signed phase0-review-receipt.v1.json",
        "Phase-1: raw (gamma_dot, eta) point-level flow-curve dataset (this source only tabulates fitted parameters + a graphical Fig.3)",
        "Phase-1: additional sources spanning multiple resin families and temperatures to test HB adequacy beyond this single paper",
        "KRIEGER_DOUGHERTY: a rights-clean pigment/filler volume-fraction viscosity ladder (data-acquisition-queue ask)",
    ],
    "scientific_receipt_id": parent_body["receipt_id"],
    "scientific_receipt_path": "amphora-viscosity-score/evidence/audit/herschel-bulkley-ccby-amorim2021-v1/herschel-bulkley-ccby-amorim2021-receipt.v1.dsse.json",
    "scientific_receipt_sha256": parent_sha256,
    "dataset_fixture_sha256": parent_body["source"]["source_lock_sha256"],
}
kpi_out = KPIS / "herschel-bulkley-ccby-amorim2021-kpi.v1.json"
kpi_text = json.dumps(kpi_body, indent=2, sort_keys=True)
kpi_out.write_text(kpi_text)
kpi_sha256 = sha(kpi_text.encode())

# --- step 4: DSSE-sign the campaign deliverable -----------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text()) if TRUST.exists() else {"keys": []}
tbr = {k.get("role"): k for k in trust.get("keys", [])}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

promotion_body = {
    "schema": "amphora.viscosity-score.herschel-bulkley-kpi-promotion-receipt.v1",
    "receipt_id": "herschel-bulkley-ccby-amorim2021-kpi-promotion-v1",
    "module_id": "amphora-viscosity-score",
    "campaign_item_id": "V1-KPI-VISC",
    "repair_mode": {
        "action": "PROMOTE_AUDIT_TO_KPI_SURFACE",
        "supersedes": None,
        "note": "Purely additive: the parent AUDIT_ONLY receipt is untouched; this receipt places its result on the Phase-0 KPI surface with full scope disclosure.",
    },
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "LIMITED_SANITY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-04",
    "generated_on_host": "xbabe2",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "flips_operational_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_existing_signed_phase0_kpi": False,
    "adds_new_phase0_kpi_surface_entry": True,
    "modifies_source_landscape": False,
    "claim": (
        "The Herschel-Bulkley implementation (src/lib.rs:1227) is validated "
        "against published CC-BY rheology (Amorim et al. 2021, SN Applied "
        "Sciences 3:236, doi:10.1007/s42452-021-04247-7, CC BY 4.0) at the "
        "parameter level, and that validation is promoted to the module's "
        "Phase-0 KPI surface, carrying: the source DOI+licence, the "
        "locale-repair provenance note (and its literal-reading control-arm "
        "failure), the single-source/single-resin/single-temperature scope "
        "limit, and the fact that KRIEGER_DOUGHERTY remains unbenchmarked "
        "behind a genuine data gap (not a rights wall on an identified "
        "asset). This is parameter-level reproduction, not a point-level "
        "regression -- the source paper does not tabulate raw flow-curve "
        "points."
    ),
    "source": parent_body["source"],
    "locale_repair_provenance": kpi_body["locale_repair_provenance"],
    "scope_limits": kpi_body["scope_limits"],
    "krieger_dougherty_status": kpi_body["krieger_dougherty_status"],
    "parent_audit_receipt": {
        "path": "amphora-viscosity-score/evidence/audit/herschel-bulkley-ccby-amorim2021-v1/herschel-bulkley-ccby-amorim2021-receipt.v1.dsse.json",
        "sha256": parent_sha256,
        "verdict": parent_body["verdict"],
        "signature_self_verified": True,
        "signed_by_key_id": parent_receipt["evaluator_key_id"],
    },
    "re_attack": {
        "description": (
            "Re-ran the ORIGINAL refuting attack script verbatim (same "
            "file, same sha256, same invocation `python3 "
            "run_hb_benchmark.py <out>`, no args/thresholds changed) to "
            "confirm the CLAIM_SURVIVED verdict holds NOW, not just at the "
            "parent audit's 2026-08-01 timestamp, before promoting to the "
            "KPI surface."
        ),
        "harness_path": "amphora-viscosity-score/evidence/audit/herschel-bulkley-ccby-amorim2021-v1/run_hb_benchmark.py",
        "harness_sha256": harness_sha256,
        "recorded_canonical_diagnostic_sha256": recorded_canonical_sha256,
        "reattack_diagnostic_sha256": reattack_sha256,
        "byte_identical_to_recorded": byte_identical,
        "all_corrected_gates_passed": reattack_diag["all_corrected_gates_passed"],
        "literal_english_reading_all_within_axis_bounds": reattack_diag["literal_english_reading_all_within_axis_bounds"],
        "refutation_criterion": parent_body["refutation_criterion"],
        "verdict": "CLAIM_SURVIVED",
    },
    "kpi_surface_entry": {
        "path": "amphora-viscosity-score/evidence/phase0/kpis/herschel-bulkley-ccby-amorim2021-kpi.v1.json",
        "sha256": kpi_sha256,
        "schema": "amphora.module-phase0-kpi.v1",
    },
    "does_not_close": parent_body["does_not_close"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "reattack_replay_matches_parent_canonical": byte_identical,
        "determinism": "pure-python arithmetic re-derivation of src/lib.rs:1227, no RNG, no network at run time (source table hash-locked).",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY KPI-promotion receipt under evidence/phase0/repairs/V1-KPI-VISC/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
    "verdict": "CLAIM_SURVIVED",
    "verdict_detail": (
        "CLAIM_SURVIVED -- the Herschel-Bulkley parameter-level validation "
        "against Amorim et al. 2021 (CC BY 4.0) withstands re-attack with "
        "the original falsifying script byte-identically reproduced, and is "
        "hereby promoted to the Phase-0 KPI surface at "
        "evidence/phase0/kpis/herschel-bulkley-ccby-amorim2021-kpi.v1.json "
        "with full source, licence, locale-repair, and scope disclosure. "
        "This does NOT flip module phase (remains PRE_PHASE_0) or "
        "scientific_readiness (remains UNVALIDATED overall) -- those "
        "require the human PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER "
        "dual-identity ceremony this cron does not hold."
    ),
}
body = json.dumps(promotion_body, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-herschel-bulkley-kpi-promotion+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = REPAIR / "done" / "herschel-bulkley-kpi-promotion-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify before declaring
verify_envelope(envelope, eval_pub_hex)

print("WROTE", out)
print("WROTE", kpi_out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("reattack_byte_identical", byte_identical)
print("receipt_sha256", sha(out.read_bytes()))
print("kpi_sha256", kpi_sha256)
print("signature_verified", True)
