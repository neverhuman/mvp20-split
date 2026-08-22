#!/usr/bin/env python3
"""
amphora-evidence-intake-validator :: host-receipt-oracle-parity-v1

Independent, NON-RUNTIME Python re-derivation of the evidence-intake acceptance
predicate. The live authority is native Rust
(amphora-assurance-capabilities/src/lib.rs, fn evaluate_evidence_intake /
host_receipt_valid; canonical hashing in amphora-core/src/lib.rs
stable_hash+canonicalize). The shipped Phase-0 KPI harness exercises the Rust
runtime only. This oracle re-implements the same predicate from a second,
independent codebase and:

  G1  reproduces the 3 shipped positive-scenario package_sha256 anchors byte-exact
  G2  re-derives the candidate contract_hash_v1 binding and shows cross-candidate
      receipt replay is rejected (real hash of a different candidate)
  G3  reproduces the shipped runtime accept/reject decision for all 17 shipped
      records (3 positive + 14 adversarial mutations) read from result.v1.json
  G4  extends with 8 NOVEL independent tamper / invariance probes the shipped
      benchmark does not cover, all fail-closed (or invariant where required)

Theory / standards anchoring (integrity + trust semantics being re-derived):
  NIST SP 800-53 Rev.5 SI-7 software/firmware/information integrity (2020)
  NIST FIPS 186-5 EdDSA (2023); RFC 8032 Ed25519 (2017)
  RFC 5280 PKIX certificate revocation (2008)
  in-toto Attestation Framework v1.0 (2020); SLSA v1.0 provenance (2023)
  NIST SP 800-207 Zero Trust (2020); Anderson 1980 reference-monitor
  RFC 8785 JSON Canonicalization (canonical-form invariance property)

No wet-lab, product-qualification, legal, or scientific authority is asserted.
This is an infrastructure front-door byte-integrity parity check only.
"""
import json, hashlib, sys

# ---------------------------------------------------------------------------
# Independent re-implementation of amphora-core canonicalize + stable_hash.
# canonicalize: recursively sort object keys; stable_hash: SHA-256 of the
# compact (serde_json::to_vec) serialization of the canonical value.
# ---------------------------------------------------------------------------
def canonicalize(v):
    if isinstance(v, dict):
        return {k: canonicalize(v[k]) for k in sorted(v.keys())}
    if isinstance(v, list):
        return [canonicalize(x) for x in v]
    return v

