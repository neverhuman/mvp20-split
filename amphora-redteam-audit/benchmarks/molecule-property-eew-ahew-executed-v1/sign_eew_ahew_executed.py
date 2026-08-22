#!/usr/bin/env python3
"""DSSE-Ed25519-sign the EEW/AHEW EXECUTED benchmark diagnostic with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f..., NOT trust-anchored).
Promotes nothing; modifies no existing receipt, manifest, census, split, or lock."""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

BENCH = Path("amphora-redteam-audit/benchmarks/molecule-property-eew-ahew-executed-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

canon = (BENCH/"diagnostic.canonical.json").read_bytes()
runB  = (BENCH/"diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
executor = (BENCH/"execute_eew_ahew_benchmark.py").read_bytes()

receipt = {
  "schema": "amphora.redteam-audit.replay-receipt.v1",
  "study_id": "MOLECULE_PROPERTY_EEW_AHEW_EXECUTED_V1",
  "authority": "AUDIT_ONLY",
  "promotes_nothing": True,
  "modifies_no_live_config": True,
  "claim": "The amphora-molecule-property Phase-0 EEW/AHEW benchmark, whose immutable "
           "2026-07-22 evaluation.v1.dsse.json is FAILED with SCIENTIFIC_BENCHMARK_NOT_EXECUTED "
           "(root cause: the Rust runner reported backend_status.available=false / "
           "pinned_rdkit_2026_03_2_available=false, so exact_controls_executed=0), was executed "
           "here under the pinned RDKit 2026.03.2 backend. Every scientific gate the failed result "
           "listed false now PASSES: the three in-scope exact coating-chemistry anchors "
           "(DGEBA EEW=170.2, DETA AHEW=20.6, IPDA AHEW=42.6 g/eq) reproduce to a max abs error of "
           "0.0338 g/eq (bar 0.5); 6/6 monodisperse records within 6.0 g/eq; 3/3 technical-grade "
           "DGEBA EEW lower-bound directional; 5/5 negative controls correctly parsed/rejected; and "
           "the frozen 300-molecule ChEBI-252 CC-BY truth set reproduces 300/300 molecular formula, "
           "300/300 full InChIKey, 300/300 stored RDKit average MW, with 299/300 (99.67%) agreement "
           "vs independent PubChem PUG-REST MW at <=0.05 g/mol. Conclusion: the benchmark FAILURE was "
           "purely a missing-backend infrastructure gap, NOT a scientific deficiency.",
  "all_gates_pass": diag["all_gates_pass"],
  "gates": diag["gates"],
  "kpi": {
    "exact_anchor_max_abs_error_g_per_eq": diag["exact_controls"]["max_abs_error_g_per_eq"],
    "exact_anchor_count": diag["exact_controls"]["n"],
    "monodisperse_hit_rate": diag["monodisperse"]["hit_rate"],
    "monodisperse_mae_g_per_eq": diag["monodisperse"]["mae_g_per_eq"],
    "technical_grade_directional_accuracy": diag["technical_grade"]["directional_accuracy"],
    "negative_control_pass_rate": diag["negative_controls"]["pass_rate"],
    "truthset_formula_reproduced": diag["truth_set_identity"]["formula_exact"],
    "truthset_inchikey_full_reproduced": diag["truth_set_identity"]["inchikey_full_exact"],
    "truthset_pubchem_mass_agreement_rate": diag["truth_set_identity"]["pubchem_mass_agreement_rate"],
    "rdkit_version": diag["rdkit_version_detected"],
  },
  "in_scope_chemistry": "Two-part epoxy-amine coating stoichiometry: DGEBA epoxide equivalent "
                        "weight (EEW) and aliphatic/cycloaliphatic amine hydrogen equivalent weight "
                        "(AHEW) for DETA and IPDA hardeners. Theory: EEW=MW/epoxide_groups, "
                        "AHEW=MW/active_amine_NH. Amide/aromatic/wildcard N excluded.",
  "diagnostic_sha256": sha(canon),
  "two_replay_gate": {"canonical_sha256": sha(canon), "runB_sha256": sha(runB), "byte_identical": canon == runB},
  "input_artifacts": {
    "eew_ahew_benchmark.v1.json_sha256": diag["benchmark_data_sha256"],
    "coating_truthset_300.v1.json_sha256": diag["truthset_sha256"],
    "execute_eew_ahew_benchmark.py_sha256": sha(executor),
  },
  "maps_to_module_failed_gates": diag["maps_to_module_failed_gates"],
  "promotion_blocked_by": "NOT this benchmark's science (all gates pass) and NOT key custody. The "
    "live blocker is a state-machine lock: the immutable signed 2026-07-22 evaluation.v1.dsse.json "
    "(phase0_eligible=false, scientific_outcome=FAILED) already exists; evaluate() refuses when a "
    "receipt exists and reissue() is forbidden after evaluation. Promotion to a real science Phase-0 "
    "needs a deliberate keyed supersession + bundle re-freeze + evaluate/review/promote, plus wiring "
    "the ChEBI source eligible in the census, embedding an independent_toolkit_receipt, wiring the "
    "pinned RDKit backend INTO the Rust benchmark runner (LD_LIBRARY_PATH / rpath / FFI so "
    "backend_status.available=true in-runner), and adding >=8 SEALED_CONTROL split rows. Deferred "
    "from autonomous cron to avoid a locked/half-wired state before the founder report. This receipt "
    "de-risks that supersession by proving the executed benchmark passes.",
  "red_team_findings": [
    "The raw ChEBI `smiles` field in coating_truthset_300.v1.json carries aromatic-tautomer forms "
    "(e.g. ring nc(=O)) that RDKit's default sanitizer rejects for 25/300 records; the build/identity "
    "field is `canonical_smiles`. A first pass that parsed `smiles` mis-reported 275/300 parse and 16 "
    "stereo-layer InChIKey mismatches. Using `canonical_smiles` the prior chebi-truthset-built '300/300' "
    "claim is confirmed. Recommend the truth-set schema flag canonical_smiles as the authoritative field.",
    "The prior chebi-truthset InChIKey cross-check compared ChEBI vs PubChem InChIKey (source consensus); "
    "this receipt additionally confirms RDKit REGENERATES the identical full InChIKey from canonical_smiles "
    "for 300/300 (stronger reproducibility claim).",
  ],
  "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"], "public_key_hex": PUB["public_key_hex"],
                  "trust_anchored": False, "note": "NOT in config/phase0-trust-store.v1.json; audit evidence only"},
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
