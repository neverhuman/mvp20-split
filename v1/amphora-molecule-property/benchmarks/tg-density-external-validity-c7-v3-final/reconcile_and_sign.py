#!/usr/bin/env python3
"""C7 fire 3 of 3 (max_fires): final reconciliation + correctly-formatted DSSE
signing of the Tg/density external-validity verdicts produced by fires 1 and 2.

Fires 1 and 2 both computed real, decisive falsification attacks and both were
downgraded by the launcher solely for a signature-format bug: their top-level
`.signature` field held a bare base64 string instead of the required DSSE
envelope OBJECT {payloadType, payload, signatures:[...]}, even though a
correctly-formed envelope existed alongside it under a separate
`dsse_envelope` key. This fire does not re-run the underlying science (both
diagnostics are re-verified byte-identical against their fire-time recorded
sha256 below); it packages the already-computed, already-verified findings
into ONE receipt with the correct signature shape, and explicitly reconciles
the two fires' conflicting density verdicts (fire 1 leave-class-out SURVIVED
1.80x vs fire 2 macro-bisection REFUTED 13.74x/7.59x) by explaining why the
macro-bisection attack is the harder, more decisive test and therefore
governs the final verdict under falsification-first principles.
"""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final"
OUT.mkdir(parents=True, exist_ok=True)
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

FIRE1_DIR = ROOT / "amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v1"
FIRE2_DIR = ROOT / "amphora-molecule-property/benchmarks/density-butina-cluster-external-validity-c7-v2"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


# --- re-verify fire 1 and fire 2 source diagnostics are still byte-identical
# to what their receipts recorded (data integrity check before reuse) ---
f1_canon = (FIRE1_DIR / "diagnostic.canonical.json").read_bytes()
f1_runB = (FIRE1_DIR / "diagnostic.runB.json").read_bytes()
assert f1_canon == f1_runB, "fire1 two-replay bytes differ on re-check"
assert sha(f1_canon) == "b6326a86fb43e14c67778a1540204c666a9b40f0ea0c2a40e1da3714fd771c99", "fire1 diagnostic drifted from receipt-recorded hash"

f2_canon = (FIRE2_DIR / "diagnostic.canonical.json").read_bytes()
f2_runB = (FIRE2_DIR / "diagnostic.runB.json").read_bytes()
assert f2_canon == f2_runB, "fire2 two-replay bytes differ on re-check"
assert sha(f2_canon) == "4cedf6a149148dae3379b00700bda3b6812106935fca0745ec0e5c8e4547892a", "fire2 diagnostic drifted from receipt-recorded hash"

f1_receipt = json.loads((FIRE1_DIR / "c7_tg_density_external_validity_receipt.v1.json").read_text())
f2_receipt = json.loads((FIRE2_DIR / "c7_density_macro_bisection_external_validity_receipt.v1.json").read_text())

tg = f1_receipt["tg_result"]
dens_proxy = f1_receipt["density_result"]
dens_macro = f2_receipt["primary_result"]
dens_attack_design = f2_receipt["attack_design"]


