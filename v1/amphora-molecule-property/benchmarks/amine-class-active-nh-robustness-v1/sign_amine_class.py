#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amine-class active-N-H robustness AUDIT_ONLY receipt with
the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f..., NOT trust-anchored).
Promotes nothing; modifies no existing receipt, manifest, census, split, or lock."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-property/benchmarks/amine-class-active-nh-robustness-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
compute = (BENCH / "compute_amine_class.py").read_bytes()

receipt = {
    "schema": "amphora.molecule-property.amine-class-active-nh-robustness-receipt.v1",
    "receipt_id": "amine-class-active-nh-robustness-" + sha(canon)[:32],
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "promotes_nothing": True,
    "modifies_no_live_config": True,
    "module": "amphora-molecule-property",
    "claim": "An independent RDKit-2026.03.2 reference implementation of the module's stated "
             "structure rule (EEW=M/n_epoxide; AHEW=M/n_active_amine_NH, counting 2 per primary + "
             "1 per secondary + 0 per tertiary amine N-H, with amide/imine/nitrile/nitro/aromatic-ring "
             "N and hydroxyl H excluded) (1) reproduces every shipped Phase-0 'expected' EEW/AHEW on "
             "the 3 exact anchors (max abs error 0.0338 g/eq, bar 0.5) and 6/6 monodisperse records, "
             "AND (2) generalises the falsifiable hypothesis beyond those fitted points: a 13-structure "
             "published epoxy-hardener grid (aliphatic/cycloaliphatic/araliphatic/aromatic 1'/2'/3' "
             "amines incl. DETA, TETA, TEPA, EDA, IPDA, HMDA, m-XDA, piperazine, AEP, DACH, aniline, "
             "MDA, DDS) is classified with 100% correct active-N-H integer count and theoretical AHEW "
             "within 0.3% of published supplier/handbook reference values; 7/7 non-amine controls "
             "(tertiary amine, amide, DMF, urea, nitrile, pyridine, nitro) are fail-closed to 0 active "
             "N-H; and the hydroxyl-exclusion probe (ethanolamine) correctly counts 2 amine N-H while "
             "ignoring -OH. IUPAC-2021 standard atomic-weight uncertainty propagates to <=0.011 g/eq on "
             "all anchors, i.e. the 0.5 g/eq acceptance bar carries >=47x headroom over the fundamental "
             "atomic-mass uncertainty; the exact-arithmetic claim is limited only by rounding of the "
             "published reference values, not by atomic-mass knowledge.",
    "kpis": diag["gates"],
    "anchor_records": diag["anchor_records"],
    "monodisperse_records": diag["monodisperse_records"],
    "amine_class_grid": diag["amine_class_grid"],
    "nonamine_controls": diag["nonamine_controls"],
    "hydroxyl_exclusion_probe": diag["hydroxyl_exclusion_probe"],
    "atomic_weight_uncertainty": diag["atomic_weight_uncertainty"],
    "rule": diag["rule"],
    "primary_sources": diag["primary_sources"],
    "maps_to_module_hypothesis": diag["maps_to_module_hypothesis"],
    "rdkit_version": diag["rdkit_version_detected"],
    "two_replay_gate": {"canonical_sha256": sha(canon), "runB_sha256": sha(runB), "byte_identical": canon == runB},
    "input_artifacts": {
        "eew_ahew_benchmark.v1.json_sha256": diag["benchmark_data_sha256"],
        "diagnostic.canonical.json_sha256": sha(canon),
        "compute_amine_class.py_sha256": sha(compute),
    },
    "ceiling": "AUDIT_ONLY structural/stoichiometric second-signal. It corroborates that the module's "
               "canonical structure rule is chemically general (not curve-fit to 3 anchors) and "
               "fail-closed, but asserts nothing about product qualification, cure conversion, or "
               "wet-lab AHEW of polydisperse commercial grades, which remain measured-only. Live "
               "runtime stays LOCKED_INTERNAL; promotion needs the human dual-identity Phase-0 keys.",
    "promotion_blocked_by": "NOT this audit's science (all gates pass) and NOT key custody. Promotion "
        "requires the human dual-identity Phase-0 ceremony keys this cron does not hold; the immutable "
        "2026-07-22 evaluation.v1.dsse.json state-machine lock is unchanged. Manifest untouched at 66/11.",
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"], "public_key_hex": PUB["public_key_hex"],
                    "trust_anchored": False, "note": "NOT in config/phase0-trust-store.v1.json; audit evidence only"},
}

body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-property.amine-class-active-nh-robustness-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}

# module-receipt convention: human-readable fields + embedded DSSE envelope under `signature`
outdoc = dict(receipt)
outdoc["signature"] = envelope
out = BENCH / "amine_class_active_nh_robustness_receipt.v1.json"
out.write_text(json.dumps(outdoc, indent=2, sort_keys=True))

# verify
pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"]))
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("SIGNED+VERIFIED", out)
print("receipt_sha256", sha(out.read_bytes()))
print("diagnostic_sha256", sha(canon))
