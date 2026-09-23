#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-A01 repair done-receipt (amphora-ingredient-library).

Construction replicated from
amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py:
pae(), load_seed(), payloadType naming, envelope fields, trust-store key
pinning. Signs under evidence/phase0/repairs/R-A01/done/; does NOT promote
authority, flip scientific_readiness, or modify any existing receipt, the
portfolio manifest, any locked dataset, or the falsification ledger.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-ingredient-library"
REPAIR = MOD / "evidence/phase0/repairs/R-A01"
WORK = REPAIR / "work"
DONE = REPAIR / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


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


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["repair_item"] == "R-A01"
d1 = diag["defect1_mission_citation_repair"]
d2 = diag["defect2_solid_band_tightening"]
assert d1["reattack"]["two_runs_byte_agree"] is True
assert d1["reattack"]["mission_citation_matches_live_result"] is True
assert d1["reattack"]["stale_hash_absent_from_mission_prose"] is True
assert d2["reattack_gap_zone_probes"]["n_probes_now_rejected"] == 4

# superseded artifact must remain byte-identical (SUPERSEDE, NEVER REWRITE)
cc_receipt = MOD / ("evidence/audit/constant-crosscheck-v1/"
                    "constant-crosscheck-receipt.v1.dsse.json")
cc_sha_now = sha(cc_receipt.read_bytes())
assert cc_sha_now == d2["superseded_receipt"]["sha256"], "superseded receipt was modified!"

