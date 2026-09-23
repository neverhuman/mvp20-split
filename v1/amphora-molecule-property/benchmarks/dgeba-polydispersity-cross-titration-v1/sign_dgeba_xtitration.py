#!/usr/bin/env python3
"""DSSE-Ed25519-sign the dgeba-polydispersity-cross-titration AUDIT_ONLY receipt with the
repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f..., NOT trust-anchored). Promotes
nothing; modifies no existing receipt, manifest, census, split, or lock (66/11 intact)."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-property/benchmarks/dgeba-polydispersity-cross-titration-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["all_gates_passed"] is True, "gates did not all pass"
compute = (BENCH / "compute_dgeba_xtitration.py").read_bytes()

g2 = diag["gates"]["G2_polydispersity_invariance"]
g3 = diag["gates"]["G3_H0_end_group_defect_robustness"]
g4 = diag["gates"]["G4_detector_sensitivity_and_specificity"]

receipt = {
    "schema": "amphora.molecule-property.dgeba-polydispersity-cross-titration-receipt.v1",
    "receipt_id": "dgeba-polydispersity-cross-titration-" + sha(canon)[:32],
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "promotes_nothing": True,
    "modifies_no_live_config": True,
    "module": "amphora-molecule-property",
    "claim": "An independent RDKit-2026.03.2 + closed-form-distribution audit lifts the "
        "module's two pure-oligomer property receipts (EEW series, hydroxyl value) from "
        "SINGLE oligomers to POLYDISPERSE mixtures, which is what a real resin is, and then "
        "attacks the result. (1) PARITY: the four structural constants and three OHV values "
        "already signed by dgeba-oligomer-eew-series-v1 and dgeba-oligomer-hydroxyl-value-v1 "
        "are re-derived independently and match to <=5e-4 (7/7 rows). (2) THEOREM "
        "(polydispersity invariance): because every ideal linear DGEBA oligomer contributes "
        "EXACTLY 2 epoxide equivalents and EXACTLY n hydroxyl equivalents while mass is "
        "additive, both titrations are ratios of number-averages of quantities LINEAR in n, "
        "so both depend on the distribution ONLY through its first moment <n> - there is no "
        "Jensen gap and no dispersity term. Verified numerically on Flory-1936 most-probable, "
        "Poisson, and adversarial bimodal (n=0 with n=8/12/40) mixtures at three commercial "
        "advancement levels: across a dispersity span of up to 6.77x at matched <n>, the "
        "mixture EEW spread is EXACTLY 0.000 g/eq and every deviation from the single-oligomer "
        "formula and from the shipped n_bar inversion is <1e-9. The shipped EEW-band -> n_bar "
        "inversion is therefore a genuine mixture property, not an artifact of assuming a pure "
        "oligomer - a strictly stronger result than the two prior receipts supported. "
        "(3) IDENTITY: eliminating <n> between the two titrations yields a zero-parameter "
        "cross-titration identity between two INDEPENDENT ASTM methods, OHV = A*(1 - E0/EEW) "
        "with A = 56100/M_repeat = 197.2874 mg KOH/g and E0 = M0/2 = 170.2095 g/eq - both "
        "already fixed by the prior receipts, nothing fitted - closing on the pure-oligomer "
        "series to <1e-12 mg KOH/g over n=0..20. (4) H0 REFUTED: the hypothesis that this "
        "identity is robust to realistic DGEBA end-group defects (<=1% relative residual up to "
        "5 mol% alpha-glycol / chlorohydrin ends, both epoxide-consuming) fails - 12 of 16 "
        "defect rows at >=1 mol% breach the 1% bar, worst case 41.02% relative, and the "
        "residual is strictly monotone in defect load while zero-defect rows sit on the "
        "identity to <1e-9 (perfect specificity). The same defects bias the shipped n_bar "
        "inversion upward by up to 30.2% relative. (5) The breach is NOT uniform, and that is "
        "the second finding: relative detector power falls 17.25x from the liquid grade "
        "(<n>=0.13, ideal OHV 19.33 mg KOH/g, 8/8 rows breach, 9.79% residual per mol% glycol) "
        "to the semisolid grade (<n>=2.35, ideal OHV 130.70, only 4/8 breach, 0.57% per mol%), "
        "because the defect hydroxyl rides on an ever larger ideal-backbone hydroxyl baseline. "
        "A single fixed relative acceptance bar is therefore NOT a valid QC rule across the "
        "DGEBA grade range. (6) Specificity 4/4: an ideal Flory resin is correctly NOT flagged "
        "while 20 mol% phenyl glycidyl ether diluent (+15.67%), 10 mol% free bisphenol-A "
        "(+60.68%) and 5 mol% fully hydrolyzed DGEBA diol (+70.54%) are all correctly flagged. "
        "The smallest refuting residual exceeds IUPAC-2021 atomic-weight uncertainty on the "
        "identity constant by 15.1x, so the signal is chemical, not numerical.",
    "gates": diag["gates"],
    "all_gates_passed": diag["all_gates_passed"],
    "rule": diag["rule"],
    "structural_constants": diag["structural_constants"],
    "headline_findings": {
        "polydispersity_invariance": "EXACT - mixture EEW/OHV spread 0.000 g/eq across "
            "dispersity spans up to 6.77x at matched <n>; all deviations <1e-9.",
        "cross_titration_identity": "OHV = 197.2874 * (1 - 170.2095/EEW), zero fitted "
            "parameters, both constants inherited from prior signed receipts.",
        "H0_verdict": g3["verdict"],
        "defect_rows_breaching_1pct_bar": "%d/%d" % (g3["defect_rows_breaching_1pct_bar"],
                                                    g3["defect_rows_tested_at_or_above_1molpct"]),
        "max_residual_relative": g3["max_residual_relative"],
        "max_nbar_inversion_relative_bias": g3["max_nbar_relative_bias"],
        "relative_sensitivity_loss_liquid_to_semisolid_fold": g3["relative_sensitivity_loss_liquid_to_semisolid_fold"],
        "specificity_controls_correct": "%d/%d" % (
            sum(1 for x in g4["specificity_controls"] if x["correct"]),
            len(g4["specificity_controls"])),
    },
    "atomic_weight_uncertainty": diag["atomic_weight_uncertainty"],
    "primary_sources": diag["primary_sources"],
    "maps_to_module_hypothesis": diag["maps_to_module_hypothesis"],
    "rdkit_version": diag["rdkit_version_detected"],
    "two_replay_gate": {"canonical_sha256": sha(canon), "runB_sha256": sha(runB),
                        "byte_identical": canon == runB},
    "input_artifacts": {
        "eew_ahew_benchmark.v1.json_sha256": diag["benchmark_data_sha256"],
        "dgeba_oligomer_eew_series_receipt.v1.json_sha256":
            diag["prior_receipt_sha256"]["dgeba_oligomer_eew_series_receipt.v1.json"],
        "dgeba_oligomer_hydroxyl_value_receipt.v1.json_sha256":
            diag["prior_receipt_sha256"]["dgeba_oligomer_hydroxyl_value_receipt.v1.json"],
        "diagnostic.canonical.json_sha256": sha(canon),
        "compute_dgeba_xtitration.py_sha256": sha(compute),
    },
    "ceiling": "AUDIT_ONLY structural/stoichiometric second-signal. The invariance theorem and "
        "the cross-titration identity are exact consequences of ideal linear DGEBA "
        "stoichiometry and are verified numerically, not fitted; but they are validated "
        "against SYNTHETIC distributions and synthetic defect loadings, NOT against measured "
        "ASTM D1652/D4274 pairs on real resin lots. No such rights-clean paired-titration "
        "dataset is held by the module, so the detector's real-world false-positive rate is "
        "UNMEASURED and the parametric detection floors (0.9-7.9 mol% glycol depending on "
        "grade and on assumed 0.5-2% relative titration precision) rest on ASSUMED precisions "
        "chosen by this audit, NOT on quoted ASTM repeatability statements. This receipt "
        "asserts no exact EEW or OHV for any named commercial grade, no product "
        "qualification, and no cure-state claim. Live runtime stays LOCKED_INTERNAL and the "
        "commercial_product_claim_locked=true lock is unchanged.",
    "promotion_blocked_by": "NOT this audit's science (all 4 gates pass) and NOT key custody. "
        "Promotion requires the human dual-identity Phase-0 ceremony keys this cron does not "
        "hold; the immutable evaluation.v1.dsse.json state-machine lock is unchanged. Manifest "
        "untouched at 66 receipts / 11 modules.",
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "public_key_hex": PUB["public_key_hex"], "trust_anchored": False,
                    "note": "NOT in config/phase0-trust-store.v1.json; audit evidence only"},
}

body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-property.dgeba-polydispersity-cross-titration-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = dict(receipt)
out["dsse_envelope"] = envelope
out["signature"] = base64.standard_b64encode(sig).decode()
outpath = BENCH / "dgeba_polydispersity_cross_titration_receipt.v1.json"
outpath.write_text(json.dumps(out, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"])).verify(sig, pae(ptype, body))
print("SIGNED_OK", outpath)
print("receipt_id", receipt["receipt_id"])
print("sig_verified True")
