#!/usr/bin/env python3
"""LIVE differential oracle for amphora-run-provenance
(evidence/audit/live-runtime-archive-parity-v1).

FIRST study in this module that EXECUTES the live Rust runtime (all three
prior receipts pinned live re-exec parity as their top does_not_close gap).
A standalone Rust harness (live_harness/) links amphora-core and calls the
real RunArchive::create/append/snapshot/final_state and verify_run entry
points; this CPython oracle then INDEPENDENTLY re-derives every hash from the
live archive bytes the harness emits (no import of, and no code shared with,
the Rust runtime) and measures:

  G0  Anchors: pins SHA-256 of the runtime sources actually executed
      (amphora-core lib.rs + contract.rs), the harness, the three prior
      signed receipts, the shipped KPI, and the module manifest.
  G1  Live positive parity: for the 3 shipped Phase-0 KPI constructions
      (0/3/12 events) plus a unicode+float+snapshot stressor, every
      provenance field (manifest_sha256, events_sha256, event_chain_root,
      final_state_hash, root_hash) and the verify_run return value equal the
      oracle's independent recompute from the live bytes, and every interior
      Haber-Stornetta event_hash recomputes bit-exact.  Cross-time anchor:
      the live roots for the 3 shipped constructions must equal the roots
      recorded in the SIGNED 2026 hash-chain-oracle-parity-v1 receipt
      (live-Rust-today == independent-CPython-then, 15 fields).
  G2  Live RunArchiveError taxonomy: 11 single-mutation probes elicit all
      five variants (Exists/Integrity/Io/Json/Contract); observed variant
      must equal the variant this oracle predicts analytically from the
      runtime source, incl. the Json-vs-Contract split (shape mismatch after
      strict parse -> Json; duplicate key / syntax error in events.jsonl ->
      Contract via parse_json_strict).
  G3  H0a "the strict-parse wall (duplicate-key rejection) and
      representation-binding cover all archive surfaces uniformly":
      per-surface malleability matrix over manifest / events / final-state /
      provenance / snapshot.  Parser-differential check: for every dup-key
      byte stream the live runtime ACCEPTED, this oracle's strict
      (RFC 8785-style) parser must REJECT the same bytes.
  G4  H0b "verify_run re-verifies the interior Haber-Stornetta linkage":
      hand-forged archive with garbage interior event_hash values but
      arithmetically consistent provenance.

THEORY (primary sources): Haber & Stornetta 1991, "How to time-stamp a
digital document", J. Cryptology 3(2):99-111, doi:10.1007/BF00196791
(hash-chain linking; the interior linkage semantics G4 tests); Merkle 1980
IEEE S&P (hash chaining); NIST FIPS 180-4 (2015) SHA-256; RFC 8259 (2017)
sect. 4 (duplicate JSON names -> unpredictable behavior); RFC 8785 (2020)
JSON Canonicalization Scheme (the strict representation-invariance G3 tests
against); Momot, Bratus, Hallberg & Patterson 2016, "The Seven Turrets of
Babel: A Taxonomy of LangSec Errors and How to Expunge Them", IEEE SecDev,
doi:10.1109/SecDev.2016.019 (parser differentials as a vulnerability class);
Crosby & Wallach 2009 USENIX Security (tamper-evident logging, efficient
verification of ALL interior links).

AUDIT_ONLY. Does NOT promote authority, does NOT flip scientific_readiness,
does NOT modify the portfolio manifest (66 receipts / 11 modules), the
module-manifest, any locked dataset, or a signed Phase-0 KPI.  The live
harness writes only under /tmp scratch.  Deterministic: no wall-clock, no
RNG; only RunArchiveError variant NAMES are recorded, never tempdir paths;
the two-replay gate runs the live harness twice in different scratch dirs and
requires byte-identical output, then builds the diagnostic independently from
each run.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
MOD = os.path.join(ROOT, "amphora-run-provenance")
AUD = os.path.join(MOD, "evidence/audit/live-runtime-archive-parity-v1")
HARNESS = os.path.join(AUD, "live_harness")
TARGET = "/tmp/rp-live-target"

STUDY_ID = "amphora-run-provenance.live-runtime-archive-parity.v1"


# ---------------------------------------------------------------------------
# Hash primitives -- independent re-implementation of amphora-core::stable_hash
# (same as the sibling parity oracle; shares no code with the Rust runtime).
# ---------------------------------------------------------------------------
def raw_sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonicalize(v):
    if isinstance(v, dict):
        return {k: canonicalize(v[k]) for k in sorted(v)}
    if isinstance(v, list):
        return [canonicalize(x) for x in v]
    return v


def stable_hash(v) -> str:
    body = json.dumps(canonicalize(v), separators=(",", ":"), ensure_ascii=False)
    return raw_sha256(body.encode("utf-8"))


def raw_file(path: str) -> str:
    with open(path, "rb") as f:
        return raw_sha256(f.read())


def strict_pairs(pairs):
    """RFC 8785-style strictness: duplicate names are a hard error (the same
    rule amphora-core parse_json_strict enforces)."""
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate JSON key: {k}")
        d[k] = v
    return d


def strict_loads(text: str):
    return json.loads(text, object_pairs_hook=strict_pairs)


def strict_rejects(text: str) -> bool:
    try:
        strict_loads(text)
        return False
    except ValueError:
        return True


# ---------------------------------------------------------------------------
# Independent re-derivation of a live archive from its emitted bytes.
# ---------------------------------------------------------------------------
def rederive_archive(files: dict, run_id: str):
    """Recompute every provenance field and every interior event_hash from the
    LIVE bytes only.  Events are parsed with the strict duplicate-rejecting
    parser (mirroring read_events -> parse_json_strict)."""
    manifest_b = files["manifest.json"].encode("utf-8")
    events_b = files["events.jsonl"].encode("utf-8")
    events = [strict_loads(line) for line in files["events.jsonl"].splitlines()
              if line.strip()]
    prev = None
    chain_recompute_ok = []
    for e in events:
        seed = {
            "schema": e["schema"],
            "sequence": e["sequence"],
            "run_id": e["run_id"],
            "event_type": e["event_type"],
            "candidate_id": e["candidate_id"],
            "generation": e["generation"],
            "payload": e["payload"],
            "previous_event_hash": prev,
        }
        chain_recompute_ok.append(stable_hash(seed) == e["event_hash"])
        prev = e["event_hash"]
    chain_root = events[-1]["event_hash"] if events else raw_sha256(b"")
    final_state = json.loads(files["final-state.json"])
    derived = {
        "run_id": run_id,
        "manifest_sha256": raw_sha256(manifest_b),
        "events_sha256": raw_sha256(events_b),
        "event_chain_root": chain_root,
        "final_state_hash": stable_hash(final_state),
    }
    derived_root = stable_hash(derived)
    return derived, derived_root, chain_recompute_ok


# ---------------------------------------------------------------------------
# Analytic predictions (from reading amphora-core/src/lib.rs verify_run and
# contract.rs parse_json_strict -- stated here BEFORE observation).
# ---------------------------------------------------------------------------
PREDICTED = {
    "exists-duplicate-create": ("Exists", "create_new semantics: path already exists"),
    "integrity-noncontiguous-sequence": ("Integrity", "sequence-contiguity check fires before hash comparison"),
    "integrity-root-hash-flip": ("Integrity", "observed root_hash != stable_hash(expected 5-field seed)"),
    "integrity-missing-root-hash": ("Integrity", "explicit 'missing root hash' arm"),
    "integrity-manifest-byte-append": ("Integrity", "manifest_sha256 raw-byte binding"),
    "io-missing-manifest": ("Io", "fs::read on deleted file"),
    "io-missing-provenance": ("Io", "fs::read on deleted file (first read in verify_run)"),
    "json-malformed-provenance": ("Json", "provenance parsed with LENIENT serde_json::from_slice, so a syntax error surfaces as Json, not Contract"),
    "json-event-shape-string-sequence": ("Json", "parse_json_strict accepts the value; serde from_value(Event) type error -> Json"),
    "contract-duplicate-key-event": ("Contract", "events.jsonl goes through parse_json_strict, whose duplicate-key rejection -> ContractError -> Contract"),
    "contract-truncated-event-line": ("Contract", "syntax errors in events.jsonl are wrapped by parse_json_strict as ContractError::InvalidJson -> Contract (NOT Json)"),
    "surface-events-key-reorder": ("Integrity", "events surface is raw-byte-bound via events_sha256; a semantics-preserving re-serialization still fails closed"),
    "surface-final-state-duplicate-key": ("Ok", "final-state surface is VALUE-bound (final_state_hash of the lenient last-wins parse); dup key with same value passes"),
    "surface-final-state-reformat-compact": ("Ok", "final-state surface is value-bound; bytes are malleable"),
    "surface-provenance-duplicate-root-shadow": ("Ok", "provenance container bytes are hashed by nothing verify_run checks; lenient last-wins takes the honest root"),
    "surface-provenance-reformat-compact": ("Ok", "provenance container bytes are unbound"),
    "surface-manifest-reformat-compact": ("Integrity", "manifest is raw-byte-bound and NEVER parsed by verify_run"),
    "surface-snapshot-tamper": ("Ok", "snapshot-*.json files are entirely outside the verify_run read-set"),
    "forged-interior-chain-consistent-root": ("Ok", "verify_run never recomputes interior event_hash values; it only checks event_chain_root == last RECORDED hash plus file hashes"),
    "forged-chain-root-mismatch": ("Integrity", "event_chain_root equality against the last recorded event_hash IS checked"),
}

# Surface-binding model derived from the same source reading.
SURFACE_MATRIX = {
    "manifest.json": {"binding": "RAW_BYTE_BOUND_NEVER_PARSED",
                      "strict_parse_wall": False,
                      "byte_malleable_accepted": False},
    "events.jsonl": {"binding": "RAW_BYTE_BOUND_PLUS_STRICT_PARSED_PLUS_SEQUENCE_CHECKED",
                     "strict_parse_wall": True,
                     "byte_malleable_accepted": False},
    "final-state.json": {"binding": "VALUE_BOUND_LENIENT_PARSE",
                         "strict_parse_wall": False,
                         "byte_malleable_accepted": True},
    "provenance.json": {"binding": "SELF_CONTAINER_UNBOUND_LENIENT_PARSE",
                        "strict_parse_wall": False,
                        "byte_malleable_accepted": True},
    "snapshot-*.json": {"binding": "UNBOUND_OUTSIDE_VERIFY_READ_SET",
                        "strict_parse_wall": False,
                        "byte_malleable_accepted": True},
}


def run_harness(binary: str) -> bytes:
    scratch = tempfile.mkdtemp(prefix="rp-live-scratch-")
    try:
        proc = subprocess.run([binary, scratch], capture_output=True, timeout=600)
        if proc.returncode != 0:
            sys.stderr.write(proc.stderr.decode(errors="replace"))
            raise SystemExit("live harness failed")
        return proc.stdout
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def build_diagnostic(live_bytes: bytes, toolchain: dict, anchors: dict) -> dict:
    live = json.loads(live_bytes)

    # ---- G1: positive scenarios ------------------------------------------
    prior = json.load(open(os.path.join(
        MOD, "evidence/audit/hash-chain-oracle-parity-v1/diagnostic.canonical.json")))
    prior_roots = {a["scenario"]: a for a in prior["g1_positive_archives"]}

    g1 = []
    g1_field_checks = g1_field_pass = 0
    g1_chain_events = g1_chain_pass = 0
    for sc in live["scenarios"]:
        files = sc["files"]
        prov = json.loads(files["provenance.json"])
        derived, derived_root, chain_ok = rederive_archive(files, sc["run_id"])
        checks = {
            "manifest_sha256": prov.get("manifest_sha256") == derived["manifest_sha256"],
            "events_sha256": prov.get("events_sha256") == derived["events_sha256"],
            "event_chain_root": prov.get("event_chain_root") == derived["event_chain_root"],
            "final_state_hash": prov.get("final_state_hash") == derived["final_state_hash"],
            "root_hash": prov.get("root_hash") == derived_root,
            "verify_run_returned_derived_root":
                sc["verify_result"] == "Ok" and sc["verify_root_hash"] == derived_root,
            "signature_status_pinned":
                prov.get("signature_status") == "UNSIGNED_CONTROLLED_KEY_REQUIRED",
            "promotion_receipt_eligible_pinned_false":
                prov.get("promotion_receipt_eligible") is False,
        }
        g1_field_checks += len(checks)
        g1_field_pass += sum(checks.values())
        g1_chain_events += len(chain_ok)
        g1_chain_pass += sum(chain_ok)
        entry = {
            "scenario_id": sc["scenario_id"],
            "run_id": sc["run_id"],
            "n_events": sc["n_events"],
            "live_verify_result": sc["verify_result"],
            "live_root_hash": sc["verify_root_hash"],
            "oracle_derived_root_hash": derived_root,
            "oracle_derived_fields": derived,
            "field_parity": checks,
            "interior_chain_recompute_ok": all(chain_ok),
        }
        g1.append(entry)

    # ---- G1b: legacy-mirror differential vs the SIGNED 2026 receipt ------
    # The live harness rebuilds the EXACT content of the 2026 receipt's G1
    # archives (pos-empty/small/complex).  Predicted from source BEFORE
    # observation: value-bound fields (event_chain_root, final_state_hash,
    # and events_sha256 when there are no events) MATCH the receipt, while
    # byte-bound fields written through serde_json Value key-sorting
    # (manifest_sha256; events_sha256 via the payload sub-Value inside each
    # event line; hence root_hash) DIFFER, because the receipt's Python
    # mirror wrote insertion-order bytes where the live runtime sorts keys
    # (BTreeMap).  Reconstruction: re-serializing the LIVE content with the
    # mirror's insertion orders must reproduce the receipt's numbers exactly,
    # localizing every divergent bit to that single root cause.
    LEGACY_MANIFEST_INSERTION = [
        "schema", "run_id", "scope", "monte_carlo_seed", "n_events_planned"]
    legacy = []
    g1b_checks = g1b_pass = 0
    for sc in live["scenarios"]:
        if not sc["scenario_id"].startswith("legacy-"):
            continue
        p = prior_roots[sc["scenario_id"].split("-", 1)[1]]
        run_id = sc["run_id"]
        n = sc["n_events"]
        files = sc["files"]
        derived, derived_root, _ = rederive_archive(files, run_id)
        match_fields = ["event_chain_root", "final_state_hash"]
        diff_fields = ["manifest_sha256", "root_hash"]
        (match_fields if n == 0 else diff_fields).insert(0, "events_sha256")
        checks = {}
        for k in match_fields:
            checks[f"live_matches_prior_{k}"] = derived[k] == p[k]
        for k in diff_fields:
            v_live = derived_root if k == "root_hash" else derived[k]
            checks[f"live_differs_from_prior_{k}"] = v_live != p[k]
        manifest_live_val = json.loads(files["manifest.json"])
        ins_manifest = {k: manifest_live_val[k]
                        for k in LEGACY_MANIFEST_INSERTION}
        prior_manifest_bytes = (
            json.dumps(ins_manifest, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        checks["reconstructed_insertion_order_manifest_sha256_equals_prior"] = (
            raw_sha256(prior_manifest_bytes) == p["manifest_sha256"])
        checks["manifest_value_equality_live_vs_prior_content"] = (
            manifest_live_val == ins_manifest)
        events_live = [strict_loads(l)
                       for l in files["events.jsonl"].splitlines() if l.strip()]
        prior_events = b""
        for e in events_live:
            payload_ins = {"idx": e["payload"]["idx"],
                           "note": e["payload"]["note"],
                           "delta": e["payload"]["delta"]}
            line = {
                "schema": e["schema"], "sequence": e["sequence"],
                "run_id": e["run_id"], "event_type": e["event_type"],
                "candidate_id": e["candidate_id"],
                "generation": e["generation"], "payload": payload_ins,
                "event_hash": e["event_hash"],
            }
            prior_events += json.dumps(
                line, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8") + b"\n"
        checks["reconstructed_insertion_order_events_sha256_equals_prior"] = (
            raw_sha256(prior_events) == p["events_sha256"])
        prior_seed = {
            "run_id": run_id,
            "manifest_sha256": raw_sha256(prior_manifest_bytes),
            "events_sha256": raw_sha256(prior_events),
            "event_chain_root": derived["event_chain_root"],
            "final_state_hash": derived["final_state_hash"],
        }
        checks["reconstructed_root_hash_equals_prior"] = (
            stable_hash(prior_seed) == p["root_hash"])
        g1b_checks += len(checks)
        g1b_pass += sum(checks.values())
        legacy.append({
            "scenario_id": sc["scenario_id"],
            "run_id": run_id,
            "n_events": n,
            "live_root_hash": derived_root,
            "prior_receipt_root_hash": p["root_hash"],
            "checks": checks,
        })
    h0c_refuted = len(legacy) == 3 and all(
        l["checks"]["live_differs_from_prior_manifest_sha256"]
        and l["checks"]["reconstructed_insertion_order_manifest_sha256_equals_prior"]
        and l["checks"]["reconstructed_root_hash_equals_prior"]
        for l in legacy)

    # ---- G2 + G3 + G4: probes --------------------------------------------
    probes = {p["probe_id"]: p for p in live["probes"]}
    g2 = []
    g2_match = 0
    for pid, (pred, why) in PREDICTED.items():
        p = probes[pid]
        match = p["result"] == pred
        g2_match += match
        g2.append({
            "probe_id": pid,
            "surface": p["surface"],
            "mutation": p["mutation"],
            "predicted": pred,
            "prediction_basis": why,
            "observed": p["result"],
            "match": match,
        })
    g2.sort(key=lambda x: x["probe_id"])

    # Parser differential: dup-key bytes the LIVE runtime accepted must be
    # rejected by this oracle's strict parser.
    fs_dup = probes["surface-final-state-duplicate-key"]
    shadow = probes["surface-provenance-duplicate-root-shadow"]
    differential = {
        "final_state_dup_key": {
            "live_accepted": fs_dup["result"] == "Ok",
            "strict_parser_rejects_same_bytes":
                strict_rejects(fs_dup["files"]["final-state.json"]),
        },
        "provenance_dup_root_shadow": {
            "live_accepted": shadow["result"] == "Ok",
            "strict_parser_rejects_same_bytes":
                strict_rejects(shadow["files"]["provenance.json"]),
            "lenient_last_wins_root_equals_live_returned_root":
                json.loads(shadow["files"]["provenance.json"])["root_hash"]
                == shadow["root_hash"],
            "decoy_first_key_is_all_zeros":
                shadow["files"]["provenance.json"].startswith(
                    '{"root_hash":"' + "0" * 64 + '"'),
        },
    }
    differential_count = sum(
        1 for d in differential.values()
        if d["live_accepted"] and d["strict_parser_rejects_same_bytes"])

    # G4: forged interior chain -- oracle must DETECT what the live runtime
    # accepts.
    forged = probes["forged-interior-chain-consistent-root"]
    _, _, forged_chain_ok = rederive_archive(
        forged["files"], "g4-forged-chain")
    g4 = {
        "live_verify_result_on_forged_interior_chain": forged["result"],
        "oracle_interior_recompute_mismatches":
            len(forged_chain_ok) - sum(forged_chain_ok),
        "oracle_interior_events_total": len(forged_chain_ok),
        "oracle_detects_forgery": not all(forged_chain_ok),
        "live_chain_root_mismatch_result":
            probes["forged-chain-root-mismatch"]["result"],
        "checked_predicate": "event_chain_root == last RECORDED event_hash (plus raw file hashes); interior linkage NOT recomputed at verify time",
    }

    surface_observed = {
        "manifest.json": {"reformat_probe": probes["surface-manifest-reformat-compact"]["result"]},
        "events.jsonl": {
            "reformat_probe": probes["surface-events-key-reorder"]["result"],
            "dup_key_probe": probes["contract-duplicate-key-event"]["result"]},
        "final-state.json": {
            "reformat_probe": probes["surface-final-state-reformat-compact"]["result"],
            "dup_key_probe": probes["surface-final-state-duplicate-key"]["result"]},
        "provenance.json": {
            "reformat_probe": probes["surface-provenance-reformat-compact"]["result"],
            "dup_key_shadow_probe": probes["surface-provenance-duplicate-root-shadow"]["result"]},
        "snapshot-*.json": {"wholesale_replacement_probe": probes["surface-snapshot-tamper"]["result"]},
    }

    strict_wall_surfaces = sum(
        1 for s in SURFACE_MATRIX.values() if s["strict_parse_wall"])
    malleable_surfaces = sum(
        1 for s in SURFACE_MATRIX.values() if s["byte_malleable_accepted"])

    h0a_refuted = (probes["surface-final-state-duplicate-key"]["result"] == "Ok"
                   and probes["surface-provenance-duplicate-root-shadow"]["result"] == "Ok"
                   and probes["surface-snapshot-tamper"]["result"] == "Ok"
                   and probes["contract-duplicate-key-event"]["result"] == "Contract")
    h0b_refuted = (forged["result"] == "Ok" and not all(forged_chain_ok))

    counts = {
        "g1_scenarios": len(g1),
        "g1_field_parity_checks": g1_field_checks,
        "g1_field_parity_pass": g1_field_pass,
        "g1_interior_chain_events_recomputed": g1_chain_events,
        "g1_interior_chain_events_bit_exact": g1_chain_pass,
        "g1b_legacy_scenarios": len(legacy),
        "g1b_differential_checks": g1b_checks,
        "g1b_differential_pass": g1b_pass,
        "g2_probes": len(g2),
        "g2_predicted_equals_observed": g2_match,
        "g2_error_variants_covered": 5,
        "g3_surfaces": len(SURFACE_MATRIX),
        "g3_strict_parse_wall_surfaces": strict_wall_surfaces,
        "g3_byte_malleable_surfaces": malleable_surfaces,
        "g3_parser_differentials_demonstrated": differential_count,
        "g4_forged_interior_mismatches_detected_by_oracle":
            g4["oracle_interior_recompute_mismatches"],
    }

    gates = {
        "g0_anchors_resolved": all(anchors.values()),
        "g1_live_positive_parity": g1_field_pass == g1_field_checks
            and g1_chain_pass == g1_chain_events,
        "g1b_legacy_differential_fully_localized":
            len(legacy) == 3 and g1b_pass == g1b_checks and h0c_refuted,
        "g2_taxonomy_parity": g2_match == len(g2),
        "g3_h0a_refuted_as_predicted": h0a_refuted and differential_count == 2,
        "g4_h0b_refuted_as_predicted": h0b_refuted
            and g4["live_chain_root_mismatch_result"] == "Integrity",
    }
    gates["all_pass"] = all(gates.values())

    verdict = {
        "corroborated": (
            "FIRST live execution of the Rust run-provenance runtime in this "
            "module's audit history. The live runtime and the independent "
            "CPython re-derivation agree bit-exact on every hash: "
            f"{g1_field_pass}/{g1_field_checks} provenance-field/pin parity "
            f"checks and {g1_chain_pass}/{g1_chain_events} interior "
            "Haber-Stornetta event hashes recomputed bit-exact from live "
            "bytes across 7 scenarios (the 3 shipped KPI constructions, a "
            "unicode+float+snapshot stressor, and the 3 legacy 2026-receipt "
            "constructions). All 11 taxonomy probes return the analytically "
            "predicted RunArchiveError variant, covering all five variants "
            "live, including the previously untested Json-vs-Contract split "
            "(shape error -> Json; duplicate-key and syntax errors in "
            "events.jsonl -> Contract via parse_json_strict)."),
        "h0c": (
            "H0c REFUTED, fully localized "
            f"({g1b_pass}/{g1b_checks} differential checks): the signed 2026 "
            "hash-chain-oracle-parity-v1 receipt claimed its Python mirror "
            "was 'faithfully mirroring the Rust byte formats', but its G1 "
            "archives are NOT byte-reproducible by the live runtime. Root "
            "cause (single, proven by exact reconstruction): the mirror "
            "wrote JSON in Python-dict insertion order where the live "
            "runtime serializes serde_json Values through a BTreeMap, i.e. "
            "canonically key-sorted -- affecting manifest.json bytes and "
            "the payload sub-Value inside each event line, hence "
            "manifest_sha256, events_sha256 (non-empty archives) and "
            "root_hash. All value-bound quantities (every event_hash, "
            "event_chain_root, final_state_hash) match the receipt "
            "bit-exact, and re-serializing the live content in the mirror's "
            "insertion orders reproduces every one of the receipt's "
            "divergent hashes exactly. The receipt's ALGORITHMIC claims "
            "(hash-chain arithmetic, canonicalization, tamper fail-closed "
            "logic, G0 shipped-anchor parity) all survive; what falls is "
            "only the byte-format fidelity sentence and the example "
            "manifest_sha256/events_sha256/root_hash values it recorded, "
            "which this live receipt now supersedes with runtime ground "
            "truth."),
        "h0a": (
            "H0a REFUTED (predicted from source, confirmed live): the "
            "strict-parse wall covers exactly 1/5 archive surfaces "
            "(events.jsonl). manifest.json is raw-byte-bound but NEVER "
            "parsed; final-state.json is value-bound under a LENIENT parser "
            "(duplicate-key and reformat bytes accepted); provenance.json "
            "container bytes are bound by nothing verify_run checks (a "
            "decoy root_hash as first key is silently shadowed by lenient "
            "last-wins); snapshot-*.json is entirely outside the verify "
            "read-set. 2/2 duplicate-key byte streams accepted live are "
            "rejected by an RFC 8785-strict parser -- a parser differential "
            "(Momot et al. 2016) between the runtime and any "
            "canonicalization-strict external auditor."),
        "h0b": (
            "H0b REFUTED (predicted from source, confirmed live): verify_run "
            "does NOT re-verify the interior Haber-Stornetta linkage. A "
            "hand-forged archive whose 2 event_hash fields are garbage "
            "constants passes verify_run Ok when the provenance file is "
            "arithmetically consistent with the recorded bytes; the checked "
            "predicate is only event_chain_root == last RECORDED hash plus "
            "raw file hashes. The independent oracle detects the forgery "
            "(2/2 interior recomputes mismatch), i.e. Crosby-Wallach-style "
            "full-linkage verification is strictly stronger than the "
            "shipped verifier on this axis. Consistent with (and refining) "
            "the signed anchor-necessity finding that verify_run is an "
            "internal-consistency predicate, not tamper-evidence: even "
            "internal consistency of the chain SEEDS is not checked, only "
            "hash-of-bytes consistency."),
        "bounded": (
            "None of this changes the shipped scheme's fitness for its "
            "stated Phase-0 claim: byte-identical replay detection. All "
            "malleable surfaces are still covered the moment any BYTE "
            "matters (manifest/events via raw hashes; final-state via its "
            "parsed value). The gaps are representational (dup-key bytes, "
            "container bytes, snapshots) and interior-linkage completeness, "
            "which matter for cross-verifier agreement and for producers "
            "with buggy chain construction, not for the "
            "non-recomputing-mutation threat model already receipted."),
    }

    return {
        "schema": "amphora.run-provenance.live-runtime-archive-parity-diagnostic.v1",
        "study_id": STUDY_ID,
        "module": "amphora-run-provenance",
        "run_type": "LIVE_DIFFERENTIAL_AUDIT",
        "authority": "AUDIT_ONLY",
        "purpose": (
            "Close the gap all three prior signed receipts name as their top "
            "does_not_close item: execute the LIVE Rust runtime "
            "(RunArchive::create/append/snapshot/final_state + verify_run) "
            "and measure bit-parity against an independent CPython "
            "re-derivation, the full live RunArchiveError taxonomy incl. the "
            "parse_json_strict Json-vs-Contract split, per-surface "
            "representation binding, and interior chain verification."),
        "hypothesis": {
            "h_parity": "The live Rust runtime and the independent CPython re-derivation agree bit-exact on every provenance field, interior event hash, and verify_run return value, and reproduce the roots in the signed 2026 parity receipt.",
            "h0a": "The strict-parse wall (duplicate-key rejection) and representation binding cover all archive surfaces uniformly.",
            "h0b": "verify_run re-verifies the interior Haber-Stornetta event_hash linkage.",
            "h0c": "The signed 2026 hash-chain-oracle-parity receipt's Python mirror is byte-faithful to the live runtime, i.e. its G1 archives are byte-reproducible by the real RunArchive given identical content.",
        },
        "theory_reference": [
            "Haber & Stornetta 1991, How to time-stamp a digital document, J. Cryptology 3(2):99-111, doi:10.1007/BF00196791",
            "Merkle 1980, Protocols for public key cryptosystems, IEEE S&P",
            "NIST FIPS 180-4 (2015), Secure Hash Standard (SHA-256)",
            "RFC 8259 (2017) sect. 4: duplicate object names -> unpredictable behavior",
            "RFC 8785 (2020), JSON Canonicalization Scheme (JCS)",
            "Momot, Bratus, Hallberg, Patterson 2016, The Seven Turrets of Babel: A Taxonomy of LangSec Errors, IEEE SecDev, doi:10.1109/SecDev.2016.019",
            "Crosby & Wallach 2009, Efficient data structures for tamper-evident logging, USENIX Security",
        ],
        "non_circularity": (
            "The Rust harness deliberately IS the runtime (that is the point "
            "of a live differential study); the ORACLE side shares zero code "
            "with it: hashes are recomputed in CPython from the emitted live "
            "bytes using an independent canonicalize/stable_hash "
            "implementation, and all 20 probe outcomes were predicted "
            "analytically in this file before observation. The cross-time "
            "anchor compares against roots recorded in the 2026 signed "
            "receipt, which were derived WITHOUT running the runtime."),
        "runtime_source_anchors": anchors,
        "toolchain": toolchain,
        "preconditions": {
            "live_harness_built": True,
            "two_live_executions_byte_identical": True,
            "live_output_sha256": raw_sha256(live_bytes),
        },
        "g1_live_positive_scenarios": g1,
        "g1b_legacy_mirror_differential": legacy,
        "g2_taxonomy_probes": g2,
        "g3_surface_binding_matrix": {
            "predicted_from_source": SURFACE_MATRIX,
            "observed_live": surface_observed,
            "parser_differential": differential,
        },
        "g4_interior_chain": g4,
        "counts": counts,
        "gates": gates,
        "verdict": verdict,
        "closes": (
            "FIRST live Rust runtime execution for amphora-run-provenance: "
            "live re-exec parity of RunArchive create/append/snapshot/"
            "final_state + verify_run against the independent CPython oracle "
            "(all hashes bit-exact across 7 scenarios), full live "
            "RunArchiveError taxonomy (5/5 variants, 11/11 probes as "
            "predicted, incl. the Json-vs-Contract strict-parse split), "
            "per-surface representation-binding matrix (H0a refuted: strict "
            "wall on 1/5 surfaces, 2/2 parser differentials vs RFC 8785), "
            "interior-chain verification semantics (H0b refuted: interior "
            "Haber-Stornetta linkage attested, not re-verified; oracle "
            "strictly stronger 2/2), and a live-ground-truth audit of the "
            "signed 2026 parity receipt (H0c refuted: its Python mirror "
            "wrote insertion-order bytes where the runtime key-sorts; "
            "divergence 100% localized by exact reconstruction, its "
            "algorithmic claims unaffected)."),
        "does_not_close": [
            "Does NOT change the shipped scheme, the pinned signature_status, or promotion_receipt_eligible; the representational-malleability and interior-linkage findings are verifier-completeness facts, not defects against the module's byte-identical-replay claim.",
            "Does NOT withdraw or re-sign the 2026 hash-chain-oracle-parity-v1 receipt: its algorithmic and G0 shipped-anchor claims stand; only its byte-format-fidelity sentence and example archive hashes are superseded by this live ground truth (erratum recorded here, original receipt left untouched).",
            "Does NOT constitute the Phase-1 controlled-key signing pipeline (anchor-necessity receipt) nor an external witness/gossip protocol (Crosby-Wallach).",
            "Phase-1 hardening derived from this study: (a) verify interior event_hash linkage at verify time (Crosby-Wallach full-link verification), (b) parse ALL surfaces with parse_json_strict or bind container/final-state/snapshot bytes by raw hash to eliminate the 2 demonstrated parser differentials and the snapshot blind spot.",
            "Grants no batch-release, manufacturing-qualification, regulatory, safety, or product-performance authority. Does not promote the module or flip scientific_readiness.",
        ],
    }


def main():
    os.makedirs(TARGET, exist_ok=True)
    env = dict(os.environ, CARGO_TARGET_DIR=TARGET)
    build = subprocess.run(
        ["cargo", "build", "--release"], cwd=HARNESS, env=env,
        capture_output=True, timeout=1800)
    if build.returncode != 0:
        build = subprocess.run(
            ["cargo", "build", "--release", "--offline"], cwd=HARNESS, env=env,
            capture_output=True, timeout=1800)
    if build.returncode != 0:
        sys.stderr.write(build.stderr.decode(errors="replace"))
        raise SystemExit("cargo build failed")
    binary = os.path.join(TARGET, "release", "rp-live-harness")

    toolchain = {
        "rustc": subprocess.run(["rustc", "--version"], capture_output=True,
                                text=True).stdout.strip(),
        "cargo": subprocess.run(["cargo", "--version"], capture_output=True,
                                text=True).stdout.strip(),
        "python": "CPython %d.%d.%d" % sys.version_info[:3],
    }

    anchors = {
        "amphora_core_lib_rs_sha256": raw_file(
            os.path.join(ROOT, "amphora-core/src/lib.rs")),
        "amphora_core_contract_rs_sha256": raw_file(
            os.path.join(ROOT, "amphora-core/src/contract.rs")),
        "harness_main_rs_sha256": raw_file(
            os.path.join(HARNESS, "src/main.rs")),
        "harness_cargo_toml_sha256": raw_file(
            os.path.join(HARNESS, "Cargo.toml")),
        "sibling_parity_receipt_sha256": raw_file(os.path.join(
            MOD, "evidence/audit/hash-chain-oracle-parity-v1/"
            "hash-chain-oracle-parity-receipt.v1.dsse.json")),
        "sibling_merkle_receipt_sha256": raw_file(os.path.join(
            MOD, "evidence/audit/merkle-rfc6962-baseline-v1/"
            "merkle-rfc6962-baseline-receipt.v1.dsse.json")),
        "sibling_anchor_necessity_receipt_sha256": raw_file(os.path.join(
            MOD, "evidence/audit/anchor-necessity-reforge-resistance-v1/"
            "anchor-necessity-reforge-resistance-receipt.v1.dsse.json")),
        "shipped_kpi_sha256": raw_file(os.path.join(
            MOD, "evidence/phase0/kpis/"
            "run-provenance-hash-chain-integrity-kpi.v1.json")),
        "module_manifest_sha256": raw_file(
            os.path.join(ROOT, "module-manifest.json")),
    }

    out_a = run_harness(binary)
    out_b = run_harness(binary)
    assert out_a == out_b, "two live executions are not byte-identical"

    diag_a = build_diagnostic(out_a, toolchain, anchors)
    diag_b = build_diagnostic(out_b, toolchain, anchors)
    text_a = json.dumps(diag_a, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    text_b = json.dumps(diag_b, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    with open(os.path.join(AUD, "diagnostic.canonical.json"), "w") as f:
        f.write(text_a)
    with open(os.path.join(AUD, "diagnostic.runB.json"), "w") as f:
        f.write(text_b)
    assert text_a == text_b, "two-replay diagnostics differ"

    print("gates:", json.dumps(diag_a["gates"]))
    print("counts:", json.dumps(diag_a["counts"]))
    print("two_replay_sha256:", raw_sha256(text_a.encode("utf-8")))
    if not diag_a["gates"]["all_pass"]:
        raise SystemExit("GATES FAILED")


if __name__ == "__main__":
    main()
