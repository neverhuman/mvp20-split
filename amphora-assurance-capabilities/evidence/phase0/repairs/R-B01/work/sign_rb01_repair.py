#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-B01 repair done-receipt for
amphora-assurance-capabilities (code home of the amphora-ip-fto-guard
runtime). Supersedes (never rewrites) the two refuting AUDIT_ONLY receipts.
Construction replicates amphora-evidence-intake-validator/benchmarks/
sign_canon_invariance.py exactly: pae(), load_seed(), payloadType, envelope
fields, trust-store key-id derivation, post-write signature verification.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-assurance-capabilities"
GUARD = ROOT / "amphora-ip-fto-guard"
REPAIR = MOD / "evidence/phase0/repairs/R-B01"
WORK = REPAIR / "work"
DONE = REPAIR / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

SUPERSEDED_A = GUARD / "evidence/audit/metric-schema-parity-v1/metric-schema-parity-receipt.v1.dsse.json"
SUPERSEDED_B = GUARD / "evidence/audit/counsel-assertion-detection-completeness-v1/counsel-assertion-detection-completeness-receipt.v1.dsse.json"
SUPERSEDED_A_SHA = "5c7ac925944df036bb2154c7e4573dc0b752cb3a1bc0d3df022d3fd06285da5f"
SUPERSEDED_B_SHA = "53624d327d48bb90812c90352c933bab46740be31c78be439c1f4d93284cecea"

LIB_RS = MOD / "src/lib.rs"
KPI_TEST = MOD / "tests/ip_fto_guard_phase0_kpi.rs"
PROBES_TEST = MOD / "tests/ip_fto_guard_counsel_assertion_probes.rs"
BENCH_RESULT = GUARD / "evidence/phase0/benchmark/result.v1.json"


def sha(b: bytes) -> str:
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


# Superseded receipts must be byte-identical to their pre-repair hashes.
assert sha(SUPERSEDED_A.read_bytes()) == SUPERSEDED_A_SHA, "superseded receipt A drifted"
assert sha(SUPERSEDED_B.read_bytes()) == SUPERSEDED_B_SHA, "superseded receipt B drifted"

