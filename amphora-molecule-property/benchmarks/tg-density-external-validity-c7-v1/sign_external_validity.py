#!/usr/bin/env python3
"""DSSE-Ed25519-sign the C7 Tg/density external-validity attack receipt with the
repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f..., NOT trust-anchored).
Promotes nothing; modifies no existing receipt, manifest, census, split, or
lock (66/11 intact)."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["all_gates_passed"] is True, "gates did not all pass"
compute = (BENCH / "compute_external_validity.py").read_bytes()

tg = diag["tg"]
density = diag["density"]

receipt = {
    "schema": "amphora.molecule-property.c7-tg-density-external-validity-receipt.v1",
    "receipt_id": "c7-tg-density-external-validity-" + sha(canon)[:32],
    "study_id": diag["study_id"],
    "campaign_item_id": diag["campaign_item_id"],
    "authority": "AUDIT_ONLY",
    "promotes_nothing": True,
    "modifies_no_live_config": True,
    "module": "amphora-molecule-property",
    "claim_under_attack": {
        "receipt_path": "amphora-molecule-property/evidence/phase0/kpis/openpoly-experimental-tg-ml-baseline-kpi.v1.json",
        "claim_text": "Within-corpus scaffold-safe performance (Tg RF LOSO MAE 51.24 K, density RF MAE 0.0566 g/cm3) transfers to out-of-corpus chemistry.",
    },
    "attack_design": {
        "pre_registered_refute_threshold": "external (or leave-family-out) MAE > 2x the apples-to-apples within-corpus MAE (same features, same RF, same seed) => REFUTED for that property.",
        "tg_method": "TRUE cross-corpus test, both directions. RadonPy PI1070 was checked and confirmed to carry NO Tg field at all (its 141-column raw header has no glass-transition-related column), so it cannot serve as the Tg external partner. The module's OTHER already rights-cleared, already-used Tg corpus is Polyuniverse Epoxy (MD-simulated, feedback/v1/external_data/polyuniverse_epoxy, used previously for the Push #20/#25 physics-Ridge baseline). Direction A: RF trained on OpenPoly-443 (Morgan fp r=2/512bit + log10(MW), seed=0), cold-predicted on a deterministic n=5000 sample of Polyuniverse Epoxy. Direction B (reverse): RF trained on that same Polyuniverse-5000 sample, cold-predicted on OpenPoly-443.",
        "density_method": "OpenPoly and Polyuniverse Epoxy were BOTH checked and confirmed to carry NO density column (verified against both raw CSV headers) -- RadonPy PI1070 is the only rights-cleared polymer-density corpus in this module, so a literal cross-corpus swap is currently impossible with rights-cleared data (this is itself a data-availability finding, filed to the acquisition queue). As the hardest available proxy, this attack uses RadonPy's OWN authentic polymer_class metadata (20 classes, not an invented clustering) for leave-class-out CV: for each of 14 classes with >=8 members, RF is trained on all OTHER classes and cold-predicts the held-out class, pooled across all 14 folds (n=1059), vs an apples-to-apples 5-fold random-split baseline with identical features.",
    },
    "tg_result": {
        "n_openpoly": tg["n_openpoly"],
        "n_polyuniverse_sample": tg["n_polyuniverse_sample"],
        "note_on_n": "Shipped headline receipt states 441/442 polymers inconsistently across its own fields; simple Tg-and-PSMILES-notna filtering on the SAME pinned CSV (sha256 verified below) yields 443. Immaterial to the verdict.",
        "within_openpoly_own_features_mae_K": tg["within_openpoly_kfold_own_features"]["mae"],
        "within_polyuniverse_own_features_mae_K": tg["within_polyuniverse_kfold_own_features"]["mae"],
        "direction_A_train_openpoly_test_polyuniverse_mae_K": tg["direction_A_train_openpoly_test_polyuniverse"]["mae"],
        "direction_A_null_baseline_mae_K": tg["direction_A_train_openpoly_test_polyuniverse"]["null_mae_using_train_median"],
        "direction_A_r2": tg["direction_A_train_openpoly_test_polyuniverse"]["r2"],
        "direction_B_train_polyuniverse_test_openpoly_mae_K": tg["direction_B_train_polyuniverse_test_openpoly"]["mae"],
        "direction_B_null_baseline_mae_K": tg["direction_B_train_polyuniverse_test_openpoly"]["null_mae_using_train_median"],
        "direction_B_r2": tg["direction_B_train_polyuniverse_test_openpoly"]["r2"],
        "degradation_factor_A": tg["degradation_factor_A_vs_own_within_corpus"],
        "degradation_factor_B": tg["degradation_factor_B_vs_own_within_corpus"],
        "train_test_y_distribution_mismatch": {
            "openpoly_Tg_median_K": tg["direction_A_train_openpoly_test_polyuniverse"]["train_y_median"],
            "openpoly_Tg_range_K": tg["direction_A_train_openpoly_test_polyuniverse"]["train_y_range"],
            "polyuniverse_Tg_median": tg["direction_A_train_openpoly_test_polyuniverse"]["test_y_median"],
            "polyuniverse_Tg_range": tg["direction_A_train_openpoly_test_polyuniverse"]["test_y_range"],
        },
        "verdict": "REFUTED",
        "why": "Both directions blow through the 2x threshold by a wide margin (6.66x and 16.60x). In BOTH directions the cross-corpus RF model is actually WORSE than the trivial null (predict-the-training-median) baseline (Direction A: MAE 253.6K vs null 227.9K, R2=-92.9; Direction B: MAE 231.7K vs null 220.6K, R2=-6.8) -- the model is anti-predictive out-of-corpus, not merely degraded. Root cause: Polyuniverse Epoxy's 'Tg' column occupies a wildly different numeric range (median 117.8, max 237.0) than OpenPoly's experimental Tg (median 346.3, max 589.0); a bagged-tree RF cannot extrapolate outside its training-label range, so it is structurally incapable of transferring across this shift regardless of chemistry overlap. This is a stronger and more mechanistically diagnosed refutation than the already-shipped dielectric external-validation finding (9.0x degradation).",
    },
    "density_result": {
        "n_polymers": density["n_polymers"],
        "eligible_classes": density["leave_polymer_class_out"]["eligible_classes"],
        "n_classes_used": len(density["leave_polymer_class_out"]["eligible_classes"]),
        "pooled_leave_class_out_n": density["leave_polymer_class_out"]["n_pooled_test"],
        "within_corpus_own_features_mae_g_per_cm3": density["own_features_within_corpus_5fold"]["mae"],
        "within_corpus_own_features_r2": density["own_features_within_corpus_5fold"]["r2"],
        "leave_class_out_pooled_mae_g_per_cm3": density["leave_polymer_class_out"]["pooled_mae"],
        "leave_class_out_pooled_r2": density["leave_polymer_class_out"]["pooled_r2"],
        "leave_class_out_pooled_null_mae_g_per_cm3": density["leave_polymer_class_out"]["pooled_null_mae_train_median"],
        "per_class_mae": density["leave_polymer_class_out"]["per_class"],
        "degradation_factor": density["degradation_factor_leave_class_out_vs_own_within_corpus"],
        "verdict": "SURVIVED",
        "why": "Leave-class-out pooled MAE 0.1023 g/cm3 vs own-features within-corpus MAE 0.0567 g/cm3 = 1.80x degradation -- real, but under the pre-registered 2x REFUTED bar, and the pooled leave-class-out model still clearly beats the leave-class-out null baseline. This attack was genuinely capable of falsifying (the Tg attack above shows the same pipeline WILL report a >2x degradation when one is actually present); it did not find one for density at the class-family granularity available. This is NOT a full external-corpus test -- see data_availability_note below -- so 'SURVIVED' here means 'survived the hardest currently-executable proxy for out-of-corpus chemistry', not 'proven to transfer to a genuinely independent density corpus'.",
        "data_availability_note": density["data_availability_note"],
    },
    "overall_verdict": "CLAIM_REFUTED",
    "overall_reasoning": "The attacked claim bundles Tg and density transferability into one sentence. Tg transferability is REFUTED outright and catastrophically in both directions. Density transferability survives the hardest available proxy attack but was NOT tested against a genuine second corpus (none exists in rights-cleared data) -- so the compound claim as literally stated ('transfers to out-of-corpus chemistry') is false for at least one of its two named properties, and the applicability domain for Tg must be restated as within-OpenPoly-distribution only.",
    "gates": diag["gates"],
    "all_gates_passed": diag["all_gates_passed"],
    "two_replay_gate": {"canonical_sha256": sha(canon), "runB_sha256": sha(runB), "byte_identical": canon == runB},
    "input_artifacts": {
        "openpoly_csv_sha256": tg["openpoly_csv_sha256"],
        "polyuniverse_epoxy_csv_sha256": tg["polyuniverse_csv_sha256"],
        "radonpy_pi1070_csv_sha256": density["radonpy_csv_sha256"],
        "diagnostic.canonical.json_sha256": sha(canon),
        "compute_external_validity.py_sha256": sha(compute),
    },
    "rights_check": "OpenPoly (DERIVATIVE_ALLOWED), Polyuniverse Epoxy (unresolved_rights_quarantined=false per its own prior shipped KPI claim_locks, already extensively used e.g. Push #20/#25), RadonPy PI1070 (already extensively used e.g. Push #33-36) -- all three previously rights-cleared and already load-bearing elsewhere in this module. No quarantined/CONTEXT_ONLY/polyverse_thermoset_mechanics source touched.",
    "ceiling": "AUDIT_ONLY red-team/external-validity diagnostic. Documents that the shipped OpenPoly Tg RF baseline's applicability domain is within-OpenPoly-experimental-distribution ONLY and must not be presented as generalizing to out-of-corpus polymer chemistry. Does not itself alter the shipped KPI receipt, module honesty ceiling, manifest, or authority ceiling.",
    "promotion_blocked_by": "NOT this audit's science (all gates pass, two-replay byte-stable) and NOT key custody. Promotion of any downstream honesty-ceiling change requires the human dual-identity Phase-0 ceremony keys this cron does not hold. Manifest untouched at 66/11.",
    "recommended_followups": [
        "Update openpoly-experimental-tg-ml-baseline-kpi.v1.json's claim_locks / capability text (human-owned edit) to state the applicability domain is within-OpenPoly-distribution only, citing this receipt.",
        "File a data-acquisition ask for an independent experimental (not MD-simulated) polymer Tg corpus and an independent polymer density corpus disjoint from RadonPy, for a true second-corpus density test in a future fire.",
    ],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"], "public_key_hex": PUB["public_key_hex"],
                    "trust_anchored": False, "note": "NOT in config/phase0-trust-store.v1.json; audit evidence only"},
}

body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-property.c7-tg-density-external-validity-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = dict(receipt)
out["dsse_envelope"] = envelope
out["signature"] = base64.standard_b64encode(sig).decode()
outpath = BENCH / "c7_tg_density_external_validity_receipt.v1.json"
outpath.write_text(json.dumps(out, indent=2, sort_keys=True))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"])).verify(sig, pae(ptype, body))
print("SIGNED_OK", outpath)
print("receipt_id", receipt["receipt_id"])
print("sig_verified True")
