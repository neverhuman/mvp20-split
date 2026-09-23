#!/usr/bin/env python3
"""V1-REAL-EIV: run the amphora-evidence-intake-validator receipt-integrity
predicate (amphora-assurance-capabilities/src/lib.rs :: evaluate_evidence_intake,
host_receipt_valid) over the REAL in-tree DSSE corpus instead of the n=3
synthetic fixtures the shipped Phase-0 KPI is scored on.

For every real receipt we:
  1. re-read the file bytes and sha256 them (freshness/integrity),
  2. extract its DSSE envelope (payload/payloadType/signatures[0]),
  3. perform a REAL Ed25519 verification of signatures[0].sig against the
     receipt's own claimed embedded public key using the exact PAE
     construction the in-tree sign_*.py scripts use
     (PAE = "DSSEv1" SP len(type) SP type SP len(body) SP body),
  4. look up signatures[0].keyid against the ONLY trust-store file that
     exists in this repo (config/phase0-trust-store.v1.json) to compute a
     real trust_store_status instead of asserting one,
  5. build the 11-field HOST_VERIFIED_RECEIPT_FEATURE object an HONEST host
     would emit from (3) and (4) -- not a host that just asserts True -- and
     feed it through a verbatim Python re-derivation of host_receipt_valid
     (amphora-assurance-capabilities/src/lib.rs, git blob sha256
     b6b2c83a8b365c4853ab3f37c48c8017a274417f, lines 648-670).

Three populations:
  CORPUS_A  n=66  the master-manifest-indexed real scientific-data receipts
                  (amphora_coating_scientific_receipts_manifest.v1.json,
                  read-only, NOT modified). All 66 are signed by the single
                  toolkit-reviewer-cbe8c0fd... key.
  CORPUS_B  n=2   the KNOWN-BAD R-A11 malformed/truncated-keyid receipts
                  (original, pre-reissue files, still present un-deleted per
                  their supersedes block) in amphora-design-rule-score and
                  amphora-molecule-property.
  CORPUS_C  n=10  a sample of the KNOWN-BAD R-A12 class: real, currently-live
                  AUDIT_ONLY receipts signed with the repo
                  LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f49591193),
                  which is NOT an entry in config/phase0-trust-store.v1.json.

Candidate-binding conjuncts (candidate_id, candidate_contract_hash_v1,
package_sha256, verifier_id, schema) are held self-consistent by
construction on both sides of the boundary -- that axis was already
independently exercised by predicate-completeness-v1 and
host-receipt-oracle-parity-v1. This run isolates the crypto/trust axis.
"""
import base64, hashlib, json, sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-evidence-intake-validator"
TRUST_STORE_PATH = ROOT / "config/phase0-trust-store.v1.json"
MANIFEST_PATH = ROOT / "amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json"
LOCAL_PUB_PATH = ROOT / ".amphora/control/local-ed25519.pub.json"

HOST_VERIFIED_RECEIPT_SCHEMA = "amphora.host-verified-evidence-receipt.v1"


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pae(payload_type: str, body: bytes) -> bytes:
    t = payload_type.encode()
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t + b" " +
            str(len(body)).encode() + b" " + body)


def real_ed25519_verify(pubkey_hex: str, sig_b64: str, payload_type: str, payload_b64: str) -> bool:
    try:
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubkey_hex))
        sig = base64.b64decode(sig_b64)
        body = base64.b64decode(payload_b64)
        pub.verify(sig, pae(payload_type, body))
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


def host_receipt_valid(receipt: dict, candidate_id: str, candidate_contract_hash_v1: str,
                        package_sha256: str) -> bool:
    """Verbatim re-derivation of amphora-assurance-capabilities/src/lib.rs
    :: host_receipt_valid (git blob b6b2c83a8b365c4853ab3f37c48c8017a274417f,
    lines 648-670)."""
    if not isinstance(receipt, dict) or len(receipt) != 11:
        return False
    return (
        receipt.get("schema") == HOST_VERIFIED_RECEIPT_SCHEMA and
        receipt.get("accepted") is True and
        receipt.get("signature_verified") is True and
        receipt.get("revocation_checked") is True and
        receipt.get("fresh") is True and
        receipt.get("signature_algorithm") == "Ed25519" and
        receipt.get("trust_store_status") == "TRUSTED" and
        receipt.get("candidate_id") == candidate_id and
        receipt.get("candidate_contract_hash_v1") == candidate_contract_hash_v1 and
        receipt.get("package_sha256") == package_sha256 and
        bool(receipt.get("verifier_id"))
    )


