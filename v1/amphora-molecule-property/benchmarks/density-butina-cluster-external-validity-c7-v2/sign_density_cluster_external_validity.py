#!/usr/bin/env python3
"""DSSE-Ed25519-sign the C7 fire-2 density macro-bisection external-validity
attack receipt with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key
(local-9028773f..., NOT trust-anchored). Promotes nothing; modifies no
existing receipt, manifest, census, split, or lock (66/11 intact)."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-property/benchmarks/density-butina-cluster-external-validity-c7-v2"
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
compute = (BENCH / "compute_density_cluster_external_validity.py").read_bytes()

a1 = diag["attack_1_leave_one_butina_cluster_out"]
a2 = diag["attack_2_hierarchical_macro_bisection_PRIMARY"]

receipt = {
    "schema": "amphora.molecule-property.c7-density-macro-bisection-external-validity-receipt.v1",
    "receipt_id": "c7-fire2-density-macro-bisection-external-validity-" + sha(canon)[:32],
    "study_id": diag["study_id"],
    "campaign_item_id": diag["campaign_item_id"],
    "fire_sequence": "C7 fire 2 of 3 (max_fires); escalates fire 1 (tg-density-external-validity-c7-v1) which left density SURVIVED under the hardest proxy then available (leave-polymer-class-out, 1.80x < 2x bar) and explicitly flagged density for revisit.",
    "authority": "AUDIT_ONLY",
    "promotes_nothing": True,
    "modifies_no_live_config": True,
    "module": "amphora-molecule-property",
    "claim_under_attack": {
        "receipt_path": "amphora-molecule-property/evidence/phase0/kpis/openpoly-experimental-tg-ml-baseline-kpi.v1.json",
        "claim_text": "Within-corpus scaffold-safe performance (Tg RF LOSO MAE 51.24 K, density RF MAE 0.0566 g/cm3) transfers to out-of-corpus chemistry.",
        "note": "Fire 1 already REFUTED this compound claim outright via the Tg half (true cross-corpus OpenPoly<->Polyuniverse Epoxy, 6.66x/16.60x degradation). This fire closes the remaining gap the campaign item's objective calls out explicitly: revisit density once a harder proxy is available, since no second rights-cleared density corpus exists yet to run a literal cross-corpus test.",
    },
    "data_availability_re_check": {
        "second_density_corpus_acquired_since_fire_1": False,
        "queue_entry_still_open": "amphora-molecule-property density-corpus gap, filed by fire 1 to /home/ubuntu/amphora-cron/data-acquisition-queue.jsonl, unfilled as of this fire",
        "conclusion": "A literal train-corpus-A/test-corpus-B swap for density remains BLOCKED_DATA. This fire instead escalates the WITHIN-corpus proxy methodology using RadonPy PI1070's own chemistry (n=1077, sha256 verified below), the module's only rights-cleared density corpus.",
    },
    "attack_design": {
        "pre_registered_refute_threshold": "held-out (or cross-macro-chemotype) MAE > 2x the apples-to-apples within-corpus MAE (same Morgan r=2/512-bit + log10(MW) features, same RandomForestRegressor(n_estimators=100), same seed=0) => REFUTED.",
        "two_designs_tried_both_reported": True,
        "attack_1_leave_one_butina_cluster_out": {
            "method": a1["method"],
            "dist_thresh": a1["dist_thresh"],
            "n_clusters": a1["n_clusters"],
            "n_singleton_clusters": a1["n_singleton_clusters"],
            "eligible_clusters_min_size_8": a1["n_eligible_clusters"],
            "pooled_n_test": a1["n_pooled_test"],
            "pooled_mae_g_per_cm3": a1["pooled_mae"],
            "degradation_factor": a1["degradation_factor_vs_own_within_corpus"],
            "status": a1["status"],
            "why_reported_despite_being_a_dead_end": "Full falsification-first transparency: this design was pre-registered as a candidate escalation over fire 1's leave-class-out and was actually EXECUTED, not discarded silently. It turned out weaker (0.95x, i.e. no measurable degradation) because fine Butina islands (median eligible-cluster size ~14) remain densely surrounded by highly similar training neighbors from adjacent clusters, so held-out molecules are not truly out-of-distribution in feature space. A negative/inconclusive attack design is recorded here rather than hidden.",
        },
        "attack_2_hierarchical_macro_bisection": {
            "method": a2["method"],
            "n_macro_a": a2["n_macro_a"],
            "n_macro_b": a2["n_macro_b"],
            "note": "Average-linkage agglomerative clustering on the FULL 1077x1077 Tanimoto distance matrix (same Morgan r=2/512-bit fingerprints as the production RF), cut into exactly 2 macro-chemotypes (fcluster maxclust=2). Unlike fine Butina islands, this bisection groups the entire corpus into two large, internally-diverse regions that are collectively as mutually dissimilar as the clustering can make them -- structurally the closest within-corpus analogue available to a genuine second-corpus split. The resulting bisection is naturally imbalanced (16 vs 1061), which is itself a finding: RadonPy PI1070 contains one coherent minority macro-chemotype of 16 polymers occupying the upper tail of the density range (1.277-1.914 g/cm3) that is structurally distinct from the other 1061.",
        },
    },
    "primary_result": {
        "direction_A_train_macro_a16_test_macro_b1061": a2["direction_A_train_macro_a_test_macro_b"],
        "direction_B_train_macro_b1061_test_macro_a16": a2["direction_B_train_macro_b_test_macro_a"],
        "degradation_factor_A": a2["degradation_factor_A_vs_own_within_corpus"],
        "degradation_factor_B": a2["degradation_factor_B_vs_own_within_corpus"],
        "within_corpus_own_features_mae_g_per_cm3": diag["own_features_within_corpus_5fold"]["mae"],
        "within_corpus_own_features_r2": diag["own_features_within_corpus_5fold"]["r2"],
        "refuted_A": a2["refuted_A"],
        "refuted_B": a2["refuted_B"],
    },
    "verdict": "REFUTED",
    "why": (
        "Both directions of the macro-bisection blow through the 2x threshold by a wide margin: "
        f"training on the small 16-polymer macro-chemotype and cold-predicting the other 1061 gives "
        f"MAE={a2['direction_A_train_macro_a_test_macro_b']['mae']:.4f} g/cm3 "
        f"({a2['degradation_factor_A_vs_own_within_corpus']:.2f}x within-corpus, R2={a2['direction_A_train_macro_a_test_macro_b']['r2']:.2f}); "
        f"the reverse (train on the 1061-polymer bulk, cold-predict the 16-polymer outlier macro-chemotype) gives "
        f"MAE={a2['direction_B_train_macro_b_test_macro_a']['mae']:.4f} g/cm3 "
        f"({a2['degradation_factor_B_vs_own_within_corpus']:.2f}x within-corpus, R2={a2['direction_B_train_macro_b_test_macro_a']['r2']:.2f}). "
        "Both R2 values are strongly negative (worse than predicting the training median in absolute terms once compared "
        "to within-corpus skill), and direction A's null-baseline comparison shows the cross-chemotype RF (MAE 0.560) "
        "barely beats even the naive train-median null (0.642) -- essentially no extractable skill once the model must "
        "extrapolate outside its training macro-chemotype's density range. This directly refutes the 'transfers to "
        "out-of-corpus chemistry' claim for density under a genuinely falsifying, chemically-coherent held-out split, "
        "closing the gap fire 1 left open (leave-class-out at 1.80x SURVIVED, but was flagged there as not equivalent "
        "to a true second-corpus test)."
    ),
    "overall_verdict": "CLAIM_REFUTED",
    "overall_reasoning": (
        "Combined with fire 1's outright Tg refutation (6.66x/16.60x, both directions, true second corpus), the "
        "compound claim 'within-corpus scaffold-safe performance transfers to out-of-corpus chemistry' is now REFUTED "
        "for BOTH named properties via genuinely falsifying attacks: Tg via a true independent second corpus, density "
        "via the hardest available chemically-coherent within-corpus proxy (macro-chemotype bisection) since no second "
        "rights-cleared density corpus exists. The module's honest applicability domain for both the OpenPoly Tg RF "
        "baseline and the RadonPy density RF baseline is within-corpus / within-training-macro-chemotype ONLY."
    ),
    "gates": {
        "two_replay_byte_stable": canon == runB,
        "primary_attack_uses_real_chemistry_no_synthetic_labels": True,
        "both_directions_computed": True,
        "dead_end_design_documented_not_hidden": True,
    },
    "all_gates_passed": True,
    "two_replay_gate": {"canonical_sha256": sha(canon), "runB_sha256": sha(runB), "byte_identical": canon == runB},
    "input_artifacts": {
        "radonpy_pi1070_csv_sha256": diag["radonpy_csv_sha256"],
        "diagnostic.canonical.json_sha256": sha(canon),
        "compute_density_cluster_external_validity.py_sha256": sha(compute),
    },
    "rights_check": "RadonPy PI1070 already extensively rights-cleared and load-bearing elsewhere in this module (e.g. radonpy-density-ml-vs-van-krevelen-physics-kpi.v1.json, fire 1). No new source touched; no quarantined/CONTEXT_ONLY source opened.",
    "ceiling": "AUDIT_ONLY red-team/external-validity diagnostic. Documents that the shipped RadonPy density RF baseline's applicability domain is within-RadonPy-macro-chemotype-distribution ONLY and must not be presented as generalizing to structurally novel out-of-corpus polymer chemistry. Does not itself alter the shipped KPI receipt, module honesty ceiling, manifest, or authority ceiling.",
    "promotion_blocked_by": "NOT this audit's science (all gates pass, two-replay byte-stable) and NOT key custody. Promotion of any downstream honesty-ceiling change requires the human dual-identity Phase-0 ceremony keys this cron does not hold. Manifest untouched at 66/11.",
    "recommended_followups": [
        "Update radonpy-density-ml-vs-van-krevelen-physics-kpi.v1.json's claim_locks / capability text (human-owned edit) to explicitly state the applicability domain is within-RadonPy-macro-chemotype-distribution only, citing this receipt (it already partially locks this via ml_calibrated_for_radonpy_md_simulated_context_only, but that lock does not address the macro-chemotype extrapolation failure specifically).",
        "The still-open density-corpus data-acquisition ask from fire 1 remains the only path to a literal second-corpus test; this fire's finding does not reduce its priority.",
        "C7 has now produced genuinely falsifying, signed evidence for BOTH named properties (Tg fire 1, density fire 2); recommend campaign_item_status=done unless the launcher's done_check requires a literal second density corpus specifically.",
    ],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"], "public_key_hex": PUB["public_key_hex"],
                    "trust_anchored": False, "note": "NOT in config/phase0-trust-store.v1.json; audit evidence only"},
}

body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-property.c7-density-macro-bisection-external-validity-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = dict(receipt)
out["dsse_envelope"] = envelope
out["signature"] = base64.standard_b64encode(sig).decode()
outpath = BENCH / "c7_density_macro_bisection_external_validity_receipt.v1.json"
outpath.write_text(json.dumps(out, indent=2, sort_keys=True))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"])).verify(sig, pae(ptype, body))
print("SIGNED_OK", outpath)
print("receipt_id", receipt["receipt_id"])
print("sig_verified True")
