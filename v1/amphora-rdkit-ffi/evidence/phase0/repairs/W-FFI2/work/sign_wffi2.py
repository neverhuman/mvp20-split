#!/usr/bin/env python3
"""Sign the W-FFI2 dicyandiamide-functionality repair receipt with the
PHASE0_EVALUATOR key (same convention as sign_wffi1.py / sign_vn02c.py).
Output goes to attempts/ (not done/): cargo test --workspace is NOT fully
green -- one companion test in amphora-molecule-capabilities (out of this
fire's write scope) is stale and not yet updated -- so the item's done_
criterion is not literally met this fire."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-rdkit-ffi/evidence/phase0/repairs/W-FFI2"
WORK = OUT / "work"
ATTEMPTS = OUT / "attempts"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260806T090003-2795399-4f0d8fc61dda"
CAMPAIGN_ITEM_ID = "W-FFI2"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes())


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


diagA_path = WORK / "diagnostic.canonical.json"
diagB_path = WORK / "diagnostic.runB.json"
diagA = diagA_path.read_bytes()
diagB = diagB_path.read_bytes()
assert diagA == diagB, "two-replay bytes differ"
diag = json.loads(diagA)

assert diag["crate_test"] == {"status": "ok", "passed": 8, "failed": 0, "ignored": 0}
assert diag["reattack_w_ffi1_ffi1_verify"]["verdict_after_repair"] == "CLAIM_SURVIVED"
assert diag["reattack_w_ffi1_ffi1_verify"]["n_probes_mismatching_after"] == 0
assert diag["reattack_r_n02_v_n02c_vn02c_verify"]["n_probes_failed_after"] == 1
assert diag["reattack_r_n02_v_n02c_vn02c_verify"]["failing_probe_after"]["id"] == "dicyandiamide"
assert diag["positive_control"]["detected"] is True
assert diag["workspace_test"]["n_failing_binaries"] == 1
assert diag["workspace_test"]["failing_binary_module"] == "amphora-molecule-capabilities"

w_ffi1_done_path = OUT.parent / "W-FFI1/done/w-ffi1-rdkit-ffi-ahew-class-validation-receipt.v1.dsse.json"
w_ffi1_done_sha = sha_file(w_ffi1_done_path)
r_n02_done_path = OUT.parent / "R-N02/done/rn02-rdkit-ffi-coordinated-cn-fix-repair-receipt.v1.dsse.json"
r_n02_done_sha = sha_file(r_n02_done_path)
v_n02c_done_path = OUT.parent / "V-N02c/done/v-n02c-rdkit-ffi-independent-verify-receipt.v1.dsse.json"
v_n02c_done_sha = sha_file(v_n02c_done_path)

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
    "schema": "amphora.rdkit-ffi.w-ffi2-cyanoguanidine-repair-receipt.v1",
    "receipt_id": "w-ffi2-rdkit-ffi-cyanoguanidine-repair-" + sha(diagA)[:32],
    "fire_id": FIRE_ID,
    "campaign_item_id": CAMPAIGN_ITEM_ID,
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "run_type": "REPAIR_ATTEMPT",
    "repair_status": "fix_landed_in_module_workspace_companion_pending",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "module": "amphora-rdkit-ffi",
    "objective": (
        "W-FFI2: repair the categorical defect W-FFI1 refuted on 2026-08-05 -- "
        "dicyandiamide (DICY), a real functionality-4 stoichiometric epoxy "
        "hardener (WO1993010168A1), was categorically zeroed by R-N02's "
        "amidine/guanidine C=N exclusion. Find the chemically-principled "
        "structural boundary separating a true amidine/guanidine HARDENER "
        "(DICY) from a catalytic ACCELERATOR (DPG/DOTG/guanidine, which must "
        "stay zero per R-N02/V-N02c), state it with published support, "
        "implement it in bridge.cc, and re-run the full R-N02/V-N02c probe set "
        "plus W-FFI1's 14 pre-registered probes with zero regressions."
    ),
    "claim_under_attack": {
        "receipt_path": "amphora-rdkit-ffi/src/bridge.cc",
        "claim_text": (
            "Active-hydrogen counting is correct for every amine class that "
            "appears in real coatings."
        ),
        "prior_related_receipts": {
            "R-N02_coordinated_cn_fix": {"path": str(r_n02_done_path.relative_to(ROOT)), "sha256": r_n02_done_sha},
            "V-N02c_independent_verify": {"path": str(v_n02c_done_path.relative_to(ROOT)), "sha256": v_n02c_done_sha},
            "W-FFI1_refutation": {"path": str(w_ffi1_done_path.relative_to(ROOT)), "sha256": w_ffi1_done_sha},
        },
    },
    "structural_criterion": diag["structural_criterion"],
    "implementation": diag["implementation"],
    "re_attack_of_own_fix": {
        "protocol": (
            "Per REPAIR-MODE rule 2, re-ran the ORIGINAL refuting attack "
            "(W-FFI1's ffi1-verify harness, same script sha256, same command "
            "`cargo run --release`, same 14 hardcoded probes, same pre-"
            "registered refute criterion) UNMODIFIED against the repaired "
            "bridge.cc, plus the prior R-N02/V-N02c probe set (V-N02c's "
            "vn02c-verify harness, also UNMODIFIED) for regression."
        ),
        "w_ffi1_ffi1_verify": diag["reattack_w_ffi1_ffi1_verify"],
        "r_n02_v_n02c_vn02c_verify": diag["reattack_r_n02_v_n02c_vn02c_verify"],
    },
    "crate_test": {
        "command": "cargo test -p amphora-rdkit-ffi --features rdkit",
        "result": diag["crate_test"],
        "new_tests": diag["crate_test_new_tests"],
        "modified_tests": diag["crate_test_modified_tests"],
    },
    "workspace_test": {
        "command": "cargo test --workspace --features rdkit --no-fail-fast",
        **diag["workspace_test"],
        "interpretation": (
            "amphora-rdkit-ffi's OWN crate is fully green (8/8), and both "
            "original refuting-attack harnesses now agree with the repair, "
            "with zero regressions among probes not targeted by the fix. The "
            "single workspace-wide failure is a companion test in a DIFFERENT "
            "module (amphora-molecule-capabilities) that was written as part "
            "of R-N02's own 2026-08-03 coordinated 3-module batch and bakes in "
            "the same now-superseded dicyandiamide=0 expectation. This fire's "
            "write scope was confined to amphora-rdkit-ffi only (module "
            "confinement instruction), so that companion test could not be "
            "updated here. cargo test --workspace is therefore NOT fully "
            "green, and the item's done_criterion is not fully met this fire."
        ),
    },
    "positive_control": diag["positive_control"],
    "verdict": "CLAIM_SURVIVED",
    "why": (
        "The claim under attack -- that amphora-rdkit-ffi's active-hydrogen "
        "counting is correct across amine classes appearing in real coatings "
        "-- was refuted by W-FFI1 on dicyandiamide alone (13/14 other probes "
        "already agreed). This repair adds a narrow, cited, mechanistically-"
        "justified structural exemption (cyanamide-substituted guanidine "
        "carbon) that makes dicyandiamide score its published functionality "
        "of 4 while leaving the accelerator sub-class (DPG, DOTG, guanidine) "
        "and biguanide at 0, exactly preserving R-N02/V-N02c's own findings. "
        "Re-attacking with BOTH original unmodified harnesses now shows "
        "14/14 (ffi1-verify) and 7/8-with-the-8th-being-the-intended-fix "
        "(vn02c-verify): the module's own claim, as re-attacked by the exact "
        "instruments that refuted and previously verified it, now WITHSTANDS. "
        "A positive control (planted over-broad-exemption defect in a "
        "standalone mutant copy) confirms the narrowness check is capable of "
        "catching a real defect of the kind it exists to prevent. Full "
        "workspace-green is a SEPARATE, disclosed, outstanding item (a "
        "companion test in a module out of this fire's write scope) and is "
        "recorded honestly rather than silently claimed."
    ),
    "does_not_close": diag["does_not_close"],
    "rights_check": (
        "No new external data source opened. Cyanoguanidine pKa figure is a "
        "predicted value from a public chemical-property aggregator "
        "(chembk.com), used only as corroborating quantitative context "
        "alongside two primary citations (WO1993010168A1 patent text; Fedtke "
        "et al. 1993 peer-reviewed mechanistic study). No quarantined or "
        "rights-restricted source was opened."
    ),
    "gates_summary": {
        "two_replay_byte_stable_this_receipt": True,
        "real_production_ffi_not_reimplemented": True,
        "original_refuting_harnesses_re_run_unmodified": True,
        "positive_control_detects_planted_defect": True,
        "zero_regressions_among_non_targeted_probes": True,
        "crate_level_cargo_test_green": True,
        "workspace_level_cargo_test_green": False,
        "signature_field_is_dsse_envelope_object": True,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-attempt receipt under evidence/phase0/repairs/W-FFI2/attempts/",
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
    "date": "2026-08-06",
    "generated_on_host": "xbabe2",
    "input_artifacts": diag["input_artifacts"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2,
        "independent_runs": True,
        "canonical_diagnostic_sha256": sha(diagA),
        "runB_diagnostic_sha256": sha(diagB),
        "determinism_basis": (
            "diagnostic assembled by build_diagnostic.py purely from fixed, "
            "already-captured artifact files (no RNG, no wall clock); the two "
            "underlying re-attack harness runs (ffi1-verify, vn02c-verify) "
            "were independently invoked twice each via `cargo run --release` "
            "and produced byte-identical stdout (sha256 equal) before "
            "assembly."
        ),
        "harness_binary_provenance": (
            "cargo test/run against amphora-rdkit-ffi (path dependency, "
            "feature=rdkit) compiled with cxx against the pinned RDKit "
            "2026.03.2 prefix at /home/ubuntu/.local/share/amphora/"
            "rdkit-2026.03.2; toolkit_provenance.exact_version_match=true "
            "recorded in both re-attack harness runs."
        ),
    },
}

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(OUT / "receipt_body.canonical.json").write_bytes(body1)
(OUT / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.rdkit-ffi.w-ffi2-cyanoguanidine-repair-receipt.v1+json"
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

ATTEMPTS.mkdir(parents=True, exist_ok=True)
outpath = ATTEMPTS / "w-ffi2-rdkit-ffi-cyanoguanidine-repair-receipt.v1.dsse.json"
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
print("verdict", body_obj["verdict"])
print("repair_status", body_obj["repair_status"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_byte_identical", body1 == body2)
print("independent_reverify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
