#!/usr/bin/env python3
"""R-A07 SELF-VERIFY: reload the signed receipt from disk, rebuild the PAE,
verify Ed25519 against the pubkey derived from the phase0 evaluator seed,
assert keyid prefix, and re-assert acceptance facts from the decoded payload."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = (ROOT / "amphora-molecule-novelty/evidence/phase0/repairs/R-A07/done/"
       "r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json")
SEED = Path.home() / ".local/share/amphora/phase0/keys/evaluator.ed25519.seed"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)
def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]

receipt = json.loads(OUT.read_text())
env = receipt["signature"]
payload = base64.standard_b64decode(env["payload"])
sig = base64.standard_b64decode(env["signatures"][0]["sig"])
keyid = env["signatures"][0]["keyid"]

sk = Ed25519PrivateKey.from_private_bytes(load_seed(SEED))
pub = sk.public_key().public_bytes_raw()
derived_key_id = f"phase0-evaluator-{sha(pub)}"

assert keyid.startswith("phase0-evaluator-3ef6b35"), f"keyid prefix mismatch: {keyid}"
assert keyid == derived_key_id, "keyid does not derive from seed"
Ed25519PublicKey.from_public_bytes(pub).verify(sig, pae(env["payloadType"], payload))

p = json.loads(payload)
assert p["repair_item"] == "R-A07"
assert p["repair_mode"] == "interactive-2026-08-03"
assert len(p["supersedes"]) == 2
assert all(s["superseded_deleted_or_modified"] is False for s in p["supersedes"])
for s in p["supersedes"]:
    assert sha((ROOT / s["superseded_path"]).read_bytes()) == s["superseded_sha256"], \
        f"superseded artifact no longer byte-intact: {s['superseded_path']}"
assert p["corrected_ipda"]["rdkit_formula_check_pass"] is True
assert p["corrected_ipda"]["corrected_formula"] == "C10H22N2"
assert p["corrected_ipda"]["recomputed_nn_tanimoto_vs_deduped_350"] == 0.16666666666666666
assert p["corrected_ipda"]["below_0_40_cutoff"] is True
assert p["dds_cross_family_count_a05"]["new_n_novel_of_4"] == 0
assert p["n_flip_cells"] == 5
assert p["top_level_five_over_five_corrected"]["n_novel"] == 5
assert p["self_tests_all_pass"] is True
assert p["reproducibility"]["two_replay_sha256_gate"] == "PASS"

print("SELF_VERIFY_OK")
print("keyid", keyid)
print("signature_valid_against_seed_derived_pubkey", True)
print("payload_sha256", sha(payload))
print("receipt_sha256", sha(OUT.read_bytes()))
print("superseded_paths_byte_intact", True)
