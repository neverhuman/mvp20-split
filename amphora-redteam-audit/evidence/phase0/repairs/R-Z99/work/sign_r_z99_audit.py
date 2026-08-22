#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit R-Z99 batch audit of Wave R
interactive doc/prose repair done receipts (CAMPAIGN item R-Z99, fire
20260805T020002-1899481-279e45d82264). AUDIT_ONLY: signs the audit receipt
under evidence/phase0/repairs/R-Z99/done/. Does not modify the master
manifest, any locked dataset, or any other module's files -- this is a
read-only audit over 9 already-signed receipts across 8 other modules.
Uses the pinned PHASE0_EVALUATOR key, cross-checked against
config/phase0-trust-store.v1.json.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/R-Z99/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/R-Z99/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


runA_bytes = (WORK / "diagnostic.runA.json").read_bytes()
runB_bytes = (WORK / "diagnostic.runB.json").read_bytes()
byte_identical = runA_bytes == runB_bytes
assert byte_identical, "two-replay bytes differ -- NOT stable, do not sign"
diag = json.loads(runA_bytes)
canon_sha = sha(runA_bytes)

harness_sha = sha((WORK / "run_r_z99_audit.py").read_bytes())

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
assert eval_pin, "evaluator key_id does not match pinned trust store"

verdict = diag["verdict"]

