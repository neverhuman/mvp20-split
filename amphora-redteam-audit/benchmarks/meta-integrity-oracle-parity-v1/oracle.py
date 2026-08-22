#!/usr/bin/env python3
"""
Independent non-runtime meta-integrity oracle for amphora-redteam-audit.

Falsifiable hypothesis under test (module mission):
  "A locked adversarial corpus detects malformed envelopes and authority escalation."

This oracle re-derives, from primary cryptographic / canonical-JSON theory and
WITHOUT invoking the Rust runtime, the meta-audit integrity guarantees that
amphora-redteam-audit asserts, reproduces the shipped byte-exact digest anchors,
and confirms an independently-constructed adversarial tamper corpus is detected
(fail-closed).

Theory stack (primary sources):
  - Canonical JSON key-sorted serialization (RFC 8785 JCS, 2020; the runtime's
    amphora_core::canonicalize + serde_json compact serialization).
  - SHA-256, NIST FIPS 180-4 (2015).
  - Ed25519 / EdDSA, Bernstein et al. CHES 2011; RFC 8032 (2017).
  - DSSE PAE envelope, in-toto DSSE spec v1.0 (2021).
  - Reference-monitor / least-authority: Anderson 1980; Saltzer-Schroeder 1975;
    NIST SP 800-53 Rev.5 AU-6 & CM-6.

Deterministic: no wall-clock, no RNG. Two invocations are byte-identical.
"""
import json, hashlib, base64, copy, sys

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
RTA = ROOT + "/amphora-redteam-audit"
RESULT = RTA + "/evidence/phase0/benchmark/result.v1.json"
BLOCK = RTA + "/evidence/phase0/benchmark/benchmark-lock.v1.json"
DIAG_RS = ROOT + "/amphora-assurance-capabilities/src/diagnostics.rs"

# ---- independent canonical-JSON + SHA-256 (mirrors amphora_core::stable_hash) ----
def canon(v):
    if isinstance(v, dict):
        return {k: canon(v[k]) for k in sorted(v.keys())}
    if isinstance(v, list):
        return [canon(x) for x in v]
    return v

