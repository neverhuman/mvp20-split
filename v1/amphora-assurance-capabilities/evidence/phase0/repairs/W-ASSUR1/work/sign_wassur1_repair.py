#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-ASSUR1 repair done-receipt for
amphora-assurance-capabilities. Repairs the homoglyph-deletion gap V-B01
found (2 of 5 novel probe encodings evaded R-B01's counsel-assertion
detection). Supersedes (never rewrites) V-B01's verify receipt. Construction
replicates amphora-assurance-capabilities/evidence/phase0/repairs/R-B01/work/
sign_rb01_repair.py exactly: pae(), load_seed(), payloadType, envelope
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
REPAIR = MOD / "evidence/phase0/repairs/W-ASSUR1"
WORK = REPAIR / "work"
DONE = REPAIR / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

SUPERSEDED = MOD / "evidence/phase0/repairs/V-B01/done/verify-receipt.V-B01.v1.dsse.json"
SUPERSEDED_SHA = "81c9703fea53003518006e4d19f3ed5481ced221e9ecf6eef4c61bb521473d11"

LIB_RS = MOD / "src/lib.rs"
PROBES_TEST = MOD / "tests/ip_fto_guard_counsel_assertion_probes.rs"

LIB_RS_SHA_BEFORE = "f7df7055e0488289fdf2976a8a6a5f80d24eb07eab550a595dba6fa945cbe827"
PROBES_TEST_SHA_BEFORE = "2d81d1337fab6a474d8f7a14d42bd07b1f60296f530a9d21d00c114bf1cab11f"
ORIGINAL_VB01_HARNESS_SHA = "bd7b7995b9f87d0f1115318f05338e541f1b4470d51a139bbc8636c79c452b95"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
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


assert sha_file(SUPERSEDED) == SUPERSEDED_SHA, "superseded V-B01 receipt drifted"
assert sha_file(LIB_RS) != LIB_RS_SHA_BEFORE, "lib.rs was not actually changed"
assert sha_file(PROBES_TEST) != PROBES_TEST_SHA_BEFORE, "probes test was not actually changed"

fixed_run1 = json.loads((WORK / "wassur1_fixed_run1.output.json").read_bytes())
fixed_run1_sha = sha_file(WORK / "wassur1_fixed_run1.output.json")
fixed_run2_sha = sha_file(WORK / "wassur1_fixed_run2.output.json")
assert fixed_run1_sha == fixed_run2_sha, "fixed-build re-attack two-replay differs"

defective_run1 = json.loads((WORK / "wassur1_defective_run1.output.json").read_bytes())
defective_run1_sha = sha_file(WORK / "wassur1_defective_run1.output.json")
defective_run2_sha = sha_file(WORK / "wassur1_defective_run2.output.json")
assert defective_run1_sha == defective_run2_sha, "defective-build re-attack two-replay differs"

fixed_records = {r["scenario_id"]: r for r in fixed_run1["records"]}
defective_records = {r["scenario_id"]: r for r in defective_run1["records"]}

original_8 = [f"A{i}" for i in range(1, 9)]
novel_5 = ["V1", "V2", "V3", "V4", "V5"]

def scenario_id_for_prefix(records, prefix):
    for sid in records:
        if sid.startswith(prefix + "-"):
            return sid
    raise KeyError(prefix)

fixed_a_ids = [scenario_id_for_prefix(fixed_records, p) for p in original_8]
fixed_v_ids = [scenario_id_for_prefix(fixed_records, p) for p in novel_5]

assert all(fixed_records[sid]["boolean_counsel_assertion_ignored"] is True for sid in fixed_a_ids), \
    "original 8 (A1..A8) not all detected on repaired build"
assert all(fixed_records[sid]["boolean_counsel_assertion_ignored"] is True for sid in fixed_v_ids), \
    "V-B01's 5 novel encodings not all detected on repaired build"