def evaluate_evidence_intake(receipt: dict, candidate_id: str, candidate_contract_hash_v1: str,
                              package_sha256: str):
    """Verbatim re-derivation of evaluate_evidence_intake status/score logic."""
    verified = host_receipt_valid(receipt, candidate_id, candidate_contract_hash_v1, package_sha256)
    return {
        "status": "SCORED" if verified else "FAILED_GATES",
        "score": 1.0 if verified else 0.0,
        "gates": {
            "host_verified_signature_receipt": verified,
            "evidence_package_accepted": verified,
        },
    }


def load_trust_store():
    ts = json.loads(TRUST_STORE_PATH.read_bytes())
    by_keyid = {k["key_id"]: k for k in ts["keys"]}
    return by_keyid


def load_local_pub():
    return json.loads(LOCAL_PUB_PATH.read_bytes())


def extract_envelope(doc: dict):
    """Return (payload_b64, payload_type, keyid, sig_b64, pubkey_hex_hint)."""
    if isinstance(doc.get("signature"), dict) and "payload" in doc["signature"]:
        env = doc["signature"]
        pubkey_hint = doc.get("reviewer_public_key_hex") or doc.get("evaluator_public_key_hex")
    elif "payload" in doc and "payloadType" in doc:
        env = doc
        pubkey_hint = doc.get("reviewer_public_key_hex") or doc.get("evaluator_public_key_hex")
    else:
        raise ValueError("no DSSE envelope found")
    sigs = env.get("signatures") or []
    if not sigs:
        raise ValueError("no signatures[] in envelope")
    keyid = sigs[0]["keyid"]
    sig_b64 = sigs[0]["sig"]
    return env["payload"], env["payloadType"], keyid, sig_b64, pubkey_hint


def resolve_pubkey_hex(keyid: str, pubkey_hint, local_pub: dict, trust_store: dict):
    """Resolve the public key an honest host would use to verify this keyid.
    Prefer an embedded hint on the receipt itself; fall back to the local
    control-plane registry for the LOCAL_DEVELOPMENT_AUDIT_ONLY key; fall
    back to the trust store for phase0-anchored keys."""
    if pubkey_hint:
        return pubkey_hint
    if keyid == local_pub.get("key_id"):
        return local_pub.get("public_key_hex")
    if keyid in trust_store:
        return trust_store[keyid]["public_key_hex"]
    return None


def build_and_evaluate(relative_path: str, expected_sha256, label: str, trust_store: dict, local_pub: dict):
    fpath = ROOT / relative_path
    raw = fpath.read_bytes()
    file_sha256 = sha256_hex(raw)
    freshness_matches_manifest = (expected_sha256 is None or file_sha256 == expected_sha256)

    doc = json.loads(raw)
    err = None
    try:
        payload_b64, payload_type, keyid, sig_b64, pubkey_hint = extract_envelope(doc)
        pubkey_hex = resolve_pubkey_hex(keyid, pubkey_hint, local_pub, trust_store)
        if pubkey_hex is None:
            signature_verified = False
            err = "no_resolvable_public_key"
        else:
            signature_verified = real_ed25519_verify(pubkey_hex, sig_b64, payload_type, payload_b64)
    except Exception as e:
        keyid, payload_b64, payload_type, sig_b64, pubkey_hint, pubkey_hex = None, None, None, None, None, None
        signature_verified = False
        err = f"envelope_extraction_failed:{e}"

    trust_entry = trust_store.get(keyid) if keyid else None
    trust_store_status = "TRUSTED" if (trust_entry is not None and trust_entry.get("revoked") is False) else "UNTRUSTED"
    revocation_checked = trust_entry is not None  # can only check revocation for a registered identity
    fresh = True  # documented limitation: none of these receipt schemas carry issued_at/expiry (see receipt-authority-derivability-freshness-v1); vacuously true, not fabricated staleness

    # honest host: only asserts accepted=true if it actually verified sig + trust
    accepted = bool(signature_verified and trust_store_status == "TRUSTED")

    candidate_id = f"real-corpus-{label}"
    candidate_contract_hash_v1 = sha256_hex(candidate_id.encode())
    package_sha256 = file_sha256  # candidate's evidence_package IS this receipt file; binding held self-consistent

    host_receipt = {
        "schema": HOST_VERIFIED_RECEIPT_SCHEMA,
        "accepted": accepted,
        "signature_verified": signature_verified,
        "revocation_checked": revocation_checked,
        "fresh": fresh,
        "signature_algorithm": "Ed25519",
        "trust_store_status": trust_store_status,
        "candidate_id": candidate_id,
        "candidate_contract_hash_v1": candidate_contract_hash_v1,
        "package_sha256": package_sha256,
        "verifier_id": "v1-real-eiv-honest-host-verifier",
    }
    assert len(host_receipt) == 11

    result = evaluate_evidence_intake(host_receipt, candidate_id, candidate_contract_hash_v1, package_sha256)

    return {
        "label": label,
        "relative_path": relative_path,
        "file_sha256": file_sha256,
        "freshness_matches_manifest": freshness_matches_manifest,
        "keyid": keyid,
        "signature_verified_real_crypto": signature_verified,
        "trust_store_status": trust_store_status,
        "revocation_checked": revocation_checked,
        "extraction_error": err,
        "predicate_status": result["status"],
        "predicate_score": result["score"],
        "predicate_gates": result["gates"],
    }


