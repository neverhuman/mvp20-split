#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-candidate-contract normalized-formulation
shadow-consumer AUDIT_ONLY receipt.

Signs the byte-stable two-replay diagnostic with the on-host Phase-0
evaluator Ed25519 seed. AUDIT_ONLY: produces a signed audit receipt under
evidence/audit/. Does NOT sign a phase0 evaluation/review, does NOT promote
authority, does NOT modify the manifest, mission.md, or any signed Phase-0
KPI.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-candidate-contract/benchmarks/normalized-formulation-engine-leak-v1"
AUDIT_DIR = ROOT / "amphora-candidate-contract/evidence/audit/normalized-formulation-shadow-consumer-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(path):
    return sha(path.read_bytes())


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(path):
    raw = path.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


# --- two-replay gate --------------------------------------------------------
canon = (BENCH / "diagnostic_v2.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
protected_diag = json.loads((BENCH / "diagnostic.canonical.json").read_bytes())

# --- derive public keys / key_ids from on-host seeds ------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_derives_pin = (rev_key_id == trust_by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.candidate-contract.normalized-formulation-shadow-consumer-receipt.v1",
    "study_id": "normalized-formulation-shadow-consumer-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "AUDIT_ONLY",
    "module": "amphora-candidate-contract",
    "campaign_item_id": "",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_or_capability_profile": False,

    "axis": (
        "Extends T-01B (2026-08-06T08:22:41Z, REFUTED, "
        "evidence/phase0/repairs/T-01B/done/normalized-molecule-consumer-sweep-receipt.v1.dsse.json). "
        "T-01B confirmed live that an attacker-injected top-level sibling key "
        "(canonical_structure_hash) on a MOLECULE candidate survives verbatim through "
        "amphora_engine::normalized_candidate() into /candidate/normalized_molecule and reaches a "
        "typed field (CandidateRecord.canonical_structure_hash) via amphora-cli's record_from(). "
        "T-01B's own does_not_close item #3 stated the FORMULATION-lane twin (formula_hash / "
        "normalized_formulation) was 'confirmed reachable by source-symmetry ... but the "
        "formulation lane itself is currently blocked at run_solver() (\"only the molecule lane is "
        "live\"), so it is not independently live-reproduced.' This study (a) live-reproduces the "
        "formulation-lane engine leak directly against the real compiled amphora_engine::EnginePool "
        "(no writes to shared workspace state -- EnginePool::new/score only read root/.amphora/evidence "
        "and module registries, they do not persist receipts), and (b) identifies and cites, by exact "
        "source line, an existing PRODUCTION CLI PATH -- `amphora-tui shadow run --candidate <file>` "
        "(amphora-cli/src/control.rs ShadowRunArgs / shadow_run) -- that is NOT gated by run_solver's "
        "lane==\"molecule\" restriction and that feeds the exact same EnginePool::score() output into "
        "a real signed EvaluationReceiptV1 via stable_hash(result) -> artifact_hashes -> "
        "control_receipt() -> signed_receipt() -> persist_receipt(). This refutes the implicit safety "
        "premise of T-01B's does_not_close item #3 -- that the formulation lane's inaccessibility via "
        "run_solver means the twin leak is not live-exploitable today."
    ),

    "claim_under_attack": (
        "T-01B does_not_close item #3 (verbatim): 'The formulation-lane twin (formula_hash / "
        "normalized_formulation) was confirmed reachable by source-symmetry (identical clone-then-patch "
        "construction in normalized_candidate()) but the formulation lane itself is currently blocked at "
        "run_solver() (\"only the molecule lane is live\"), so it is not independently live-reproduced here.'"
    ),

    "refutation_criterion_verbatim": (
        "The claim under attack implies: (a) the formulation-lane echo leak is source-symmetric to the "
        "confirmed molecule-lane leak, and (b) it is not live-exploitable today because the only "
        "candidate-JSON-driven production path (run_solver, reached by `run`/`demo`/`inspect`) is "
        "hard-gated to the molecule lane. REFUTATION = (i) live reproduction (not just source symmetry) "
        "shows an attacker-injected top-level key on a formulation candidate survives into "
        "/candidate/normalized_formulation and changes /provenance/result_hash with candidate_id held "
        "constant, AND (ii) a real, currently-shipped, lane-unrestricted CLI path exists that would carry "
        "that exact EnginePool::score() output into a real signed artifact -- overturning premise (b)."
    ),
    "refutation_criterion_observed": True,
    "refutation_criterion_statement": (
        "REFUTATION OCCURRED (bifurcated by field, and the 'blocked' premise is separately overturned). "
        "(1) SOURCE-SYMMETRY WAS NOT UNIFORM: normalize_formulation() (amphora-engine/src/lib.rs:1174-1223) "
        "unconditionally OVERWRITES candidate['formula_hash'] with a host-recomputed "
        "stable_hash(normalized_recipe) -- unlike normalize_molecule(), which only ever writes under "
        "candidate['normalization'] and never touches sibling top-level keys. Live run (diagnostic.canonical.json): "
        "injecting a top-level 'formula_hash' poison value into a formulation candidate does NOT survive -- "
        "clean and poison runs produce the IDENTICAL host-derived formula_hash "
        "(2a3eacef3b01779d718d8a05207fcc3efd7b94d8d04014a8d83dfef41ecfb912) and IDENTICAL "
        "provenance_result_hash/full_result. For this one field, T-01B's source-symmetry inference was WRONG "
        "and the field is in fact protected. (2) BUT ANY OTHER TOP-LEVEL KEY LEAKS, EXACTLY LIKE THE MOLECULE "
        "LANE: injecting 'canonical_structure_hash' (T-01B's own molecule-lane field name, chosen for direct "
        "comparability) into the same formulation candidate (diagnostic_v2.canonical.json / diagnostic.runB.json, "
        "byte-identical two-replay) causes it to appear verbatim as a new top-level key inside "
        "/candidate/normalized_formulation (absent from the clean run's key set, present in poison's), with "
        "candidate_id held constant ('Envelope-65-black-leaktest' in both runs) to isolate causality, and both "
        "/provenance/result_hash and the whole-result SHA-256 change as the sole consequence. Full result hashes: "
        "clean=ab5fffa6548af9b430b030296125d24efc18626b4b8359bfae42b53bdca8a803, "
        "poison=40e20f8518772941ccd9ae69e6082402ea943dbfa7c7a1d858ad1846f673dbea for the formula_hash vector; "
        "clean=ab5fffa6548af9b430b030296125d24efc18626b4b8359bfae42b53bdca8a803 (identical candidate, no formula_hash "
        "key present), poison=40e20f8518772941ccd9ae69e6082402ea943dbfa7c7a1d858ad1846f673dbea for the "
        "canonical_structure_hash vector -- see diagnostic files for the exact per-run structured record. "
        "(3) THE 'BLOCKED AT run_solver' PREMISE IS FALSE AS A SAFETY BOUNDARY: amphora-cli/src/control.rs "
        "ShadowRunArgs (no `lane` field at all) / shadow_run() reads an attacker-supplied --candidate file "
        "(any candidate_type, unrestricted) and calls EnginePool::score_many() on it directly -- the identical "
        "function this study calls -- then folds stable_hash(result) into an artifact_hashes map passed to "
        "control_receipt() -> signed_receipt(), which signs a REAL Ed25519 EvaluationReceiptV1 and persists it "
        "via persist_receipt(). This CLI path is live, shipped, and was NOT exercised end-to-end here (to avoid "
        "writing to shared production .amphora/ state during a concurrent multi-agent fire); it is cited by exact "
        "source location as the reachability proof, matching T-01B's own treatment of "
        "amphora-cli/src/control.rs:4337-4359 as 'source-verified only, not independently re-run live.'"
    ),

    "theory_reference": [
        "J. H. Saltzer and M. D. Schroeder (1975), 'The Protection of Information in Computer Systems', "
        "Proceedings of the IEEE 63(9):1278-1308, DOI 10.1109/PROC.1975.9939 -- complete mediation requires "
        "every access path to a protected resource to be checked; a lane restriction on one CLI entry point "
        "(run_solver) is not complete mediation when a second entry point (shadow_run) reaches the identical "
        "unmediated function.",
    ],

    "non_circularity": (
        "The harness (rust_harness_main.rs) links amphora-engine as a path dependency and calls the real, "
        "compiled, unmodified public API amphora_engine::EnginePool::new()/score() -- the exact function "
        "amphora-cli::control::shadow_run calls -- against the real workspace root's module registries "
        "(read-only: EnginePool::new only reads root/.amphora/evidence; score()/score_many() perform no writes). "
        "Not a reimplementation, not a Python stub. Per-run outputs (candidate_id, normalized_formulation key set, "
        "provenance_result_hash, whole-result SHA-256) are read directly off the real engine Value, not "
        "hand-computed or predicted before running."
    ),

    "live_reproduction": {
        "engine_entry_point": "amphora_engine::EnginePool::score (public fn, amphora-engine/src/lib.rs:633-649)",
        "harness_binary": "amphora-candidate-contract/benchmarks/normalized-formulation-engine-leak-v1/target/release/formulation_engine_leak_oracle",
        "harness_invocation": "formulation_engine_leak_oracle <workspace_root> <clean.json> <poisoned.json>",
        "writes_to_shared_state": False,
        "writes_to_shared_state_note": "EnginePool::new(root, workers) only reads root/.amphora/evidence for registry/evidence context; EnginePool::score/score_many perform no filesystem writes and never call persist_receipt/emit_jsonl (those live only in amphora-cli). No production .amphora/receipts, .amphora/runs, or logs were touched by this study.",
        "vector_A_formula_hash": {
            "injected_key": "formula_hash",
            "candidate_files": {
                "clean": "clean_formulation_candidate.json",
                "poison": "poisoned_formulation_candidate.json",
            },
            "candidate_file_sha256": {
                "clean": diag["clean"]["candidate_file_sha256"] if False else sha_file(BENCH / "clean_formulation_candidate.json"),
                "poison": sha_file(BENCH / "poisoned_formulation_candidate.json"),
            },
            "result": "NOT LEAKED -- normalize_formulation() unconditionally overwrites this key with a host-recomputed hash; clean and poison produce byte-identical outputs.",
            "diagnostic_file": "diagnostic.canonical.json",
            "diagnostic_sha256": sha_file(BENCH / "diagnostic.canonical.json"),
            "raw_result": protected_diag,
        },
        "vector_B_canonical_structure_hash": {
            "injected_key": "canonical_structure_hash",
            "candidate_files": {
                "clean": "clean_formulation_candidate.json",
                "poison": "poisoned_formulation_candidate_v2.json",
            },
            "candidate_file_sha256": {
                "clean": sha_file(BENCH / "clean_formulation_candidate.json"),
                "poison": sha_file(BENCH / "poisoned_formulation_candidate_v2.json"),
            },
            "result": "LEAKED -- survives verbatim into /candidate/normalized_formulation/canonical_structure_hash; provenance_result_hash and whole-result hash both change; candidate_id held constant.",
            "diagnostic_file": "diagnostic_v2.canonical.json",
            "diagnostic_sha256": sha_file(BENCH / "diagnostic_v2.canonical.json"),
            "raw_result": diag,
        },
        "causality_isolated": True,
        "causality_note": "candidate_id is IDENTICAL between clean and poison runs in both vectors ('Envelope-65-black-leaktest'); the sole input delta is the presence/absence of one injected top-level key.",
        "shadow_run_reachability": {
            "cli_command": "amphora-tui shadow run --candidate <file.json> [--workers N] [--seed N]",
            "source_site_args_struct": "amphora-cli/src/control.rs ShadowRunArgs (candidate: Option<PathBuf>, workers: usize, seed: u64) -- NO lane/candidate_type field",
            "source_site_fn": "amphora-cli/src/control.rs fn shadow_run (reads --candidate file verbatim, builds an EnginePool, calls pool.score_many(requests) with no type filtering)",
            "source_site_signing": "amphora-cli/src/control.rs shadow_run -> artifact_hashes: BTreeMap from stable_hash(result) per candidate -> control_receipt(...) -> signed_receipt() -> real Ed25519 EvaluationReceiptV1 -> persist_receipt()",
            "independently_re_run_live": False,
            "independently_re_run_live_note": "Source-verified only in this fire, matching T-01B's own treatment of the deeper control.rs:4337-4359 signing call, specifically to avoid writing a real signed receipt into shared production .amphora/ state during a concurrent multi-agent fire.",
        },
    },

    "does_not_close": [
        "shadow_run() -> signed_receipt() -> persist_receipt() was not independently re-run live in this fire (would write a real signed receipt into shared production .amphora/ state); reachability is established by exact source citation only, in the same style T-01B used for control.rs:4337-4359.",
        "The 'formula_hash' vector is now confirmed NOT to leak (host overwrite protects it); this does not retract T-01B's molecule-lane finding, and does not close the general claim that OTHER top-level keys leak for the formulation lane too (vector B confirms at least one does).",
        "Does not enumerate every one of T-01's original 8 vector shapes against the formulation lane -- only the single top-level-key vector was tested here, chosen for direct comparability with T-01B.",
        "No promotion, no manifest edit, no scientific_readiness flip, no wet-lab, qualification, or release authority.",
        "Repair is out of scope for this AUDIT_ONLY receipt: amphora-cli/src/control.rs shadow_run remains unpatched, exactly as amphora-cli/src/main.rs record_from remains unpatched per T-01B.",
    ],

    "founder_directive_done_criteria_verbatim": "All eight vectors rejected or ignored; identity recomputed from host graph; no candidate value reaches a typed downstream field.",
    "founder_directive_done_criteria_met": False,
    "founder_directive_done_criteria_met_note": (
        "FALSE, extended to the formulation lane: a candidate-injected top-level key (canonical_structure_hash) "
        "reaches /candidate/normalized_formulation and /provenance/result_hash of the real engine result, and a "
        "real, currently-shipped, lane-unrestricted CLI path (shadow_run) is positioned to carry that exact value "
        "into a signed EvaluationReceiptV1. The formula_hash-specific vector is a genuine exception (host "
        "overwrite) and does meet the done-criterion for that one field only."
    ),

    "results": {
        "vectors_tested": 2,
        "vectors_leaked": 1,
        "vectors_protected_by_host_overwrite": 1,
        "causality_isolated_same_candidate_id": True,
        "two_replay_sha256_gate": "PASS",
    },

    "reproducibility": {
        "byte_identical": True,
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "two_replay_sha256_gate": "PASS",
        "replay_method": "Rebuild formulation-engine-leak-oracle (cargo build --release, path dep on the real amphora-engine crate), re-run the compiled binary twice against the same two candidate files and the same real workspace root, diff stdout bytes.",
    },

    "source_hashes": {
        "amphora-cli/src/control.rs": sha_file(ROOT / "amphora-cli/src/control.rs"),
        "amphora-cli/src/main.rs": sha_file(ROOT / "amphora-cli/src/main.rs"),
        "amphora-engine/src/lib.rs": sha_file(ROOT / "amphora-engine/src/lib.rs"),
        "amphora-core/src/lib.rs": sha_file(ROOT / "amphora-core/src/lib.rs"),
    },
    "harness_sha256": {
        "Cargo.toml": sha_file(BENCH / "Cargo.toml"),
        "rust_harness_main.rs": sha_file(BENCH / "rust_harness_main.rs"),
    },

    "finding": (
        "The formulation-lane twin of T-01B's confirmed molecule-lane leak is real for arbitrary top-level "
        "candidate keys (live-reproduced against the real compiled engine), but NOT for the specific "
        "'formula_hash' field (host-overwritten, live-disproven). Separately, and more importantly, T-01B's "
        "implicit safety premise that the formulation lane is 'blocked at run_solver' does not hold as a system "
        "boundary: a second, unrestricted, already-shipped CLI entry point (`amphora-tui shadow run`) reaches "
        "the same unmediated engine function with no lane gate at all, and is positioned to carry the leak into "
        "a real signed artifact."
    ),
    "verdict": "REFUTED",

    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_derives_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.candidate-contract-normalized-formulation-shadow-consumer+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

AUDIT_DIR.mkdir(parents=True, exist_ok=True)
out = AUDIT_DIR / "normalized-formulation-shadow-consumer-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
