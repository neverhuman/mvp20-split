#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit V1-RESOLVE portfolio retraction-index
RESOLUTION sweep (CAMPAIGN item V1-RESOLVE, fire 20260804T110002-476145-ec80205b2d42).
Escalates R-A00 (presence-only: does the index exist and do cited paths resolve) to
RESOLUTION: for every row of every module's RETRACTION-INDEX.md, verifies (a) the
superseded-by target exists on disk, (b) it DSSE-verifies against the pinned Phase-0
evaluator key, (c) its payload -- read directly, not inferred from index prose --
actually addresses the specific claim under attack in that row.
AUDIT_ONLY: signs a receipt under evidence/phase0/repairs/V1-RESOLVE/done/.
Does not modify the master manifest, any locked dataset, or any other module's files.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/V1-RESOLVE/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/V1-RESOLVE/done"
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


runA_bytes = (WORK / "diagnostic.runA.full.json").read_bytes()
runB_bytes = (WORK / "diagnostic.runB.full.json").read_bytes()
byte_identical = runA_bytes == runB_bytes
assert byte_identical, "two-replay bytes differ -- NOT stable, do not sign"
diag = json.loads(runA_bytes)
canon_sha = sha(runA_bytes)

harness_shas = {
    "run_v1_resolve_sweep.py": sha((WORK / "run_v1_resolve_sweep.py").read_bytes()),
    "build_v1_resolve_table.py": sha((WORK / "build_v1_resolve_table.py").read_bytes()),
    "run_v1_resolve_full.py": sha((WORK / "run_v1_resolve_full.py").read_bytes()),
}

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
assert diag["trust_store"]["pinned_evaluator_key_id"] == eval_key_id

resolution = diag["resolution_summary"]
not_resolved = diag["not_resolved_rows"]
n_not_resolved = resolution["n_not_resolved"]

# The escalated claim under attack (per campaign item V1-RESOLVE): every row's
# superseded-by target exists, DSSE-verifies, and actually covers the refuted claim.
verdict = "CLAIM_SURVIVED" if n_not_resolved == 0 else "CLAIM_REFUTED"

