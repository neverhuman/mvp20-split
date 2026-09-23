#!/usr/bin/env python3
"""Independent self-verification of the R-A06 signed repair receipt.
Reloads from disk, rebuilds the PAE, verifies Ed25519 against the pubkey
DERIVED FROM THE SEED (not from the receipt), checks keyid prefix, and
re-asserts every acceptance/supersedes invariant."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-generator"
RCPT = MOD / "evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json"
SEED = Path.home() / ".local/share/amphora/phase0/keys/evaluator.ed25519.seed"


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


ok = {}
r = json.loads(RCPT.read_text())
env = r["signature"]
body = base64.standard_b64decode(env["payload"])
ptype = env["payloadType"]
kid = env["signatures"][0]["keyid"]
sig = base64.standard_b64decode(env["signatures"][0]["sig"])

# pubkey derived from the SEED, independently of anything in the receipt
pub = Ed25519PrivateKey.from_private_bytes(load_seed(SEED)).public_key().public_bytes_raw()
Ed25519PublicKey.from_public_bytes(pub).verify(sig, pae(ptype, body))
ok["ed25519_signature_verifies_against_seed_derived_pubkey"] = True
ok["keyid_prefix_phase0_evaluator_3ef6b35"] = kid.startswith("phase0-evaluator-3ef6b35")
ok["keyid_equals_sha256_of_seed_pubkey"] = (kid == f"phase0-evaluator-{sha(pub)}")
ok["receipt_pubkey_matches_seed_pubkey"] = (r["evaluator_public_key_hex"] == pub.hex())
ok["payload_type"] = ptype

# tamper control: a single flipped payload byte must fail verification
bad = bytearray(body); bad[0] ^= 0x01
try:
    Ed25519PublicKey.from_public_bytes(pub).verify(sig, pae(ptype, bytes(bad)))
    ok["tamper_control_rejects_mutated_payload"] = False
except Exception:
    ok["tamper_control_rejects_mutated_payload"] = True

p = json.loads(body)
ok["repair_item"] = p["repair_item"] == "R-A06"
ok["repair_mode"] = p["repair_mode"] == "interactive-2026-08-03"
att = p["attestation"]
ok["attest_modifies_existing_receipts_false"] = att["modifies_existing_receipts"] is False
ok["attest_modifies_manifest_false"] = att["modifies_manifest"] is False
ok["attest_promotes_authority_false"] = att["promotes_authority"] is False
ok["attest_flips_scientific_readiness_false"] = att["flips_scientific_readiness"] is False
ok["attest_trust_anchored_in_phase0_store_true"] = att["trust_anchored_in_phase0_store"] is True
ok["attest_two_replay_gate_pass"] = att["two_replay_sha256_gate"]["status"] == "PASS"
ok["attest_two_replay_byte_identical"] = att["two_replay_sha256_gate"]["byte_identical"] is True

# supersedes blocks: required keys + live sha256 match + originals byte-intact
sup = p["supersedes"]
ok["n_supersedes_blocks"] = len(sup)
for s in sup:
    for k in ("superseded_path", "superseded_sha256", "superseded_deleted_or_modified", "reason"):
        assert k in s, f"missing {k}"
    live = sha((ROOT / s["superseded_path"]).read_bytes())
    ok[f"original_intact::{Path(s['superseded_path']).name}"] = (live == s["superseded_sha256"])
    ok[f"not_deleted_or_modified::{Path(s['superseded_path']).name}"] = (
        s["superseded_deleted_or_modified"] is False)

acc = p["acceptance"]
ok["acceptance_all_pass"] = acc["all_pass"] is True
for k in ("a_clopper_pearson_matches_refuting_receipt",
          "b_corrected_yield_matches_refuting_receipt",
          "c_family_diversity_matches_refuting_receipt",
          "aggregate_intdiv1_parity_with_superseded_receipt",
          "structures_unchanged"):
    ok["acceptance::" + k] = acc[k] is True

cv = p["corrected_values"]
ok["cp_ci_4dp_is_0.9075_1.0"] = [round(cv["feasible_fraction_exact_clopper_pearson95_ci"][0], 4),
                                 round(cv["feasible_fraction_exact_clopper_pearson95_ci"][1], 4)] == [0.9075, 1.0]
ok["corrected_yield_29"] = cv["valid_unique_difunctional_feasible_yield"] == 29
ok["f1_intdiv1_0.1851"] = round(cv["intdiv1_within_F1_polyethyleneamine"], 4) == 0.1851
ok["f2_intdiv1_0.0870"] = round(cv["intdiv1_within_F2_alpha_omega_diamine"], 4) == 0.0870
ok["structures_changed_false"] = cv["structures_changed"] is False
ok["n_mislabeled_embedded"] = len(p["derivation"]["2_corrected_difunctional_yield"]["mislabeled_proposals"])
ok["re_attack_present"] = set(p["re_attack"]) == {
    "a_ci_inadmissibility", "b_functionality_mislabel", "c_homolog_fingerprint_saturation"}
ok["re_attack_all_original_findings_reproduced"] = all(
    v["original_finding_reproduced"] for v in p["re_attack"].values())

print(json.dumps(ok, indent=2))
fails = [k for k, v in ok.items() if v is False]
print("RECEIPT_SHA256", sha(RCPT.read_bytes()))
print("FAILURES", fails)
print("SELF_VERIFY", "PASS" if not fails else "FAIL")
