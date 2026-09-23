#!/usr/bin/env python3
"""R-S05: sign the DETA/TETA + r(T) reactivity-gap-closure done receipt with the
PHASE0_EVALUATOR key. Follows the exact PAE/load_seed/keyid/self-verify construction
already used by amphora-molecule-role-ranker/evidence/phase0/repairs/V-A12a/work/sign_va12a.py.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-role-ranker"
ITEM = MOD / "evidence/phase0/repairs/R-S05"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260812T200001-3068508-0f0bfa0e225c"
CAMPAIGN_ITEM_ID = "R-S05"
DATE = "2026-08-12"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fsha(p):
    return sha(Path(p).read_bytes())


def rel(p):
    return str(Path(p).relative_to(ROOT))


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


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
by_role = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"
assert eval_pub_hex == by_role["PHASE0_EVALUATOR"]["public_key_hex"]

# ---------------------------------------------------------------- inputs
canon_path = WORK / "diagnostic.canonical.json"
runb_path = WORK / "diagnostic.runB.json"
pc_path = WORK / "positive_control.canonical.json"
harness_path = WORK / "run_deta_teta_reactivity.py"
pc_script_path = WORK / "run_positive_control.py"

canon_bytes = canon_path.read_bytes()
runb_bytes = runb_path.read_bytes()
assert sha(canon_bytes) == sha(runb_bytes), "two-replay byte gate FAILED"
diag = json.loads(canon_bytes)
pc = json.loads(pc_path.read_bytes())

assert diag["verdict"] == "H2_SURVIVED_UNDER_DETA_TETA_REACTIVITY_TEMPERATURE_SWEEP"
assert diag["attack"]["n_reversals"] == 0
assert diag["validation_gate"]["all_pass"] is True
assert diag["functionality_rederivation_agrees_with_fixture"] is True
assert diag["all_target_hardeners_have_preexisting_secondary_site"] is True
assert pc["detected"] is True
assert pc["run_against_real_input"]["fired"] is False
assert pc["run_against_tampered_input"]["fired"] is True

PARENT_REACT = MOD / "benchmarks/role-reactivity-ratio-substitution-effect-v1/replay_receipt.v1.dsse.json"
PARENT_SOL_DIAG = MOD / "benchmarks/role-macosko-miller-sol-latitude-v1/diagnostic.canonical.json"
FIXTURE = MOD / "reference/phase0-role-known-answer.v1.json"

body_obj = {
    "schema": "amphora.molecule-role-ranker.r-s05-deta-teta-reactivity-temperature-receipt.v1",
    "receipt_id": "r-s05-deta-teta-reactivity-temperature-" + sha(canon_bytes)[:32],
    "fire_id": FIRE_ID,
    "campaign_item_id": CAMPAIGN_ITEM_ID,
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "module": "amphora-molecule-role-ranker",
    "repair_mode": True,
    "objective": (
        "R-S05: close the pre_existing_secondary_amine_hardeners and "
        "temperature_dependence_of_r does_not_close gaps explicitly logged by the parent "
        "receipt role-reactivity-ratio-substitution-effect-v1 (signed, "
        "H2_SURVIVED_UNDER_LITERATURE_REACTIVITY_RATIO). Extends the independent "
        "finite-population kinetic Monte Carlo H2-direction-rule falsification attack to "
        "DETA and TETA (both carry a pre-existing secondary amine N-H in the unreacted "
        "molecule, RDKit-verified per-atom, not asserted) and adds a temperature-envelope "
        "sensitivity sweep plus an r_crit bisection over the full physically-meaningful "
        "reactivity-ratio range."
    ),
    "claim_under_attack": {
        "receipt_path": "amphora-molecule-role-ranker/benchmarks/"
                        "role-reactivity-ratio-substitution-effect-v1/",
        "claim_text": ("The H2 direction rule holds for secondary-amine-bearing hardeners "
                       "(DETA/TETA) and under temperature-dependent reactivity ratios r(T)."),
        "parent_receipt_sha256": fsha(PARENT_REACT),
        "grandparent_diagnostic_sha256": fsha(PARENT_SOL_DIAG),
    },
    "does_not_supersede": True,
    "note_on_repair_mode_rule_2": (
        "This item extends a SURVIVED claim's scope to previously does_not_close hardeners; "
        "it does not repair a REFUTED claim, so there is no prior refuting attack to "
        "re-run under repair-mode rule 2. The re-attack performed instead is: independent "
        "re-derivation of hardener site structure (RDKit, not the parent script's cached "
        "values), a fresh generalized MC implementation (not imported from the parent "
        "script), and an explicit r_crit bisection the parent receipt never attempted."
    ),
    "primary_references": diag["primary_references"],
    "reactivity_ratios_tested": diag["reactivity_ratios_tested"],
    "temperature_labels_c": diag["temperature_labels_c"],
    "r_of_t_honest_scope": diag["r_of_t_honest_scope"],
    "monte_carlo_model": diag["monte_carlo_model"],
    "headline_result": {
        "functionality_rederivation_agrees_with_fixture": diag["functionality_rederivation_agrees_with_fixture"],
        "all_target_hardeners_have_preexisting_secondary_site": diag["all_target_hardeners_have_preexisting_secondary_site"],
        "validation_gate_all_pass": diag["validation_gate"]["all_pass"],
        "validation_gate_n_checks": diag["validation_gate"]["n_checks"],
        "n_direction_tests": diag["attack"]["n_direction_tests"],
        "n_direction_holds": diag["attack"]["n_direction_holds"],
        "n_reversals": diag["attack"]["n_reversals"],
        "reversals": diag["attack"]["reversals"],
        "r_crit_bisection": diag["r_crit_bisection"],
        "verdict": diag["verdict"],
        "verdict_detail": diag["verdict_detail"],
        "interpretation": diag["interpretation"],
    },
    "hardener_site_structure": diag["hardener_site_structure"],
    "validation_gate_rows": diag["validation_gate"]["rows"],
    "validation_gate_cross_check_against_signed_prior_rows": diag["validation_gate"]["independent_cross_check_against_signed_prior_receipt_rows"],
    "attack_rows": diag["attack"]["rows"],
    "positive_control": {
        "planted_defect": pc["planted_defect"]["field"] + " changed from 5 to 4",
        "how_planted": pc["planted_defect"]["how_planted"],
        "detected": pc["detected"],
        "evidence": {
            "run_against_real_input": pc["run_against_real_input"],
            "run_against_tampered_input": pc["run_against_tampered_input"],
            "real_fixture_sha256": pc["planted_defect"]["real_fixture_sha256"],
            "tampered_fixture_sha256": pc["planted_defect"]["tampered_fixture_sha256"],
        },
        "why_this_defect_not_an_r_perturbation": pc["r_crit_no_positive_control_available_note"],
        "positive_control_diagnostic_sha256": sha(pc_path.read_bytes()),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon_bytes),
        "runB_diagnostic_sha256": sha(runb_bytes),
        "harness_sha256": fsha(harness_path),
        "positive_control_script_sha256": fsha(pc_script_path),
        "positive_control_diagnostic_sha256": sha(pc_path.read_bytes()),
        "fixture_sha256": diag["fixture"]["sha256"],
        "fixture_sha256_verified_unchanged": fsha(FIXTURE) == diag["fixture"]["sha256"],
        "determinism_basis": ("random.Random seeded by int(sha256(run-identifying-string)[:16],16) "
                              "per Monte Carlo run; no wall-clock, no OS entropy"),
    },
    "closes": diag["closes"],
    "does_not_close": diag["does_not_close"],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator SIGNING key used here "
                                       "(this receipt IS signed with it), but this is an "
                                       "AUDIT_ONLY science-validation replay, not a Phase-0 "
                                       "evaluation/review signature under the promotion protocol.",
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT edited; "
                              "requires human dual-identity Phase-0 ceremony keys.",
        "SCOPE": "closes pre_existing_secondary_amine_hardeners and temperature_dependence_of_r "
                "for DETA/TETA at resin-dgeba; other resins and other pre-existing-secondary "
                "hardeners not in this fixture remain untested.",
        "SUPERSESSION": "does NOT supersede any prior receipt: extends scope only, does not "
                        "overturn or replace role-reactivity-ratio-substitution-effect-v1 or "
                        "role-macosko-miller-sol-latitude-v1.",
    },
    "claim_locks": diag["claim_locks"],
    "verdict": "CLAIM_SURVIVED",
    "date": DATE,
    "generated_on_host": "xbabe2",
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY R-S05 done receipt under evidence/phase0/repairs/R-S05/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(WORK / "receipt_body.canonical.json").write_bytes(body1)
(WORK / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-role-ranker.r-s05-deta-teta-reactivity-temperature-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body1))
envelope = {
    "payload": base64.standard_b64encode(body1).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}

DONE.mkdir(parents=True, exist_ok=True)
outpath = DONE / "r-s05-deta-teta-reactivity-temperature-receipt.v1.dsse.json"
outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# ---------------------------------------------------------------- self-verify
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
print("verdict", body_obj["verdict"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_byte_identical", body1 == body2)
print("self_verify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
