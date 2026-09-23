#!/usr/bin/env python3
"""
amphora-evidence-intake-validator :: canonicalization-invariance-tamper-completeness-v1

Independent NON-RUNTIME CPython audit of the BYTE-BINDING layer of the
evidence-intake acceptance predicate. The live authority is native Rust
(amphora-assurance-capabilities/src/lib.rs host_receipt_valid /
evaluate_evidence_intake; canonical hashing amphora-core stable_hash+canonicalize).
Prior audits covered (a) shipped decision parity + 8 tamper probes
[host-receipt-oracle-parity-v1] and (b) the exhaustive 2^11 boolean-clause truth
table [predicate-completeness-v1]. NEITHER characterised the byte-level integrity
property that the whole predicate rests on: that package_sha256 is a
canonicalization-INVARIANT, tamper-COMPLETE binding of the evidence package bytes.

This audit closes that gap over a coating-domain (epoxy-amine / DGEBA-amine) evidence
corpus with four gates:

  G0  reproduce the 3 shipped positive package_sha256 anchors byte-exact
  G1  INVARIANCE: for every package, all JCS-equivalent re-encodings (key-order
      permutation at every nesting depth, source-whitespace, unicode escape-form
      \\uXXXX vs literal, compact vs spaced separators) yield an IDENTICAL
      package_sha256 -> the ACCEPT decision is preserved (reorder/reformat cannot
      evade). RFC 8785 JSON Canonicalization Scheme invariance property.
  G2  TAMPER COMPLETENESS: for every package, every single-atom semantic mutation
      (numeric delta incl. 1-ULP, int<->float type flip, string char flip, key
      rename, field add, field remove, value/type swap) CHANGES package_sha256
      (zero silent collisions) AND flips the runtime decision ACCEPT->FAILED_GATES
      because the frozen receipt's package_sha256 / candidate_contract_hash_v1 no
      longer match the recomputed bytes. NIST SP 800-53 SI-7 integrity.
  G3  AVALANCHE: over all mutations the SHA-256 digest bit-flip fraction has
      min>0 and mean within a broad [0.30,0.70] band (FIPS 180-4 diffusion),
      i.e. tamper detection is not marginal.

Scope note (honest): canonicalization is nominal/TYPE-exact, NOT numeric-normalizing;
integer 110, float 110.0, and string "110" are DISTINCT bindings (G2 exercises this
as a detected change). This matches the shipped Rust semantics and the portfolio
packager-canonicalization finding (110.0 != 110). No wet-lab, product-qualification,
legal, regulatory, or scientific authority is asserted -- infrastructure front-door
byte-integrity only.

Theory / standards anchoring:
  RFC 8785 JSON Canonicalization Scheme (2020) -- canonical-form invariance
  NIST FIPS 180-4 SHA-256 (2015); avalanche/diffusion of a cryptographic hash
  NIST SP 800-53 Rev.5 SI-7 information integrity (2020)
  NIST FIPS 186-5 EdDSA (2023); RFC 8032 Ed25519 (2017)
"""
import json, hashlib, sys

DATE = "2026-07-30"

# --- independent re-impl of amphora-core canonicalize + stable_hash ---------
def canonicalize(v):
    if isinstance(v, dict):
        return {k: canonicalize(v[k]) for k in sorted(v.keys())}
    if isinstance(v, list):
        return [canonicalize(x) for x in v]
    return v

