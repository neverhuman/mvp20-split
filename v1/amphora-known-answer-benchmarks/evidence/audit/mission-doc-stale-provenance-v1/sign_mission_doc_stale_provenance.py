#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-known-answer-benchmarks mission-doc-stale-provenance-v1
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT
sign a phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest, module-manifest.json,
docs/mission.md, or any signed Phase-0 KPI. Derived key_id cross-checked vs pinned
trust store."""
import base64, hashlib, json, subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-known-answer-benchmarks"
AUDIT = MOD / "evidence/audit/mission-doc-stale-provenance-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

VERIFIER = AUDIT / "verify_mission_doc_stale_provenance.py"
REPORT = AUDIT / "mission_doc_stale_provenance_report.v1.json"
MISSION = MOD / "docs/mission.md"


def sha(b): return hashlib.sha256(b).hexdigest()


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


report = json.loads(REPORT.read_bytes())
assert report["verdict"]["overall"] == "REFUTED", "report did not REFUTE"

# Two-replay: re-run the verifier fresh into a scratch path and confirm byte-stable report.
replay = subprocess.run(
    ["python3", str(VERIFIER)], cwd=str(AUDIT), capture_output=True, text=True
)
assert replay.returncode == 0, replay.stderr
replay_report = json.loads(Path("/tmp/mission_doc_stale_provenance_report.v1.json").read_bytes())
assert replay_report == report, "replay report differs from checked-in report -- not byte-stable"
replay_b_sha = sha(json.dumps(replay_report, indent=2, sort_keys=True).encode())
report_sha = sha(REPORT.read_bytes())
assert replay_b_sha == report_sha, f"replay hash {replay_b_sha} != checked-in {report_sha}"

verifier_sha = sha(VERIFIER.read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())
mission_sha = sha(MISSION.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw()
rev_pub_hex = rev_pub.hex()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"

eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

v = report["live_recompute"]
c = report["claims_extracted"]
rc = report["root_cause_trace"]

body_obj = {
    "schema": "amphora.known-answer-benchmarks.mission-doc-stale-provenance-receipt.v1",
    "receipt_id": "mission-doc-stale-provenance-v1",
    "module_id": "amphora-known-answer-benchmarks",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "LIMITED_SANITY",
    "decision_use_ceiling": "AUDIT_ONLY",
    "attacked_claim": {
        "location": "amphora-known-answer-benchmarks/docs/mission.md",
        "section": "Honest current state / Current benchmark result",
        "mission_md_sha256_at_attack_time": mission_sha,
        "quoted_text_1": "The live checked implementation is native Rust at "
            "`amphora-assurance-capabilities/src/lib.rs` with SHA-256 "
            f"`{c['lib_rs_pinned_sha256']}`.",
        "quoted_text_2": "It emits a byte-stable canonical receipt at "
            f"`{c['result_path_claimed']}` (SHA-256 `{c['result_pinned_sha256']}`).",
        "quoted_text_3": f"The Phase-0 KPI receipt lives at `{c['kpi_path_claimed']}`.",
    },
    "hypothesis_advanced": "Known answers expose arithmetic, unit, and applicability "
        "regressions (module mission). This audit exercises the module's OWN standing "
        "documentation as a known-answer target: mission.md pins exact SHA-256 hashes "
        "and file paths as evidence of a live, checked implementation; those pins are "
        "themselves independently re-derivable and falsifiable exactly like any other "
        "known-answer control.",
    "falsification_criterion": {
        "refuted_if": "any of the three hash/path claims in mission.md's 'Current "
            "benchmark result' section fails to reproduce against the live on-disk "
            "state, AND the mismatch is not attributable to a mission.md typo alone "
            "(i.e. the pinned value traces to a real but non-live artifact).",
        "survives_if": "all three pinned hashes/paths reproduce bit-exact against the "
            "live tree.",
    },
    "design": {
        "method": "independent SHA-256 recompute of every hash-pinned artifact named in "
            "mission.md's Current-benchmark-result section, existence check of the "
            "claimed live KPI receipt path, portfolio-wide grep to trace any stale hash "
            "to its true source, and a full git log walk of every tracked revision of "
            "the pinned implementation file to rule out simple timing coincidence.",
        "gate_arithmetic": "hashlib.sha256 byte-exact only; no floating point; report is "
            "regenerated from scratch on replay and asserted byte-identical (two-replay "
            "gate) before signing.",
    },
    "results": {
        "lib_rs_identity_pin": {
            "verdict": report["verdict"]["lib_rs_identity_pin"],
            "pinned_sha256": c["lib_rs_pinned_sha256"],
            "live_sha256": v["lib_rs_live_sha256"],
            "matches_any_tracked_git_revision": report["lib_rs_provenance_search"]["matches_any_tracked_git_revision"],
            "note": "The pinned hash does not match the current file, nor any of the "
                "4 git-tracked revisions of amphora-assurance-capabilities/src/lib.rs "
                "found in history (baseline 2026-08-03 plus autocommits 2026-08-05, "
                "2026-08-06, 2026-08-11). The identical pinned hash is also copy-pasted "
                "verbatim into at least 7 OTHER modules' mission.md files (source-ledger, "
                "redteam-audit, sourceability-ehs, report-packager, ip-fto-guard, "
                "evidence-intake-validator, cro-protocol-packager) because they share the "
                "same underlying lib.rs -- meaning this staleness is systemic across the "
                "portfolio's mission.md corpus, not unique to this module, and none of "
                "the mission.md files were updated across 3 subsequent commits to the "
                "file they claim to pin.",
        },
        "benchmark_result_pin": {
            "verdict": report["verdict"]["benchmark_result_pin"],
            "pinned_sha256": c["result_pinned_sha256"],
            "live_sha256": v["result_v1_live_sha256"],
            "traced_to": rc["result_hash_traced_to_superseded_file"],
            "note": "The pinned hash does NOT match the live evidence/phase0/benchmark/"
                "result.v1.json (has been 3f2f6853... since at least 2026-08-03, per an "
                "independent prior audit receipt evidence/audit/arith-volume-solids-"
                "mass-basis-conflation-v1/receipt.v1.dsse.json#attacked_result_sha256). "
                "It instead matches the internal benchmark_result_sha256 field of "
                "evidence/superseded/supersession-82a1fbbd.../phase0/kpis/known-answer-"
                "benchmarks-audit-kpi.v1.json, a KPI draft formally superseded for reason "
                "STALE_UNSIGNED_PREPARATION_REISSUE and flagged unsigned_preparation_"
                "only=true in its own supersession record -- i.e. mission.md is citing "
                "byte-provenance from a retracted, never-signed preparation artifact as "
                "though it were the live benchmark result.",
        },
        "kpi_receipt_path_claim": {
            "verdict": report["verdict"]["kpi_receipt_path_claim"],
            "claimed_path": c["kpi_path_claimed"],
            "exists_at_claimed_path": v["kpi_file_exists_at_claimed_live_path"],
            "note": "evidence/phase0/kpis/ contains only RETRACTION-INDEX.md; the file "
                "mission.md names is absent from the live tree and exists solely under "
                "evidence/superseded/.",
        },
        "control_receipt_pin_for_contrast": {
            "verdict": report["verdict"]["control_receipt_pin"],
            "pinned_sha256": c["control_receipt_pinned_sha256"],
            "live_sha256": v["control_receipt_live_sha256"],
            "note": "Included as a positive contrast: this fourth hash pin in the SAME "
                "mission.md paragraph DOES still match live state, showing the failure "
                "is not uniform document rot across every citation but a specific "
                "desync following the 2026-08-03/08-04 supersession + harness fix that "
                "was never propagated back into the prose.",
        },
    },
    "root_cause": "Commit history shows evidence/phase0/benchmark/result.v1.json and the "
        "harness test amphora-assurance-capabilities/tests/known_answer_benchmarks_"
        "phase0_kpi.rs were both touched on 2026-08-04 (git commit 3cf79e2) by a fix "
        "(in-source comment 'SCHEMA-ERA FIX (B2)') that stopped the harness from writing "
        "its KPI-shaped output to the shipped evidence path at all -- because doing so "
        "collided with the separate phase0-evaluation verifier's schema and 'silently "
        "dropped the module out of phase0_count'. The harness now writes only to a "
        "per-target cargo scratch tmpdir and 'never mutates shipped evidence'. mission.md "
        "(unchanged since 2026-07-22, predating this fix) still describes the harness as "
        "the live emitter of evidence/phase0/benchmark/result.v1.json at a hash that "
        "traces to the pre-fix, already-superseded, never-signed KPI draft.",
    "does_not_close": [
        "Does not establish that the module's substantive KPI numbers (13/14 "
            "VERIFIED_PASS, 6/6 arithmetic subset, etc.) are themselves wrong -- the "
            "live result.v1.json and the compile-time-embedded control_by_control_"
            "receipt.v1.json (still hash-matched) report the same figures mission.md "
            "quotes; this is a provenance/citation-integrity break, not (on this "
            "evidence alone) a numeric regression.",
        "Does not modify docs/mission.md, module-manifest.json, or any signed Phase-0 "
            "KPI; flags them for human/repair-fire correction only.",
        "Does not establish whether the other 7 modules sharing the same stale lib.rs "
            "citation have the same or different downstream severity; out of scope for "
            "this module-scoped fire.",
    ],
    "artifacts": {
        "report": {"path": "amphora-known-answer-benchmarks/evidence/audit/mission-doc-stale-provenance-v1/mission_doc_stale_provenance_report.v1.json", "sha256": report_sha},
        "verifier": {"path": "amphora-known-answer-benchmarks/evidence/audit/mission-doc-stale-provenance-v1/verify_mission_doc_stale_provenance.py", "sha256": verifier_sha},
    },
    "provenance": {"module_manifest_sha256": manifest_sha},
    "two_replay_gate": {
        "replays": 2, "byte_stable": True,
        "replay_a_report_sha256": report_sha, "replay_b_report_sha256": replay_b_sha,
    },
    "edits_portfolio_manifest": False,
    "flips_front_matter": False,
    "promotes_authority": False,
    "human_dual_identity_ceremony_performed": False,
    "signing_key": {
        "authority": "AUDIT_ONLY", "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing only; no dual-identity ceremony",
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "trust_anchored_in_phase0_promotion_store": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
    "verdict": "REFUTED",
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.known-answer-benchmarks-mission-doc-stale-provenance-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
for k in ("schema", "receipt_id", "module_id", "authority", "authority_ceiling"):
    receipt[k] = body_obj[k]
AUDIT.mkdir(parents=True, exist_ok=True)
out = AUDIT / "receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("report_sha256", report_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_len", len(receipt["signature"]["signatures"][0]["sig"]))
print("signature_verified", True)
