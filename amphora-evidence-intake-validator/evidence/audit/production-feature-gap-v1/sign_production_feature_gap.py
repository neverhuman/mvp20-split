#!/usr/bin/env python3
"""DSSE-Ed25519-sign the production-feature-gap-v1 AUDIT_ONLY receipt for
amphora-evidence-intake-validator. Does not modify the master manifest, any
locked dataset, the shipped Phase-0 KPI, or the runtime."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-evidence-intake-validator"
RECEIPT_ID = "production-feature-gap-v1"
AUDIT_DIR = MOD / "evidence/audit" / RECEIPT_ID
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"

ENGINE_RS = ROOT / "amphora-engine/src/lib.rs"
ASSURANCE_RS = ROOT / "amphora-assurance-capabilities/src/lib.rs"
FORMULATION_RS = ROOT / "amphora-formulation-capabilities/src/lib.rs"
CORE_LIB_RS = ROOT / "amphora-core/src/lib.rs"
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


canon = (AUDIT_DIR / "diagnostic.canonical.json").read_bytes()
runB = (AUDIT_DIR / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["all_gates_passed"] is True

engine_rs_sha = sha(ENGINE_RS.read_bytes())
assurance_rs_sha = sha(ASSURANCE_RS.read_bytes())
formulation_rs_sha = sha(FORMULATION_RS.read_bytes())
core_lib_rs_sha = sha(CORE_LIB_RS.read_bytes())
mission_sha = sha(MISSION.read_bytes())
probe_main_sha = sha((AUDIT_DIR / "runtime_probe/src/main.rs").read_bytes())
probe_cargo_sha = sha((AUDIT_DIR / "runtime_probe/Cargo.toml").read_bytes())

# Repo-wide static grep, re-run at signing time, non-test-dir hits only.
import subprocess
grep_out = subprocess.run(
    ["grep", "-rn", "HOST_VERIFIED_RECEIPT_FEATURE", "--include=*.rs", "."],
    cwd=str(ROOT), capture_output=True, text=True
).stdout.splitlines()
grep_out = [l for l in grep_out if "/target/" not in l]

# Insertion sites confirmed, by direct source inspection at audit time, to
# sit inside a #[cfg(test)] mod / #[test] fn body even though the file is a
# production src/lib.rs (not under tests/ or evidence/).
CONFIRMED_TEST_FN_SITES = {
    "./amphora-assurance-capabilities/src/lib.rs:1450",
    "./amphora-formulation-capabilities/src/lib.rs:2426",
    "./amphora-formulation-capabilities/src/lib.rs:2483",
}

insertion_lines = [l for l in grep_out if ".insert(HOST_VERIFIED_RECEIPT_FEATURE" in l]
non_test_insertion_lines = []
for line in insertion_lines:
    path, lineno = line.split(":", 2)[0], line.split(":", 2)[1]
    site = f"{path}:{lineno}"
    is_under_tests_dir = "/tests/" in path
    is_confirmed_test_fn = site in CONFIRMED_TEST_FN_SITES
    is_under_evidence_dir = path.startswith("./amphora-evidence-intake-validator/evidence/")
    if not (is_under_tests_dir or is_confirmed_test_fn or is_under_evidence_dir):
        non_test_insertion_lines.append(line)

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

body_obj = {
    "schema": "amphora.evidence-intake-validator.production-feature-gap-receipt.v1",
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
    "date": "2026-08-17",
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
        "docs/mission.md 'Honest current state': operational_readiness is "
        "asserted COMPLETE (front-matter) and the module's stated decision "
        "is 'whether observed evidence bytes may enter the accepted "
        "evidence store.' Prior audits (host-receipt-oracle-parity-v1, "
        "predicate-completeness-v1, canonicalization-invariance-tamper-v1, "
        "receipt-authority-derivability-freshness-v1, V1-REAL-EIV, T-04, "
        "W-T-EIV, from-value-strict-parse-bypass-v1) all probed "
        "evaluate_evidence_intake/host_receipt_valid by hand-constructing a "
        "FeatureSnapshot containing HOST_VERIFIED_RECEIPT_FEATURE, exactly "
        "as the module's own #[test] harnesses do. None asked whether the "
        "ONE non-test code path in the whole repository that ever builds "
        "the FeatureSnapshot passed into a real scoring call -- "
        "amphora-engine/src/lib.rs execute(), lines ~733-742 -- ever "
        "inserts that key at all."
    ),

    "baseline": {
        "name": "amphora-engine's own committed production feature-building code",
        "citation": (
            "amphora-engine/src/lib.rs (sha256 " + engine_rs_sha + "), "
            "fn execute(), lines ~733-742: the feature_values BTreeMap is "
            "seeded with exactly two unconditional keys (chemistry_backend, "
            "rights_cleared_scientific_corpus) plus two conditional keys "
            "gated on /normalization/molecule_facts_v1 and "
            "/normalization/error pointers present only for candidate_type="
            "molecule. This receipt's runtime_probe replicates that key set "
            "verbatim for candidate_type=evidence_package (which never "
            "reaches the molecule-only branches) in production_feature_"
            "values(), then asks the real, live predicate to decide with it."
        ),
    },

    "claim": (
        "PRODUCTION-WIRING VERDICT, established with a LIVE Rust probe "
        "linking the real amphora-core and amphora-assurance-capabilities "
        "crates end to end (not a re-implementation): "
        "evaluate_evidence_intake/host_receipt_valid "
        "(amphora-assurance-capabilities/src/lib.rs, sha256 " + assurance_rs_sha + ", "
        "lines 673/729) can ONLY ever return verified=true if "
        "features.values contains the key HOST_VERIFIED_RECEIPT_FEATURE "
        "(\"evidence_intake.host_verified_receipt\") as an object with 11 "
        "specific fields; absent that key, host_receipt_valid short-circuits "
        "to false at its first line (`let Some(receipt) = features.values."
        "get(...) else { return false }`). A repo-wide static grep for "
        "HOST_VERIFIED_RECEIPT_FEATURE (re-run at signing time; " +
        str(len(grep_out)) + " total hits, listed verbatim in "
        "results.static_grep.all_hits) finds exactly " +
        str(len(non_test_insertion_lines)) + " call sites that ever INSERT "
        "this key into a FeatureSnapshot, and every one of them is either "
        "a #[test] fn body (amphora-assurance-capabilities/src/lib.rs:1450, "
        "sha256 " + assurance_rs_sha + "; amphora-formulation-capabilities/"
        "src/lib.rs:2426 and :2483, sha256 " + formulation_rs_sha + ", all "
        "confirmed by direct source inspection to sit inside #[cfg(test)] "
        "mod tests) or a test/repair/audit-probe .rs file under tests/ or "
        "evidence/. amphora-engine/src/lib.rs -- the ONLY non-test module "
        "in the whole repository that builds a FeatureSnapshot for a real "
        "scoring call (fn execute, called exclusively by the public "
        "EnginePool::score/score_many/score_campaign_modules API, which is "
        "in turn the only thing amphora-cli's real candidate-scoring "
        "commands call) -- has ZERO such insertions, unconditionally, for "
        "every candidate type including evidence_package. The live probe "
        "confirms the consequence directly against the REAL predicate: a "
        "maximally honest, correctly-bound, 11-field, all-fields-true, "
        "Ed25519/TRUSTED host-verified receipt for a legitimate marine-"
        "coating ISO-4624 pull-off evidence package -- built the same way "
        "the module's own shipped positive KPI fixtures are built -- is "
        "REJECTED (status=FAILED_GATES, score_0_1=0.0, "
        "gates.evidence_package_accepted=false, missing_inputs=[\"missing "
        "or invalid host receipt in FeatureSnapshot key evidence_intake."
        "host_verified_receipt\"]) when evaluated with the FeatureSnapshot "
        "production code actually builds (G1), and is ACCEPTED "
        "(status=SCORED, score_0_1=1.0, gates.evidence_package_accepted="
        "true) with the identical candidate and identical receipt the "
        "moment the receipt is manually inserted into features the way "
        "every prior audit's harness does it (G2 control, proving the "
        "predicate logic itself is not broken -- only unreachable). "
        "Because no other production code path supplies this key either, "
        "the practical consequence is unconditional: as currently wired, "
        "amphora-evidence-intake-validator's accept branch "
        "(evidence_package_accepted=true) can never be reached by ANY real "
        "invocation of the live engine, for ANY evidence, honest or "
        "forged. Every prior adversarial and constructive finding about "
        "this predicate (T-04's forgeries, V1-REAL-EIV's real-corpus rate, "
        "receipt-authority-derivability-freshness-v1's H0 REFUTED) tested a "
        "code path that is itself never actually exercised by production."
    ),

    "gates": {
        "g1_production_features_lack_receipt_key": diag["gates"]["g1_production_features_lack_receipt_key"],
        "g1_honest_receipt_rejected_under_production_features": diag["gates"]["g1_honest_receipt_rejected_under_production_features"],
        "g2_same_receipt_accepted_when_manually_supplied": diag["gates"]["g2_same_receipt_accepted_when_manually_supplied"],
        "static_g_zero_non_test_insertions_repo_wide": len(non_test_insertion_lines) == 0,
        "all_gates_passed": diag["all_gates_passed"] and (len(non_test_insertion_lines) == 0),
    },

    "results": {
        "probe_diagnostic": diag,
        "static_grep": {
            "command": "grep -rn HOST_VERIFIED_RECEIPT_FEATURE --include=*.rs . (run from repo root, /target/ excluded)",
            "total_hits": len(grep_out),
            "all_hits": grep_out,
            "insertion_call_sites": insertion_lines,
            "non_test_production_insertion_sites": non_test_insertion_lines,
            "insertion_sites_classification": {
                "amphora-assurance-capabilities/src/lib.rs:1450": "#[test] fn (mod tests, cfg(test)), confirmed by direct source read at audit time",
                "amphora-formulation-capabilities/src/lib.rs:2426": "#[test] fn (mod tests, cfg(test)), confirmed by direct source read at audit time",
                "amphora-formulation-capabilities/src/lib.rs:2483": "#[test] fn (mod tests, cfg(test)), confirmed by direct source read at audit time",
                "amphora-assurance-capabilities/tests/evidence_intake_validator_t04_adversarial_forgery.rs:129": "integration test file (tests/)",
                "amphora-assurance-capabilities/tests/evidence_intake_validator_phase0_kpi.rs:131": "integration test file (tests/)",
                "amphora-evidence-intake-validator/evidence/phase0/repairs/T-04/work/evidence_intake_validator_t04_adversarial_forgery.rs:129": "repair work-copy of the same test file",
            },
        },
        "engine_execute_feature_block": {
            "file": "amphora-engine/src/lib.rs",
            "sha256": engine_rs_sha,
            "lines": "733-742",
            "unconditional_keys_inserted": ["chemistry_backend", "rights_cleared_scientific_corpus"],
            "conditional_keys_inserted": ["molecule_facts_v1 (only if candidate_type=molecule and normalization succeeds)", "molecule_normalization_error (only if candidate_type=molecule and normalization fails)"],
            "host_verified_receipt_feature_inserted": False,
        },
    },

    "does_not_establish": [
        "No wet-lab, product-qualification, batch-release, legal, regulatory or scientific authority.",
        "Not a claim that host_receipt_valid's own 11-conjunct logic is newly broken: G2 shows it correctly accepts a valid receipt and (per T-04/receipt-authority-derivability-freshness-v1) correctly/incorrectly handles various forged ones exactly as previously found, once it is actually given a receipt. This receipt finds a DIFFERENT, upstream defect: production code never gives it one, for any candidate, ever.",
        "Not a claim that EnginePool::new()/with_evidence_root() cannot be constructed in some deployment with different wiring; this receipt tests the fn execute() feature-building code as committed today and as reachable from the only exported scoring API (EnginePool::score/score_many/score_campaign_modules), which is what amphora-cli's real scoring commands call.",
        "Not a claim that some other, not-yet-discovered, non-Rust or out-of-repo component populates this feature before invoking the engine binary; the static grep and source citations here are scoped to this repository (mvp20-split) as committed, which is also the scope every prior mission.md claim and every prior audit of this module was scoped to.",
        "No runtime source file is modified by this receipt; the probe is a read-only, standalone, non-workspace-member crate that links the real code and observes its behavior (AUDIT_ONLY).",
    ],

    "verdict": "CLAIM_REFUTED",
    "verdict_reason": (
        "mission.md asserts operational_readiness COMPLETE and describes "
        "this module's decision as gating whether evidence bytes 'may enter "
        "the accepted evidence store.' A live Rust probe linking the real "
        "amphora-core and amphora-assurance-capabilities crates, combined "
        "with a repo-wide static grep re-run at signing time, shows that "
        "the ONLY production code path that ever builds the FeatureSnapshot "
        "for a real scoring call (amphora-engine::execute) never inserts "
        "the one feature key (evidence_intake.host_verified_receipt) the "
        "predicate requires to accept anything, under any condition, for "
        "any candidate type. A maximally honest, correctly-bound receipt "
        "for a legitimate evidence package is rejected end to end "
        "(FAILED_GATES, score 0.0) when evaluated with the feature set "
        "production code actually builds, and is accepted (SCORED, score "
        "1.0) only when the receipt is hand-inserted the way every prior "
        "test/audit harness -- but no production code -- does it. As "
        "currently wired, the module's accept branch is unconditionally "
        "unreachable by the real engine: it cannot enter ANY evidence into "
        "the accepted evidence store, honest or forged, contradicting the "
        "operational_readiness=COMPLETE claim and the decision mission.md "
        "says this module makes."
    ),

    "provenance": {
        "probe_path": "amphora-evidence-intake-validator/evidence/audit/production-feature-gap-v1/runtime_probe",
        "probe_main_rs_sha256": probe_main_sha,
        "probe_cargo_toml_sha256": probe_cargo_sha,
        "probe_diagnostic_canonical_sha256": sha(canon),
        "engine_rs_sha256": engine_rs_sha,
        "assurance_capabilities_lib_rs_sha256": assurance_rs_sha,
        "formulation_capabilities_lib_rs_sha256": formulation_rs_sha,
        "core_lib_rs_sha256": core_lib_rs_sha,
        "mission_md_sha256_at_audit_time": mission_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "byte_identical": canon == runB,
        "determinism_note": (
            "No RNG, no wall clock, no filesystem writes by the probe. The "
            "probe links the real crates as ordinary Cargo path "
            "dependencies (`[workspace]` empty table opts it out of the "
            "mvp20-split workspace, same pattern as the sibling "
            "from-value-strict-parse-bypass-v1 / evaluate-evidence-intake-"
            "bomb-probe-v1 probes) and prints one deterministic JSON object "
            "to stdout."
        ),
        "replay_method": "cargo build --release in runtime_probe/ (amphora-core + amphora-assurance-capabilities path dependencies), then run the binary with no arguments.",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/" + RECEIPT_ID + "/",
        "signs_phase0_evaluation_or_review": False,
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.evidence-intake-validator-production-feature-gap+json"
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
out = AUDIT_DIR / "production-feature-gap-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("verdict", body_obj["verdict"])
print("receipt_sha256", sha(out.read_bytes()))
print("self_verify_signature", "OK")
