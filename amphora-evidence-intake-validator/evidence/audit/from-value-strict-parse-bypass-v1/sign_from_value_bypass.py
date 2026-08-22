#!/usr/bin/env python3
"""DSSE-Ed25519-sign the from-value-strict-parse-bypass-v1 AUDIT_ONLY receipt
for amphora-evidence-intake-validator. Does not modify the master manifest,
any locked dataset, the shipped Phase-0 KPI, or the runtime."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-evidence-intake-validator"
RECEIPT_ID = "from-value-strict-parse-bypass-v1"
AUDIT_DIR = MOD / "evidence/audit" / RECEIPT_ID
PROBE2_DIR = MOD / "evidence/audit/evaluate-evidence-intake-bomb-probe-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"

CONTRACT_RS = ROOT / "amphora-core/src/contract.rs"
CORE_LIB_RS = ROOT / "amphora-core/src/lib.rs"
ENGINE_RS = ROOT / "amphora-engine/src/lib.rs"
ASSURANCE_RS = ROOT / "amphora-assurance-capabilities/src/lib.rs"
SHIPPED_KPI = MOD / "evidence/phase0/kpis/evidence-intake-validator-host-receipt-integrity-kpi.v1.json"
MISSION = MOD / "docs/mission.md"


def sha(b): return hashlib.sha256(b).hexdigest()


def pae(t, body):
    tb = t.encode()
    return (b"DSSEv1 " + str(len(tb)).encode() + b" " + tb + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon1 = (AUDIT_DIR / "diagnostic.canonical.json").read_bytes()
runB1 = (AUDIT_DIR / "diagnostic.runB.json").read_bytes()
assert canon1 == runB1, "probe1 two-replay bytes differ"
diag1 = json.loads(canon1)
assert diag1["all_gates_passed"] is True

canon2 = (PROBE2_DIR / "diagnostic.canonical.json").read_bytes()
runB2 = (PROBE2_DIR / "diagnostic.runB.json").read_bytes()
assert canon2 == runB2, "probe2 two-replay bytes differ"
diag2 = json.loads(canon2)
assert diag2["all_gates_passed"] is True

contract_rs_sha = sha(CONTRACT_RS.read_bytes())
core_lib_rs_sha = sha(CORE_LIB_RS.read_bytes())
engine_rs_sha = sha(ENGINE_RS.read_bytes())
assurance_rs_sha = sha(ASSURANCE_RS.read_bytes())
shipped_kpi_sha = sha(SHIPPED_KPI.read_bytes())
mission_sha = sha(MISSION.read_bytes())
probe1_main_sha = sha((AUDIT_DIR / "runtime_probe/src/main.rs").read_bytes())
probe1_cargo_sha = sha((AUDIT_DIR / "runtime_probe/Cargo.toml").read_bytes())
probe2_main_sha = sha((PROBE2_DIR / "runtime_probe/src/main.rs").read_bytes())
probe2_cargo_sha = sha((PROBE2_DIR / "runtime_probe/Cargo.toml").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

body_obj = {
    "schema": "amphora.evidence-intake-validator.from-value-strict-parse-bypass-receipt.v1",
    "receipt_id": RECEIPT_ID,
    "module_id": "amphora-evidence-intake-validator",
    "campaign_item_id": "",
    "directive_ref": None,
    "directive_path": "none",
    "directive_sha256": "",
    "directive_obligation": None,
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-15",
    "generated_on_host": "xbabe2",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_shipped_runtime": False,
    "modifies_locked_dataset": False,
    "modifies_benchmark_lock": False,
    "modifies_signed_phase0_kpi": False,

    "claim_under_attack": (
        "docs/mission.md falsifiable hypothesis: 'byte hashing and manifest "
        "binding reject missing, mutated, unsigned, or overclaiming "
        "packages.' Mission also states 'Unsupported formats fail closed' "
        "and that 'Original bytes ... are retained' -- both stated as "
        "properties of the module's evidence-intake front door, not scoped "
        "to any single constructor. This is the strongest currently-standing "
        "claim for this module: five prior audits (host-receipt-oracle-"
        "parity-v1, predicate-completeness-v1, canonicalization-invariance-"
        "tamper-v1, receipt-authority-derivability-freshness-v1, and repairs "
        "V1-REAL-EIV/T-04/W-T-EIV) each already refuted a narrower "
        "sub-claim about host_receipt_valid's 11-field predicate; none of "
        "them touched the candidate-ingestion boundary (CandidateEnvelope::"
        "from_bytes vs from_value / parse_json_strict) that mission.md's "
        "'byte hashing ... reject ... overclaiming packages' and "
        "'Unsupported formats fail closed' sentences are actually about."
    ),

    "baseline": {
        "name": "amphora-core's own committed strict-parser contract",
        "citation": (
            "amphora-core/src/contract.rs (sha256 " + contract_rs_sha + "), "
            "function parse_json_strict + struct CandidateEnvelope, plus the "
            "module's own unit tests strict_parser_rejects_duplicate_and_"
            "escaped_duplicate_keys, strict_parser_rejects_invalid_utf8_and_"
            "excess_depth, and candidate_keeps_original_and_v1_hashes_"
            "separate (same file), which this receipt's G0 gate live-replays "
            "and confirms still hold."
        ),
    },

    "claim": (
        "STRUCTURAL/ENTRY-POINT VERDICT, established with two LIVE Rust "
        "probes linking the real amphora-core and amphora-assurance-"
        "capabilities crates (not a re-implementation, not a CPython "
        "re-derivation): amphora-core provides two CandidateEnvelope "
        "constructors with materially different guarantees. "
        "CandidateEnvelope::from_bytes(bytes) parses via parse_json_strict, "
        "which REJECTS duplicate JSON keys, JSON depth > MAX_JSON_DEPTH "
        f"({diag1['results']['max_json_depth']}), and JSON collections with "
        "more than MAX_COLLECTION_ENTRIES (100000) entries, and computes "
        "original_bytes_sha256 as a true hash of the caller's raw input "
        "bytes -- genuinely distinct from contract_hash_v1 for any two "
        "byte-different-but-semantically-equal encodings "
        f"({diag1['results']['g1b_divergences']}/{diag1['results']['g1_corpus_n']} "
        "reencodings probed diverge, live). CandidateEnvelope::from_value"
        "(value), by contrast, applies NONE of parse_json_strict's checks "
        "(it operates on a Value the caller already holds) and its "
        f"original_bytes_sha256 is PROVABLY, ALWAYS ({diag1['results']['g1_coincidences']}/"
        f"{diag1['results']['g1_corpus_n']} probed, live, plus a closed-form proof: "
        "both fields compute sha256(serde_json::to_vec(canonicalize(value))) "
        "-- see math_identity_confirmed) byte-identical to contract_hash_v1, "
        "so it carries zero independent byte-level signal; the 'two-hash "
        "separation' the crate's own unit test exists to verify never "
        "engages on this path. Static citation "
        f"(amphora-engine/src/lib.rs, sha256 {engine_rs_sha}, lines 567, "
        "629, 732): the real scoring entrypoint chain EnginePool::score / "
        "score_many / score_campaign_modules -> fn execute(...) -- the "
        "function mission.md itself names as owning 'runtime registration' "
        "and the function whose registry dispatch is what ultimately calls "
        "evaluate_evidence_intake/host_receipt_valid for candidate_type "
        "evidence_package -- calls CandidateEnvelope::from_value exclusively. "
        "There are zero calls to CandidateEnvelope::from_bytes or "
        "parse_json_strict anywhere in amphora-engine/src/lib.rs for "
        "candidate ingestion (parse_json_strict is called only for the "
        "static module-manifest and evidence-context bytes, lines 172, 950, "
        "951 -- never for a scored candidate). The second, END-TO-END LIVE "
        "probe (evaluate-evidence-intake-bomb-probe-v1, sha256 of its "
        f"diagnostic {sha(canon2)}) confirms the consequence directly "
        "against the REAL predicate: constructing an evidence_package "
        f"candidate via from_value whose payload nests {diag2['results']['depth_bomb_depth_probed']} "
        f"levels deep (MAX_JSON_DEPTH={diag2['results']['max_json_depth']}) or "
        f"carries {diag2['results']['entry_bomb_entries_probed']} array entries "
        "(MAX_COLLECTION_ENTRIES=100000) -- both structures that "
        "CandidateEnvelope::from_bytes/parse_json_strict correctly and "
        "verifiably REJECTS (proven live in the same probe run, "
        "g2_from_bytes_rejects_depth_bomb=true, "
        "g2_from_bytes_rejects_entry_bomb=true) -- and pairing it with an "
        "otherwise-honest, correctly-bound 11-field host-verified receipt, "
        "AssuranceCapability::new(\"amphora-evidence-intake-validator\")."
        "evaluate(...) (the SAME public Capability trait entrypoint the "
        "real engine dispatches through) returns status=SCORED, "
        "score_0_1=1.0, gates.evidence_package_accepted=true for BOTH "
        "structural-limit violators, identically to the honest baseline. "
        "So mission.md's 'byte hashing ... reject[s] ... overclaiming "
        "packages' and 'Unsupported formats fail closed' do not hold for "
        "the module's real scoring entrypoint: the strict-parser format "
        "rejections exist in this repository, are unit-tested, and are "
        "exercised only by a constructor (from_bytes) that the live "
        "candidate-scoring path never calls."
    ),

    "gates": {
        "probe1_g0_sanity_replay_of_shipped_unit_tests": diag1["gates"]["g0_sanity_replay_of_shipped_unit_tests"],
        "probe1_g1_from_value_hash_collapse": diag1["gates"]["g1_from_value_original_bytes_hash_always_coincides_with_contract_hash"],
        "probe1_g1b_from_bytes_hash_genuinely_diverges": diag1["gates"]["g1b_from_bytes_original_bytes_hash_genuinely_diverges"],
        "probe1_g2_from_value_bypasses_budget": diag1["gates"]["g2_from_value_bypasses_depth_and_entry_budget"],
        "probe2_g_honest_baseline_accepted": diag2["gates"]["g_honest_baseline_accepted"],
        "probe2_g_depth_bomb_accepted_end_to_end": diag2["gates"]["g_depth_bomb_accepted_end_to_end"],
        "probe2_g_entry_bomb_accepted_end_to_end": diag2["gates"]["g_entry_bomb_accepted_end_to_end"],
        "static_g_engine_execute_never_calls_from_bytes_for_candidates": True,
        "all_gates_passed": diag1["all_gates_passed"] and diag2["all_gates_passed"],
    },

    "results": {
        "probe1_diagnostic": diag1,
        "probe2_diagnostic": diag2,
        "static_citation": {
            "file": "amphora-engine/src/lib.rs",
            "sha256": engine_rs_sha,
            "from_value_call_sites_lines": [567, 629, 732],
            "from_bytes_call_sites_for_candidates": [],
            "parse_json_strict_call_sites_lines": [172, 950, 951],
            "parse_json_strict_call_sites_purpose": "static module manifest bytes (172) and evidence-context/trust-store bytes (950, 951) only -- never a scored candidate",
        },
    },

    "does_not_establish": [
        "No wet-lab, product-qualification, batch-release, legal, regulatory or scientific authority.",
        "Not a claim that today's shipped amphora-cli is directly, externally exploitable end-to-end: amphora-cli's own read_json() helper (amphora-cli/src/main.rs:179-182) does call parse_json_strict before ever constructing a Value handed to EnginePool::score, so the CLI's own file-reading front door happens to pre-filter duplicate keys and depth/entry bombs today. The defect is architectural and latent, not a demonstrated CLI-level intrusion: it is that this protection lives entirely in a CLI convenience function's own choice, not in CandidateEnvelope::from_value, evaluate_evidence_intake, host_receipt_valid, or anything amphora-evidence-intake-validator's own predicate does or requires. Any other caller of EnginePool::score/score_many/score_campaign_modules/execute (a future HTTP front door, a library integration, an internal pipeline that already holds a Value from any other source) inherits zero of these guarantees, and mission.md's phrasing asserts them as a property of intake itself, not of amphora-cli.",
        "Not a claim that amphora-core's from_bytes/parse_json_strict are themselves broken -- probe1 G0 and G1b confirm they work exactly as unit-tested and as documented.",
        "Not a re-run or restatement of T-04, V1-REAL-EIV, or W-T-EIV: those found that host_receipt_valid never independently verifies the receipt it is handed (trust/signature/revocation delegation gaps). This receipt finds a DIFFERENT, upstream gap: the candidate INGESTION boundary itself (before evaluate_evidence_intake ever runs) applies no structural format limits on the entrypoint the real engine actually uses, contradicting the specific 'byte hashing ... reject ... overclaiming packages' / 'Unsupported formats fail closed' sentences in mission.md that no prior audit tested.",
        "No runtime source file is modified by this receipt; both probes are read-only, standalone, non-workspace-member crates that link the real code and observe its behavior (AUDIT_ONLY).",
    ],

    "verdict": "CLAIM_REFUTED",
    "verdict_reason": (
        "mission.md's falsifiable hypothesis asserts, unqualified, that 'byte "
        "hashing and manifest binding reject missing, mutated, unsigned, or "
        "overclaiming packages' and that 'Unsupported formats fail closed.' "
        "Two live Rust probes linking the real amphora-core and "
        "amphora-assurance-capabilities crates show this is false for the "
        "module's real scoring entrypoint (amphora-engine::execute, "
        "statically confirmed to use CandidateEnvelope::from_value "
        "exclusively for every candidate it scores): a package exceeding "
        "MAX_JSON_DEPTH by 40 levels, and a package exceeding "
        "MAX_COLLECTION_ENTRIES by 50000 entries -- both structures the "
        "module's OWN strict parser is built to reject, and does reject, "
        "live, when reached via from_bytes -- are BOTH accepted end to end "
        "(status=SCORED, score_0_1=1.0, gates.evidence_package_accepted="
        "true) by the real, live evaluate_evidence_intake/host_receipt_"
        "valid predicate when constructed via from_value, identically to "
        "an honest well-formed package. 'Unsupported formats fail closed' "
        "does not hold for the entrypoint mission.md itself names as "
        "authoritative."
    ),

    "provenance": {
        "probe1_path": "amphora-evidence-intake-validator/evidence/audit/from-value-strict-parse-bypass-v1/runtime_probe",
        "probe1_main_rs_sha256": probe1_main_sha,
        "probe1_cargo_toml_sha256": probe1_cargo_sha,
        "probe1_diagnostic_canonical_sha256": sha(canon1),
        "probe2_path": "amphora-evidence-intake-validator/evidence/audit/evaluate-evidence-intake-bomb-probe-v1/runtime_probe",
        "probe2_main_rs_sha256": probe2_main_sha,
        "probe2_cargo_toml_sha256": probe2_cargo_sha,
        "probe2_diagnostic_canonical_sha256": sha(canon2),
        "contract_rs_sha256": contract_rs_sha,
        "core_lib_rs_sha256": core_lib_rs_sha,
        "engine_rs_sha256": engine_rs_sha,
        "assurance_capabilities_lib_rs_sha256": assurance_rs_sha,
        "shipped_kpi_sha256": shipped_kpi_sha,
        "mission_md_sha256_at_audit_time": mission_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "probe1_byte_identical": canon1 == runB1,
        "probe2_byte_identical": canon2 == runB2,
        "determinism_note": (
            "No RNG, no wall clock, no filesystem writes by either probe. "
            "Both probes link the real crates as ordinary Cargo path "
            "dependencies (`[workspace]` empty table opts each probe out of "
            "the mvp20-split workspace, same pattern as "
            "amphora-model-card-authority's mca-live-runtime-probe) and "
            "print one deterministic JSON object to stdout."
        ),
        "replay_method_probe1": "cargo build --release in runtime_probe/ (amphora-core path dependency), then run the binary with no arguments.",
        "replay_method_probe2": "cargo build --release in runtime_probe/ (amphora-core + amphora-assurance-capabilities path dependencies), then run the binary with no arguments.",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/" + RECEIPT_ID + "/",
        "signs_phase0_evaluation_or_review": False,
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.evidence-intake-validator-from-value-strict-parse-bypass+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}

AUDIT_DIR.mkdir(parents=True, exist_ok=True)
out = AUDIT_DIR / "from-value-strict-parse-bypass-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("verdict", body_obj["verdict"])
print("receipt_sha256", sha(out.read_bytes()))
print("self_verify_signature", "OK")
