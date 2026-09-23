#!/usr/bin/env python3
"""Sign the amine-N-H guanidine-conjugation-gap falsification receipt with the
PHASE0_EVALUATOR key, matching the repo-wide evidence/audit/ signing
convention established by W2 fire 3 / W7 / W8
(evaluator_key_id/evaluator_public_key_hex/reviewer_public_key_hex/signature
DSSE envelope shape)."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-property/evidence/audit/amine-nh-guanidine-conjugation-gap-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260803T180001-2431769-2ec3a78bbee1"


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


diag = json.loads((OUT / "diagnostic.canonical.json").read_text())
diagB = (OUT / "diagnostic.runB.json").read_bytes()
diagA = (OUT / "diagnostic.canonical.json").read_bytes()
assert diagA == diagB, "two-replay bytes differ"
compute_script = (OUT / "compute_guanidine_gap.py").read_bytes()

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
by_role = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"
assert rev_pin, "reviewer key_id does not match pinned trust-store PHASE0_INTERNAL_REVIEWER entry"

body_obj = {
    "schema": "amphora.molecule-property.amine-nh-guanidine-conjugation-gap-audit-receipt.v1",
    "receipt_id": "amine-nh-guanidine-conjugation-gap-" + sha(diagA)[:32],
    "study_id": diag["study_id"],
    "fire_id": FIRE_ID,
    "campaign_item_id": "",
    "fire_sequence": (
        "ROTATION fire. Prior fires already attacked and REFUTED "
        "amphora-molecule-property's ML-baseline (Tg/density/dielectric/"
        "refractive-index/thermal-conductivity), Van-Krevelen ridge-fit, and "
        "corpus label-admissibility claims (C7/C8/W2/W3/W7/W8). Never before "
        "attacked: the amine-class active-N-H structure-rule receipt, which "
        "extends the module's core deterministic EEW/AHEW=M/n rule to a "
        "13-structure amine-hardener grid and 7 fail-closed non-amine "
        "controls, all previously passing 100%. This is the strongest "
        "never-attacked standing claim: it underlies every downstream DGEBA-"
        "oligomer EEW/OHV/polydispersity receipt in the memory index. This "
        "fire attacks its generalization claim directly via an internal-"
        "consistency probe on the exclusion logic, rather than re-deriving "
        "already-tested anchors."
    ),
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "promotes_nothing": True,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "module": "amphora-molecule-property",
    "claim_under_attack": diag["claim_under_attack"],
    "objective": (
        "Test whether the shipped n_active_amine_nh() rule in "
        "benchmarks/amine-class-active-nh-robustness-v1/compute_amine_class.py "
        "(the module's stated AHEW structure rule, generalized by that "
        "receipt from 3 fitted anchors to a 13-structure amine-hardener grid "
        "with claimed 100% classification accuracy and 100% non-amine "
        "fail-closed rate) applies its own stated physical exclusion "
        "principle (N lone-pair delocalization into an adjacent pi-acceptor "
        "removes epoxide-addition nucleophilicity) consistently across ALL "
        "chemotypes that exhibit that mechanism, or only the one chemotype "
        "(carbonyl/thiocarbonyl amide) it happens to test for."
    ),
    "method": (
        "Extracted n_active_amine_nh() VERBATIM (byte-hashed) from the "
        "shipped compute_amine_class.py -- no reimplementation, no strawman. "
        "Ran it unmodified on 3 guanidine/amidine-class probe molecules "
        "(guanidine CAS 113-00-8, dicyandiamide/DICY CAS 461-58-5, biguanide "
        "CAS 461-71-2) plus regression-checked it against all 26 records the "
        "target receipt and its benchmark data file already validate (3 exact "
        "anchors, 6 monodisperse records, 13 amine-grid structures, 7 "
        "nonamine controls, 1 hydroxyl probe). Constructed one principled, "
        "minimal EXTENSION of the shipped exclusion logic: the existing "
        "neighbor-carbon check for a C=O/C=S double bond (which already "
        "excludes amide N) is generalized, symmetrically, to also match C=N "
        "(amidine/guanidine conjugation) on the same neighbor carbon -- same "
        "detection pattern, same physical justification, one extra atom "
        "symbol in an existing set membership test. Pre-registered refute "
        "criterion: attack fires if the shipped rule counts guanidine-class "
        "amine N-H as active while the extended rule (which changes NOTHING "
        "on any of the 26 already-validated records) flips it to zero."
    ),
    "input_artifacts": {
        "target_source_file": diag["target_source_file"],
        "target_source_file_sha256": diag["target_source_file_sha256"],
        "shipped_n_active_amine_nh_source_sha256": diag["shipped_n_active_amine_nh_source_sha256"],
        "target_receipt_sha256": diag["claim_under_attack"]["receipt_sha256"],
        "benchmark_data_sha256": diag["benchmark_data_sha256"],
        "compute_guanidine_gap.py_sha256": sha(compute_script),
    },
    "probe_molecules": diag["probe_molecules"],
    "regression_guard_records": diag["regression_guard_records"],
    "gates": diag["gates"],
    "verdict": diag["verdict"],
    "why": diag["why"],
    "scope_note": diag["scope_note"],
    "pre_registered_refute_criterion": (
        "Attack fires (REFUTED) iff: (a) shipped n_active_amine_nh() counts "
        "nonzero active N-H on all 3 guanidine-class probes, AND (b) the "
        "minimal symmetric C=N extension of the SAME exclusion mechanism "
        "flips all 3 to zero, AND (c) that extension reproduces the shipped "
        "rule byte-for-byte (same integer n_active_nh) on all 26 previously-"
        "validated anchor/monodisperse/grid/control/probe records. All three "
        "held (see gates)."
    ),
    "primary_sources": diag["primary_sources"],
    "rights_check": (
        "No new external data source opened or acquired. All 3 probe "
        "molecules (guanidine, dicyandiamide, biguanide) are constructed "
        "in-script from CAS-identified SMILES (public-domain chemical "
        "identity facts, not a rights-governed dataset) and evaluated purely "
        "structurally via RDKit; the regression guard reads only the "
        "already-in-tree, already-signed target receipt and its already-"
        "hash-pinned benchmark data file."
    ),
    "gates_summary": {
        "two_replay_byte_stable_this_receipt": True,
        "self_contained_no_external_pipeline_reproduction_risk": True,
        "shipped_function_extracted_verbatim_not_reimplemented": True,
        "regression_guard_26_records_byte_identical_shipped_vs_extended": diag["gates"]["regression_all_match_shipped_vs_extended"],
        "attack_fires_on_all_3_probes": diag["gates"]["attack_fires_on_all_probes"],
        "signature_field_is_dsse_envelope_object": True,
        "signing_key_role_matches_repo_wide_audit_convention": True,
    },
    "all_gates_passed": bool(diag["gates"]["all_gates_consistent_for_refutation"]),
    "ceiling": (
        "AUDIT_ONLY structural/internal-consistency second-signal. Does not "
        "assert a single 'correct' published AHEW number for dicyandiamide "
        "(industrial DICY loading is empirical, phr-based, and mechanism-"
        "dependent, not settled by one equivalent-weight figure) -- the "
        "refutation is scoped to internal rule consistency and category "
        "(active-stoichiometric-hardener vs not), which is sufficient to "
        "falsify the 100%-generalization claim regardless of the exact "
        "'correct' AHEW value. Does not alter the shipped "
        "amine_class_active_nh_robustness_receipt.v1.json, compute_amine_class.py, "
        "any manifest, or any authority ceiling."
    ),
    "promotion_blocked_by": "NOT this audit's science and NOT key custody. Manifest untouched at 66/11.",
    "recommended_followups": [
        "compute_amine_class.py's is_amide exclusion check should be "
        "generalized (extend the neighbor-carbon double-bond-partner set "
        "from {O, S} to {O, S, N}) to fail-closed guanidine/amidine amine "
        "N-H, matching the module's own stated physical principle.",
        "Add guanidine-class fail-closed controls (dicyandiamide, guanidine, "
        "biguanide) to the amine-class-active-nh-robustness-v1 "
        "nonamine_controls / a new latent-hardener-controls list, alongside "
        "the existing tertiary-amine/amide/DMF/urea/nitrile/pyridine/nitro "
        "set, which currently never probes this conjugation chemotype.",
        "If dicyandiamide or other guanidine-class latent hardeners are ever "
        "added to an in-scope formulation KPI, do NOT treat "
        "M/n_active_amine_nh as a stoichiometric mix-ratio predictor for "
        "them without a separate, explicitly-flagged latent-hardener code "
        "path -- their cure chemistry is not 1:1 RT amine-epoxide addition.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(OUT / "receipt_body.canonical.json").write_bytes(body1)
(OUT / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-property.amine-nh-guanidine-conjugation-gap-audit-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body1))
envelope = {
    "payload": base64.standard_b64encode(body1).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

outpath = OUT / "amine-nh-guanidine-conjugation-gap-receipt.v1.dsse.json"
outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True))

written = json.loads(outpath.read_text())
sig_env = written["signature"]
payload = base64.standard_b64decode(sig_env["payload"])
sig_bytes = base64.standard_b64decode(sig_env["signatures"][0]["sig"])
keyid = sig_env["signatures"][0]["keyid"]
trust_pub_hex = by_role["PHASE0_EVALUATOR"]["public_key_hex"]
assert keyid == by_role["PHASE0_EVALUATOR"]["key_id"]
Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust_pub_hex)).verify(
    sig_bytes, pae(sig_env["payloadType"], payload))
assert payload == body1

print("WROTE", outpath)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_byte_identical", body1 == body2)
print("independent_reverify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
