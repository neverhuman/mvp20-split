#!/usr/bin/env python3
"""DSSE-Ed25519-sign the dgeba-oligomer-eew-series AUDIT_ONLY receipt with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f..., NOT trust-anchored). Promotes
nothing; modifies no existing receipt, manifest, census, split, or lock (66/11 intact)."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-property/benchmarks/dgeba-oligomer-eew-series-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["all_gates_passed"] is True, "gates did not all pass"
compute = (BENCH / "compute_dgeba_oligomer.py").read_bytes()

receipt = {
    "schema": "amphora.molecule-property.dgeba-oligomer-eew-series-receipt.v1",
    "receipt_id": "dgeba-oligomer-eew-series-" + sha(canon)[:32],
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "promotes_nothing": True,
    "modifies_no_live_config": True,
    "module": "amphora-molecule-property",
    "claim": "An independent RDKit-2026.03.2 reference implementation extends the module's "
        "canonical EEW structure rule (EEW = M / n_epoxide) from the pure n=0 DGEBA monomer "
        "to the linear difunctional DGEBA oligomer SERIES. (1) The n=0 monomer reproduces the "
        "shipped Phase-0 expected EEW 170.2 g/eq (abs err 0.01, bar 0.5). (2) Four independently "
        "RDKit-constructed oligomers n=0..3 (C21H24O4, C39H44O7, C57H64O10, C75H84O13) each carry "
        "EXACTLY 2 terminal epoxide groups and are mass-additive: the bisphenol-A/2-hydroxy-"
        "propylene repeat mass is a byte-exact constant 284.355 g/mol across all three adjacent "
        "pairs (spread 0.0, max additivity deviation 0.0), so EEW(n) = 170.21 + 142.18*n exactly. "
        "(3) The mole-weighted number-average EEW_bar = 170.21 + 142.18*n_bar maps every published "
        "commercial DGEBA EEW band (liquid Epon 828/DER 331, near-monomer DER 332, semisolid "
        "Epon 1001F, solid Epon 1004F) to a non-negative n_bar that overlaps the independently "
        "published number-average degree of polymerization, mechanistically explaining why "
        "commercial grades read EEW > 170.2 WITHOUT asserting an exact EEW for the polydisperse "
        "mixture (composition is measured, not derived). (4) Four fail-closed controls (bisphenol-A "
        "0 epoxide, phenyl glycidyl ether 1 epoxide, mono-hydrolyzed DGEBA 1 epoxide, fully advanced "
        "DGEBA-diol 0 epoxide) are all correctly excluded as non-difunctional-DGEBA exact anchors. "
        "IUPAC-2021 standard-atomic-weight uncertainty propagates to <=0.0085 g/eq on EEW(n=0), so "
        "the 0.5 g/eq acceptance bar carries ~59x headroom over fundamental atomic-mass uncertainty.",
    "gates": diag["gates"],
    "all_gates_passed": diag["all_gates_passed"],
    "oligomers_built": diag["oligomers_built"],
    "repeat_mass_from_each_pair": diag["repeat_mass_from_each_pair"],
    "rule": diag["rule"],
    "atomic_weight_uncertainty": diag["atomic_weight_uncertainty"],
    "primary_sources": diag["primary_sources"],
    "maps_to_module_hypothesis": diag["maps_to_module_hypothesis"],
    "rdkit_version": diag["rdkit_version_detected"],
    "two_replay_gate": {"canonical_sha256": sha(canon), "runB_sha256": sha(runB), "byte_identical": canon == runB},
    "input_artifacts": {
        "eew_ahew_benchmark.v1.json_sha256": diag["benchmark_data_sha256"],
        "diagnostic.canonical.json_sha256": sha(canon),
        "compute_dgeba_oligomer.py_sha256": sha(compute),
    },
    "ceiling": "AUDIT_ONLY structural/stoichiometric second-signal. It corroborates that the "
        "module's canonical EEW structure rule is self-consistent across the entire DGEBA oligomer "
        "series (not curve-fit to the n=0 monomer) and gives the mechanistic account of commercial-"
        "grade EEW elevation, but asserts nothing about the exact EEW of polydisperse commercial "
        "grades (measured composition required), product qualification, or cure conversion. Live "
        "runtime stays LOCKED_INTERNAL; the commercial_product_claim_locked=true lock is unchanged.",
    "promotion_blocked_by": "NOT this audit's science (all gates pass) and NOT key custody. Promotion "
        "requires the human dual-identity Phase-0 ceremony keys this cron does not hold; the immutable "
        "2026-07-22 evaluation.v1.dsse.json state-machine lock is unchanged. Manifest untouched at 66/11.",
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"], "public_key_hex": PUB["public_key_hex"],
                    "trust_anchored": False, "note": "NOT in config/phase0-trust-store.v1.json; audit evidence only"},
}

body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-property.dgeba-oligomer-eew-series-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
# The receipt file itself carries the DSSE envelope plus a plain 'signature' field so the
# byte-stability harness / jq '.signature|length' check can read it directly.
out = dict(receipt)
out["dsse_envelope"] = envelope
out["signature"] = base64.standard_b64encode(sig).decode()
outpath = BENCH / "dgeba_oligomer_eew_series_receipt.v1.json"
outpath.write_text(json.dumps(out, indent=2, sort_keys=True))
# verify
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"])).verify(sig, pae(ptype, body))
print("SIGNED_OK", outpath)
print("receipt_id", receipt["receipt_id"])
print("sig_verified True")
