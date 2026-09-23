#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-novelty citation-provenance
threshold-source AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt
under evidence/audit/; does NOT sign a phase0 evaluation/review, does NOT
promote authority, does NOT flip scientific_readiness, does NOT modify the
manifest, any locked dataset, or the signed Phase-0 novelty KPI (supersede-
never-rewrite: the KPI and its underlying scientific receipt are read-only
inputs to this audit, cited by sha256, never edited). Derived key_id
cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-novelty/evidence/audit/citation-provenance-threshold-source-v1"
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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_citation_provenance_audit.py").read_bytes())

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
assert eval_pin, "evaluator key does not match pinned Phase-0 trust store"

fetched_html_sha = sha((BENCH / "fetched/pmc4456712_real.html").read_bytes())
fetched_idconv_sha = sha((BENCH / "fetched/idconv_response.json").read_bytes())
assert fetched_html_sha == diag["fetched_evidence"]["html_sha256"]
assert fetched_idconv_sha == diag["fetched_evidence"]["idconv_api_response_sha256"]

body_obj = {
    "schema": "amphora.molecule-novelty.citation-provenance-threshold-source-audit.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "NOVELTY_CITATION_PROVENANCE_THRESHOLD_SOURCE_AUDIT",
    "module": "amphora-molecule-novelty",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "attack_type": diag["attack_type"],
    "claim_under_attack": diag["claim_under_attack"],
    "source_identity_verification": diag["source_identity_verification"],
    "fetched_evidence": diag["fetched_evidence"],
    "topic_anchor_search": diag["topic_anchor_search"],
    "threshold_term_search_on_real_fetched_paper": diag["threshold_term_search_on_real_fetched_paper"],
    "positive_control": diag["positive_control"],
    "kpi_threshold_block_observed": diag["kpi_threshold_block_observed"],
    "kpi_sha256": diag["kpi_sha256"],
    "scientific_receipt_threshold_block_observed": diag["scientific_receipt_threshold_block_observed"],
    "scientific_receipt_sha256": diag["scientific_receipt_sha256"],
    "downstream_files_inheriting_this_citation_unmodified": diag["downstream_files_inheriting_this_citation_unmodified"],
    "n_downstream_files_inheriting_citation": diag["n_downstream_files_inheriting_citation"],
    "finding": diag["finding"],
    "verdict": "CLAIM_REFUTED",
    "verdict_note": (
        "The 'threshold_source: Bajusz-Rácz-Héberger 2015 J. Cheminform.' citation "
        "attached to the 0.40/0.55/0.75 novelty-classification cutoffs is fabricated "
        "attribution: the identity-verified cited paper (DOI 10.1186/s13321-015-0069-3) "
        "contains none of these values and no similarity-classification threshold scheme "
        "at all. This does not overturn the raw NN-Tanimoto numbers (independently "
        "re-derived correct 6 times by prior fires), only the specific literature basis "
        "claimed for the numeric boundaries that turn those numbers into a NOVEL/"
        "not-NOVEL verdict -- see finding.scope_of_refutation."
    ),
    "closes": [
        "Whether the specific 0.40/0.55/0.75 Tanimoto novelty-classification thresholds "
        "used by every novelty verdict this module has issued trace to a real, checkable "
        "published source: NO, they do not.",
    ],
    "does_not_close": [
        "Does not contest the raw NN-Tanimoto similarity values themselves (0.1579-0.3929).",
        "Does not assert the qualitative NOVEL conclusion is wrong -- only that its cited "
        "numeric threshold provenance is unsupported.",
        "Grants no batch-release, manufacturing-qualification, optimizer, product-"
        "performance, regulatory, safety, solver, or patentability/FTO authority.",
        "Does not repair the defect (no corrected threshold_source or re-derived cutoff "
        "is proposed here); that is follow-up work for an R- campaign item.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "note": (
            "Byte-stability is over the harness's re-parse of the ONE frozen fetched "
            "HTML file on disk (sha256 pinned in fetched_evidence), not over two "
            "independent web fetches -- web responses are not guaranteed byte-stable "
            "across requests, so the raw fetch was done once and pinned as an input "
            "fixture, exactly as the module's other audits pin their input CSVs."
        ),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-novelty-citation-provenance-threshold-source-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "citation-provenance-threshold-source-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