body_obj = {
    "schema": "amphora.redteam-audit.r-z99-wave-r-batch-audit-receipt.v1",
    "receipt_id": "r-z99-wave-r-interactive-repairs-batch-audit-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "R-Z99",
    "fire_id": "20260805T020002-1899481-279e45d82264",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_other_module_files": False,
    "claim_under_attack": diag["claim_under_attack"],
    "attack_description": (
        "Batch mechanical audit of all 9 done receipts filed under "
        "*/evidence/phase0/repairs/R-A0{1,2,3,4,9}/done/ and R-A1{0,1,3}/done/ "
        "across 8 modules (amphora-ingredient-library R-A01, "
        "amphora-cure-potlife-gate R-A02, amphora-viscosity-score R-A03, "
        "amphora-sourceability-ehs R-A04, amphora-molecule-property R-A09, "
        "amphora-solvency-score R-A10, amphora-design-rule-score R-A11, "
        "amphora-molecule-property R-A11 [duplicate id, distinct repair -- see "
        "observations_non_fatal], amphora-ip-fto-guard R-A13). For each "
        "receipt: (1) every path cited in its supersedes block(s) was "
        "sha256-recomputed live and checked against the declared "
        "superseded_sha256 -- directly for artifacts claimed byte-unmodified "
        "(other receipts, fixtures, a synthesized 21-file KPI-directory "
        "listing digest for R-A09), or against a preserved pre-repair backup "
        "file for the two receipts (R-A02, R-A10) that intentionally amended "
        "docs/mission.md prose going forward; (2) each receipt's DSSE "
        "envelope was rebuilt with the DSSEv1 PAE construction and verified "
        "against the pinned PHASE0_EVALUATOR key derived live from the seed "
        "and cross-checked against config/phase0-trust-store.v1.json, "
        "including that the signature's keyid equals the pinned key_id; (3) "
        "each of the 8 owning modules' live docs/mission.md front-matter "
        "(phase, scientific_readiness, authority_ceiling, "
        "operational_readiness) was diffed against that module's entry in "
        "the most recent portfolio rank snapshot "
        "(reports/portfolio-status-2026-08-03/data/rank.json) to catch a "
        "promotion smuggled in via a repair; additionally, for R-A02 and "
        "R-A10, the front-matter block was diffed byte-for-byte between the "
        "preserved pre-repair mission.md and the live mission.md to confirm "
        "the repair rule (PROSE edits allowed, front-matter never) was "
        "actually honored, not just self-declared; (4) 3 receipts (R-A04, "
        "R-A11/design-rule-score, R-A13) were read in full and hand-judged "
        "for substantive vs boilerplate corrected-claim content."
    ),
    "pre_registered_refutation_criteria": diag["pre_registered_refutation_criteria"],
    "verdict": verdict,
    "pass_fail_table": [
        {
            "receipt_path": r["receipt_path"],
            "module": r["module"],
            "repair_item": r["repair_item"],
            "dsse_verify_pass": r["dsse_verify"]["pass"],
            "supersedes_pass": r["supersedes_pass"],
            "n_supersedes_entries_checked": r["supersedes_entries_checked"],
            "mission_frontmatter_parity_pass": r["mission_frontmatter_parity_pass"],
            "mission_frontmatter_prose_edit_identity_check": r["mission_frontmatter_prose_edit_identity_check"],
            "row_pass": r["row_pass"],
        }
        for r in diag["rows"]
    ],
    "supersedes_check_detail": [
        {"receipt_path": r["receipt_path"], "supersedes_results": r["supersedes_results"]}
        for r in diag["rows"]
    ],
    "dsse_verify_detail": [
        {"receipt_path": r["receipt_path"], "dsse_verify": r["dsse_verify"]}
        for r in diag["rows"]
    ],
    "module_frontmatter_parity_vs_rank_snapshot": diag["module_frontmatter_parity"],
    "rank_snapshot_used": "reports/portfolio-status-2026-08-03/data/rank.json",
    "spot_check_substantiveness_judgment": diag["spot_check_substantiveness_judgment"],
    "observations_non_fatal": diag["observations_non_fatal"],
    "summary_counts": diag["summary_counts"],
    "interpretation": (
        "CLAIM_SURVIVED. All 9/9 Wave R interactive-repair done receipts "
        "pass all four mechanical checks: every supersedes-block path "
        "resolves to its declared superseded_sha256 (either the live "
        "artifact or, for the two mission.md prose amendments R-A02/R-A10, "
        "a preserved pre-repair backup whose bytes match); every DSSE "
        "envelope verifies against the pinned PHASE0_EVALUATOR key with a "
        "matching keyid; every owning module's live mission.md front-matter "
        "matches its rank-snapshot entry exactly (no promotion smuggled in), "
        "and for the two prose-editing repairs the front-matter is byte-"
        "identical between the pre-repair backup and the live file "
        "(independently confirming, not just trusting, the repairs' own "
        "front_matter_unchanged claims); and all 3 hand-read spot-checked "
        "receipts (R-A04, R-A11/design-rule-score, R-A13) contain specific, "
        "independently-verifiable corrected claims backed by named sources "
        "(29 CFR 1910.1000 Table Z-2, EP2653485A2 claim-1 text, a live "
        "anchored-reissue artifact + freshly-created RETRACTION-INDEX.md), "
        "not boilerplate. This attack was genuinely capable of falsifying: "
        "an earlier iteration of this same audit harness (before two bugs "
        "were fixed -- a directory-vs-file dispatch bug on R-A09's "
        "surface_listing, and a wrong parent-directory depth when searching "
        "for R-A02's unstructured backup pointer) produced a false "
        "CLAIM_REFUTED on 2/9 rows, demonstrating the check is sensitive "
        "enough to catch a real mismatch, not a rubber stamp."
    ),
    "does_not_close": [
        "Whether the corrected numeric/scientific content of each repair is "
        "itself correct against ground truth -- this audit checks mechanical "
        "soundness (hash integrity, signature validity, front-matter "
        "non-promotion, and presence of substantive vs boilerplate prose), "
        "not independent re-derivation of each repair's underlying science.",
        "Substantiveness of the 6 receipts NOT hand-read in full (R-A01, "
        "R-A02, R-A03, R-A09, R-A10, R-A11/molecule-property) beyond the "
        "structural review captured in this receipt's pass_fail_table and "
        "supersedes_check_detail -- the objective's item (4) calls for a "
        "3-receipt spot-check, which was performed; a full 9/9 substantive "
        "read was not.",
        "The R-A11 duplicate repair_item id across two modules is flagged as "
        "a campaign-numbering collision (observations_non_fatal); resolving "
        "the collision itself is out of this audit's scope.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "canonical_diagnostic_sha256": canon_sha,
        "runA_diagnostic_sha256": sha(runA_bytes),
        "runB_diagnostic_sha256": sha(runB_bytes),
        "byte_identical": byte_identical,
        "harness_sha256": harness_sha,
        "harness_path": "amphora-redteam-audit/evidence/phase0/repairs/R-Z99/work/run_r_z99_audit.py",
        "determinism": "pure filesystem read + sha256 + DSSE-verify + JSON "
                        "front-matter parse over the live module trees and a "
                        "pinned rank snapshot at read time; no RNG, no model "
                        "fitting, no wall-clock embedded in the diagnostic body",
    },
    "toolchain": {"python": "3", "note": "stdlib json/hashlib/re/base64/os + cryptography.hazmat Ed25519"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/repairs/R-Z99/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit-r-z99-wave-r-batch-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "r-z99-wave-r-batch-audit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", verdict)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", canon_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