def stable_hash(v):
    b = json.dumps(canonicalize(v), separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

HOST_VERIFIED_RECEIPT_SCHEMA = "amphora.host-verified-evidence-receipt.v1"

# ---------------------------------------------------------------------------
# Fixture reconstruction, byte-identical to the Rust KPI harness.
# ---------------------------------------------------------------------------
def evidence_candidate(cid, payload_extra):
    package = {"payload_kind": "lab_measurement", "payload_extra": payload_extra}
    return {
        "candidate_id": cid,
        "candidate_type": "evidence_package",
        "evidence_refs": {"evidence_package": package},
    }

def candidate_id(cand):
    return cand["candidate_id"]

def contract_hash_v1(cand):
    # amphora-core CandidateEnvelope::build -> stable_hash(full value)
    return stable_hash(cand)

def package_of(cand):
    return cand["evidence_refs"]["evidence_package"]

def build_valid_receipt(cand, verifier_id="host-trust-kernel-phase0"):
    return {
        "schema": HOST_VERIFIED_RECEIPT_SCHEMA,
        "accepted": True,
        "signature_verified": True,
        "revocation_checked": True,
        "fresh": True,
        "signature_algorithm": "Ed25519",
        "trust_store_status": "TRUSTED",
        "candidate_id": candidate_id(cand),
        "candidate_contract_hash_v1": contract_hash_v1(cand),
        "package_sha256": stable_hash(package_of(cand)),
        "verifier_id": verifier_id,
    }

# ---------------------------------------------------------------------------
# Independent re-implementation of host_receipt_valid + evaluate_evidence_intake.
# receipt may be None (feature omitted). Returns (accepted: bool).
# ---------------------------------------------------------------------------
def host_receipt_valid(cand, receipt, package_sha256):
    if not isinstance(receipt, dict):
        return False
    return (
        len(receipt) == 11
        and receipt.get("schema") == HOST_VERIFIED_RECEIPT_SCHEMA
        and receipt.get("accepted") is True
        and receipt.get("signature_verified") is True
        and receipt.get("revocation_checked") is True
        and receipt.get("fresh") is True
        and receipt.get("signature_algorithm") == "Ed25519"
        and receipt.get("trust_store_status") == "TRUSTED"
        and receipt.get("candidate_id") == candidate_id(cand)
        and receipt.get("candidate_contract_hash_v1") == contract_hash_v1(cand)
        and receipt.get("package_sha256") == package_sha256
        and isinstance(receipt.get("verifier_id"), str)
        and len(receipt.get("verifier_id")) > 0
    )

def evaluate(cand, receipt):
    pkg = package_of(cand)
    package_sha256 = stable_hash(pkg)
    verified = host_receipt_valid(cand, receipt, package_sha256)
    return {
        "status": "SCORED" if verified else "FAILED_GATES",
        "score_0_1": 1.0 if verified else 0.0,
        "evidence_package_accepted_gate": verified,
        "host_verified_signature_receipt_gate": verified,
        "package_sha256": package_sha256,
    }

# ---------------------------------------------------------------------------
# G1 + shipped positive scenarios
# ---------------------------------------------------------------------------
POSITIVE = [
    ("baseline-primer-lab-measurement", "phase0-kpi-primer-lab",
     {"measurement": "gel_time_h", "value": 4.2},
     "10b52299f7cf514efa5156d0c85bf98dc2088db3d8d00f09eb149ba1fcbb1fef"),
    ("topcoat-thickness-measurement", "phase0-kpi-topcoat-dft",
     {"measurement": "dft_mil", "value": 3.1, "instrument": "elcometer"},
     "27590e304c82e058783946f740230febb7aeca70e918cf75a79bedc860a71d54"),
    ("adhesive-pull-off-strength", "phase0-kpi-adhesive-pull",
     {"measurement": "pull_off_mpa", "value": 8.5, "n_replicates": 5},
     "5436647075373dad729c4ba1378acb1fa9d353961b951e2d9a3c57cf679d27bc"),
]

def make_mutate(receipt, key, value):
    r = dict(receipt); r[key] = value; return r

def make_remove(receipt, key):
    r = dict(receipt); r.pop(key, None); return r

# ---------------------------------------------------------------------------
# Shipped 14 adversarial mutation probes (anchor candidate), reconstructed
# ---------------------------------------------------------------------------
def shipped_mutations():
    anchor = evidence_candidate("phase0-kpi-adversarial-anchor",
                                {"measurement": "adhesion_mpa", "value": 8.0})
    other = evidence_candidate("phase0-kpi-different-candidate",
                               {"measurement": "different"})
    base = build_valid_receipt(anchor)
    probes = [
        ("no_host_receipt_feature", None),
        ("wrong_schema_string", make_mutate(base, "schema", "amphora.wrong-schema.v99")),
        ("accepted_false", make_mutate(base, "accepted", False)),
        ("signature_verified_false", make_mutate(base, "signature_verified", False)),
        ("revocation_unchecked", make_mutate(base, "revocation_checked", False)),
        ("receipt_stale", make_mutate(base, "fresh", False)),
        ("wrong_signature_algorithm_es256", make_mutate(base, "signature_algorithm", "ES256")),
        ("trust_store_untrusted", make_mutate(base, "trust_store_status", "UNTRUSTED")),
        ("wrong_candidate_id", make_mutate(base, "candidate_id", candidate_id(other))),
        ("wrong_contract_hash", make_mutate(base, "candidate_contract_hash_v1", "f" * 64)),
        ("wrong_package_sha256", make_mutate(base, "package_sha256", "0" * 64)),
        ("empty_verifier_id", make_mutate(base, "verifier_id", "")),
        ("receipt_has_twelfth_extra_field", make_mutate(base, "adversary_extra_field", "payload smuggle")),
        ("receipt_missing_one_required_field", make_remove(base, "revocation_checked")),
    ]
    return anchor, other, base, probes

def main():
    result_path = sys.argv[1]  # shipped Rust result.v1.json
    shipped = json.load(open(result_path))
    shipped_records = {}
    for rec in shipped["records"]:
        key = rec.get("scenario_id") or rec.get("probe_id")
        shipped_records[key] = rec

    diag = {"schema": "amphora.evidence-intake-oracle-parity.v1"}

    # ---- G1: reproduce 3 shipped package anchors byte-exact ----
    g1 = []
    for sid, cid, extra, expected in POSITIVE:
        cand = evidence_candidate(cid, extra)
        got = stable_hash(package_of(cand))
        g1.append({"scenario_id": sid, "candidate_id": cid,
                   "oracle_package_sha256": got,
                   "shipped_anchor_sha256": expected,
                   "match": got == expected})
    g1_pass = all(x["match"] for x in g1)

    # ---- positive-scenario decision parity vs shipped runtime ----
    pos_parity = []
    for sid, cid, extra, expected in POSITIVE:
        cand = evidence_candidate(cid, extra)
        receipt = build_valid_receipt(cand)
        out = evaluate(cand, receipt)
        srec = shipped_records[sid]
        parity = (out["status"] == srec["status"]
                  and out["evidence_package_accepted_gate"] == srec["evidence_package_accepted_gate"]
                  and out["host_verified_signature_receipt_gate"] == srec["host_verified_signature_receipt_gate"]
                  and out["package_sha256"] == srec["package_sha256"])
        pos_parity.append({"scenario_id": sid, "oracle_status": out["status"],
                           "shipped_status": srec["status"], "parity": parity})
    pos_pass = all(x["parity"] for x in pos_parity)

    # ---- G2: contract-hash binding + real cross-candidate replay rejection ----
    anchor, other, base, probes = shipped_mutations()
    # receipt validly built for `anchor`; replay it against `other` (real,
    # valid, but DIFFERENT contract hash + candidate_id + package)
    replay_against_other = evaluate(other, base)
    g2 = {
        "anchor_contract_hash_v1": contract_hash_v1(anchor),
        "other_contract_hash_v1": contract_hash_v1(other),
        "hashes_distinct": contract_hash_v1(anchor) != contract_hash_v1(other),
        "valid_receipt_on_own_candidate_accepts": evaluate(anchor, base)["status"] == "SCORED",
        "same_receipt_replayed_on_other_candidate_rejected": replay_against_other["status"] == "FAILED_GATES",
    }
    g2_pass = (g2["hashes_distinct"] and g2["valid_receipt_on_own_candidate_accepts"]
               and g2["same_receipt_replayed_on_other_candidate_rejected"])

    # ---- G3: reproduce shipped decisions for all 14 mutation probes ----
    g3 = []
    for pid, receipt in probes:
        out = evaluate(anchor, receipt)
        srec = shipped_records[pid]
        parity = (out["status"] == srec["status"]
                  and out["evidence_package_accepted_gate"] == srec["evidence_package_accepted_gate"]
                  and out["host_verified_signature_receipt_gate"] == srec["host_verified_signature_receipt_gate"])
        fail_closed = out["status"] == "FAILED_GATES"
        g3.append({"probe_id": pid, "oracle_status": out["status"],
                   "shipped_status": srec["status"], "parity": parity,
                   "fail_closed": fail_closed})
    g3_pass = all(x["parity"] and x["fail_closed"] for x in g3)

    # ---- G4: 8 NOVEL independent probes beyond the shipped benchmark ----
    novel = []

    # N1 canonical-form invariance (POSITIVE): reordering evidence_package keys
    # must NOT change package_sha256 -> no false reject from key order.
    cand = evidence_candidate("phase0-oracle-invariance",
                              {"measurement": "gel_time_h", "value": 4.2})
    reordered = {"payload_extra": {"value": 4.2, "measurement": "gel_time_h"},
                 "payload_kind": "lab_measurement"}
    novel.append({"probe_id": "canonical_key_order_invariance",
                  "expect": "INVARIANT_ACCEPT",
                  "pass": stable_hash(package_of(cand)) == stable_hash(reordered)})

    # N2 type-confusion: package value as STRING "4.2" vs number 4.2 -> distinct
    # hash; a receipt bound to the numeric package must reject the stringified one.
    numeric = evidence_candidate("phase0-oracle-typeconf", {"measurement": "x", "value": 4.2})
    stringy = evidence_candidate("phase0-oracle-typeconf", {"measurement": "x", "value": "4.2"})
    r_numeric = build_valid_receipt(numeric)
    novel.append({"probe_id": "number_vs_string_type_confusion",
                  "expect": "REJECT",
                  "pass": evaluate(stringy, r_numeric)["status"] == "FAILED_GATES"
                          and stable_hash(package_of(numeric)) != stable_hash(package_of(stringy))})

    # N3 cross-package swap: valid receipt for package A presented with package B
    # (both valid candidates, same candidate_id) -> reject (2nd-preimage guard).
    packB = evidence_candidate("phase0-oracle-typeconf", {"measurement": "x", "value": 9.9})
    novel.append({"probe_id": "cross_package_swap_second_preimage",
                  "expect": "REJECT",
                  "pass": evaluate(packB, r_numeric)["status"] == "FAILED_GATES"})

    # N4 hash-hex uppercase: package_sha256 correct value but upper-cased ->
    # reject (exact-string compare, no case folding).
    up = make_mutate(r_numeric, "package_sha256", r_numeric["package_sha256"].upper())
    novel.append({"probe_id": "package_sha256_uppercase_hex",
                  "expect": "REJECT",
                  "pass": evaluate(numeric, up)["status"] == "FAILED_GATES"})

    # N5 truncated contract hash (63 chars) -> reject.
    tr = make_mutate(r_numeric, "candidate_contract_hash_v1",
                     contract_hash_v1(numeric)[:63])
    novel.append({"probe_id": "contract_hash_truncated_63",
                  "expect": "REJECT",
                  "pass": evaluate(numeric, tr)["status"] == "FAILED_GATES"})

    # N6 whitespace-padded schema string -> reject (no trim).
    ws = make_mutate(r_numeric, "schema", HOST_VERIFIED_RECEIPT_SCHEMA + " ")
    novel.append({"probe_id": "schema_trailing_whitespace",
                  "expect": "REJECT",
                  "pass": evaluate(numeric, ws)["status"] == "FAILED_GATES"})

    # N7 boolean-as-string 'true' for accepted -> reject (strict bool, no coerce).
    bs = make_mutate(r_numeric, "accepted", "true")
    novel.append({"probe_id": "accepted_string_true_not_bool",
                  "expect": "REJECT",
                  "pass": evaluate(numeric, bs)["status"] == "FAILED_GATES"})

    # N8 verifier_id whitespace-only survives (Rust checks only is_empty(), not
    # trim) -> documents the EXACT boundary: a single space is NON-empty so it
    # ACCEPTS. Honest boundary characterization, not a defect claim.
    sp = build_valid_receipt(numeric, verifier_id=" ")
    novel.append({"probe_id": "verifier_id_single_space_boundary",
                  "expect": "ACCEPT_DOCUMENTED_BOUNDARY",
                  "pass": evaluate(numeric, sp)["status"] == "SCORED"})

    g4_pass = all(x["pass"] for x in novel)

    diag["g1_package_anchor_reproduction"] = {"records": g1, "all_match": g1_pass}
    diag["positive_decision_parity"] = {"records": pos_parity, "all_parity": pos_pass}
    diag["g2_contract_hash_binding"] = g2
    diag["g3_mutation_decision_parity"] = {"records": g3, "all_parity_fail_closed": g3_pass}
    diag["g4_novel_probes"] = {"records": novel, "all_pass": g4_pass}
    diag["gates"] = {
        "g1_anchors_reproduced": g1_pass,
        "g2_contract_binding_replay_rejected": g2_pass,
        "g3_shipped_decisions_reproduced": pos_pass and g3_pass,
        "g4_novel_probes_pass": g4_pass,
        "all_pass": g1_pass and pos_pass and g2_pass and g3_pass and g4_pass,
    }
    diag["counts"] = {
        "positive_scenarios": len(POSITIVE),
        "shipped_mutation_probes": len(probes),
        "novel_probes": len(novel),
        "total_cases": len(POSITIVE) + len(probes) + len(novel),
    }
    print(json.dumps(diag))

if __name__ == "__main__":
    main()
