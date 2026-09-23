#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ChEBI/PubChem coating truth-set BUILT diagnostic with the
repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f...), NOT trust-anchored.
Promotes nothing; modifies no existing receipt, manifest, census, split, or lock."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

BENCH = Path("amphora-redteam-audit/benchmarks/molecule-property-chebi-truthset-built-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

canon = (BENCH/"diagnostic.canonical.json").read_bytes()
runB  = (BENCH/"diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
truth = (BENCH/"coating_truthset_300.v1.json").read_bytes()
cache = (BENCH/"pubchem_cross_check_cache.v1.json").read_bytes()

receipt = {
  "schema":"amphora.redteam-audit.replay-receipt.v1",
  "study_id":"MOLECULE_PROPERTY_CHEBI_PUBCHEM_TRUTHSET_BUILT_V1",
  "authority":"AUDIT_ONLY",
  "promotes_nothing":True,
  "modifies_no_live_config":True,
  "claim":"Frozen 300-molecule in-scope coating truth set built from ChEBI-252 CC-BY, "
          "independently cross-checked against PubChem PUG-REST (exact InChIKey, exact formula, "
          "mass<=0.05 g/mol); RDKit-2026.03.2 reproduces EEW/AHEW facts on 300/300; the three "
          "independent EXACT accuracy anchors (DGEBA/DETA/IPDA) reproduce to <=0.034 g/eq.",
  "kpi": diag["independent_cross_check"] | {"exact_anchor_max_err_g_per_eq": diag["exact_accuracy_anchors"]["max_abs_error_g_per_eq"]},
  "gates": diag["gates"],
  "diagnostic_sha256": sha(canon),
  "two_replay_gate":{"canonical_sha256":sha(canon),"runB_sha256":sha(runB),"byte_identical":canon==runB},
  "input_artifacts":{
    "chebi_sdf_sha256": diag["chebi_sdf_sha256"],
    "coating_truthset_300.v1.json": sha(truth),
    "pubchem_cross_check_cache.v1.json": sha(cache),
  },
  "builder_scripts":["chebi_probe.py","build_truthset.py","verify_truthset.py"],
  "promotion_blocked_by":"NOT key custody (evaluator+internal-reviewer ed25519 seeds ARE on host at ~/.local/share/amphora/phase0/keys/ and verify vs trust-store public keys). Real blocker is a state-machine lock: an immutable signed 2026-07-22 evaluation.v1.dsse.json (phase0_eligible=false, scientific_outcome=FAILED, SCIENTIFIC_BENCHMARK_NOT_EXECUTED) already exists; evaluate() refuses when a receipt exists and reissue() is forbidden after evaluation. Promotion needs a deliberate keyed supersession + bundle re-freeze + evaluate/review/promote, plus wiring the ChEBI source eligible in census, embedding this receipt as independent_toolkit_receipt, and adding >=8 SEALED_CONTROL split rows. Deferred from autonomous cron to avoid a locked/half-wired state before the founder report.",
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
pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"]))
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]), pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("SIGNED+VERIFIED", out)
print("diagnostic_sha256", sha(canon))
print("envelope_sha256", sha(out.read_bytes()))