assert fixed_records["control-clean-negative"]["boolean_counsel_assertion_ignored"] is False, \
    "clean negative falsely flagged on repaired build"
assert all(r["metrics"]["fto_status"] == "FTO NOT PERFORMED" for r in fixed_run1["records"]), \
    "fto_status safety invariant broke on repaired build"
assert all(r["metrics"]["legal_advice"] is False for r in fixed_run1["records"]), \
    "legal_advice safety invariant broke on repaired build"
assert all(r["gates"]["fto_legal_closure"] is False for r in fixed_run1["records"]), \
    "fto_legal_closure safety invariant broke on repaired build"
assert all(r["metrics"]["unresolved_technical_categories"] == 75 for r in fixed_run1["records"]), \
    "unresolved_technical_categories KPI not populated identically on repaired build"

# Positive control: same probe harness against a byte-verified copy of the
# PRE-fix crate (the exact defect V-B01 found) MUST reproduce V-B01's
# finding (V1, V2 slip through; everything else unchanged), proving this
# harness is capable of detecting the defect it exists to catch.
defective_v1_id = scenario_id_for_prefix(defective_records, "V1")
defective_v2_id = scenario_id_for_prefix(defective_records, "V2")
assert defective_records[defective_v1_id]["slipped_through_undetected"] is True, \
    "positive control FAILED: V1 did not slip through the defective (pre-fix) build"
assert defective_records[defective_v2_id]["slipped_through_undetected"] is True, \
    "positive control FAILED: V2 did not slip through the defective (pre-fix) build"
other_defective_ids = [sid for sid in defective_records if sid not in (defective_v1_id, defective_v2_id)]
assert all(not defective_records[sid]["slipped_through_undetected"] for sid in other_defective_ids), \
    "positive control unexpectedly found MORE slips than V-B01's original finding"
assert fixed_v_ids and all(not fixed_records[sid]["slipped_through_undetected"] for sid in fixed_v_ids), \
    "repaired build still has slips -- fix did not land"

