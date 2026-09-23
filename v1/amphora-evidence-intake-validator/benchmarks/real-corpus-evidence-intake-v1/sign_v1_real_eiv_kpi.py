#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V1-REAL-EIV superseding KPI for
amphora-evidence-intake-validator: real-in-tree-DSSE-corpus results for the
receipt-integrity predicate, run under evidence/phase0/repairs/V1-REAL-EIV/."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-evidence-intake-validator"
ITEM = "V1-REAL-EIV"
WORK = MOD / "evidence/phase0/repairs" / ITEM / "work"
DONE = MOD / "evidence/phase0/repairs" / ITEM / "done"
BM = MOD / "benchmarks/real-corpus-evidence-intake-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
SHIPPED_KPI = MOD / "evidence/phase0/kpis/evidence-intake-validator-host-receipt-integrity-kpi.v1.json"
MANIFEST = ROOT / "amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json"


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


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
diag_sha = sha(canon)

harness_sha = sha((BM / "run_real_corpus_evidence_intake.py").read_bytes())
shipped_kpi_sha = sha(SHIPPED_KPI.read_bytes())
manifest_sha = sha(MANIFEST.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

s = diag["summary"]
corpus_b = diag["results"]["corpus_b_known_bad_ra11"]
corpus_c = diag["results"]["corpus_c_known_bad_ra12"]

known_bad_table = [
    {
        "label": r["label"], "relative_path": r["relative_path"], "defect_class":
            ("R-A11: signature cryptographically invalid against embedded key (malformed/truncated keyid)"
             if r["label"] == "B-RA11-0" else
             "R-A11/R-A12 class: signature cryptographically valid but signing key not phase0-trust-store-anchored"),
        "signature_verified_real_crypto": r["signature_verified_real_crypto"],
        "trust_store_status": r["trust_store_status"],
        "predicate_status": r["predicate_status"],
        "correctly_flagged_bad": r["predicate_status"] == "FAILED_GATES",
    } for r in corpus_b
] + [
    {
        "label": r["label"], "relative_path": r["relative_path"],
        "defect_class": "R-A12 class: signature cryptographically valid (local-9028773f49591193) but signing key not phase0-trust-store-anchored",
        "signature_verified_real_crypto": r["signature_verified_real_crypto"],
        "trust_store_status": r["trust_store_status"],
        "predicate_status": r["predicate_status"],
        "correctly_flagged_bad": r["predicate_status"] == "FAILED_GATES",
    } for r in corpus_c
]

body_obj = {
    "schema": "amphora.evidence-intake-validator.real-corpus-superseding-kpi.v1",
    "receipt_id": "v1-real-eiv-superseding-kpi",
    "module_id": "amphora-evidence-intake-validator",
    "campaign_item_id": "V1-REAL-EIV",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-04",
    "generated_on_host": "xbabe2",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_shipped_runtime": False,
    "modifies_existing_receipts": False,
    "claim": (
        "SUPERSEDING KPI: re-runs the shipped receipt-integrity predicate "
        "(amphora-assurance-capabilities/src/lib.rs :: evaluate_evidence_intake, "
        "host_receipt_valid) over the REAL in-tree DSSE receipt corpus instead "
        "of the shipped n=3 synthetic fixtures, and tests whether it correctly "
        "flags real known-defective receipts. Method: for every receipt, "
        "independently re-derive the 11-field HOST_VERIFIED_RECEIPT_FEATURE an "
        "HONEST host would emit -- a REAL Ed25519 verification of the DSSE "
        "signature against the receipt's own embedded public key (not an "
        "asserted True), and a REAL trust_store_status lookup of the signing "
        "keyid against the only trust-store file that exists in this repo "
        "(config/phase0-trust-store.v1.json), not an asserted TRUSTED -- then "
        "feed that into a verbatim re-derivation of the shipped predicate. "
        "RESULT ON THE 66-RECEIPT MASTER-MANIFEST CORPUS (amphora_coating_"
        "scientific_receipts_manifest.v1.json, read-only, unmodified): "
        f"{s['corpus_a_signature_verified_real_crypto_rate']*100:.0f}% "
        f"({int(s['corpus_a_signature_verified_real_crypto_rate']*s['corpus_a_n'])}/{s['corpus_a_n']}) "
        "carry a cryptographically VALID Ed25519 signature against their own "
        "claimed public key, but 0% pass the predicate's trust_store_status=="
        "TRUSTED conjunct, because every one of the 66 real receipts is signed "
        "by the single toolkit-reviewer-cbe8c0fd... identity, and that keyid "
        "has NO entry anywhere in config/phase0-trust-store.v1.json (which "
        "lists only PHASE0_EVALUATOR and PHASE0_INTERNAL_REVIEWER). An "
        "honestly-implemented host therefore computes positive_scenarios_"
        f"scored_rate={s['corpus_a_scored_rate']} (n={s['corpus_a_n']}) on the "
        "real corpus, sharply diverging from the shipped KPI's 1.0 (n=3 "
        "synthetic fixtures, which assert trust_store_status=TRUSTED by "
        "construction). THE LITERAL CLAIM UNDER TEST -- 'the 1.0 rates hold on "
        "the real in-tree DSSE corpus, not just on n=3 synthetic fixtures' -- "
        "IS REFUTED for the acceptance-rate axis. SEPARATELY, on n=9 real, "
        "documented, known-defective receipts (2x R-A11: one with a "
        "cryptographically invalid signature from a malformed/truncated "
        "keyid, one with a valid signature under an embedded key that is not "
        "phase0-trust-store-anchored; 7x R-A12 class: cryptographically valid "
        "signatures under the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key "
        "local-9028773f49591193, which is likewise absent from the trust "
        "store), the predicate correctly returns FAILED_GATES for "
        f"{s['corpus_b_correctly_flagged_failed_gates_rate']*100:.0f}% "
        f"({s['corpus_b_n']}/{s['corpus_b_n']}) of the R-A11 sample and "
        f"{s['corpus_c_correctly_flagged_failed_gates_rate']*100:.0f}% "
        f"({s['corpus_c_n']}/{s['corpus_c_n']}) of the R-A12 sample -- it does "
        "NOT admit any of these known-bad artifacts. But it rejects them for "
        "the SAME reason (trust_store_status != TRUSTED) that it rejects all "
        "66 genuine scientific receipts, so this run cannot show the predicate "
        "discriminating good real evidence from bad real evidence on the "
        "trust axis -- it discriminates phase0-evaluator-anchored signers from "
        "everyone else, and no real evidence-generation pipeline in this repo "
        "signs with a phase0-evaluator-anchored key. On the pure-signature-"
        "validity axis (ignoring trust anchoring) it DOES discriminate "
        "correctly: 1/9 known-bad receipts (B-RA11-0) has a forged/invalid "
        "signature and is caught on that basis; the other 8/9 have valid "
        "signatures under a wrong/unanchored identity and are caught only on "
        "the trust-anchoring axis, the same axis that fails 66/66 genuine "
        "receipts."
    ),
    "relationship_to_shipped_kpi": {
        "shipped_kpi_path": "amphora-evidence-intake-validator/evidence/phase0/kpis/evidence-intake-validator-host-receipt-integrity-kpi.v1.json",
        "shipped_kpi_sha256": shipped_kpi_sha,
        "shipped_kpi_not_modified_or_deleted": True,
        "shipped_kpi_numbers_remain_accurate_for_its_stated_population": "3 positive synthetic scenarios + 14 adversarial mutation probes + 3 fail-closed probes, all with hand-constructed FeatureSnapshot objects asserting trust_store_status/signature_verified rather than independently deriving them",
        "supersedes": {
            "superseded_path": "amphora-evidence-intake-validator/evidence/phase0/kpis/evidence-intake-validator-host-receipt-integrity-kpi.v1.json",
            "superseded_sha256": shipped_kpi_sha,
            "superseded_deleted_or_modified": False,
            "reason": (
                "Does not alter the shipped n=3 KPI's own numbers (still "
                "correct for its synthetic population). Supersedes any "
                "implicit reliance on that 1.0 figure as evidence the "
                "predicate's acceptance rate generalizes to the module's own "
                "real in-tree DSSE corpus: on n=66 real receipts, honestly "
                "verified, the rate is 0.0, not 1.0.")
        },
    },
    "does_not_establish": [
        "No wet-lab, product-qualification, batch-release, legal, regulatory or scientific authority.",
        "Not a claim that the toolkit-reviewer signing identity is illegitimate or that the 66 real receipts are scientifically wrong -- their scientific content is out of scope here. The finding is narrowly that the predicate's TRUSTED conjunct, honestly evaluated against the only trust-store file in this repo, cannot admit ANY of them.",
        "Not a claim about whether a production 'host' component outside this repo maintains a broader trust store that DOES anchor the toolkit identity -- config/phase0-trust-store.v1.json is the only trust-store artifact present in-tree, and it is read-only, protected input to this evaluation, not authored by this receipt.",
        "The runtime (amphora-assurance-capabilities/src/lib.rs) is not modified. This is an independent CPython re-derivation (AUDIT_ONLY); ceiling remains the pinned Rust runtime = Phase-1.",
        "Candidate-binding conjuncts (candidate_id, candidate_contract_hash_v1, package_sha256, verifier_id, schema) are held self-consistent by construction on both sides of the test boundary in this run; that axis was already independently exercised by predicate-completeness-v1 and host-receipt-oracle-parity-v1. This run isolates the crypto/trust axis only.",
        "freshness (fresh=true) is asserted vacuously per receipt because none of the real receipt schemas in this repo carry an issued_at/expiry field to check -- consistent with, and does not re-litigate, the 0-of-11-temporal-binding-fields finding already established in receipt-authority-derivability-freshness-v1.",
    ],
    "live_authority_under_test": {
        "runtime": "amphora-assurance-capabilities/src/lib.rs :: evaluate_evidence_intake, host_receipt_valid",
        "runtime_git_blob_sha256": "b6b2c83a8b365c4853ab3f37c48c8017a274417f",
        "runtime_modified": False,
        "oracle": "independent CPython re-derivation (AUDIT_ONLY, verbatim port of host_receipt_valid); ceiling remains the pinned Rust runtime = Phase-1",
    },
    "trust_store_used": {
        "path": "config/phase0-trust-store.v1.json",
        "sha256": sha((ROOT / "config/phase0-trust-store.v1.json").read_bytes()),
        "keys_present": ["PHASE0_EVALUATOR", "PHASE0_INTERNAL_REVIEWER"],
        "toolkit_reviewer_key_present": False,
        "local_development_audit_only_key_present": False,
    },
    "manifest_used": {
        "path": "amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json",
        "sha256": manifest_sha,
        "n_receipts_indexed": diag["summary"]["corpus_a_n"],
        "not_modified": True,
        "note": "master receipts manifest is human-owned and protected; read only, never edited",
    },
    "corpus": {
        "corpus_a_real_manifest_receipts": {
            "n": s["corpus_a_n"],
            "positive_scenarios_scored_rate": s["corpus_a_scored_rate"],
            "signature_cryptographically_valid_rate": s["corpus_a_signature_verified_real_crypto_rate"],
            "trust_store_status_trusted_rate": s["corpus_a_trusted_rate"],
            "shipped_kpi_comparison_positive_scenarios_scored_rate": 1.0,
            "shipped_kpi_comparison_n": 3,
        },
        "corpus_b_known_bad_ra11": {
            "n": s["corpus_b_n"],
            "correctly_flagged_failed_gates_rate": s["corpus_b_correctly_flagged_failed_gates_rate"],
        },
        "corpus_c_known_bad_ra12": {
            "n": s["corpus_c_n"],
            "correctly_flagged_failed_gates_rate": s["corpus_c_correctly_flagged_failed_gates_rate"],
        },
    },
    "known_bad_receipt_results": known_bad_table,
    "metrics": [
        {
            "name": "real_corpus_positive_scenarios_scored_rate",
            "direction": "MAXIMIZE", "floor": 1.0,
            "observed": s["corpus_a_scored_rate"], "sample_size": s["corpus_a_n"],
            "passed": s["corpus_a_scored_rate"] == 1.0, "authority": "AUDIT_ONLY",
            "note": "Superseding measurement of the shipped positive_scenarios_scored_rate metric, on n=66 real receipts instead of n=3 synthetic fixtures, using honestly-derived (not asserted) FeatureSnapshot values.",
        },
        {
            "name": "real_corpus_signature_cryptographic_validity_rate",
            "direction": "MAXIMIZE", "floor": 1.0,
            "observed": s["corpus_a_signature_verified_real_crypto_rate"], "sample_size": s["corpus_a_n"],
            "passed": s["corpus_a_signature_verified_real_crypto_rate"] == 1.0, "authority": "AUDIT_ONLY",
            "note": "Real Ed25519 verification (cryptography lib, DSSE PAE construction) of signatures[0].sig against each receipt's own embedded public key.",
        },
        {
            "name": "real_corpus_trust_store_anchored_rate",
            "direction": "MAXIMIZE", "floor": 1.0,
            "observed": s["corpus_a_trusted_rate"], "sample_size": s["corpus_a_n"],
            "passed": s["corpus_a_trusted_rate"] == 1.0, "authority": "AUDIT_ONLY",
            "note": "Fraction of the 66 real receipts whose signing keyid is an entry in config/phase0-trust-store.v1.json.",
        },
        {
            "name": "known_bad_ra11_fail_closed_rate",
            "direction": "MAXIMIZE", "floor": 1.0,
            "observed": s["corpus_b_correctly_flagged_failed_gates_rate"], "sample_size": s["corpus_b_n"],
            "passed": s["corpus_b_correctly_flagged_failed_gates_rate"] == 1.0, "authority": "AUDIT_ONLY",
            "note": "Predicate correctly returns FAILED_GATES for both real R-A11 pre-reissue defective receipts when fed honestly-derived verification results.",
        },
        {
            "name": "known_bad_ra12_fail_closed_rate",
            "direction": "MAXIMIZE", "floor": 1.0,
            "observed": s["corpus_c_correctly_flagged_failed_gates_rate"], "sample_size": s["corpus_c_n"],
            "passed": s["corpus_c_correctly_flagged_failed_gates_rate"] == 1.0, "authority": "AUDIT_ONLY",
            "note": "Predicate correctly returns FAILED_GATES for a 7-receipt sample of the R-A12 (unanchored local-key) class when fed honestly-derived verification results.",
        },
    ],
    "gates": {
        "known_bad_receipts_correctly_rejected": (
            s["corpus_b_correctly_flagged_failed_gates_rate"] == 1.0 and
            s["corpus_c_correctly_flagged_failed_gates_rate"] == 1.0
        ),
        "real_corpus_1p0_generalization_claim_survives": s["corpus_a_scored_rate"] == 1.0,
    },
    "verdict": "CLAIM_REFUTED",
    "verdict_reason": (
        "The pinned campaign claim is 'the receipt-integrity validator's 1.0 "
        "rates hold on the real in-tree DSSE corpus, not just on n=3 synthetic "
        "fixtures.' Measured honestly on n=66 real receipts, "
        "positive_scenarios_scored_rate=0.0, not 1.0. The claim as literally "
        "stated is false; the predicate does correctly reject known-bad "
        "receipts (n=9, 9/9), but it rejects genuine real evidence for the "
        "identical reason (no trust-store anchor for the signing identity "
        "actually used across the portfolio's real evidence-generation "
        "pipeline), so this run cannot certify that the 1.0 rate generalizes."
    ),
    "provenance": {
        "harness_sha256": {"run_real_corpus_evidence_intake.py": harness_sha},
        "diagnostic_canonical_sha256": diag_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "determinism_note": "No RNG, no wall clock; every value is a deterministic function of on-disk receipt bytes, the trust-store file, and the local-key registry file.",
        "replay_method": "python3 amphora-evidence-intake-validator/benchmarks/real-corpus-evidence-intake-v1/run_real_corpus_evidence_intake.py",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair receipt under evidence/phase0/repairs/V1-REAL-EIV/done/",
        "signs_phase0_evaluation_or_review": False,
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.evidence-intake-validator-v1-real-eiv-superseding-kpi+json"
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

DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "v1-real-eiv-superseding-kpi.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("verdict", body_obj["verdict"])
print("corpus_a_scored_rate", s["corpus_a_scored_rate"], "n=", s["corpus_a_n"])
print("corpus_b_fail_closed_rate", s["corpus_b_correctly_flagged_failed_gates_rate"])
print("corpus_c_fail_closed_rate", s["corpus_c_correctly_flagged_failed_gates_rate"])
print("two_replay_sha256", diag_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("self_verify_signature", "OK")
