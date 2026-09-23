#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-ingredient-library hansen-block-sphere-coherence-v1
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/; does
NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest (66 receipts / 11
modules), module-manifest.json, any locked dataset, or a signed Phase-0 KPI.
Derived key_id cross-checked vs pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-ingredient-library/evidence/audit/hansen-block-sphere-coherence-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b): return hashlib.sha256(b).hexdigest()


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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
oracle_sha = sha((BENCH / "run_hansen_block.py").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

sph = diag["G2_G3_sphere"]
g1 = diag["G1_hvk_coherence"]

body_obj = {
    "schema": "amphora.ingredient-library.hansen-block-sphere-coherence-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": diag["run_type"],
    "module": "amphora-ingredient-library",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False,
    "modifies_manifest": False, "modifies_module_manifest": False,
    "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
    "purpose": diag["purpose"],
    "hypothesis": diag["hypothesis"],
    "non_circularity": diag["non_circularity"],
    "theory_reference": diag["theory_reference"],
    "prereg_gate": diag["prereg_gate"],
    "results": {
        "verdict": diag["verdict"],
        "G0_hansen_block_provenance": {
            "n_hansen_facts": diag["G0_hansen_block_provenance"]["n_hansen_facts"],
            "n_load_bearing": diag["G0_hansen_block_provenance"]["n_load_bearing"],
            "n_single_sourced": diag["G0_hansen_block_provenance"]["n_single_sourced"],
            "n_with_single_source_waiver":
                diag["G0_hansen_block_provenance"]["n_with_single_source_waiver"],
            "dgeba_sphere_issn_0008_6223_is_journal_carbon":
                diag["G0_hansen_block_provenance"]["dgeba_sphere_issn_0008_6223_is_journal_carbon"],
            "finding": diag["G0_hansen_block_provenance"]["finding"],
        },
        "G1_hvk_coherence": {
            "gate_passed": g1["gate_passed"],
            "kpi_core": g1["kpi_core_excl_declared_aromatic_boundary"],
            "kpi_all": g1["kpi_all_incl_boundary"],
            "per_solvent": [{k: s[k] for k in (
                "fact_key", "family", "smiles", "declared_boundary",
                "rdkit_molar_mass_g_per_mol", "shipped_density_g_per_mL",
                "molar_volume_cm3_per_mol_from_shipped_rho", "group_counts",
                "shipped_hsp_MPa0.5", "hvk_predicted_hsp_MPa0.5",
                "residual_MPa0.5", "hansen_Ra_pred_vs_shipped_MPa0.5",
                "Ra_shift_from_rho_rounding_pm0.005_MPa0.5")} for s in g1["per_solvent"]],
        },
        "G2_sphere_coherence": {
            "gate_passed": sph["G2_coherence_gate_passed"],
            "n_shipped_solvents": sph["n_shipped_solvents"],
            "n_admitted": sph["n_shipped_solvents_admitted"],
            "shipped_solvents": sph["shipped_solvents"],
        },
        "G3_sphere_discrimination": {
            "gate_passed": sph["G3_discrimination_gate_passed"],
            "n_known_non_solvents": sph["n_known_non_solvents"],
            "known_non_solvents_falsely_admitted": sph["known_non_solvents_falsely_admitted"],
            "known_non_solvents": sph["known_non_solvents"],
            "radius_calibration_analysis": sph["radius_calibration_analysis"],
        },
        "G4_fail_closed_mutation_demo": diag["G4_fail_closed_mutation_demo"],
        "G5_shipped_sphere_permissiveness": diag["G5_shipped_sphere_permissiveness"],
    },
    "refuted_facts": [{
        "fact_key": "binder.dgeba.hsp_radius",
        "shipped_value_MPa0.5": diag["inputs"]["shipped_dgeba_sphere_radius_MPa0.5"],
        "refutation": ("admits cyclohexane, a known DGEBA non-solvent, when used as a "
                       "solvent-admission threshold"),
        "shipped_load_bearing": False,
        "admissible_replacement_interval_MPa0.5":
            sph["radius_calibration_analysis"]["exact_separating_R0_interval_MPa0.5"],
        "downstream_impact_today": ("none: the fact is load_bearing=false and no "
                                    "consumer currently gates on it"),
    }],
    "corroborated_facts": [
        "solvent.mak.hsp", "solvent.mibk.hsp", "solvent.n_butanol.hsp",
        "solvent.pm.hsp", "solvent.pma.hsp", "solvent.xylene.hsp",
        "binder.dgeba.hsp",
    ],
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "facts_json_path": diag["inputs"]["facts_json_path"],
        "facts_json_sha256": diag["inputs"]["facts_json_sha256"],
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
        "hvk_group_table_source": ("byte-identical to amphora-redteam-audit/benchmarks/"
                                   "hvk-hansen-vector-ccby-v1 (already-signed portfolio audit)"),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.ingredient-library-hansen-block-sphere-coherence-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "hansen-block-sphere-coherence-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