def main():
    trust_store = load_trust_store()
    local_pub = load_local_pub()
    manifest = json.loads(MANIFEST_PATH.read_bytes())
    index = manifest["kpis"]["index_of_receipts"]
    assert len(index) == 66, f"manifest index changed size: {len(index)}"

    results = {"corpus_a_real_manifest_receipts": [], "corpus_b_known_bad_ra11": [], "corpus_c_known_bad_ra12": []}

    # CORPUS_A: all 66 manifest-indexed real receipts
    for entry in index:
        r = build_and_evaluate(entry["relative_path"], entry["receipt_sha256"],
                                f"A-{entry['receipt_id'][:24]}", trust_store, local_pub)
        results["corpus_a_real_manifest_receipts"].append(r)

    # CORPUS_B: known-bad R-A11 malformed/truncated-keyid originals (pre-reissue, still present)
    mp_log = json.loads((MOD.parent / "amphora-molecule-property/evidence/phase0/repairs/R-A11/work/R-A11-work-log.a.v1.json").read_bytes())
    ra11_paths = [
        "amphora-design-rule-score/benchmarks/guth-gold-physical-baseline-v1/physical_baseline_receipt.v1.json",
        mp_log["target"],
    ]
    for i, p in enumerate(ra11_paths):
        try:
            r = build_and_evaluate(p, None, f"B-RA11-{i}", trust_store, local_pub)
            results["corpus_b_known_bad_ra11"].append(r)
        except Exception as e:
            results["corpus_b_known_bad_ra11"].append({"label": f"B-RA11-{i}", "relative_path": p, "error": str(e)})

    # CORPUS_C: sample of known-bad R-A12 class (real, live, local-key-signed AUDIT_ONLY receipts)
    ra12_candidates = [
        "amphora-solvency-score/benchmarks/molar-volume-density-v1/replay_receipt.v1.dsse.json",
        "amphora-solvency-score/benchmarks/bigsoldb-v1/inhouse_benchmark_receipt.v1.dsse.json",
        "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/replay_receipt.v1.dsse.json",
        "amphora-molecule-role-ranker/benchmarks/role-macosko-miller-sol-latitude-v1/replay_receipt.v1.dsse.json",
        "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/replay_receipt.v1.dsse.json",
        "amphora-molecule-role-ranker/benchmarks/role-parsimony-conformal-v1/replay_receipt.v1.dsse.json",
        "amphora-molecule-role-ranker/benchmarks/role-flory-gelation-v1/replay_receipt.v1.dsse.json",
    ]
    for i, p in enumerate(ra12_candidates):
        fp = ROOT / p
        if not fp.exists():
            continue
        try:
            r = build_and_evaluate(p, None, f"C-RA12-{i}", trust_store, local_pub)
            results["corpus_c_known_bad_ra12"].append(r)
        except Exception as e:
            results["corpus_c_known_bad_ra12"].append({"label": f"C-RA12-{i}", "relative_path": p, "error": str(e)})

    def rate(lst, key="predicate_status", val="SCORED"):
        if not lst:
            return None
        return sum(1 for x in lst if x.get(key) == val) / len(lst)

    summary = {
        "corpus_a_n": len(results["corpus_a_real_manifest_receipts"]),
        "corpus_a_scored_rate": rate(results["corpus_a_real_manifest_receipts"]),
        "corpus_a_signature_verified_real_crypto_rate": sum(
            1 for x in results["corpus_a_real_manifest_receipts"] if x.get("signature_verified_real_crypto")
        ) / len(results["corpus_a_real_manifest_receipts"]),
        "corpus_a_trusted_rate": sum(
            1 for x in results["corpus_a_real_manifest_receipts"] if x.get("trust_store_status") == "TRUSTED"
        ) / len(results["corpus_a_real_manifest_receipts"]),
        "corpus_b_n": len(results["corpus_b_known_bad_ra11"]),
        "corpus_b_correctly_flagged_failed_gates_rate": rate(results["corpus_b_known_bad_ra11"], "predicate_status", "FAILED_GATES"),
        "corpus_c_n": len(results["corpus_c_known_bad_ra12"]),
        "corpus_c_correctly_flagged_failed_gates_rate": rate(results["corpus_c_known_bad_ra12"], "predicate_status", "FAILED_GATES"),
    }

    out = {"summary": summary, "results": results}
    print(json.dumps(out, indent=2, sort_keys=True))
    return out


if __name__ == "__main__":
    main()
