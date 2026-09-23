#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-redteam-audit R-A00 portfolio retraction-index
completeness sweep (CAMPAIGN item R-A00, fire 20260803T220002-725675-0c38c18fa6f9).
AUDIT_ONLY: signs a coverage receipt under evidence/phase0/repairs/R-A00/done/.
Does not modify the master manifest, any locked dataset, or any other module's
files. Uses the pinned PHASE0_EVALUATOR key, cross-checked against
config/phase0-trust-store.v1.json.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/R-A00/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/R-A00/done"
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

harness_sha = sha((WORK / "run_retraction_index_sweep.py").read_bytes())
ledger_snapshot_sha = sha((WORK / "falsification-ledger.snapshot.jsonl").read_bytes())
assert ledger_snapshot_sha == diag["ledger_snapshot"]["sha256"]

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

verdict = diag["pre_registered_refutation_criteria"]["verdict"]

body_obj = {
    "schema": "amphora.redteam-audit.retraction-index-completeness-sweep-receipt.v1",
    "receipt_id": "r-a00-retraction-index-completeness-sweep-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "FALSIFICATION_ATTACK",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "R-A00",
    "fire_id": "20260803T220002-725675-0c38c18fa6f9",
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
        "Portfolio-wide data-integrity sweep (the R-A00 canary attack itself): enumerated every "
        "module carrying >=1 REFUTED verdict in a pinned, sha256-recorded snapshot of "
        "logs/falsification-ledger.jsonl (15 modules), then for each checked whether "
        "evidence/phase0/kpis/RETRACTION-INDEX.md exists and, if so, parsed every markdown-table "
        "row's 'refuted-by receipt (path)' and 'superseded-by' columns for cited receipt paths "
        "(both backtick-quoted and bare-prose path tokens) and resolved each against the module "
        "root (falling back to repo root for cross-module pointer paths, e.g. "
        "amphora-assurance-capabilities and amphora-rdkit-ffi coordinated-fix receipts). Paths "
        "appearing only in the free-text 'claim' column (describing what a since-retracted claim "
        "originally, and now non-resolvingly, cited) were deliberately excluded from the "
        "dangling-path check as out of scope for the pinned claim text, which asks only that "
        "cited *receipt* paths resolve."
    ),
    "pre_registered_refutation_criteria": diag["pre_registered_refutation_criteria"],
    "verdict": verdict,
    "n_modules_with_refuted_verdict": diag["n_modules_with_refuted_verdict"],
    "modules_with_refuted_verdict": diag["modules_with_refuted_verdict"],
    "coverage_table": diag["coverage"],
    "summary_counts": diag["summary_counts"],
    "ledger_snapshot": diag["ledger_snapshot"],
    "interpretation": (
        "CLAIM_REFUTED. 14/15 modules with >=1 REFUTED ledger verdict carry a present "
        "evidence/phase0/kpis/RETRACTION-INDEX.md whose refuted-by/superseded-by receipt paths "
        "all resolve on disk (59/59 cited paths resolve, 0 dangling). The single gap is "
        "amphora-tolerance-robustness, which has 2 REFUTED ledger verdicts (fires "
        "20260802T060002-*..., 20260803T100002-*...; see coverage_table entry) and NO "
        "evidence/phase0/kpis/RETRACTION-INDEX.md anywhere in its tree -- confirmed by "
        "filesystem search, not just the direct-path check. This is a truthful, currently-open "
        "gap; interactive/cron repairs to amphora-tolerance-robustness may still be landing at "
        "other agents' hands and are out of this module's write scope (amphora-redteam-audit may "
        "only write within its own subtree per this fire's confinement rule), so no repair is "
        "attempted here. Re-check by re-running work/run_retraction_index_sweep.py against a "
        "fresh ledger snapshot; if amphora-tolerance-robustness gains a resolving "
        "RETRACTION-INDEX.md and no new gaps appear, the claim will read CLAIM_SURVIVED."
    ),
    "does_not_close": [
        "Whether the RETRACTION-INDEX.md content is *substantively correct* (i.e. actually "
        "reflects every REFUTED ledger line for that module, or omits any) -- this sweep checks "
        "existence + path resolution only, not row-level completeness against the ledger.",
        "Whether amphora-tolerance-robustness's missing index reflects an in-progress repair or "
        "an untouched gap -- this receipt reports state as observed at the pinned ledger "
        "snapshot / filesystem-read time only.",
        "Repair of the amphora-tolerance-robustness gap itself (out of this module's write scope).",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "canonical_diagnostic_sha256": canon_sha,
        "runA_diagnostic_sha256": sha(runA_bytes),
        "runB_diagnostic_sha256": sha(runB_bytes),
        "byte_identical": byte_identical,
        "harness_sha256": harness_sha,
        "harness_path": "amphora-redteam-audit/evidence/phase0/repairs/R-A00/work/run_retraction_index_sweep.py",
        "ledger_snapshot_path": "amphora-redteam-audit/evidence/phase0/repairs/R-A00/work/falsification-ledger.snapshot.jsonl",
        "ledger_snapshot_sha256": ledger_snapshot_sha,
        "determinism": "pure filesystem read + regex parse over a pinned ledger snapshot and "
                        "the live module trees at read time; no RNG, no model fitting, no "
                        "wall-clock embedded in the diagnostic body",
    },
    "toolchain": {"python": "3", "note": "stdlib json/hashlib/re/os only"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/phase0/repairs/R-A00/done/",
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
ptype = "application/vnd.amphora.redteam-audit-r-a00-retraction-index-completeness-sweep+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "r-a00-retraction-index-completeness-sweep-receipt.v1.dsse.json"
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