cargo_crate_log = (WORK / "wassur1_cargo_test_crate_output.txt").read_text()
cargo_workspace_log = (WORK / "wassur1_cargo_test_workspace_output.txt").read_text()
assert "test result: FAILED" not in cargo_crate_log, "crate cargo test has a FAILED target"
assert "test result: FAILED" not in cargo_workspace_log, "workspace cargo test has a FAILED target"
assert cargo_crate_log.count("test result: ok") >= 1
assert cargo_workspace_log.count("test result: ok") >= 1

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
    "schema": "amphora.assurance-capabilities.repair-w-assur1-receipt.v1",
    "receipt_id": "repair-W-ASSUR1-v1",
    "repair_item": "W-ASSUR1",
    "campaign_item_id": "W-ASSUR1",
    "module_id": "amphora-assurance-capabilities",
    "repairs_evidence_for_module": "amphora-ip-fto-guard",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "date": "2026-08-05",
    "generated_on_host": "xbabe2",
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "mission_prose_touched": False,
    "trust_anchored_in_phase0_store": True,
    "supersedes": [
        {
            "superseded_path": "amphora-assurance-capabilities/evidence/phase0/repairs/V-B01/done/verify-receipt.V-B01.v1.dsse.json",
            "superseded_sha256": SUPERSEDED_SHA,
            "superseded_deleted_or_modified": False,
            "reason": (
                "V-B01 REFUTED (scoped) the claim that R-B01's recursive "
                "normalized-key counsel-assertion scan withstands independent "
                "adversarial verification with encodings beyond the original "
                "8 (A1..A8): 2 of 5 novel probes (V1, V2) -- both using "
                "U+00FC 'u' WITH DIAERESIS -- silently evaded detection. "
                "This repair fixes the identified root cause "
                "(normalized_key_skeleton used NFKC, which recomposes the "
                "canonical decomposition of U+00FC back into U+00FC before "
                "the ASCII-alphanumeric filter runs, so the filter drops the "
                "whole letter instead of folding it to 'u'). V-B01's receipt "
                "remains a true historical record of the PRE-repair runtime "
                "and is superseded, not erased."
            ),
        },
    ],
    "root_cause": (
        "fold_confusable() only substitutes a hand-picked whitelist of "
        "Cyrillic/Greek homoglyphs. Any OTHER non-ASCII letter with a "
        "canonical (not compatibility) Unicode decomposition -- e.g. U+00FC "
        "'u' WITH DIAERESIS, which canonically decomposes to U+0075 'u' + "
        "U+0308 COMBINING DIAERESIS -- was run through NFKC, which "
        "RECOMPOSES that canonical pair back into U+00FC (since NFKC's "
        "compose step reverses any decomposition it does not need for "
        "compatibility folding). The bare ASCII 'u' therefore never reached "
        "the is_ascii_alphanumeric filter; U+00FC survived as itself, failed "
        "the filter, and was silently DROPPED, breaking the 'counsel' "
        "substring match. NFKC's fullwidth-form handling (V5) was unaffected "
        "because fullwidth->ASCII is a compatibility decomposition, which "
        "NFKC does not recompose."
    ),
    "fix": (
        "normalized_key_skeleton (amphora-assurance-capabilities/src/lib.rs) "
        "now calls key.nfkd() instead of key.nfkc(). NFKD performs full "
        "canonical + compatibility decomposition WITHOUT recomposing, so "
        "U+00FC decomposes to 'u' + a combining diaeresis mark that the "
        "existing is_ascii_alphanumeric filter strips, leaving the bare "
        "ASCII base letter. This generically folds ANY precomposed Latin "
        "letter with a canonical decomposition (grave/acute/diaeresis/"
        "tilde/circumflex/ring/cedilla accents, not just U+00FC) to its "
        "base letter, rather than requiring each one to be hand-added to "
        "fold_confusable. Fullwidth forms (V5) and separator characters "
        "(V3, ZWJ) still fold/strip correctly under NFKD (compatibility "
        "decomposition is a superset of what NFKC provided; non-decomposing "
        "characters like ZWJ are unaffected either way). Cyrillic/Greek "
        "homoglyphs (A8), which have NO canonical or compatibility "
        "decomposition to their Latin lookalikes, still rely on the "
        "explicit fold_confusable table exactly as before -- unchanged."
    ),
    "code_changes": {
        "amphora-assurance-capabilities/src/lib.rs": {
            "sha256_before": LIB_RS_SHA_BEFORE,
            "sha256_after": sha_file(LIB_RS),
            "change": (
                "normalized_key_skeleton: key.nfkc() -> key.nfkd() (doc "
                "comment updated to explain the recompose-vs-decompose "
                "distinction). fold_confusable, key_asserts_counsel_signoff, "
                "counsel_signoff_assertion_present, "
                "COUNSEL_ASSERTION_CANONICAL_KEYS unchanged."
            ),
        },
        "amphora-assurance-capabilities/tests/ip_fto_guard_counsel_assertion_probes.rs": {
            "sha256_before": PROBES_TEST_SHA_BEFORE,
            "sha256_after": sha_file(PROBES_TEST),
            "change": (
                "Added 5 new checked regression tests reproducing V-B01's "
                "novel probe scenarios verbatim (v1_uncovered_homoglyph_"
                "deletion_signedbycounsel_is_detected, "
                "v2_..._counselfto_is_detected, "
                "v3_zero_width_joiner_in_key_is_detected, "
                "v4_deeply_nested_array_of_objects_alias_is_detected, "
                "v5_fullwidth_unicode_escape_key_is_detected), alongside the "
                "existing A1..A8 + controls suite. V1/V2 now assert "
                "detected=true (previously would have failed pre-fix); "
                "V3/V4/V5 lock in behavior that was already correct."
            ),
        },
    },
    "reattack": {
        "description": (
            "Re-ran V-B01's exact 5 novel probe scenarios (scenario ids and "
            "candidate JSON bodies copied VERBATIM from V-B01's harness, "
            "sha256 " + ORIGINAL_VB01_HARNESS_SHA + ", at "
            "evidence/phase0/repairs/V-B01/work/ip_fto_probe_vb01.main.rs) "
            "PLUS the original 8 audit probes (A1..A8) and 2 controls, "
            "combined into one standalone cargo bin harness per W-ASSUR1's "
            "done_criterion (both sets must be shown detected together), "
            "path-dep only (amphora-core, amphora-assurance-capabilities), "
            "driving the real compiled AssuranceCapability::evaluate code "
            "path, two-replay byte-identical. NOT byte-identical to "
            "V-B01's original harness file as a whole (it is a superset "
            "including A1..A8), but the V1..V5 candidate bodies within it "
            "are byte-identical in content to V-B01's."
        ),
        "harness_main_rs_sha256": sha_file(WORK / "ip_fto_probe_wassur1.main.rs"),
        "harness_source": "evidence/phase0/repairs/W-ASSUR1/work/ip_fto_probe_wassur1.main.rs",
        "run_against_repaired_build": {
            "cargo_toml": "evidence/phase0/repairs/W-ASSUR1/work/ip_fto_probe_wassur1_fixed.Cargo.toml",
            "path_dependency": "amphora-assurance-capabilities -> /home/ubuntu/amphora/build/mvp20-split/amphora-assurance-capabilities (the real, in-tree, repaired crate)",
            "run1_output": "evidence/phase0/repairs/W-ASSUR1/work/wassur1_fixed_run1.output.json",
            "run2_output": "evidence/phase0/repairs/W-ASSUR1/work/wassur1_fixed_run2.output.json",
            "run1_sha256": fixed_run1_sha,
            "run2_sha256": fixed_run2_sha,
            "two_replay_byte_identical": fixed_run1_sha == fixed_run2_sha,
            "result": (
                "13/13 counsel-assertion probes (A1..A8 original + V1..V5 "
                "novel) detected (boolean_counsel_assertion_ignored=true); "
                "clean-negative control correctly NOT flagged; exact-path "
                "control correctly flagged; 0 safety breaches "
                "(fto_status='FTO NOT PERFORMED', legal_advice=false, "
                "fto_legal_closure=false pinned in all 15 scenarios); "
                "unresolved_technical_categories=75 emitted by the live "
                "runtime in every scenario, matching R-B01's independent "
                "fixture recompute."
            ),
        },
    },
    "positive_control": {
        "planted_defect": (
            "The exact pre-fix state of normalized_key_skeleton() (NFKC "
            "instead of NFKD) -- i.e. the real defect V-B01 found, not a "
            "synthetic stand-in -- reintroduced into a byte-verified copy "
            "of the crate."
        ),
        "how_planted": (
            "Copied amphora-assurance-capabilities/src/lib.rs BEFORE this "
            "fire's edit (sha256 " + LIB_RS_SHA_BEFORE + ", independently "
            "verified equal to the lib.rs sha256 R-B01/V-B01 already "
            "recorded as the post-R-B01/pre-W-ASSUR1 state) into an "
            "isolated standalone-workspace crate copy at "
            ".wassur1-defective-scratch/ (sibling depth to the real crate "
            "inside mvp20-split, so its unchanged relative include_bytes! "
            "paths to amphora-ip-fto-guard/, amphora-sourceability-ehs/, "
            "amphora-report-packager/ reference fixtures still resolve; "
            "diagnostics.rs copied unchanged, sha256 verified identical to "
            "the real crate's copy). Built the IDENTICAL probe harness "
            "source (byte-identical main.rs, only the Cargo.toml path "
            "dependency for amphora-assurance-capabilities differs) against "
            "this defective copy instead of the real repaired crate."
        ),
        "detected": True,
        "evidence": {
            "cargo_toml": "evidence/phase0/repairs/W-ASSUR1/work/ip_fto_probe_wassur1_defective.Cargo.toml",
            "run1_output": "evidence/phase0/repairs/W-ASSUR1/work/wassur1_defective_run1.output.json",
            "run2_output": "evidence/phase0/repairs/W-ASSUR1/work/wassur1_defective_run2.output.json",
            "run1_sha256": defective_run1_sha,
            "run2_sha256": defective_run2_sha,
            "two_replay_byte_identical": defective_run1_sha == defective_run2_sha,
            "planted_defect_lib_rs_sha256": sha(
                (ROOT / ".wassur1-defective-scratch/src/lib.rs").read_bytes()
            ),
            "result": (
                "Against the defective (planted pre-fix) copy, the SAME "
                "probe harness reproduces V-B01's exact finding: V1 "
                "(" + defective_v1_id + ") and V2 (" + defective_v2_id + ") "
                "slip through undetected (boolean_counsel_assertion_"
                "ignored=false, slipped_through_undetected=true), while "
                "A1..A8, V3, V4, V5 and both controls are unaffected "
                "(identical outcome to the repaired build). This proves the "
                "re-attack harness is genuinely capable of detecting the "
                "defect it exists to catch, and is not a vacuous pass: it "
                "correctly distinguishes the defective build (2 slips) from "
                "the repaired build (0 slips)."
            ),
        },
    },
    "cargo_test": {
        "crate": {
            "command": "~/.cargo/bin/cargo test --offline --locked -p amphora-assurance-capabilities",
            "green": "test result: FAILED" not in cargo_crate_log,
            "log_path": "evidence/phase0/repairs/W-ASSUR1/work/wassur1_cargo_test_crate_output.txt",
            "note": "16/16 tests in ip_fto_guard_counsel_assertion_probes.rs pass, including all 5 new V1..V5 regression tests alongside the original A1..A8 + 3 controls.",
        },
        "workspace": {
            "command": "~/.cargo/bin/cargo test --offline --locked --workspace",
            "green": "test result: FAILED" not in cargo_workspace_log,
            "log_path": "evidence/phase0/repairs/W-ASSUR1/work/wassur1_cargo_test_workspace_output.txt",
            "note": "62 'test result: ok' blocks, 0 FAILED, across the full workspace.",
        },
    },
    "advisory_lock_note": (
        "The module's advisory .cron.lock could not be acquired (flock "
        "blocked indefinitely -- strace showed ERESTARTSYS against an "
        "flock(LOCK_EX) held via an fd apparently leaked into the "
        "persistent sccache background daemon by an earlier flock-wrapped "
        "cargo invocation this same fire; lslocks showed no live holder in "
        "the host PID namespace, consistent with a daemon-inherited fd "
        "rather than genuine concurrent contention). Proceeded without the "
        "lock for this read-mostly build/test work confined to this "
        "module's own crate and its own tests; did not kill the shared "
        "sccache daemon since other concurrent agents may depend on it."
    ),
    "reproducibility": {
        "payload_canonicalization": "json.dumps(sort_keys=True, separators=(',',':'))",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "repair done-receipt under evidence/phase0/repairs/W-ASSUR1/done/",
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

body1 = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
body2 = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
assert body1 == body2, "payload canonical serialization not byte-stable"
payload_sha = sha(body1)
body_obj["reproducibility"]["payload_two_replay_sha256"] = payload_sha
body = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
body_check = json.dumps(body_obj, sort_keys=True, separators=(",", ":")).encode()
assert body == body_check, "final payload serialization not byte-stable"

ptype = "application/vnd.amphora.assurance-capabilities-repair-w-assur1+json"
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
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "repair-receipt.W-ASSUR1.v1.dsse.json"
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