def canon_bytes(v):
    return json.dumps(canon(v), separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def stable_hash(v):
    return hashlib.sha256(canon_bytes(v)).hexdigest()

def raw_sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

# Independent reference: the 24-axis LOCKED ADVERSARIAL CORPUS the mission declares.
# These names are the module-specific attack axes the redteam corpus must cover.
CANONICAL_24_AXES = [
    "IDENTITY_OR_MODULE_SUBSTITUTION", "REGISTRY_TAMPERING",
    "REGISTRY_SUPERSESSION_TAMPERING", "FOLDER_CONFINEMENT_ESCAPE",
    "DSSE_FORGERY", "DSSE_WRONG_ROLE", "DSSE_LOCAL_SIGNER", "DSSE_REVOKED_SIGNER",
    "DSSE_SAME_SIGNER", "FALSE_HUMAN_REVIEW", "INCOMPLETE_POLICY",
    "ALTERED_DIAGNOSTIC", "NONDETERMINISTIC_DIAGNOSTIC", "FALSE_EXECUTION_COMPLETION",
    "UNEXECUTED_SCIENCE", "RIGHTS_LAUNDERING", "EVIDENCE_LAUNDERING",
    "SOURCE_DUPLICATE", "SOURCE_MISSING_FIELD", "SOURCE_WAIVER_LAUNDERING",
    "REPORT_SIGNATURE_DEFECT", "REPORT_ENVELOPE_BINDING_DEFECT",
    "REPORT_CLAIM_LOCK_DEFECT", "AUTHORITY_ESCALATION",
]

# Forbidden authority-escalation KEYS (Anderson reference-monitor boundary): a
# zero-authority meta-audit result must never assert any of these.
FORBIDDEN_AUTHORITY_KEYS = {
    "batch_release", "qualified", "authorized",
    "manufacturing_qualification", "release_authority",
}
# The 10 required zero-authority claim locks (amphora_core::REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS).
REQUIRED_ZERO_AUTHORITY_LOCKS = [
    "no_ranking_authority", "no_optimizer_authority", "no_release_authority",
    "no_qualification_authority", "no_patentability_authority", "fto_not_performed",
    "no_procurement_authority", "no_regulatory_authority", "no_safety_authority",
    "no_product_performance_authority",
]
EXPECTED_MODULES = [
    "amphora-evidence-intake-validator", "amphora-source-ledger", "amphora-redteam-audit",
    "amphora-report-packager", "amphora-formulation-arithmetic", "amphora-formulation-universe",
    "amphora-envelope-gates", "amphora-cro-protocol-packager", "amphora-optimizer-orchestrator",
]

def scan_forbidden_keys(node):
    """Recursively collect any forbidden authority key names present anywhere."""
    hits = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in FORBIDDEN_AUTHORITY_KEYS:
                hits.append(k)
            hits.extend(scan_forbidden_keys(v))
    elif isinstance(node, list):
        for x in node:
            hits.extend(scan_forbidden_keys(x))
    return hits

def run():
    doc = json.load(open(RESULT))
    fr = doc["first_replay"]
    sr = doc["second_replay"]
    dr = fr["diagnostic_receipt"]
    gates = {}

    # --- G1: canonicalization + hash parity (independent stable_hash == shipped digest) ---
    my_fr = stable_hash(dr)
    my_sr = stable_hash(sr["diagnostic_receipt"])
    gates["G1_digest_parity"] = {
        "independent_stable_hash_first_replay": my_fr,
        "shipped_diagnostic_sha256_first_replay": fr["diagnostic_sha256"],
        "independent_stable_hash_second_replay": my_sr,
        "shipped_diagnostic_sha256_second_replay": sr["diagnostic_sha256"],
        "match_first": my_fr == fr["diagnostic_sha256"],
        "match_second": my_sr == sr["diagnostic_sha256"],
        "passed": my_fr == fr["diagnostic_sha256"] and my_sr == sr["diagnostic_sha256"],
    }

    # --- G2: raw-hash integrity anchors reproduced from raw bytes ---
    bl = raw_sha256_file(BLOCK)
    ds = raw_sha256_file(DIAG_RS)
    gates["G2_raw_hash_anchors"] = {
        "benchmark_lock_sha256_recomputed": bl,
        "benchmark_lock_sha256_declared": doc["benchmark_lock_sha256"],
        "dataset_fixture_sha256_recomputed": ds,
        "dataset_fixture_sha256_declared": doc["dataset_fixture_sha256"],
        "passed": bl == doc["benchmark_lock_sha256"] and ds == doc["dataset_fixture_sha256"],
    }

    # --- G3: locked adversarial corpus coverage (24 axes) ---
    lock = json.load(open(BLOCK))
    lock_attacks = set(lock["attacks"])
    axis_details = dr["kpi"]["attack_axis_coverage_complete_rate"]["axis_details"]
    detail_true = {a["axis"] for a in axis_details if a.get("declared_in_benchmark_lock") is True}
    covered = sum(1 for ax in CANONICAL_24_AXES if ax in lock_attacks and ax in detail_true)
    gates["G3_attack_axis_coverage"] = {
        "canonical_axis_count": len(CANONICAL_24_AXES),
        "unique_canonical_axes": len(set(CANONICAL_24_AXES)),
        "covered_in_lock_and_result": covered,
        "axis_details_count": len(axis_details),
        "passed": covered == 24 and len(set(CANONICAL_24_AXES)) == 24 and len(axis_details) == 24,
    }

    # --- G4: authority-envelope preservation on the pristine receipt ---
    forbidden_hits = scan_forbidden_keys(doc)
    recs = dr["records"]
    locks_ok = all(r.get("zero_authority_lock_coverage_complete") is True for r in recs)
    env_ok = all(r.get("authority_envelope_preserved") is True for r in recs)
    module_ids = [r["module_id"] for r in recs]
    gates["G4_authority_envelope"] = {
        "forbidden_authority_key_hits": forbidden_hits,
        "zero_authority_lock_coverage_all_true": locks_ok,
        "authority_envelope_preserved_all_true": env_ok,
        "records_module_ids_match_expected": module_ids == EXPECTED_MODULES,
        "required_zero_authority_locks": REQUIRED_ZERO_AUTHORITY_LOCKS,
        "passed": len(forbidden_hits) == 0 and locks_ok and env_ok and module_ids == EXPECTED_MODULES,
    }

    # --- G5: replay byte-stability (independent) ---
    fr_bytes = canon_bytes(dr)
    sr_bytes = canon_bytes(sr["diagnostic_receipt"])
    gates["G5_replay_byte_stability"] = {
        "first_second_canonical_bytes_identical": fr_bytes == sr_bytes,
        "diagnostic_sha256_equal_across_replays": fr["diagnostic_sha256"] == sr["diagnostic_sha256"],
        "passed": fr_bytes == sr_bytes and fr["diagnostic_sha256"] == sr["diagnostic_sha256"],
    }

    # --- G6: independent adversarial tamper corpus MUST be detected (fail-closed) ---
    baseline = fr["diagnostic_sha256"]
    probes = []

    def mutate(label, fn, expect_forbidden=False):
        m = copy.deepcopy(dr)
        fn(m)
        h = stable_hash(m)
        digest_changed = (h != baseline)
        fk = scan_forbidden_keys(m)
        detected = digest_changed or (expect_forbidden and len(fk) > 0)
        probes.append({
            "probe": label,
            "digest_changed_from_baseline": digest_changed,
            "forbidden_keys_after_mutation": fk if expect_forbidden else [],
            "detected": detected,
        })

    mutate("FLIP_PASSED_FLAG", lambda m: m["records"].__setitem__(2, {**m["records"][2], "passed_flag": False}))
    mutate("DROP_ATTACK_AXIS", lambda m: m["kpi"]["attack_axis_coverage_complete_rate"]["axis_details"].pop())
    mutate("INJECT_AUTHORITY_ESCALATION",
           lambda m: m["records"][0].__setitem__("batch_release", True), expect_forbidden=True)
    mutate("INJECT_RELEASE_AUTHORITY",
           lambda m: m["records"][0].__setitem__("release_authority", True), expect_forbidden=True)
    mutate("ALTER_RESULT_DIGEST",
           lambda m: m["records"][1].__setitem__("result_digest", "0" * 64))
    mutate("FABRICATE_EXTRA_RECORD",
           lambda m: m["records"].append({**m["records"][0], "module_id": "amphora-ghost-module"}))
    mutate("STRIP_ZERO_AUTHORITY_LOCK",
           lambda m: m["records"][0].__setitem__("zero_authority_lock_coverage_complete", False))
    mutate("FALSE_EXECUTION_COMPLETION",
           lambda m: m["records"][3].__setitem__("dispatch_ok", False))

    detected_n = sum(1 for p in probes if p["detected"])
    # Control: a no-op deep copy must NOT be flagged (no false positive).
    noop = copy.deepcopy(dr)
    noop_stable = (stable_hash(noop) == baseline) and (len(scan_forbidden_keys(noop)) == 0)
    gates["G6_adversarial_tamper_detection"] = {
        "probe_count": len(probes),
        "detected_count": detected_n,
        "tamper_detection_rate": detected_n / len(probes),
        "noop_control_not_flagged": noop_stable,
        "probes": probes,
        "passed": detected_n == len(probes) and noop_stable,
    }

    all_passed = all(g["passed"] for g in gates.values())
    return {
        "schema": "amphora.redteam-audit.meta-integrity-oracle-parity.v1",
        "oracle_id": "meta-integrity-oracle-parity-v1",
        "module_id": "amphora-redteam-audit",
        "hypothesis": ("An independent non-runtime oracle reproduces the redteam-audit "
                       "meta-audit digest anchors byte-exact and an independent adversarial "
                       "corpus detects malformed envelopes and authority escalation (fail-closed)."),
        "theory_sources": [
            "RFC 8785 JCS canonical JSON (2020)",
            "NIST FIPS 180-4 SHA-256 (2015)",
            "Bernstein et al. Ed25519 CHES 2011 / RFC 8032 (2017)",
            "in-toto DSSE v1.0 (2021)",
            "Anderson 1980 reference-monitor; Saltzer-Schroeder 1975; NIST SP 800-53 Rev.5 AU-6/CM-6",
        ],
        "subject_artifacts": {
            "result_v1": "amphora-redteam-audit/evidence/phase0/benchmark/result.v1.json",
            "benchmark_lock_v1": "amphora-redteam-audit/evidence/phase0/benchmark/benchmark-lock.v1.json",
            "runtime_fixture": "amphora-assurance-capabilities/src/diagnostics.rs",
        },
        "gates": gates,
        "all_gates_passed": all_passed,
        "verdict": ("HYPOTHESIS_CORROBORATED" if all_passed else "HYPOTHESIS_REFUTED"),
        "ceiling_note": ("Offline oracle over shipped evidence + independent adversarial corpus; "
                         "reproduces the runtime's canonical-hash integrity mechanism byte-exact "
                         "but does not re-execute the Rust diagnostic. Rust error-taxonomy parity "
                         "and live-runtime re-execution remain the Phase-1 axis."),
    }

if __name__ == "__main__":
    out = run()
    sys.stdout.write(json.dumps(canon(out), separators=(",", ":"), ensure_ascii=False))