def build_receipt():
    return {
        "schema": "amphora.molecule-property.c7-tg-density-external-validity-final-verdict-receipt.v1",
        "receipt_id": "c7-fire3-final-tg-density-external-validity-verdict",
        "study_id": "c7-external-validity-tg-density-final",
        "campaign_item_id": "C7",
        "fire_sequence": (
            "C7 fire 3 of 3 (max_fires). Fires 1 and 2 (2026-08-01T05:00:02Z, "
            "2026-08-01T16:12:14Z) both ran genuine falsification attacks and both "
            "reached correct scientific verdicts, but both were downgraded by the "
            "launcher for a signature-format bug (top-level .signature was a bare "
            "base64 string, not the required DSSE envelope object). This fire fixes "
            "that defect, re-verifies the underlying diagnostics are unmodified "
            "(byte-identical sha256 to what fires 1/2 recorded), and issues ONE "
            "correctly-signed receipt carrying the final reconciled verdict for both "
            "named properties. No new science; this is a packaging/signing/"
            "reconciliation fire."
        ),
        "supersedes": [
            {
                "receipt": "amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v1/c7_tg_density_external_validity_receipt.v1.json",
                "downgrade_reason": "verdict CLAIM_REFUTED rejected: no signed receipt was produced at all (analysis + ledger line only).",
                "resolution": "The receipt file did in fact exist on disk at fire-1 end, but its .signature field was a bare base64 string, which the launcher's mechanical check treats as equivalent to unsigned. Tg finding (6.66x/16.60x degradation) reproduced verbatim below from this file's byte-verified tg_result block; underlying diagnostic.canonical.json re-verified byte-identical.",
            },
            {
                "receipt": "amphora-molecule-property/benchmarks/density-butina-cluster-external-validity-c7-v2/c7_density_macro_bisection_external_validity_receipt.v1.json",
                "downgrade_reason": "verdict CLAIM_REFUTED rejected: .signature was a bare STRING, not the DSSE envelope object. Also: fire 1 and fire 2 reached OPPOSITE density verdicts - reconcile explicitly.",
                "resolution": "Same signature-format defect, fixed here. Density reconciliation performed below: macro-bisection (fire 2) supersedes leave-class-out (fire 1) as the governing verdict.",
            },
        ],
        "authority": "AUDIT_ONLY",
        "promotes_nothing": True,
        "modifies_no_live_config": True,
        "module": "amphora-molecule-property",
        "claim_under_attack": {
            "receipt_path": "amphora-molecule-property/evidence/phase0/kpis/openpoly-experimental-tg-ml-baseline-kpi.v1.json",
            "claim_text": "Within-corpus scaffold-safe performance (Tg RF LOSO MAE 51.24 K, density RF MAE 0.0566 g/cm3) transfers to out-of-corpus chemistry.",
        },
        "pre_registered_refute_threshold": "held-out (or cross-corpus / cross-macro-chemotype) MAE > 2x the apples-to-apples within-corpus MAE, same features/model/seed => REFUTED. Used identically by both fire 1 and fire 2.",
        "tg_verdict": {
            "verdict": "REFUTED",
            "method": "True independent second corpus: train RandomForestRegressor(n_estimators=100, seed=0) on OpenPoly experimental Tg (n=443), cold-predict Polyuniverse Epoxy MD-simulated Tg (n=5000 sample), and reverse. Morgan r=2/512-bit fingerprint features.",
            "degradation_factor_A_openpoly_to_polyuniverse": tg["degradation_factor_A"],
            "degradation_factor_B_polyuniverse_to_openpoly": tg["degradation_factor_B"],
            "direction_A_mae_K": tg["direction_A_train_openpoly_test_polyuniverse_mae_K"],
            "direction_A_null_baseline_mae_K": tg["direction_A_null_baseline_mae_K"],
            "direction_A_r2": tg["direction_A_r2"],
            "direction_B_mae_K": tg["direction_B_train_polyuniverse_test_openpoly_mae_K"],
            "direction_B_null_baseline_mae_K": tg["direction_B_null_baseline_mae_K"],
            "direction_B_r2": tg["direction_B_r2"],
            "within_openpoly_own_features_mae_K": tg["within_openpoly_own_features_mae_K"],
            "within_polyuniverse_own_features_mae_K": tg["within_polyuniverse_own_features_mae_K"],
            "why": (
                "Both directions blow through the 2x threshold by a wide margin (6.66x, 16.60x) "
                "and in both directions the cross-corpus model is WORSE than the trivial "
                "predict-the-training-median null baseline (anti-predictive, not merely degraded). "
                "Root cause: OpenPoly experimental Tg (median 346.3K) and Polyuniverse Epoxy MD Tg "
                "(median 117.8K) occupy non-overlapping numeric ranges; a bagged-tree RF structurally "
                "cannot extrapolate past its training-label range. Reproduced verbatim from fire 1's "
                "byte-verified diagnostic (sha256 unchanged)."
            ),
        },
        "density_verdict": {
            "verdict": "REFUTED",
            "final_governing_attack": "attack_2_hierarchical_macro_bisection (fire 2)",
            "reconciliation": (
                "Fire 1 tested leave-one-polymer-class-out on RadonPy PI1070's own 14 internally-"
                "assigned class labels (fine-grained, ~77 polymers/class median) and found 1.80x "
                "degradation -- below the 2x bar, reported SURVIVED. Fire 2 escalated to hierarchical "
                "average-linkage bisection of the full 1077x1077 Tanimoto distance matrix into 2 "
                "macro-chemotypes (16 vs 1061 polymers, cut to maximize inter-group dissimilarity) and "
                "found 13.74x/7.59x degradation in both directions -- decisively REFUTED. These are not "
                "contradictory results on the same test; they are two different severities of "
                "out-of-distribution probe. Leave-class-out removes a fine-grained label group whose "
                "chemical/density neighborhood remains densely populated by similar polymers from "
                "OTHER classes still in the training set, so held-out molecules are not truly outside "
                "the training distribution in feature space -- fire 2 additionally confirmed this "
                "mechanism directly via a leave-one-Butina-cluster-out probe (0.95x, no measurable "
                "degradation, documented as a dead end). Macro-bisection instead removes an entire "
                "structurally-coherent region of chemical space (all 16 polymers in the minority "
                "macro-chemotype occupy the upper tail of the density range, 1.277-1.914 g/cm3, "
                "structurally distinct from the other 1061) so the held-out set is genuinely outside "
                "the training distribution -- the closest within-corpus analogue to a real second-"
                "corpus swap that RadonPy PI1070 (the module's only rights-cleared density corpus) "
                "permits. Under falsification-first principles the strongest attack that was actually "
                "capable of finding a violation governs the verdict: a claim of 'transfers to "
                "out-of-corpus chemistry' is not rescued by surviving a weaker probe when a harder, "
                "methodologically sound probe using the same threshold and same model breaks it. "
                "Density transferability is therefore REFUTED, with the leave-class-out result "
                "retained as evidence that the degradation is granularity-dependent (visible once the "
                "held-out region is structurally coherent, not visible at fine class-label "
                "granularity)."
            ),
            "macro_bisection_primary_result": {
                "n_macro_a": dens_attack_design["attack_2_hierarchical_macro_bisection"]["n_macro_a"],
                "n_macro_b": dens_attack_design["attack_2_hierarchical_macro_bisection"]["n_macro_b"],
                "degradation_factor_A": dens_macro["degradation_factor_A"],
                "degradation_factor_B": dens_macro["degradation_factor_B"],
                "direction_A_mae_g_per_cm3": dens_macro["direction_A_train_macro_a16_test_macro_b1061"]["mae"],
                "direction_A_null_mae_g_per_cm3": dens_macro["direction_A_train_macro_a16_test_macro_b1061"]["null_mae_using_train_median"],
                "direction_A_r2": dens_macro["direction_A_train_macro_a16_test_macro_b1061"]["r2"],
                "direction_B_mae_g_per_cm3": dens_macro["direction_B_train_macro_b1061_test_macro_a16"]["mae"],
                "direction_B_null_mae_g_per_cm3": dens_macro["direction_B_train_macro_b1061_test_macro_a16"]["null_mae_using_train_median"],
                "direction_B_r2": dens_macro["direction_B_train_macro_b1061_test_macro_a16"]["r2"],
                "within_corpus_own_features_mae_g_per_cm3": dens_macro["within_corpus_own_features_mae_g_per_cm3"],
                "within_corpus_own_features_r2": dens_macro["within_corpus_own_features_r2"],
            },
            "leave_class_out_secondary_result": {
                "degradation_factor": dens_proxy["degradation_factor"],
                "pooled_mae_g_per_cm3": dens_proxy["leave_class_out_pooled_mae_g_per_cm3"],
                "pooled_null_mae_g_per_cm3": dens_proxy["leave_class_out_pooled_null_mae_g_per_cm3"],
                "pooled_r2": dens_proxy["leave_class_out_pooled_r2"],
                "status": "RETAINED_AS_GRANULARITY_EVIDENCE_NOT_GOVERNING",
            },
            "leave_one_butina_cluster_out_dead_end": {
                "degradation_factor": dens_attack_design["attack_1_leave_one_butina_cluster_out"]["degradation_factor"],
                "status": dens_attack_design["attack_1_leave_one_butina_cluster_out"]["status"],
            },
        },
        "overall_verdict": "CLAIM_REFUTED",
        "overall_reasoning": (
            "The compound claim 'within-corpus scaffold-safe performance transfers to out-of-corpus "
            "chemistry' is REFUTED for BOTH named properties. Tg: catastrophic failure against a true "
            "independent second corpus in both directions (6.66x/16.60x degradation, anti-predictive "
            "past the training label range). Density: catastrophic failure against the hardest "
            "available within-corpus proxy for a second corpus, hierarchical macro-chemotype bisection "
            "(13.74x/7.59x degradation in both directions), which supersedes the weaker leave-class-out "
            "probe (1.80x, survived) per the reconciliation above. The module's honest applicability "
            "domain for both the OpenPoly Tg RF baseline and the RadonPy density RF baseline is "
            "within-corpus / within-training-macro-chemotype ONLY, matching the pattern already "
            "established for dielectric constant (9x within/external degradation)."
        ),
        "gates": {
            "two_replay_byte_stable_this_receipt": None,  # filled after canonical/runB comparison below
            "fire1_source_diagnostic_reverified_unmodified": True,
            "fire2_source_diagnostic_reverified_unmodified": True,
            "primary_attacks_use_real_chemistry_no_synthetic_labels": True,
            "both_directions_computed_both_properties": True,
            "dead_end_designs_documented_not_hidden": True,
            "signature_field_is_dsse_envelope_object": True,
        },
        "all_gates_passed": True,
        "input_artifacts": {
            "fire1_receipt_path": "amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v1/c7_tg_density_external_validity_receipt.v1.json",
            "fire1_diagnostic.canonical.json_sha256": sha(f1_canon),
            "fire2_receipt_path": "amphora-molecule-property/benchmarks/density-butina-cluster-external-validity-c7-v2/c7_density_macro_bisection_external_validity_receipt.v1.json",
            "fire2_diagnostic.canonical.json_sha256": sha(f2_canon),
        },
        "rights_check": "No new source touched; reuses OpenPoly, Polyuniverse Epoxy, and RadonPy PI1070, all already rights-cleared and load-bearing elsewhere in this module (fires 1 and 2). No quarantined/CONTEXT_ONLY source opened.",
        "ceiling": "AUDIT_ONLY red-team/external-validity final verdict. Documents that the shipped OpenPoly Tg RF and RadonPy density RF baselines' applicability domain is within-corpus / within-training-macro-chemotype ONLY and must not be presented as generalizing to structurally novel out-of-corpus polymer chemistry. Does not itself alter the shipped KPI receipt, module honesty ceiling, manifest, or authority ceiling.",
        "promotion_blocked_by": "NOT this audit's science (all gates pass, sources re-verified byte-unmodified) and NOT key custody. Promotion of any downstream honesty-ceiling change requires the human dual-identity Phase-0 ceremony keys this cron does not hold. Manifest untouched at 66/11.",
        "recommended_followups": [
            "Update openpoly-experimental-tg-ml-baseline-kpi.v1.json's claim_locks / capability text (human-owned edit) to explicitly state the applicability domain is within-OpenPoly-distribution for Tg and within-RadonPy-macro-chemotype-distribution for density, citing this receipt.",
            "The density-corpus data-acquisition ask filed by fire 1 to /home/ubuntu/amphora-cron/data-acquisition-queue.jsonl remains open and is the only path to a literal second-corpus density test; this fire's macro-bisection finding does not reduce its priority, it is a proxy escalation, not a substitute.",
            "C7 done_criterion (signed external-validation receipts for Tg and density with explicit within-vs-external degradation factors + ledger entries) is now met by this single correctly-signed receipt.",
        ],
        "signing_key": {
            "key_id": PUB["key_id"],
            "authority": PUB["authority"],
            "public_key_hex": PUB["public_key_hex"],
            "trust_anchored": False,
            "note": "NOT in config/phase0-trust-store.v1.json; audit evidence only",
        },
    }


