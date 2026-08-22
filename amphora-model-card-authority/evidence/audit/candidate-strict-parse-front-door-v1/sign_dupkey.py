#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-model-card-authority
candidate-strict-parse-front-door-v1 AUDIT_ONLY receipt. AUDIT_ONLY: signs an
audit receipt under evidence/audit/; does NOT sign a phase0 evaluation/review,
does NOT promote authority, does NOT flip scientific_readiness, does NOT
modify the portfolio manifest (66 receipts / 11 modules), the
module-manifest.json, any locked dataset, or a signed Phase-0 KPI. Derived
key_id cross-checked vs pinned trust store."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-model-card-authority/evidence/audit/candidate-strict-parse-front-door-v1"
KPI = ROOT / "amphora-model-card-authority/evidence/audit/live-runtime-envelope-parity-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

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

canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

path1 = diag["path1_real_strict_front_door_parse_json_strict"]
path2 = diag["path2_kpi_methodology_lenient_parse_then_score_campaign_modules"]
assert path1["is_err"] is True, "strict front door unexpectedly accepted the duplicate key -- refusing to sign a false claim"
assert "duplicate JSON key" in path1["display"]
assert path2["score_campaign_modules_outcome"]["ok"] is True, "expected the KPI methodology path to silently accept"
assert path2["lenient_parse_which_candidate_type_won"] == "formulation"

