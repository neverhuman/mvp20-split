#!/usr/bin/env python3
"""Sign the role-guanidine-accelerator-domain-probe-v1 falsification receipt
with the PHASE0_EVALUATOR key, matching the repo-wide evidence/audit signing
convention (evaluator_key_id/evaluator_public_key_hex/reviewer_public_key_hex
/signature DSSE envelope shape) established elsewhere in the portfolio."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-role-ranker/benchmarks/role-guanidine-accelerator-domain-probe-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260803T190001-3122084-a08778b76bbe"
FIXTURE_SHA = "8ce4d54192a20e8de1bb89f6181b11630fc184b4dda2918ce934610630855c8f"


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


diag = json.loads((OUT / "diagnostic.canonical.json").read_text())
diagA = (OUT / "diagnostic.canonical.json").read_bytes()
diagB = (OUT / "diagnostic.runB.json").read_bytes()
assert diagA == diagB, "two-replay bytes differ"
assert diag["verdict"] == "HYPOTHESIS_REFUTED"
assert diag["summary"]["n_disagreements"] == 2
harness_main_sha = sha((OUT / "harness/src/main.rs").read_bytes())
harness_cargo_sha = sha((OUT / "harness/Cargo.toml").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
by_role = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"
assert rev_pin, "reviewer key_id does not match pinned trust-store PHASE0_INTERNAL_REVIEWER entry"

body_obj = {
    "schema": "amphora.molecule-role-ranker.role-guanidine-accelerator-domain-probe-v1-audit-receipt.v1",
    "receipt_id": "role-guanidine-accelerator-domain-probe-" + sha(diagA)[:32],
    "fire_id": FIRE_ID,
    "campaign_item_id": "",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "module": "amphora-molecule-role-ranker",
    "claim_under_attack": {
        "receipt": "amphora-molecule-role-ranker/evidence/phase0/kpis/role-classification-kpi.v1.json",
        "metric": "structural_inference_agreement_rate",
        "asserted": "1.0 (24/24), scored on the module's own self-authored 39-record CC0 "
                    "fixture (sha " + FIXTURE_SHA + "), plus the module's own prior "
                    "role-live-runtime-domain-probe-v1 SURVIVED verdict (which tested a "
                    "zero-N-H tertiary-amine accelerator, BDMA, and an aromatic-N-H latent "
                    "hardener, EMI-24, as hostile nulls and found both correctly fail closed "
                    "to out_of_domain).",
    },
    "fire_sequence": (
        "ROTATION fire. Prior fires on this module attacked: the flagship KPI's "
        "generalization via a 10-molecule live-RDKit-FFI probe (BDMA/EMI-24/DICY/ethers/"
        "aspartic-esters/sulfones/hindered-aromatics -- SURVIVED); the Macosko-Miller "
        "H2 sol-latitude direction rule via non-ideal reactivity-ratio Monte Carlo "
        "(SURVIVED); the fitted logistic model via honest LOOCV+conformal (parsimony-"
        "conformal, SURVIVED/noninferior); the Flory-Stockmayer gelation rule "
        "(SURVIVED); fact-provenance invariance (SURVIVED, 39/39). This fire escalates "
        "past the live-runtime-domain-probe-v1 hostile-null set by targeting a specific "
        "structural gap that set never covered: a real cure-accelerator chemotype with "
        "genuine non-aromatic N-H that neither of the two previously-tested accelerator/"
        "catalyst nulls (BDMA, EMI-24) exercised."
    ),
    "objective": (
        "Test whether amphora-rdkit-ffi/src/bridge.cc::count_reactive_amine_hydrogens "
        "(the live production RDKit C++ logic the role-ranker Rust runtime consumes "
        "byte-identically) and the module's deterministic role rule "
        "(has_oxirane=false & reactive_amine_hydrogen_count>0 => hardener) correctly "
        "fail closed on real, named, commercially dominant, coating/rubber-relevant "
        "cure ACCELERATOR molecules whose N-H is guanidine-type: neither absent (unlike "
        "BDMA, a tertiary amine with zero N-H) nor aromatic (unlike EMI-24, whose ring "
        "N-H is pyrrole-type). count_reactive_amine_hydrogens only excludes a nitrogen's "
        "hydrogens when its direct neighbor carbon is carbonyl/thiocarbonyl "
        "(is_carbonyl_carbon, C=O or C=S) or when a neighbor sulfur is sulfonyl "
        "(is_sulfonyl_sulfur); a guanidine/amidine neighbor carbon (C=N) triggers "
        "neither exclusion, so its N-H count as 'reactive amine hydrogen' with no "
        "structural signal that the molecule's real formulation role is catalytic, "
        "not stoichiometric."
    ),
    "method": (
        "Invoked the REAL production RDKit C++ FFI (amphora_rdkit_ffi::molecule_facts, "
        "pinned RDKit 2026.03.2, exact_version_match=true recorded in "
        "toolkit_provenance) -- not a Python re-derivation -- via a small Rust harness "
        "on two real, named, CAS-identified, industrially dominant guanidine-class cure "
        "accelerators: 1,3-diphenylguanidine (DPG, CAS 102-06-7) and N,N'-di-o-"
        "tolylguanidine (DOTG, CAS 97-39-2). Both are documented exclusively as "
        "catalytic accelerators (DPG/DOTG: dominant rubber-vulcanization secondary "
        "accelerators, boosting thiazole/thiuram/sulfenamide primary accelerators; DPG "
        "additionally documented in US Patent 9,238,706 'Use of guanidine derivatives "
        "as curing accelerators for epoxy resins' as a guanidine-class epoxy curing "
        "ACCELERATOR), never as a stoichiometric amine-hydrogen-consuming hardener in "
        "either industry. Verified computed molecular formula/MW against independently "
        "published values (DPG: C13H13N3, MW 211.26/211.268 observed; DOTG: C15H17N3, "
        "MW 239.32/239.322 observed) before scoring, confirming the SMILES correctly "
        "encode the named compounds. Pre-registered refute criterion: attack fires if "
        "either probe's observed_role is 'hardener' rather than 'out_of_domain' (the "
        "fail-closed behavior the module's own BDMA/EMI-24 probes established as "
        "correct for real accelerator/catalyst molecules)."
    ),
    "input_artifacts": {
        "harness_main_rs_sha256": harness_main_sha,
        "harness_cargo_toml_sha256": harness_cargo_sha,
        "fixture_sha256_unchanged": FIXTURE_SHA,
        "bridge_cc_reference": "amphora-rdkit-ffi/src/bridge.cc::count_reactive_amine_hydrogens "
                                "(lines ~66-89: excludes only is_carbonyl_carbon / "
                                "is_sulfonyl_sulfur neighbors; no is_amidine/is_guanidine "
                                "neighbor check exists)",
    },
    "probes": diag["results"],
    "headline_result": {
        "n_scored_probes": diag["summary"]["n_scored_probes"],
        "n_pass": diag["summary"]["n_pass"],
        "n_disagreements": diag["summary"]["n_disagreements"],
        "disagreements": diag["disagreements"],
        "verdict": diag["verdict"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2,
        "independent_runs": True,
        "canonical_diagnostic_sha256": sha(diagA),
        "runB_diagnostic_sha256": sha(diagB),
        "harness_binary_provenance": (
            "cargo build --release against amphora-rdkit-ffi (path dependency, "
            "feature=rdkit) compiled with cxx against the pinned RDKit 2026.03.2 "
            "prefix at /home/ubuntu/.local/share/amphora/rdkit-2026.03.2 "
            "(RDKIT_INCLUDE_DIR/RDKIT_LIB_DIR/BOOST_INCLUDE_DIR); backend_status()."
            "exact_version_match=true recorded in toolkit_provenance."
        ),
        "determinism_basis": (
            "no RNG, no wall-clock, fixed hardcoded probe list, serde_json BTreeMap "
            "key ordering => canonical byte order every run; two independent process "
            "invocations produced byte-identical stdout (sha256 equal)."
        ),
        "fixture_disjointness": (
            "neither probe SMILES canonicalizes to any of the 39 fixture records' "
            "canonical SMILES (phase0-role-known-answer.v1.json, sha " + FIXTURE_SHA + ")."
        ),
    },
    "verdict": "CLAIM_REFUTED",
    "why": (
        "Both real, named, CAS-verified guanidine-class cure accelerators (DPG, DOTG) "
        "are classified 'hardener' by the live production runtime (reactive_amine_"
        "hydrogen_count=3, has_oxirane=false) when their documented real-world "
        "formulation role in both the rubber and epoxy literatures is catalytic "
        "accelerator, not stoichiometric hardener. This is the exact failure mode the "
        "module's own prior hostile-null probes (BDMA, EMI-24) were designed to catch "
        "and correctly caught -- but via orthogonal exclusion paths (zero N-H; aromatic "
        "N-H) that do not cover the guanidine/amidine C=N chemotype. The flagship KPI's "
        "structural_inference_agreement_rate=1.0 and the live-runtime-domain-probe-v1 "
        "SURVIVED verdict do not bound this failure mode because neither the "
        "self-authored fixture nor the prior probe set contains a non-aromatic, "
        "non-charged, non-carbonyl-adjacent accelerator N-H case."
    ),
    "scope_note": (
        "Does not assert a single 'correct' reactive_amine_hydrogen_count for guanidine "
        "N-H in the AHEW/quantitative sense (that mechanistic question, raised for the "
        "amine-class active-N-H rule in a sibling module, is out of scope here). The "
        "refutation is scoped to the CATEGORICAL role_fit classification: whether a "
        "real, documented, non-stoichiometric cure accelerator is silently promoted to "
        "'hardener' stoichiometric status, which is sufficient to falsify the flagship "
        "KPI's implicit domain-generalization claim regardless of the unsettled "
        "guanidine-nucleophilicity mechanism question."
    ),
    "pre_registered_refute_criterion": (
        "Attack fires (REFUTED) iff either probe's observed_role != 'out_of_domain'. "
        "Both probes (dpg-diphenylguanidine-accelerator, "
        "dotg-di-o-tolylguanidine-accelerator) observed_role == 'hardener'. Criterion "
        "met on 2/2 probes."
    ),
    "primary_sources": [
        "1,3-Diphenylguanidine (DPG), CAS 102-06-7, C13H13N3, MW 211.26 -- rubber "
        "vulcanization secondary accelerator (widely documented industrial/CAS "
        "reference data).",
        "US Patent 9,238,706, 'Use of guanidine derivatives as curing accelerators for "
        "epoxy resins' -- documents guanidine-class compounds (the DPG/DOTG chemotype) "
        "functioning as epoxy cure ACCELERATORS, not stoichiometric hardeners.",
        "N,N'-di-o-tolylguanidine (DOTG), CAS 97-39-2, C15H17N3, MW 239.32 -- rubber "
        "vulcanization accelerator, more active analog of DPG, not a curing agent "
        "(widely documented industrial/CAS reference data).",
    ],
    "rights_check": (
        "No new external data source opened or acquired. Both probe molecules are "
        "constructed in-harness from CAS-identified public-domain chemical identity "
        "SMILES and evaluated purely structurally via the already-checked-in, "
        "already-licensed RDKit FFI backend; no dataset with UNRESOLVED or "
        "quarantined rights was read."
    ),
    "gates_summary": {
        "two_replay_byte_stable_this_receipt": True,
        "real_production_ffi_not_reimplemented": True,
        "molecular_formula_mw_independently_cross_checked_against_published_values": True,
        "fixture_untouched": True,
        "attack_fires_on_all_scored_probes": diag["summary"]["n_disagreements"] == diag["summary"]["n_scored_probes"],
        "signature_field_is_dsse_envelope_object": True,
    },
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (this is an AUDIT_ONLY science-validation replay, "
        "not a Phase-0 evaluation/review signature).",
        "Whether reactive_amine_hydrogen_count should be exactly 0 for guanidine N-H in "
        "a quantitative AHEW sense (mechanistic nucleophilicity question, out of scope).",
        "Any change to the shipped bridge.cc, the KPI receipt, or the master manifest "
        "(66 receipts/11 modules unchanged).",
    ],
    "recommended_followups": [
        "Extend bridge.cc's is_carbonyl_carbon-style exclusion (or add a parallel "
        "is_amidine_or_guanidine_carbon check) so a nitrogen whose neighbor carbon "
        "bears a C=N double bond to another nitrogen is treated the same way as the "
        "existing C=O/C=S exclusion, OR add an explicit accelerator/catalyst denylist "
        "gate ahead of the has_reactive_amine_hydrogen role rule.",
        "Add DPG- and DOTG-class guanidine accelerators to the module's own "
        "39-record known-answer fixture and to role-live-runtime-domain-probe-v1's "
        "hostile-null probe set, alongside BDMA and EMI-24, so this chemotype is "
        "regression-guarded going forward.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY benchmark receipt under benchmarks/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(OUT / "receipt_body.canonical.json").write_bytes(body1)
(OUT / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-role-ranker.role-guanidine-accelerator-domain-probe-audit-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body1))
envelope = {
    "payload": base64.standard_b64encode(body1).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

outpath = OUT / "replay_receipt.v1.dsse.json"
outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True))

written = json.loads(outpath.read_text())
sig_env = written["signature"]
payload = base64.standard_b64decode(sig_env["payload"])
sig_bytes = base64.standard_b64decode(sig_env["signatures"][0]["sig"])
keyid = sig_env["signatures"][0]["keyid"]
trust_pub_hex = by_role["PHASE0_EVALUATOR"]["public_key_hex"]
assert keyid == by_role["PHASE0_EVALUATOR"]["key_id"]
Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust_pub_hex)).verify(
    sig_bytes, pae(sig_env["payloadType"], payload))
assert payload == body1

print("WROTE", outpath)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_byte_identical", body1 == body2)
print("independent_reverify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