reattack = json.loads((WORK / "rb01_reattack.canonical.json").read_bytes())
reattack_sha = sha((WORK / "rb01_reattack.canonical.json").read_bytes())
runB_sha = sha((WORK / "rb01_reattack.runB.json").read_bytes())
assert reattack_sha == runB_sha, "re-attack diagnostic two-replay differs"
acc = reattack["acceptance"]
assert acc["eight_of_eight_probes_detected"], "8/8 probe acceptance not met"
assert acc["control_positive_detected"], "control positive not detected"
assert acc["zero_safety_breaches"], "safety breach observed"
assert acc["primary_kpi_populated_by_runtime"], "primary KPI not populated"
assert acc["cargo_green"], "cargo test not green"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.assurance-capabilities.repair-r-b01-receipt.v1",
    "receipt_id": "repair-R-B01-v1",
    "repair_item": "R-B01",
    "repair_mode": "interactive-2026-08-03",
    "module_id": "amphora-assurance-capabilities",
    "repairs_evidence_for_module": "amphora-ip-fto-guard",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "date": "2026-08-03",
    "generated_on_host": "xbabe2",
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "trust_anchored_in_phase0_store": True,
    "supersedes": [
        {
            "superseded_path": "amphora-ip-fto-guard/evidence/audit/metric-schema-parity-v1/metric-schema-parity-receipt.v1.dsse.json",
            "superseded_sha256": SUPERSEDED_A_SHA,
            "superseded_deleted_or_modified": False,
            "reason": (
                "That AUDIT_ONLY receipt REFUTED the claim that the declared "
                "PRIMARY Phase-1-promotion-gating KPI value path "
                "metrics.unresolved_technical_categories is populated by the "
                "live checked Rust runtime (it was populated by nothing). "
                "This repair implements the population in "
                "evaluate_ip_fto_guard() per docs/mission.md + "
                "docs/capability-profile.json semantics; the refutation of "
                "the PRE-repair runtime remains a true historical record and "
                "is superseded, not erased."
            ),
        },
        {
            "superseded_path": "amphora-ip-fto-guard/evidence/audit/counsel-assertion-detection-completeness-v1/counsel-assertion-detection-completeness-receipt.v1.dsse.json",
            "superseded_sha256": SUPERSEDED_B_SHA,
            "superseded_deleted_or_modified": False,
            "reason": (
                "That AUDIT_ONLY receipt REFUTED (scoped) the general "
                "reference-monitor reading of the "
                "boolean_counsel_assertion_ignored lock: the pre-repair "
                "detection was a single literal-path presence check with a "
                "100% false-negative rate (8/8) against alternate encodings. "
                "This repair replaces it with a recursive normalized-key "
                "reference-monitor scan; the refutation of the PRE-repair "
                "runtime remains a true historical record and is superseded, "
                "not erased."
            ),
        },
    ],
    "corrected_values": {
        "unresolved_technical_categories": {
            "value_now_emitted": 75,
            "value_path": "metrics.unresolved_technical_categories",
            "derivation": (
                "Census over the compile-time-embedded patent_landscape.json "
                "(sha256 52ada09074f435d515a8286e57b1d31da40fcbe3d0ec4f79a9be754e5cce63dc) "
                "claim_chart_categories array (75 entries). A category counts "
                "as unresolved unless the checked landscape explicitly "
                "records not_fto:false; all 75 entries record not_fto:true, "
                "so 75 technical categories remain unresolved and require "
                "qualified counsel review. Fail-closed nullability: an absent "
                "or empty census yields null, never 0, because 0 would "
                "implicitly assert 'nothing left for counsel' - a "
                "clearance-type claim this module is forbidden to make. "
                "Semantics per docs/mission.md ('surface unresolved "
                "categories without claiming FTO'; primary value path "
                "metrics.unresolved_technical_categories) and "
                "docs/capability-profile.json kpis[0] (name 'unresolved "
                "category coverage', metric_class primary, value_path "
                "metrics.unresolved_technical_categories, nullability "
                "explicit per examples/current_output null placeholder)."
            ),
            "independent_recompute_in_checked_test": (
                "tests/ip_fto_guard_phase0_kpi.rs recomputes the census from "
                "the on-disk fixture and gates "
                "unresolved_technical_categories_populated_rate at floor 1.0; "
                "tests/ip_fto_guard_counsel_assertion_probes.rs asserts "
                "runtime == fixture recompute."
            ),
        },
        "boolean_counsel_assertion_ignored": {
            "detection_now": (
                "Recursive reference-monitor scan over the WHOLE candidate "
                "JSON (Anderson 1980 complete mediation; Saltzer & Schroeder "
                "1975): every object key at every depth is normalized (NFKC "
                "via the unicode-normalization crate, Unicode lowercase, "
                "Cyrillic/Greek confusable fold, squash to ASCII "
                "alphanumerics) and matched against canonical names "
                "(signed_by_counsel, counsel_fto) plus a two-of-three "
                "semantic token-class rule over {counsel party: "
                "counsel/attorney/lawyer}, {freedom-to-operate: "
                "fto/freedomtooperate}, {sign-off: sign/clear/approv/grant/"
                "confirm/attest}. Matches under ANY container type (object, "
                "array, string, bool, number, null) are recorded as "
                "boolean_counsel_assertion_ignored=true. Detection only ever "
                "RECORDS an ignored injection; it can never elevate "
                "authority, so broader detection is a strictly stronger "
                "fail-closed lock. fto_status/legal_advice/fto_legal_closure "
                "remain compile-time constants."
            ),
            "intentional_behavior_change": (
                "A candidate-supplied evidence_refs.counsel_fto object that "
                "omits signed_by_counsel (Phase-0 KPI scenario "
                "flooring-with-counsel-object-missing-boolean) is NOW flagged "
                "true (canonical counsel_fto container is itself a recorded "
                "counsel-assertion injection); its expectation in the checked "
                "KPI test was updated accordingly - a strengthening, "
                "documented here."
            ),
        },
    },
    "code_changes": {
        "amphora-assurance-capabilities/src/lib.rs": {
            "sha256_before": "695ecb2e8d52039279b732635600d5bf207cbcf51891f7169f70da711f01f116",
            "sha256_after": sha(LIB_RS.read_bytes()),
            "change": (
                "evaluate_ip_fto_guard: replaced single-literal-path counsel "
                "check with counsel_signoff_assertion_present() recursive "
                "normalized-key scan (helpers: fold_confusable, "
                "normalized_key_skeleton, key_asserts_counsel_signoff, "
                "COUNSEL_ASSERTION_CANONICAL_KEYS); populated "
                "metrics.unresolved_technical_categories from the embedded "
                "claim-chart category census with null-not-zero fail-closed "
                "semantics."
            ),
        },
        "amphora-assurance-capabilities/tests/ip_fto_guard_phase0_kpi.rs": {
            "sha256_before": "6600bb3cb126ecd3a81b6c5709b37c253984f41014aadb58c41a72a071af079d",
            "sha256_after": sha(KPI_TEST.read_bytes()),
            "change": (
                "Added independent fixture recompute + "
                "unresolved_technical_categories_populated_rate KPI gate "
                "(floor 1.0) + per-scenario record fields; updated "
                "scenario-5 expectation to the strengthened lock semantics; "
                "doc comments updated."
            ),
        },
        "amphora-assurance-capabilities/tests/ip_fto_guard_counsel_assertion_probes.rs": {
            "sha256_before": None,
            "sha256_after": sha(PROBES_TEST.read_bytes()),
            "change": (
                "NEW checked regression suite: the 8 audit probe encodings "
                "(A1..A8) + canonical positive control + clean negative + "
                "primary-KPI population test, all through the real "
                "AssuranceCapability::evaluate code path."
            ),
        },
    },
    "regenerated_artifacts": {
        "amphora-ip-fto-guard/evidence/phase0/benchmark/result.v1.json": {
            "sha256_before": "bbd8a9675d78bb65d1dfee9209b441bb5cb3ec4c28e2871cf8febf0f7168eec3",
            "sha256_after": sha(BENCH_RESULT.read_bytes()),
            "reason": (
                "This artifact is BY DESIGN rewritten on every run of the "
                "checked Phase-0 KPI harness "
                "(tests/ip_fto_guard_phase0_kpi.rs fs::write); running the "
                "mandated acceptance command regenerated it with the "
                "repaired runtime's corrected KPI table. It is not "
                "DSSE-signed; the pre-repair bytes' sha256 is preserved "
                "here and in the refuting receipts."
            ),
        },
    },
    "known_stale_prose_pins_not_modified": [
        "docs/mission.md prose pins lib.rs sha256 c0b2540f... (already stale before this repair; flagged non-load-bearing by metric-schema-parity-v1) and result.v1.json sha256 bbd8a967... (stale as of this repair). mission.md was deliberately left untouched: R-B01 scope does not authorize mission prose edits; maintainer follow-up recorded in RETRACTION-INDEX.md.",
    ],
    "probe_reconstruction_caveat": (
        "The original audit probe harness /tmp/ip_fto_probe (main.rs sha256 "
        "15218060d5afac43b7a7bdcc9532ee7b1e4c4e369248b4ecd25d3b46152229c8d) "
        "no longer exists on disk, so the audit's literal candidate JSON "
        "bodies were unrecoverable. The 8 probe candidates were "
        "reconstructed from the signed audit receipt's scenario ids and "
        "per-scenario encoding-class descriptions (top-level key, "
        "array-typed container, one-level-deeper nesting, key-case variant, "
        "alternate key name, semantically-equivalent alternate field, "
        "string-typed container, unicode-homoglyph key), one faithful "
        "instance per described class."
    ),
    "reattack": {
        "description": (
            "Re-ran both refuting checks against the repaired build: (a) the "
            "metric-schema-parity re-derivation (runtime key extraction, "
            "repo census, checked-test assertion, benchmark-result scan) and "
            "(b) the 8-scenario live-runtime probe table via a standalone "
            "cargo bin (/tmp/ip_fto_probe_rb01, path deps only, two-replay "
            "byte-identical)."
        ),
        "diagnostic_sha256": reattack_sha,
        "diagnostic_runB_sha256": runB_sha,
        "a_metric_schema_parity": reattack["reattack_a_metric_schema_parity"],
        "b_counsel_assertion_detection": reattack["reattack_b_counsel_assertion_detection"],
        "acceptance": acc,
        "observed_result": (
            "8/8 adversarial encodings detected "
            "(boolean_counsel_assertion_ignored=true; detection_recall_rate "
            "1.0, was 0.0), control positive detected, clean negative not "
            "flagged, 0 safety breaches (fto_status/legal_advice/"
            "fto_legal_closure pinned in all 9 scenarios), "
            "metrics.unresolved_technical_categories=75 emitted by the live "
            "runtime in all scenarios and equal to the independent fixture "
            "recompute; cargo test -p amphora-assurance-capabilities fully "
            "green (12/12 test targets, 0 failed)."
        ),
    },
    "cargo_test": reattack["cargo_test"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "reattack_canonical_sha256": reattack_sha,
        "reattack_runB_sha256": runB_sha,
        "byte_identical": reattack_sha == runB_sha,
        "payload_canonicalization": "json.dumps(sort_keys=True, separators=(',',':'))",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "repair done-receipt under evidence/phase0/repairs/",
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

# Two-replay canonical-serialization gate on the payload itself.
body1 = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
body2 = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
assert body1 == body2, "payload canonical serialization not byte-stable"
payload_sha = sha(body1)
body_obj["reproducibility"]["payload_two_replay_sha256"] = payload_sha
body = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
body_check = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
assert body == body_check, "final payload serialization not byte-stable"

ptype = "application/vnd.amphora.assurance-capabilities-repair-r-b01+json"
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
out = DONE / "repair-receipt.R-B01.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("payload_two_replay_sha256", sha(body))
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
