#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score KRIEGER_DOUGHERTY rights-wall
finding (campaign C9, fire 2). AUDIT_ONLY: does NOT promote the module, does
NOT edit the signed FFW/melt-viscosity Phase-0 KPI or the HERSCHEL_BULKLEY
fire-1 receipt, does NOT modify the 66-receipt master manifest, does NOT
modify reference/rheology/source-landscape.v1.json, does NOT extract or
reproduce any data from the rights-restricted Reynolds et al. 2024 source."""
import base64, hashlib, json, subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"
EV = MOD / "evidence/audit/krieger-dougherty-rights-wall-reynolds2024-v1"
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


canon = (EV / "diagnostic.canonical.json").read_bytes()
runB = (EV / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["verdict"] == "BLOCKED_RIGHTS"

# independent 3rd confirmatory replay into a temp path
third = EV / "diagnostic.runC.tmp.json"
subprocess.run(["python3", str(EV / "run_rights_audit.py"), str(third)], check=True, cwd=str(EV))
third_sha = sha(third.read_bytes())
third.unlink()
assert third_sha == diag_sha, f"3rd replay FAIL {third_sha} != {diag_sha}"

harness_sha = sha((EV / "run_rights_audit.py").read_bytes())
finding_lock_sha = sha((EV / "source_reynolds2024_finding.v1.json").read_bytes())
assert finding_lock_sha == diag["finding_lock_sha256"], "finding lock hash mismatch"

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

finding = json.loads((EV / "source_reynolds2024_finding.v1.json").read_bytes())

body_obj = {
    "schema": "amphora.viscosity-score.krieger-dougherty-rights-wall-receipt.v1",
    "receipt_id": "krieger-dougherty-rights-wall-reynolds2024-v1",
    "module_id": "amphora-viscosity-score",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-01",
    "generated_on_host": "xbabe2 (search performed from xbabe1 via WebSearch/WebFetch)",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_source_landscape": False,
    "modifies_prior_c9_fire1_receipt": False,
    "campaign_item_id": "C9",
    "claim_under_attack": diag["claim_under_attack"],
    "scope_of_this_run": diag["scope_of_this_run"],
    "claim": (
        "C9 fire 2: continued the KRIEGER_DOUGHERTY (src/lib.rs:1208) half of "
        "the C9 objective left pending by fire 1. Extended the open-literature "
        "sweep (MDPI supplementary files, Zenodo/Figshare, PMC, RSC Advances, "
        "Wiley, De Gruyter) and located a genuine candidate: Reynolds, "
        "Unterhalter, Francoeur, Bortner & Raeymaekers (2024), 'Viscosity of "
        "Mono- and Polydisperse Mixtures of Photopolymer and Rigid Spheres for "
        "Manufacturing of Engineered Composite Materials Using Vat "
        "Photopolymerization', Advanced Engineering Materials 26(10):2301630, "
        "doi:10.1002/adem.202301630 -- a UV-cure photopolymer resin (model "
        "system, per the C9 objective's explicit allowance) filled with rigid "
        "glass microspheres, experimentally sweeping particle volume fraction "
        "Phi and explicitly fitting the Krieger and Dougherty (1959) model "
        "including a maximum-packing-fraction bound (Phi_m ~= 0.54 cited for "
        "simple-cubic packing). This is exactly the eta-vs-phi ladder the C9 "
        "objective asked for. It is BLOCKED from use: the paper's own license "
        "line states it is published under Creative Commons "
        "Attribution-NonCommercial-NoDerivs (CC BY-NC-ND), not CC BY. Per "
        "governance rule 5, this cron does not extract, transcribe, or derive "
        "a benchmark from CC BY-NC-ND content without human rights review, "
        "since (a) the NoDerivs clause plausibly covers re-typesetting the "
        "paper's data into a comparison receipt, and (b) the NonCommercial "
        "clause plausibly covers any use inside a commercial coating-IP "
        "portfolio even if the receipt is never externally distributed. "
        "No data values from the source were extracted, transcribed, or used "
        "in this receipt or its artifacts -- see not_extracted field."
    ),
    "search_record": finding["sources_checked_this_fire"],
    "why_rights_block_not_data_wall": finding["why_this_is_a_rights_block_not_a_data_wall"],
    "human_action_needed": finding["human_action_needed"],
    "not_extracted": finding["not_extracted"],
    "results": {
        "n_sources_checked_this_fire": diag["n_sources_checked_this_fire"],
        "n_cc_by_confirmed_but_unusable": diag["n_cc_by_confirmed_but_unusable"],
        "n_access_blocked_no_license_determined": diag["n_access_blocked_no_license_determined"],
        "n_rights_blocked_usable_content_found": diag["n_rights_blocked_usable_content_found"],
        "usable_content_found": diag["usable_content_found"],
        "blocking_source_doi": diag["blocking_source_doi"],
        "blocking_license": diag["blocking_license"],
    },
    "refutation_criterion": diag["refutation_criterion"],
    "verdict": "BLOCKED_RIGHTS",
    "does_not_close": diag["does_not_close"],
    "provenance": {
        "harness_sha256": {"run_rights_audit.py": harness_sha},
        "finding_lock_sha256": finding_lock_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "third_replay_sha256": third_sha,
        "byte_identical": canon == runB,
        "determinism": "pure-python summarization of a hash-locked search-finding JSON, no RNG, no network at run time.",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY rights-wall receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-krieger-dougherty-rights-wall+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = EV / "krieger-dougherty-rights-wall-reynolds2024-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
