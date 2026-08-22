#!/usr/bin/env python3
"""DSSE-Ed25519-sign the molecule-property ChEBI truth-set unlock AUDIT diagnostic
with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), NOT trust-anchored.
Promotes nothing; modifies no existing receipt or manifest."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/molecule-property-chebi-truthset-unlock-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

canon = (BENCH/"diagnostic.canonical.json").read_bytes()
runB  = (BENCH/"diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)

receipt = {
  "schema":"amphora.redteam-audit.replay-receipt.v1",
  "study_id":"MOLECULE_PROPERTY_CHEBI_TRUTHSET_UNLOCK_V1",
  "authority":"AUDIT_ONLY",
  "promotes_nothing":True,
  "diagnostic_sha256":diag_sha,
  "two_replay_gate":{"canonical_sha256":sha(canon),"runB_sha256":sha(runB),"byte_identical":canon==runB},
  "builder_script":"build_diagnostic.py",
  "signing_key":{"key_id":PUB["key_id"],"authority":PUB["authority"],"public_key_hex":PUB["public_key_hex"],
                 "trust_anchored":False,"note":"NOT in config/phase0-trust-store.v1.json; audit evidence only"},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH/"replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))

# verify
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"]))
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]), pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("SIGNED+VERIFIED", out)
print("diagnostic_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