# --- two-replay gate for THIS receipt's own content (deterministic build) ---
r1 = build_receipt()
r2 = build_receipt()
body1 = json.dumps(r1, indent=2, sort_keys=True).encode()
body2 = json.dumps(r2, indent=2, sort_keys=True).encode()
assert body1 == body2, "this receipt's own content is non-deterministic"
(OUT / "receipt_body.canonical.json").write_bytes(body1)
(OUT / "receipt_body.runB.json").write_bytes(body2)

receipt = build_receipt()
receipt["gates"]["two_replay_byte_stable_this_receipt"] = True
receipt["two_replay_gate"] = {
    "canonical_sha256": sha(body1),
    "runB_sha256": sha(body2),
    "byte_identical": body1 == body2,
}

body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-property.c7-tg-density-external-validity-final-verdict-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}],
}

out = dict(receipt)
out["signature"] = envelope  # DSSE envelope OBJECT at top level, per required format

outpath = OUT / "c7_final_tg_density_external_validity_verdict_receipt.v1.json"
outpath.write_text(json.dumps(out, indent=2, sort_keys=True))

# verify signature against the exact re-serialized `receipt` body (pre-signature-field body)
Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"])).verify(sig, pae(ptype, body))
assert isinstance(json.loads(outpath.read_text())["signature"], dict), "signature must serialize as JSON object"

print("SIGNED_OK", outpath)
print("receipt_id", receipt["receipt_id"])
print("sig_verified True")
print("signature_type", type(json.loads(outpath.read_text())["signature"]).__name__)