probe_main_rs = (BENCH / "probe/src/main.rs").read_bytes()
probe_cargo_toml = (BENCH / "probe/Cargo.toml").read_bytes()
kpi_probe_main_rs = (KPI / "runtime_probe/src/main.rs").read_bytes()
kpi_run_live_parity_py = (KPI / "run_live_parity.py").read_bytes()
kpi_receipt = (KPI / "live-runtime-envelope-parity-receipt.v1.dsse.json").read_bytes()
amphora_core_contract_rs = (ROOT / "amphora-core/src/contract.rs").read_bytes()
amphora_engine_lib_rs = (ROOT / "amphora-engine/src/lib.rs").read_bytes()

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.model-card-authority.candidate-strict-parse-front-door-receipt.v1",
    "study_id": "amphora-model-card-authority-candidate-strict-parse-front-door-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "live_rust_differential_probe",
    "module": "amphora-model-card-authority",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_module_manifest": False,
    "modifies_locked_dataset": False, "modifies_signed_phase0_kpi": False,
    "claim_under_attack": {
        "quote": (
            "Every candidate enters through the strict candidate-contract "
            "front door exactly as a hostile caller would exercise it."
        ),
        "source_file": "amphora-model-card-authority/evidence/audit/live-runtime-envelope-parity-v1/runtime_probe/src/main.rs",
        "source_file_sha256": sha(kpi_probe_main_rs),
        "carried_by_receipt": "amphora-model-card-authority/evidence/audit/live-runtime-envelope-parity-v1/live-runtime-envelope-parity-receipt.v1.dsse.json",
        "carried_by_receipt_sha256": sha(kpi_receipt),
        "carried_by_kpi": "amphora-model-card-authority-phase0-live-runtime-envelope-parity-v1",
        "carried_by_kpi_ledger_verdict": "SURVIVED (fire 20260804T130003-1196944-c7d3f6deb911)",
    },
    "purpose": (
        "Test whether the live-runtime-envelope-parity-v1 KPI's own ground-truth "
        "probe actually exercises amphora-model-card-authority's real scoring "
        "path 'as a hostile caller would', specifically with respect to the "
        "strict duplicate-JSON-key front door (amphora_core::parse_json_strict / "
        "StrictSeed) that amphora-core ships specifically to close RFC 8259's "
        "implementation-defined duplicate-key ambiguity."
    ),
    "hypothesis": (
        "H0: a raw candidate payload containing a duplicate 'candidate_type' "
        "object key is rejected identically whether it is scored through the "
        "documented strict front door or through the KPI's own probe "
        "methodology, because the probe's docstring asserts entry is 'exactly "
        "as a hostile caller would exercise it'."
    ),
    "method": (
        "A single fixed raw-bytes candidate (embedded verbatim in probe/src/main.rs, "
        "sha256 of the source file below) encodes the JSON object key "
        "'candidate_type' TWICE -- first 'evidence_package', then 'formulation' "
        "-- both payload shapes ('evidence_refs' and 'formulation') present so "
        "no incidental payload-mismatch confounds the result. The SAME fixed "
        "bytes are fed through two REAL, live-linked paths in one binary: "
        "(1) amphora_core::parse_json_strict (the function CandidateEnvelope::"
        "from_bytes actually calls -- the true byte-level front door); "
        "(2) plain serde_json::from_slice (what live-runtime-envelope-parity-v1's "
        "own run_live_parity.py / runtime_probe/src/main.rs actually do to read "
        "their corpus) followed immediately by the REAL "
        "EnginePool::score_campaign_modules, unmodified, with amphora-model-"
        "card-authority as the sole requested module. No candidate contract "
        "or engine logic is re-implemented; both paths link the real crates. "
        "Executed twice (two-replay) with zero randomness, zero clock, zero "
        "filesystem writes, for a byte-stability gate."
    ),
    "results": {
        "two_replay_byte_identical": canon == runB,
        "path1_real_strict_front_door": path1,
        "path2_kpi_methodology_probe_equivalent": path2,
        "refutation_criterion": (
            "H0 is refuted if path1 rejects the duplicate key (is_err=true, "
            "'duplicate JSON key' in the display string) while path2 (the "
            "exact mechanism the KPI's own probe uses) accepts it (ok=true) "
            "with no error and no divergence flagged by any g0-g5 gate."
        ),
        "refutation_criterion_occurred": True,
        "verdict": "CLAIM_REFUTED",
        "what_is_refuted": (
            "The specific methodological claim in live-runtime-envelope-parity-v1's "
            "own probe docstring -- that its ground truth is captured 'exactly "
            "as a hostile caller would exercise it' via 'the strict candidate-"
            "contract front door' -- is false. The probe's corpus reader uses "
            "serde_json's default (lenient, implementation-defined last-key-wins) "
            "parser and hands the result to CandidateEnvelope::from_value, which "
            "never calls parse_json_strict. A hostile caller submitting the "
            "identical bytes to the real byte-level front door "
            "(CandidateEnvelope::from_bytes) would be rejected with 'duplicate "
            "JSON key: candidate_type'; the same bytes silently resolve to "
            "'formulation' (last key) and score successfully via the KPI's own "
            "tested code path. Every one of the KPI's g0-g5 gates would report "
            "PASS on this input because none of them distinguish `from_bytes` "
            "from `from_value` entry -- the KPI has no gate capable of detecting "
            "this class of divergence at all."
        ),
        "scope_and_what_is_not_refuted": (
            "This does NOT demonstrate an authority escalation for "
            "amphora-model-card-authority itself: source review of "
            "TrustCapability::evaluate (amphora-engine/src/lib.rs) confirms the "
            "module's own scoring branch for the literal project string "
            "'amphora-model-card-authority' is a hardcoded default arm "
            "(ModuleResult::quarantined(...)) that inspects neither "
            "candidate_type content nor candidate payload content -- it is "
            "identical for the winning 'formulation' key or a hypothetical "
            "'evidence_package' win, and usable_by_optimizer / ranking_eligible "
            "/ granted_level are all descriptor-derived constants never read "
            "from candidate JSON, so no client-controlled field (duplicate-key "
            "or otherwise) can raise this module's own granted authority. What "
            "is refuted is narrower and still real: the KPI's claim that its "
            "differential-testing methodology equals a hostile caller's real "
            "entry point, and the KPI's blindness to this entire class of "
            "duplicate-key divergence which amphora-core visibly built defenses "
            "against elsewhere in the same crate."
        ),
        "proposed_followup": (
            "run_live_parity.py should read live_corpus.v1.json's 'candidate' "
            "sub-objects through amphora_core::parse_json_strict (via a small "
            "FFI/CLI shim, since the corpus is authored as Python JSON) rather "
            "than construct Values purely in Python/serde_json's default parser, "
            "OR the KPI should add a g6 gate asserting CandidateEnvelope::"
            "from_bytes and CandidateEnvelope::from_value agree on every corpus "
            "case's raw serialized bytes. Either closes the blind spot; neither "
            "is done by this receipt."
        ),
    },
    "runtime_source_anchors": {
        "amphora-core/src/contract.rs": sha(amphora_core_contract_rs),
        "amphora-engine/src/lib.rs": sha(amphora_engine_lib_rs),
        "probe/src/main.rs": sha(probe_main_rs),
        "probe/Cargo.toml": sha(probe_cargo_toml),
        "attacked_kpi_probe_main_rs": sha(kpi_probe_main_rs),
        "attacked_kpi_run_live_parity_py": sha(kpi_run_live_parity_py),
    },
    "provenance": {
        "module_manifest_sha256": sha((ROOT / "module-manifest.json").read_bytes()),
        "cargo_target_dir": "/tmp/amphora-mca-dupkey-probe-target (scratch, outside workspace)",
        "dependencies_pinned_path": ["../../../../../amphora-core", "../../../../../amphora-engine"],
        "no_workspace_membership": True,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "probe_main_rs_sha256": sha(probe_main_rs),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.model-card-authority-candidate-strict-parse-front-door+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "candidate-strict-parse-front-door-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