harness_sha = sha((WORK / "run_repair_ra01.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
assert eval_key_id.startswith("phase0-evaluator-3ef6b35"), eval_key_id
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key not pinned in phase0 trust store"


def build_payload():
    return {
        "schema": "amphora.ingredient-library.repair-R-A01-done-receipt.v1",
        "receipt_id": "repair-R-A01-done",
        "module_id": "amphora-ingredient-library",
        "repair_item": "R-A01",
        "repair_mode": "interactive-2026-08-03",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "EVIDENCE_ONLY",
        "phase": "PRE_PHASE_0",
        "date": "2026-08-03",
        "generated_on_host": "xbabe2",
        "supersedes": {
            "superseded_path": d2["superseded_receipt"]["path"],
            "superseded_sha256": d2["superseded_receipt"]["sha256"],
            "superseded_deleted_or_modified": False,
            "reason": (
                "constant-crosscheck-v1 Check-1's solid_type1_epoxy EEW admissibility "
                "band [383.5, 667.8] g/eq (n in [1.5, 3.5], not tabulated in its own "
                "cited literature) was refuted 2026-08-03T14:06 by "
                "eew-solid-band-mislabel-gap-v1 as 2.84x wider than the Hexion "
                "HCD-4022 manufacturer TDS band already recorded in facts.json for "
                "the identical fact; 4/4 gap-zone probe values passed undetected. "
                "This receipt supersedes that sub-check with the TDS band "
                "[450.0, 550.0] g/eq; the original receipt remains in place, "
                "unmodified, for the audit trail. Scope: supersedes ONLY the "
                "solid_type1_epoxy sub-check of Check-1; the liquid-DGEBA sub-check, "
                "Check-2 densities, pigment diagnostic and AHEW honest-negative are "
                "NOT superseded."),
        },
        "defect1_mission_citation_repair": {
            "refuting_receipt": d1["refuting_receipt"],
            "stale_cited_result_sha256": d1["stale_cited_result_sha256"],
            "corrected_cited_result_sha256": d1["corrected_cited_result_sha256"],
            "derivation": (
                "Live sha re-derived by re-running the parity receipt's exact "
                "re-execution command twice as independent OS processes "
                "(cargo test --workspace --locked --package "
                "amphora-formulation-capabilities --test ingredient_library_phase0_kpi "
                "under flock on .cron.lock) and hashing "
                "evidence/phase0/benchmark/result.v1.json after each run; both runs "
                "byte-agree at the corrected sha. The parity audit had already "
                "confirmed all 13 numeric KPI bullets correct, so only the citation "
                "block was edited (mission.md PROSE only; front-matter untouched, "
                "asserted byte-identical)."),
            "mission_md_sha256_before": d1["mission_md_sha256_before"],
            "mission_md_sha256_after": d1["mission_md_sha256_after"],
            "front_matter_unchanged": d1["front_matter_unchanged"],
            "superseded_kpi_receipt_disclosed": {
                "formerly_cited_live_path":
                    "evidence/phase0/kpis/ingredient-library-ledger-quarantine-kpi.v1.json",
                "actual_location":
                    "evidence/superseded/supersession-6aba291aa333b4c3ae40d584ebe0fe295"
                    "5e6949a33cb2506a5e7113021fff1c1/phase0/kpis/"
                    "ingredient-library-ledger-quarantine-kpi.v1.json",
                "supersession_reason": "STALE_UNSIGNED_PREPARATION_REISSUE",
            },
        },
        "defect2_corrected_values": {
            "corrected_band": d2["corrected_band"],
            "corrected_check1_per_constant": d2["corrected_check1_per_constant"],
            "catalog_value_status": d2["catalog_value_status"],
            "refuting_receipt": d2["refuting_receipt"],
            "liquid_dgeba_subcheck_unchanged": d2["liquid_dgeba_subcheck_unchanged"],
        },
        "reattack_results": {
            "note": "Re-run of the checks from both refuting receipts against the "
                    "repaired state (IRON RULE 8).",
            "defect1_parity_recheck": d1["reattack"],
            "defect2_gap_zone_recheck": d2["reattack_gap_zone_probes"],
        },
        "headline": diag["headline"],
        "closes": diag["closes"],
        "does_not_close": diag["does_not_close"],
        "modifies_existing_receipts": False,
        "modifies_manifest": False,
        "modifies_module_manifest": False,
        "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False,
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "trust_anchored_in_phase0_store": True,
        "reproducibility": {
            "two_replay_sha256_gate": "PASS",
            "canonical_diagnostic_sha256": diag_sha,
            "runB_diagnostic_sha256": sha(runB),
            "byte_identical": canon == runB,
            "replay_method": (
                "run_repair_ra01.py builds the full diagnostic twice (including an "
                "idempotent mission-repair pass and independent cargo-test "
                "re-executions), serializes each with json.dumps(sort_keys=True, "
                "separators=(',',':')), asserts byte-equality, and records the sha256."),
        },
        "provenance": {
            "harness_sha256": {"work/run_repair_ra01.py": harness_sha},
            "superseded_receipt_sha256_verified_intact_at_signing": cc_sha_now,
        },
        "signing_key": {
            "role": "PHASE0_EVALUATOR",
            "key_id": eval_key_id,
            "public_key_hex": eval_pub_hex,
            "used_for": "AUDIT_ONLY repair done-receipt under evidence/phase0/repairs/",
            "signs_phase0_evaluation_or_review": False,
            "derives_pinned_trust_store_key_id": bool(eval_pin),
        },
        "reviewer_reference": {
            "role": "PHASE0_INTERNAL_REVIEWER",
            "key_id": rev_key_id,
            "public_key_hex": rev_pub_hex,
            "derives_pinned_trust_store_key_id": bool(rev_pin),
            "reviewer_signature_present": False,
            "note": "Reviewer key referenced for provenance only; no independent "
                    "human review performed.",
        },
    }


# two-replay gate on the signed payload itself
body1 = json.dumps(build_payload(), sort_keys=True, separators=(",", ":")).encode()
body2 = json.dumps(build_payload(), sort_keys=True, separators=(",", ":")).encode()
assert body1 == body2, "payload two-replay bytes differ"
body = body1
ptype = "application/vnd.amphora.ingredient-library-repair-r-a01-done-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "repair-R-A01-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# ---- SELF-VERIFY (IRON RULE 5): reload from disk, rebuild PAE, verify ------
reloaded = json.loads(out.read_bytes())
env2 = reloaded["signature"]
assert env2["signatures"][0]["keyid"].startswith("phase0-evaluator-3ef6b35"), \
    env2["signatures"][0]["keyid"]
pub_from_seed = Ed25519PrivateKey.from_private_bytes(
    load_seed(EVAL_SEED)).public_key().public_bytes_raw()
Ed25519PublicKey.from_public_bytes(pub_from_seed).verify(
    base64.standard_b64decode(env2["signatures"][0]["sig"]),
    pae(env2["payloadType"], base64.standard_b64decode(env2["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_diagnostic_sha256", diag_sha)
print("payload_sha256", sha(body))
print("receipt_sha256", sha(out.read_bytes()))
print("signature_self_verified_from_disk", True)
