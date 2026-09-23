#!/usr/bin/env python3
"""DSSE-Ed25519-sign the dgeba-oligomer-hydroxyl-value AUDIT_ONLY receipt with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f..., NOT trust-anchored). Promotes
nothing; modifies no existing receipt, manifest, census, split, or lock (66/11 intact)."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-property/benchmarks/dgeba-oligomer-hydroxyl-value-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["all_gates_passed"] is True, "gates did not all pass"
compute = (BENCH / "compute_dgeba_hydroxyl.py").read_bytes()

receipt = {
    "schema": "amphora.molecule-property.dgeba-oligomer-hydroxyl-value-receipt.v1",
    "receipt_id": "dgeba-oligomer-hydroxyl-value-" + sha(canon)[:32],
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "promotes_nothing": True,
    "modifies_no_live_config": True,
    "module": "amphora-molecule-property",
    "claim": "An independent RDKit-2026.03.2 reference implementation adds a NEW molecular "
        "property to the module's canonical-structure-rule claim: the HYDROXYL VALUE (hydroxyl "
        "number) OHV of the linear DGEBA oligomer series, OHV(n) = 56100 * n / (M0 + n*M_repeat) "
        "in mg KOH/g (ASTM D4274 definition; M(KOH)=56.1056 g/mol). (1) The unadvanced n=0 DGEBA "
        "monomer carries ZERO titratable hydroxyls, so OHV(0)=0 exactly (structural anchor). "
        "(2) For each independently RDKit-built oligomer n=0..3, total -OH == n AND all n are "
        "secondary aliphatic (0 phenolic, 0 primary), giving OHV = [0, 89.79, 123.42, 141.02] "
        "mg KOH/g. (3) The series is monotone increasing and bounded above by the "
        "C18H20O3-repeat asymptote 56100/M_repeat = 197.29 mg KOH/g; the hydroxyl count equals "
        "the mass-advancement variable n for every oligomer, so OHV and EEW(n)=170.21+142.18n "
        "are two independent structural read-outs of ONE advancement state. (4) Four fail-closed "
        "controls (bisphenol-A 2 phenolic OH, glycidol 1 primary OH, neopentyl glycol 2 primary "
        "OH, fully-hydrolyzed DGEBA diol 2 primary+2 secondary OH) are all correctly excluded as "
        "non-advancement-series members. IUPAC-2021 standard-atomic-weight uncertainty propagates "
        "to <=0.0046 mg KOH/g on OHV(n=1), so the 0.5 mg KOH/g bar carries ~110x headroom. "
        "Corroborative only: asserts no exact OHV for polydisperse commercial grades (composition "
        "is measured, not derived) and modifies no live lock.",
    "gates": diag["gates"],
    "all_gates_passed": diag["all_gates_passed"],
    "oligomers": diag["oligomers"],
    "rule": diag["rule"],
    "koh_molar_mass_g_per_mol": diag["koh_molar_mass_g_per_mol"],
    "atomic_weight_uncertainty": diag["atomic_weight_uncertainty"],
    "primary_sources": diag["primary_sources"],
    "maps_to_module_hypothesis": diag["maps_to_module_hypothesis"],
    "rdkit_version": diag["rdkit_version_detected"],
    "two_replay_gate": {"canonical_sha256": sha(canon), "runB_sha256": sha(runB), "byte_identical": canon == runB},
    "input_artifacts": {
        "eew_ahew_benchmark.v1.json_sha256": diag["benchmark_data_sha256"],
        "diagnostic.canonical.json_sha256": sha(canon),
        "compute_dgeba_hydroxyl.py_sha256": sha(compute),
    },
    "ceiling": "AUDIT_ONLY structural/stoichiometric second-signal for a NEW target property "
        "(hydroxyl value). It corroborates that the module's advancement variable n governs both "
        "EEW and OHV self-consistently across the pure DGEBA oligomer series (not curve-fit) and "
        "cleanly separates advancement secondary OH from phenolic/primary OH, but asserts nothing "
        "about the exact OHV of polydisperse commercial grades (measured composition required), "
        "product qualification, or cure conversion. Live runtime stays LOCKED_INTERNAL; the "
        "commercial_product_claim_locked=true lock is unchanged.",
    "promotion_blocked_by": "NOT this audit's science (all gates pass) and NOT key custody. "
        "Promotion requires the human dual-identity Phase-0 ceremony keys this cron does not hold; "
        "the immutable evaluation.v1.dsse.json state-machine lock is unchanged. Manifest untouched at 66/11.",
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"], "public_key_hex": PUB["public_key_hex"],
                    "trust_anchored": False, "note": "NOT in config/phase0-trust-store.v1.json; audit evidence only"},
}

body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-property.dgeba-oligomer-hydroxyl-value-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = dict(receipt)
out["dsse_envelope"] = envelope
out["signature"] = base64.standard_b64encode(sig).decode()
outpath = BENCH / "dgeba_oligomer_hydroxyl_value_receipt.v1.json"
outpath.write_text(json.dumps(out, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"])).verify(sig, pae(ptype, body))
print("SIGNED_OK", outpath)
print("receipt_id", receipt["receipt_id"])
print("sig_verified True")