body_obj = {
    "schema": "amphora.redteam-audit.v1-resolve-retraction-resolution-receipt.v1",
    "receipt_id": "v1-resolve-retraction-resolution-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "V1-RESOLVE",
    "fire_id": "20260804T110002-476145-ec80205b2d42",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_other_module_files": False,
    "escalates": {
        "prior_receipt": "amphora-redteam-audit/evidence/phase0/repairs/R-A00/done/r-a00-retraction-index-completeness-sweep-receipt.v1.dsse.json",
        "prior_scope": "PRESENCE ONLY: does evidence/phase0/kpis/RETRACTION-INDEX.md exist per module, and do its cited receipt paths resolve on disk. Did not check DSSE signature validity of the cited targets, and explicitly disclaimed row-level content judgment ('does_not_close').",
        "this_scope": "RESOLUTION: for every row of every RETRACTION-INDEX.md found anywhere in the live tree (16 files, 80 rows -- not conditioned on the R-A00 ledger snapshot's 15-module REFUTED-verdict filter, since a RETRACTION-INDEX.md can exist for a module without a REFUTED ledger line, e.g. via anchored-reissue-only sections), checks (a) exists, (b) Ed25519 DSSE-verifies against the single pinned PHASE0_EVALUATOR key in config/phase0-trust-store.v1.json, and (c) the resolved payload's own content -- read directly via work/payload_summaries.txt, not inferred from the index's own prose -- actually addresses the specific claim in that row.",
    },
    "claim_under_attack": {
        "receipt_path": "amphora-redteam-audit/evidence/phase0/repairs/R-A00/done/",
        "claim_text": "Every RETRACTION-INDEX row's superseded-by target exists, DSSE-verifies, and actually covers the refuted claim.",
    },
    "attack_description": (
        "Portfolio-wide RETRACTION-INDEX resolution sweep. Step 1 (mechanical, "
        "work/run_v1_resolve_sweep.py): enumerated all 16 RETRACTION-INDEX.md files "
        "in the live tree by filesystem walk (not the R-A00 ledger-driven module "
        "list), parsed all 80 rows across both markdown-table and bullet-list "
        "formats (amphora-tolerance-robustness uses '## <claim>' + '- refuted-by:' / "
        "'- superseded-by:' bullets, not a table), extracted every path token cited "
        "in each row's superseded-by cell, flagged literal 'PENDING' tokens, resolved "
        "each path (module-relative, falling back to repo-root), and Ed25519-verified "
        "every resolved JSON target carrying a {payload,payloadType,signatures} DSSE "
        "envelope against the single pinned PHASE0_EVALUATOR key -- self-tested with a "
        "negative control (one tampered payload byte) that correctly fails verification "
        "before trusting any PASS result (see work/ transcript). Step 2 (read-and-judge, "
        "work/build_v1_resolve_table.py): for every one of the 33 distinct DSSE-verified "
        "superseding targets, the actual decoded payload was read (work/"
        "payload_summaries.txt: each target's own 'supersedes[].reason' or equivalent, "
        "not the RETRACTION-INDEX.md prose describing it) and hand-judged against the "
        "row's specific claim text -- 29 distinct targets covering 77 of the 80 rows "
        "were judged covers_the_claim=True because each payload names the exact refuted "
        "value/inference and states a concrete corrected value or scope-limited "
        "supersession matching the row. 4 rows citing 'same R-<id> receipt' (a same-table "
        "ditto shorthand with no literal path token, all in amphora-solvency-score) were "
        "resolved by hand to the first row's already-verified target in the same table "
        "section, not counted as dangling. 1 row (amphora-molecule-property "
        "property-eew-ahew-kpi.v1.json) is marked refuted-by='n/a' in its own text -- a "
        "pre-existing housekeeping supersession predating the live falsification surface, "
        "not a claim needing coverage judgment -- and is reported NOT_APPLICABLE, excluded "
        "from the pass/fail count."
    ),
    "pre_registered_refutation_criteria": {
        "criterion": (
            "CLAIM_REFUTED if any row's superseded-by cell (a) is the literal token "
            "PENDING, (b) cites a path that does not resolve on disk, (c) cites a path "
            "that fails Ed25519 DSSE verification against the pinned PHASE0_EVALUATOR "
            "key, or (d) resolves and verifies but whose own payload content -- read "
            "directly -- does not actually address the row's specific claim (a receipt "
            "merely filed in the right directory does not count). CLAIM_SURVIVED only if "
            "every row (excluding rows explicitly marked refuted-by=n/a, which carry no "
            "claim to cover) passes all three checks."
        ),
        "verdict": verdict,
    },
    "sweep_summary_counts": diag["sweep_summary_counts"],
    "n_index_files_found": diag["n_index_files"],
    "index_files_found": diag["index_files_found"],
    "n_distinct_superseded_by_targets": diag["n_distinct_superseded_by_targets"],
    "resolution_summary": resolution,
    "not_resolved_rows": not_resolved,
    "resolution_table": diag["resolution_table"],
    "interpretation": (
        f"{verdict}. Of 80 RETRACTION-INDEX rows across all 16 module indexes found in "
        f"the live tree, {resolution['n_resolved']} are RESOLVED (superseded-by target "
        f"exists, DSSE-verifies against the pinned evaluator key, and its own payload "
        f"content demonstrably addresses the row's specific claim), 1 is NOT_APPLICABLE "
        f"(refuted-by='n/a', a pre-existing housekeeping note with no claim to cover), and "
        f"{n_not_resolved} are NOT_RESOLVED, both in amphora-tolerance-robustness: (1) the "
        f"OpenPoly Tg split-conformal-coverage row's superseded-by cell is the literal "
        f"token 'PENDING' -- the queued repair (campaign item R-C01) has not landed, so "
        f"exists=False; this is exactly the gap the V1-RESOLVE campaign item's own "
        f"objective text named in advance ('a literal PENDING is a failure - "
        f"amphora-tolerance-robustness has one'). (2) The RadonPy eps_r conformal-coverage "
        f"row's cited targets (amphora-molecule-property's dielectric-retraction-v1 chain "
        f"and logs/claims-requiring-retraction.jsonl) exist and DSSE-verify, but reading "
        f"dielectric-retraction-v1's own claim_under_attack directly shows it refutes "
        f"'Dielectric-constant ML results ... rest on admissible labels' -- a LABEL-"
        f"ADMISSIBILITY claim, not this row's own claim (that the reported conformal "
        f"COVERAGE number, 0.9558, is valid). No signed artifact anywhere in the portfolio "
        f"currently republishes a corrected coverage number for this KPI; the row's own "
        f"text admits as much ('coverage under admissibility stratification queued within "
        f"R-C01 scope'). Escalating from R-A00's presence-only check to row-level content "
        f"judgment converts what R-A00 reported as a clean 14/15-module pass (on a "
        f"narrower, ledger-filtered module set) into 2 concrete open gaps, both already "
        f"self-disclosed by the index text itself but not previously checked against a "
        f"pre-registered pass/fail criterion."
    ),
    "does_not_close": [
        "Repair of either amphora-tolerance-robustness gap (R-C01 scaffold-aware "
        "conformal repair; a coverage-specific correction stratified by label "
        "admissibility) -- out of this module's write scope per the fire's confinement "
        "rule (amphora-redteam-audit may only write within its own subtree).",
        "Whether the 29 covers_the_claim=True judgments would survive an independent "
        "second reader; this is a single-reviewer read-and-judge pass, not a two-person "
        "adversarial review.",
        "Row-level completeness of each RETRACTION-INDEX.md against its own module's "
        "full REFUTED ledger history (i.e. whether every REFUTED verdict for a module "
        "has a corresponding row at all) -- that is R-A00's claim, not this one's; this "
        "receipt only judges rows that already exist.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "canonical_diagnostic_sha256": canon_sha,
        "runA_diagnostic_sha256": sha(runA_bytes),
        "runB_diagnostic_sha256": sha(runB_bytes),
        "byte_identical": byte_identical,
        "harness_sha256": harness_shas,
        "harness_paths": {
            "sweep": "amphora-redteam-audit/evidence/phase0/repairs/V1-RESOLVE/work/run_v1_resolve_sweep.py",
            "table_builder": "amphora-redteam-audit/evidence/phase0/repairs/V1-RESOLVE/work/build_v1_resolve_table.py",
            "combined_runner": "amphora-redteam-audit/evidence/phase0/repairs/V1-RESOLVE/work/run_v1_resolve_full.py",
            "payload_dumper": "amphora-redteam-audit/evidence/phase0/repairs/V1-RESOLVE/work/dump_payload_summaries.py",
            "payload_summaries": "amphora-redteam-audit/evidence/phase0/repairs/V1-RESOLVE/work/payload_summaries.txt",
        },
        "negative_control": "verify_dsse() re-tested against a copy of amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json with one payload byte XORed before signing verification; result verifies=False (correctly rejected), confirming the verifier is discriminating and not a rubber stamp. Original file re-verified True in the same run.",
        "determinism": "pure filesystem read + regex parse + Ed25519 verify over the live module trees at read time; hand-authored covers_the_claim judgments are a fixed lookup table in build_v1_resolve_table.py (not derived at run time), so re-running is byte-stable absent a tree change.",
    },
    "toolchain": {"python": "3", "note": "stdlib json/hashlib/re/os/base64 + cryptography.hazmat Ed25519"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/repairs/V1-RESOLVE/done/",
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
ptype = "application/vnd.amphora.redteam-audit-v1-resolve-retraction-resolution+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "v1-resolve-retraction-resolution-receipt.v1.dsse.json"
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
print("n_rows", resolution["n_rows"], "n_resolved", resolution["n_resolved"],
      "n_not_resolved", resolution["n_not_resolved"], "n_not_applicable", resolution["n_not_applicable"])
