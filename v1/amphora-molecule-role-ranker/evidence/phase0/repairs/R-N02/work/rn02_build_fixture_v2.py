#!/usr/bin/env python3
"""R-N02: build phase0-role-known-answer.v2.json ALONGSIDE the immutable v1.

v1 (sha 8ce4d541...) is cited by sha in signed receipts and is NEVER touched.
v2 = v1's 39 records byte-identical + 5 new guanidine-class out_of_domain
records (DPG, DOTG, guanidine, DICY, biguanide -- the R-N02 probe molecules),
facts taken verbatim from the post-fix real-FFI sweep
(ffi_sweep.POST.runA.json), fulfilling the refuting receipts' follow-up
'Add DPG- and DOTG-class guanidine accelerators to the module's own 39-record
known-answer fixture ... so this chemotype is regression-guarded going
forward.' Deterministic: json.dumps(indent=2, sort_keys=True) + newline,
same as v1.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
V1 = ROOT / "amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json"
V2 = ROOT / "amphora-molecule-role-ranker/reference/phase0-role-known-answer.v2.json"
SWEEP = ROOT / "amphora-molecule-role-ranker/evidence/phase0/repairs/R-N02/work/ffi_sweep.POST.runA.json"

V1_LOCKED_SHA = "8ce4d54192a20e8de1bb89f6181b11630fc184b4dda2918ce934610630855c8f"

v1_bytes = V1.read_bytes()
assert hashlib.sha256(v1_bytes).hexdigest() == V1_LOCKED_SHA, "v1 fixture drifted"
v1 = json.loads(v1_bytes)
sweep = json.loads(SWEEP.read_text())
probe = {p["id"]: p for p in sweep["probe_records"]}

SOURCES = {
    "dpg-diphenylguanidine-accelerator": [
        "PubChem CID 7593 (1,3-diphenylguanidine, CAS 102-06-7)",
        "US Patent 9,238,706 (guanidine derivatives as epoxy curing accelerators)",
    ],
    "dotg-di-o-tolylguanidine-accelerator": [
        "PubChem CID 7261 (N,N'-di-o-tolylguanidine, CAS 97-39-2)",
    ],
    "guanidine": ["PubChem CID 3520 (guanidine, CAS 113-00-8)"],
    "dicyandiamide": [
        "PubChem CID 10005 (dicyandiamide/cyanoguanidine, CAS 461-58-5)",
        "Lee & Neville, Handbook of Epoxy Resins, McGraw-Hill 1967 (latent DGEBA hardener; cure is catalytic/elevated-temperature, not RT 1:1 amine-epoxide addition)",
    ],
    "biguanide": ["PubChem CID 7939 (biguanide, CAS 461-71-2)"],
}

new_records = []
for pid in [
    "ood-guanidine-dpg-accelerator",
    "ood-guanidine-dotg-accelerator",
    "ood-guanidine",
    "ood-guanidine-dicy-latent-hardener",
    "ood-guanidine-biguanide",
]:
    key = {
        "ood-guanidine-dpg-accelerator": "dpg-diphenylguanidine-accelerator",
        "ood-guanidine-dotg-accelerator": "dotg-di-o-tolylguanidine-accelerator",
        "ood-guanidine": "guanidine",
        "ood-guanidine-dicy-latent-hardener": "dicyandiamide",
        "ood-guanidine-biguanide": "biguanide",
    }[pid]
    p = probe[key]
    assert p["reactive_amine_hydrogen_count"] == 0 and p["inferred_role"] == "out_of_domain", key
    new_records.append({
        "canonical_structure_sha256": hashlib.sha256(
            p["canonical_isomeric_smiles"].encode()).hexdigest(),
        "class": "out_of_domain",
        "facts": {
            "average_molecular_weight_g_mol": p["average_molecular_weight_g_mol"],
            "dual_role": False,
            "formula": p["formula"],
            "has_oxirane": False,
            "has_reactive_amine_hydrogen": False,
            "oxirane_ring_count": 0,
            "reactive_amine_hydrogen_count": 0,
        },
        "record_id": pid,
        "smiles": p["smiles"],
        "sources": SOURCES[key],
    })

v2 = dict(v1)
v2["fixture_id"] = "amphora-molecule-role-ranker-phase0-known-answer-2026-08-03-v2"
v2["schema"] = "amphora.molecule-role-ranker-phase0-known-answer.v2"
v2["records"] = v1["records"] + new_records
v2["supersedes"] = {
    "superseded_path": "amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json",
    "superseded_sha256": V1_LOCKED_SHA,
    "superseded_deleted_or_modified": False,
    "reason": (
        "R-N02 coordinated C=N categorical fix (repair_mode interactive-2026-08-03): "
        "the 39 v1 records are carried over byte-identical; 5 guanidine-class "
        "out_of_domain records (DPG CAS 102-06-7, DOTG CAS 97-39-2, guanidine CAS "
        "113-00-8, dicyandiamide CAS 461-58-5, biguanide CAS 461-71-2) are appended "
        "per the follow-ups of the two 2026-08-03 refuting receipts "
        "(amine-nh-guanidine-conjugation-gap-v1, role-guanidine-accelerator-domain-"
        "probe-v1) so the amidine/guanidine chemotype is regression-guarded going "
        "forward. Facts derive from the post-fix production RDKit FFI (bridge.cc "
        "count_reactive_amine_hydrogens with the amidine/guanidine-carbon exclusion). "
        "The v1 KPI arithmetic (1.0 on 39 records) stands -- v1 records are untouched "
        "by the bug; what R-N02 repairs is the generalization inference. The "
        "quantitative question whether guanidine N-H is exactly 0 in an AHEW sense "
        "stays explicitly OPEN; class assignments here are categorical only."
    ),
    "repair_item": "R-N02",
    "repair_mode": "interactive-2026-08-03",
}

out = json.dumps(v2, indent=2, sort_keys=True) + "\n"
V2.write_text(out)
print("WROTE", V2)
print("v2_sha256", hashlib.sha256(out.encode()).hexdigest())
print("n_records_v2", len(v2["records"]))
# verify v1 untouched and v1 records embedded byte-identically
assert hashlib.sha256(V1.read_bytes()).hexdigest() == V1_LOCKED_SHA
assert json.loads(V2.read_text())["records"][:39] == v1["records"]
print("v1_intact_and_embedded_identically", True)