def stable_hash_obj(v):
    b = json.dumps(canonicalize(v), separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

HOST_SCHEMA = "amphora.host-verified-evidence-receipt.v1"

def evidence_candidate(cid, payload_extra):
    package = {"payload_kind": "lab_measurement", "payload_extra": payload_extra}
    return {"candidate_id": cid, "candidate_type": "evidence_package",
            "evidence_refs": {"evidence_package": package}}

def package_of(c): return c["evidence_refs"]["evidence_package"]
def contract_hash_v1(c): return stable_hash_obj(c)

def build_valid_receipt(cand):
    return {"schema": HOST_SCHEMA, "accepted": True, "signature_verified": True,
            "revocation_checked": True, "fresh": True, "signature_algorithm": "Ed25519",
            "trust_store_status": "TRUSTED", "candidate_id": cand["candidate_id"],
            "candidate_contract_hash_v1": contract_hash_v1(cand),
            "package_sha256": stable_hash_obj(package_of(cand)),
            "verifier_id": "host-trust-kernel-phase0"}

def host_receipt_valid(cand, receipt, package_sha256):
    if not isinstance(receipt, dict): return False
    return (len(receipt) == 11
        and receipt.get("schema") == HOST_SCHEMA
        and receipt.get("accepted") is True
        and receipt.get("signature_verified") is True
        and receipt.get("revocation_checked") is True
        and receipt.get("fresh") is True
        and receipt.get("signature_algorithm") == "Ed25519"
        and receipt.get("trust_store_status") == "TRUSTED"
        and receipt.get("candidate_id") == cand["candidate_id"]
        and receipt.get("candidate_contract_hash_v1") == contract_hash_v1(cand)
        and receipt.get("package_sha256") == package_sha256
        and isinstance(receipt.get("verifier_id"), str)
        and len(receipt.get("verifier_id")) > 0)

def decide(cand, receipt):
    ps = stable_hash_obj(package_of(cand))
    return "SCORED" if host_receipt_valid(cand, receipt, ps) else "FAILED_GATES"

# --- corpus: 3 shipped anchors + coating-domain extensions ------------------
POSITIVE_ANCHORS = [
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
# extra epoxy-amine domain evidence packages (multi-key, mixed types, unicode)
EXTRA = [
    ("dgeba-eew-titration", "phase0-eew",
     {"measurement": "eew_g_per_eq", "value": 170.21, "method": "ASTM_D1652", "resin": "DGEBA"}),
    ("teta-ahew-value", "phase0-ahew",
     {"measurement": "ahew_g_per_eq", "value": 24.37, "hardener": "TETA"}),
    ("brookfield-viscosity", "phase0-visc",
     {"measurement": "viscosity_mpa_s", "value": 1250.0, "instrument": "Brookfield-DV³",
      "spindle": 4, "rpm": 20}),
]

def all_candidates():
    out = []
    for sid, cid, extra, _ in POSITIVE_ANCHORS:
        out.append((sid, evidence_candidate(cid, extra)))
    for sid, cid, extra in EXTRA:
        out.append((sid, evidence_candidate(cid, extra)))
    return out

# --- JCS-equivalent re-encodings (semantic-preserving) ----------------------
def reverse_keys_recursive(v):
    if isinstance(v, dict):
        return {k: reverse_keys_recursive(v[k]) for k in reversed(list(v.keys()))}
    if isinstance(v, list):
        return [reverse_keys_recursive(x) for x in v]
    return v

def encodings_of(pkg):
    """Return list of (label, serialized_bytes) all parsing to a package
    semantically identical to pkg under JCS canonicalization."""
    rev = reverse_keys_recursive(pkg)
    return [
        ("compact_insertion_order", json.dumps(pkg, separators=(",", ":"), ensure_ascii=False)),
        ("compact_sorted", json.dumps(pkg, separators=(",", ":"), sort_keys=True, ensure_ascii=False)),
        ("indent4_whitespace", json.dumps(pkg, indent=4, ensure_ascii=False)),
        ("indent2_sorted", json.dumps(pkg, indent=2, sort_keys=True, ensure_ascii=False)),
        ("reversed_key_order", json.dumps(rev, separators=(",", ":"), ensure_ascii=False)),
        ("ascii_escaped_unicode", json.dumps(pkg, separators=(",", ":"), ensure_ascii=True)),
        ("spaced_separators", json.dumps(pkg, separators=(", ", ": "), ensure_ascii=False)),
    ]

# --- single-atom semantic mutations (each MUST change the hash) -------------
def mutations_of(pkg):
    """Yield (label, mutated_pkg) list; each is a semantic change."""
    muts = []
    keys = list(pkg.keys())
    extra = pkg["payload_extra"]
    ekeys = list(extra.keys())
    # top-level key rename
    m = {("payload_kind_X" if k == "payload_kind" else k): pkg[k] for k in keys}
    muts.append(("rename_top_key", m))
    # top-level field add
    m = dict(pkg); m["injected_field"] = "smuggle"; muts.append(("add_top_field", m))
    # top-level field remove
    m = {k: pkg[k] for k in keys if k != "payload_kind"}; muts.append(("remove_top_field", m))
    # payload_kind string char flip
    m = json.loads(json.dumps(pkg)); m["payload_kind"] = m["payload_kind"][:-1] + "X"
    muts.append(("flip_payload_kind_char", m))
    for ek in ekeys:
        val = extra[ek]
        base = json.loads(json.dumps(pkg))
        if isinstance(val, bool):
            base["payload_extra"][ek] = (not val); muts.append((f"flip_bool_{ek}", base))
        elif isinstance(val, (int, float)) and not isinstance(val, bool):
            # coarse numeric change
            b1 = json.loads(json.dumps(pkg)); b1["payload_extra"][ek] = val + 1
            muts.append((f"num_plus1_{ek}", b1))
            # 1-ULP-ish minimal float delta
            b2 = json.loads(json.dumps(pkg)); b2["payload_extra"][ek] = float(val) + 1e-9
            muts.append((f"num_epsilon_{ek}", b2))
            # int<->float type flip (nominal/type-exact binding)
            b3 = json.loads(json.dumps(pkg))
            b3["payload_extra"][ek] = float(val) if isinstance(val, int) else int(val)
            if b3["payload_extra"][ek] != val or type(b3["payload_extra"][ek]) != type(val):
                muts.append((f"num_type_flip_{ek}", b3))
            # number -> string (type change)
            b4 = json.loads(json.dumps(pkg)); b4["payload_extra"][ek] = str(val)
            muts.append((f"num_to_string_{ek}", b4))
        elif isinstance(val, str):
            b1 = json.loads(json.dumps(pkg))
            b1["payload_extra"][ek] = (val[:-1] + "Z") if val else "Z"
            muts.append((f"flip_string_{ek}", b1))
        # rename this extra key
        bk = json.loads(json.dumps(pkg))
        newextra = {(ek + "_X" if k == ek else k): bk["payload_extra"][k]
                    for k in bk["payload_extra"].keys()}
        bk["payload_extra"] = newextra; muts.append((f"rename_extra_key_{ek}", bk))
    # add nested field
    m = json.loads(json.dumps(pkg)); m["payload_extra"]["nested_injected"] = 1
    muts.append(("add_nested_field", m))
    return muts

def bitflip_fraction(hex_a, hex_b):
    a = int(hex_a, 16); b = int(hex_b, 16)
    return bin(a ^ b).count("1") / 256.0

def main():
    shipped_path = sys.argv[1]
    shipped = json.load(open(shipped_path))
    shipped_rec = {}
    for r in shipped["records"]:
        shipped_rec[r.get("scenario_id") or r.get("probe_id")] = r

    cands = all_candidates()

    # ---- G0: shipped anchors byte-exact + parity to shipped runtime ----
    g0 = []
    for sid, cid, extra, expected in POSITIVE_ANCHORS:
        cand = evidence_candidate(cid, extra)
        got = stable_hash_obj(package_of(cand))
        srec = shipped_rec.get(sid, {})
        g0.append({"scenario_id": sid, "oracle_package_sha256": got,
                   "shipped_anchor_sha256": expected, "match": got == expected,
                   "shipped_status": srec.get("status"),
                   "shipped_package_sha256_match": srec.get("package_sha256") == got})
    g0_pass = all(x["match"] and x["shipped_status"] == "SCORED"
                  and x["shipped_package_sha256_match"] for x in g0)

    # ---- G1: canonicalization invariance -> accept preserved ----
    g1_records = []
    g1_total_encodings = 0
    g1_disagreements = 0
    for sid, cand in cands:
        pkg = package_of(cand)
        base_hash = stable_hash_obj(pkg)
        receipt = build_valid_receipt(cand)  # frozen on canonical package
        assert decide(cand, receipt) == "SCORED"
        enc_hashes = []
        enc_decisions = []
        for label, text in encodings_of(pkg):
            reparsed = json.loads(text)
            h = stable_hash_obj(reparsed)
            enc_hashes.append(h)
            recand = {"candidate_id": cand["candidate_id"],
                      "candidate_type": cand["candidate_type"],
                      "evidence_refs": {"evidence_package": reparsed}}
            enc_decisions.append(decide(recand, receipt))
            g1_total_encodings += 1
        n_unique = len(set(enc_hashes))
        invariant = (n_unique == 1 and enc_hashes[0] == base_hash)
        accept_preserved = all(d == "SCORED" for d in enc_decisions)
        if not (invariant and accept_preserved):
            g1_disagreements += 1
        g1_records.append({"scenario_id": sid, "n_encodings": len(enc_hashes),
                           "unique_hashes": n_unique, "invariant": invariant,
                           "accept_preserved_all_encodings": accept_preserved,
                           "package_sha256": base_hash})
    g1_pass = (g1_disagreements == 0 and
               all(r["invariant"] and r["accept_preserved_all_encodings"] for r in g1_records))

    # ---- G2 + G3: tamper completeness + avalanche ----
    g2_records = []
    total_mut = 0
    hash_collisions = 0     # mutation that did NOT change package_sha256
    silent_accepts = 0      # mutation still accepted by frozen receipt
    contract_still_binds = 0
    flips = []
    for sid, cand in cands:
        pkg = package_of(cand)
        base_hash = stable_hash_obj(pkg)
        receipt = build_valid_receipt(cand)  # frozen on ORIGINAL bytes
        n_mut = 0
        for label, mpkg in mutations_of(pkg):
            total_mut += 1; n_mut += 1
            mhash = stable_hash_obj(mpkg)
            if mhash == base_hash:
                hash_collisions += 1
            else:
                flips.append(bitflip_fraction(base_hash, mhash))
            mcand = {"candidate_id": cand["candidate_id"],
                     "candidate_type": cand["candidate_type"],
                     "evidence_refs": {"evidence_package": mpkg}}
            dec = decide(mcand, receipt)
            if dec == "SCORED":
                silent_accepts += 1
            # attribute rejection to byte-binding: recomputed contract hash differs
            if contract_hash_v1(mcand) == receipt["candidate_contract_hash_v1"]:
                contract_still_binds += 1
        g2_records.append({"scenario_id": sid, "n_mutations": n_mut})
    g2_pass = (hash_collisions == 0 and silent_accepts == 0 and total_mut > 0)
    mean_flip = sum(flips) / len(flips) if flips else 0.0
    min_flip = min(flips) if flips else 0.0
    max_flip = max(flips) if flips else 0.0
    g3_pass = (len(flips) == total_mut and min_flip > 0.0 and 0.30 <= mean_flip <= 0.70)

    all_pass = g0_pass and g1_pass and g2_pass and g3_pass

    diag = {
        "schema": "amphora.evidence-intake-canonicalization-invariance-tamper.v1",
        "date": DATE,
        "module_id": "amphora-evidence-intake-validator",
        "generated_on_host": "xbabe2",
        "live_authority_under_test": {
            "rust_predicate": "amphora-assurance-capabilities/src/lib.rs "
                              "host_receipt_valid / evaluate_evidence_intake",
            "rust_canonical_hash": "amphora-core stable_hash + canonicalize",
            "oracle_is_runtime": False},
        "theory": [
            "RFC 8785 JSON Canonicalization Scheme (2020) canonical-form invariance",
            "NIST FIPS 180-4 SHA-256 (2015) avalanche/diffusion",
            "NIST SP 800-53 Rev.5 SI-7 information integrity (2020)",
            "NIST FIPS 186-5 EdDSA (2023); RFC 8032 Ed25519 (2017)"],
        "corpus": {"n_packages": len(cands),
                   "packages": [s for s, _ in cands],
                   "domain": "epoxy-amine / DGEBA-amine coating lab evidence"},
        "g0_shipped_anchor_reproduction": {"pass": g0_pass, "records": g0},
        "g1_canonicalization_invariance": {
            "pass": g1_pass, "total_encodings_checked": g1_total_encodings,
            "disagreements": g1_disagreements, "records": g1_records,
            "property": "reorder/reformat/unicode-escape/whitespace cannot change "
                        "package_sha256 -> accept decision preserved"},
        "g2_tamper_completeness": {
            "pass": g2_pass, "total_mutations": total_mut,
            "hash_collisions": hash_collisions, "silent_accepts": silent_accepts,
            "contract_hash_still_binds_after_mutation": contract_still_binds,
            "records": g2_records,
            "property": "every single-atom semantic mutation changes package_sha256 "
                        "AND flips decision ACCEPT->FAILED_GATES; zero silent accept"},
        "g3_avalanche": {
            "pass": g3_pass, "n_measured": len(flips),
            "mean_bitflip_fraction": mean_flip, "min_bitflip_fraction": min_flip,
            "max_bitflip_fraction": max_flip, "band": [0.30, 0.70]},
        "scope_note": "canonicalization is nominal/type-exact NOT numeric-normalizing; "
                      "int 110, float 110.0, string '110' are DISTINCT bindings "
                      "(exercised as detected changes in G2). Matches shipped Rust "
                      "semantics and portfolio packager-canonicalization finding.",
        "closes": "byte-binding representation-invariance + tamper/avalanche "
                  "completeness gap left open by host-receipt-oracle-parity-v1 "
                  "(decision parity) and predicate-completeness-v1 (boolean clauses)",
        "does_not_establish": [
            "product qualification", "batch release", "legal freedom to operate",
            "regulatory compliance", "wet-lab performance", "scientific readiness"],
        "gates": {"G0_shipped_anchors": g0_pass, "G1_invariance": g1_pass,
                  "G2_tamper_completeness": g2_pass, "G3_avalanche": g3_pass},
        "all_gates_passed": all_pass,
        "counts": {"n_packages": len(cands), "n_encodings": g1_total_encodings,
                   "n_mutations": total_mut,
                   "total_decisions_evaluated": g1_total_encodings + total_mut + len(cands)},
    }
    sys.stdout.write(json.dumps(diag, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
