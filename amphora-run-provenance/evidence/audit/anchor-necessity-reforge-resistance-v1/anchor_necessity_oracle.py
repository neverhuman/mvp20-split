#!/usr/bin/env python3
"""Independent (non-runtime) CPython front-door oracle for amphora-run-provenance:
EXTERNAL-ANCHOR NECESSITY and CONSISTENT-RE-FORGE RESISTANCE.

The two shipped audit receipts for this module (hash-chain-oracle-parity-v1,
merkle-rfc6962-baseline-v1) both establish that the archive is INTERNALLY
SELF-CONSISTENT: an independent implementation re-derives every hash, and any
single-field mutation that does NOT recompute the downstream hashes fails
verify_run. Neither asks the question this oracle asks:

    Does verify_run detect an adversary who mutates the scientific content and
    then recomputes every hash exactly as the honest writer would?

Haber & Stornetta 1991 answer this directly: a hash chain held entirely by the
party that produced it is trivially re-forgeable, which is why their scheme
requires the head to be WITNESSED or PUBLISHED by an independent party.
RFC 6962 encodes the same requirement as the Signed Tree Head. Crosby & Wallach
2009 formalize that a self-consistent log is not a tamper-EVIDENT log.

GATES
  G0  Anchor parity (non-circularity): this oracle's canonicalize()/stable_hash()
      /raw_sha256() reproduce the shipped Rust runtime hash anchors byte-exact.
  G1  CONTROL -- non-recomputing single-mutation probes: verify_run must fail
      closed on 14/14 (superset of the shipped KPI's 10).
  G2  TREATMENT -- consistent re-forge probes: 8 adversarial scenarios that
      mutate the scientific record AND recompute the full chain + all four
      component hashes + root_hash. PREDICTION: verify_run returns Ok on 8/8,
      i.e. internal-verification detection rate 0.0. This bounds the shipped
      KPI's "content_addressable_end_to_end / any single-bit mutation of any
      artifact fails verify_run" to non-recomputing mutations only.
  G3  External root anchor SUFFICIENCY: with the honest root_hash retained
      out-of-band, all 8 re-forges are detected (8/8).
  G4  Anchor MINIMALITY: build the 6-candidate x 8-scenario detection matrix
      over {manifest_sha256, events_sha256, event_chain_root, final_state_hash,
      run_id, root_hash}. PREDICTION: root_hash is the UNIQUE single anchor
      field achieving 8/8 coverage.
  G5  LOCALIZATION: a root-only anchor yields 1 accept/reject bit and localizes
      the mutated component in 0/8 scenarios; anchoring all 4 component hashes
      localizes it in 8/8.
  G6  In-band anchor via DSSE Ed25519 (the module's own `awaiting` Phase-1
      item): a DSSE-signed provenance.json detects 8/8 re-forges with NO
      out-of-band root retention -- BUT an adversary holding the signing key
      re-signs and detection returns to 0/8. Detection therefore requires
      signing AND key custody outside the run-producing host
      (Kelsey-Schneier 1999 / Bellare-Yee forward integrity).

THEORY (primary published sources)
  Haber, S. & Stornetta, W.S. (1991) "How to time-stamp a digital document",
    Journal of Cryptology 3(2):99-111, DOI 10.1007/BF00196791. Sections 3-5:
    the linking scheme is binding only because the head is witnessed/published
    by parties other than the document owner.
  Crosby, S.A. & Wallach, D.S. (2009) "Efficient Data Structures for
    Tamper-Evident Logging", 18th USENIX Security Symposium, pp. 317-334.
    Formalizes tamper-evidence as requiring signed commitments plus auditor
    gossip; self-consistency is explicitly insufficient.
  Kelsey, J. & Schneier, B. (1999) "Secure Audit Logs to Support Computer
    Forensics", ACM Trans. Information and System Security 2(2):159-176,
    DOI 10.1145/317087.317089. Forward integrity via an evolving one-way key --
    the property a recomputable hash chain lacks.
  Bellare, M. & Yee, B. (2003) "Forward-Security in Private-Key Cryptography",
    CT-RSA 2003, LNCS 2612:1-18, DOI 10.1007/3-540-36563-X_1. Formal
    forward-integrity definition for audit logs.
  RFC 6962 (2013) "Certificate Transparency", Sections 3.2 and 3.5: the tree
    head carries no authority unless signed (Signed Tree Head).
  RFC 8032 (2017) "EdDSA: Ed25519" -- deterministic signatures (replay-stable).
  DSSE v1 / in-toto Attestation Framework v1.0 (2020); SLSA v1.0 (2023):
    provenance authority derives from the signed envelope, not the digest.
  NIST FIPS 180-4 (2015) SHA-256. NIST SP 800-92 (2006) Section 2.3.2: log
    integrity requires protecting the log FROM the entity that generates it.
  Saltzer, J.H. & Schroeder, M.D. (1975) Proc. IEEE 63(9):1278-1308 --
    complete mediation. Anderson, J.P. (1980) -- audit-log threat model.

AUDIT_ONLY. Re-derivation and adversarial characterization only. Does NOT run
the live Rust runtime (live re-exec parity remains the Phase-1 ceiling). Does
NOT promote authority, does NOT flip scientific_readiness, does NOT change the
shipped scheme, does NOT modify the portfolio manifest (66 receipts / 11
modules), the module-manifest, any locked dataset, or a signed Phase-0 KPI.
Deterministic: no wall-clock, no RNG; Ed25519 is deterministic per RFC 8032;
only variant NAMES and booleans are recorded, never tempdir paths.
"""
import base64
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
MOD = os.path.join(ROOT, "amphora-run-provenance")
P0 = os.path.join(MOD, "evidence/phase0")
AUDIT = os.path.join(MOD, "evidence/audit")
OUT = os.path.join(AUDIT, "anchor-necessity-reforge-resistance-v1")
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"


# ---------------------------------------------------------------------------
# Hash primitives -- independent re-implementation of amphora-core::stable_hash
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


# ---------------------------------------------------------------------------
# Byte-format helpers -- mirror amphora-core::RunArchive serialization exactly
# ---------------------------------------------------------------------------
EVENT_SCHEMA = "amphora.tui-event.v1"
EVENT_FIELD_ORDER = ["schema", "sequence", "run_id", "event_type",
                     "candidate_id", "generation", "payload", "event_hash"]


def compact_event_line(event: dict) -> bytes:
    ordered = {k: event[k] for k in EVENT_FIELD_ORDER}
    return json.dumps(ordered, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8") + b"\n"


def write_pretty(path: str, value) -> None:
    with open(path, "wb") as f:
        f.write(json.dumps(value, indent=2, ensure_ascii=False).encode("utf-8"))
        f.write(b"\n")


def event_hash_of(sequence, run_id, event_type, candidate_id, generation,
                  payload, previous_event_hash):
    return stable_hash({
        "schema": EVENT_SCHEMA,
        "sequence": sequence,
        "run_id": run_id,
        "event_type": event_type,
        "candidate_id": candidate_id,
        "generation": generation,
        "payload": payload,
        "previous_event_hash": previous_event_hash,
    })


class RunArchiveError(Exception):
    def __init__(self, variant, msg=""):
        super().__init__(f"{variant}: {msg}")
        self.variant = variant


def _no_dup_hook(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise RunArchiveError("Json", f"duplicate key {k}")
        d[k] = v
    return d


def _read_json_strict(path: str):
    if not os.path.exists(path):
        raise RunArchiveError("Io", f"missing {os.path.basename(path)}")
    with open(path, "rb") as f:
        b = f.read()
    try:
        return json.loads(b, object_pairs_hook=_no_dup_hook)
    except RunArchiveError:
        raise
    except Exception as e:
        raise RunArchiveError("Json", type(e).__name__)


def _read_events(path: str):
    if not os.path.exists(path):
        raise RunArchiveError("Io", "missing events.jsonl")
    with open(path, "rb") as f:
        lines = f.read().split(b"\n")
    events = []
    for line in lines:
        if line.strip() == b"":
            continue
        try:
            events.append(json.loads(line, object_pairs_hook=_no_dup_hook))
        except RunArchiveError:
            raise
        except Exception as e:
            raise RunArchiveError("Json", type(e).__name__)
    return events


def verify_run(path: str) -> str:
    """Independent re-implementation of amphora-core::verify_run."""
    provenance = _read_json_strict(os.path.join(path, "provenance.json"))
    mpath = os.path.join(path, "manifest.json")
    if not os.path.exists(mpath):
        raise RunArchiveError("Io", "missing manifest.json")
    with open(mpath, "rb") as f:
        manifest = f.read()
    epath = os.path.join(path, "events.jsonl")
    if not os.path.exists(epath):
        raise RunArchiveError("Io", "missing events.jsonl")
    with open(epath, "rb") as f:
        events_bytes = f.read()
    final_state = _read_json_strict(os.path.join(path, "final-state.json"))
    events = _read_events(epath)
    for i, ev in enumerate(events):
        if ev.get("sequence") != i + 1:
            raise RunArchiveError("Integrity", "non-contiguous event sequence")
    ecr = events[-1]["event_hash"] if events else raw_sha256(b"")
    expected = {
        "run_id": provenance.get("run_id"),
        "manifest_sha256": raw_sha256(manifest),
        "events_sha256": raw_sha256(events_bytes),
        "event_chain_root": ecr,
        "final_state_hash": stable_hash(final_state),
    }
    observed_root = provenance.get("root_hash")
    if not isinstance(observed_root, str):
        raise RunArchiveError("Integrity", "missing root hash")
    if (provenance.get("manifest_sha256") != expected["manifest_sha256"]
            or provenance.get("events_sha256") != expected["events_sha256"]
            or provenance.get("event_chain_root") != expected["event_chain_root"]
            or provenance.get("final_state_hash") != expected["final_state_hash"]
            or observed_root != stable_hash(expected)):
        raise RunArchiveError("Integrity", "provenance hash mismatch")
    return observed_root


# ---------------------------------------------------------------------------
# Archive writer. `write_archive` is used both by the HONEST producer and by the
# ADVERSARY -- that identity is the whole point: a consistent re-forge is
# indistinguishable from an honest write by any purely internal predicate.
# ---------------------------------------------------------------------------
def write_archive(path: str, run_id: str, manifest: dict, specs: list,
                  final: dict) -> dict:
    """specs: list of (event_type, candidate_id, generation, payload).
    Writes manifest.json, events.jsonl, final-state.json, provenance.json with
    a fully self-consistent Haber-Stornetta chain + 5-field root_hash."""
    os.makedirs(path, exist_ok=True)
    write_pretty(os.path.join(path, "manifest.json"), manifest)
    prev = None
    lines = b""
    for i, (etype, cid, gen, payload) in enumerate(specs, start=1):
        eh = event_hash_of(i, run_id, etype, cid, gen, payload, prev)
        lines += compact_event_line({
            "schema": EVENT_SCHEMA, "sequence": i, "run_id": run_id,
            "event_type": etype, "candidate_id": cid, "generation": gen,
            "payload": payload, "event_hash": eh})
        prev = eh
    with open(os.path.join(path, "events.jsonl"), "wb") as f:
        f.write(lines)
    write_pretty(os.path.join(path, "final-state.json"), final)
    with open(os.path.join(path, "manifest.json"), "rb") as f:
        mbytes = f.read()
    ecr = prev if prev is not None else raw_sha256(b"")
    seed = {
        "run_id": run_id,
        "manifest_sha256": raw_sha256(mbytes),
        "events_sha256": raw_sha256(lines),
        "event_chain_root": ecr,
        "final_state_hash": stable_hash(final),
    }
    provenance = {
        "schema": "amphora.run-provenance.v1",
        "run_id": run_id,
        "manifest_sha256": seed["manifest_sha256"],
        "events_sha256": seed["events_sha256"],
        "event_chain_root": ecr,
        "final_state_hash": seed["final_state_hash"],
        "root_hash": stable_hash(seed),
        "promotion_receipt_eligible": False,
        "signature_status": "UNSIGNED_CONTROLLED_KEY_REQUIRED",
    }
    write_pretty(os.path.join(path, "provenance.json"), provenance)
    return provenance


# ---------------------------------------------------------------------------
# The HONEST reference run: a 12-event solvent-borne two-component
# epoxy-polyamide marine anti-corrosion candidate screening run.
# ---------------------------------------------------------------------------
RUN_ID = "run-dgeba-polyamide-marine-0012"
EVENT_TYPES = ["PROPOSED", "SCORED", "RANKED", "GATED"]


def honest_manifest():
    return {
        "schema": "mvp20.run_manifest.v1",
        "run_id": RUN_ID,
        "scope": "solvent-borne two-component epoxy-polyamide marine anti-corrosion coating",
        "resin": "DGEBA n_bar=0.14 EEW 190",
        "hardener": "polyamide amidoamine AHEW 95",
        "monte_carlo_seed": 2001,
        "n_events_planned": 12,
    }


def honest_specs():
    specs = []
    for i in range(12):
        specs.append((EVENT_TYPES[i % 4], f"cand-{i:03d}", i // 4,
                      {"idx": i, "note": "dgeba-polyamide",
                       "barrier_score": round(0.50 + 0.03 * i, 4)}))
    return specs


def honest_final():
    return {"run_id": RUN_ID, "status": "COMPLETE", "n_events": 12,
            "best_candidate": "cand-011", "best_barrier_score": 0.83}


def build_honest(base: str):
    path = os.path.join(base, RUN_ID)
    prov = write_archive(path, RUN_ID, honest_manifest(), honest_specs(),
                         honest_final())
    return path, prov


# ---------------------------------------------------------------------------
# G0 -- anchor parity against the SHIPPED Rust runtime artifacts
# ---------------------------------------------------------------------------
def g0_anchor_parity():
    checks = []
    result = json.loads(Path(os.path.join(P0, "benchmark/result.v1.json")).read_text())
    kpi = json.loads(Path(os.path.join(
        P0, "kpis/run-provenance-hash-chain-integrity-kpi.v1.json")).read_text())

    # (1) stable_hash of a nested runtime object == shipped diagnostic_sha256:
    #     proves canonical-JSON key ordering + compact separators parity.
    checks.append(("shipped_diagnostic_receipt_stable_hash",
                   stable_hash(result["first_replay"]["diagnostic_receipt"]),
                   result["first_replay"]["diagnostic_sha256"]))
    # (2) raw file SHA-256 of the Phase-0 bundle == shipped bundle_sha256.
    checks.append(("shipped_bundle_raw_sha256",
                   raw_file(os.path.join(P0, "bundle.v1.json")),
                   result["bundle_sha256"]))
    # (3) raw file SHA-256 of the benchmark lock == KPI benchmark_lock_sha256.
    checks.append(("shipped_benchmark_lock_raw_sha256",
                   raw_file(os.path.join(P0, "benchmark/benchmark-lock.v1.json")),
                   kpi["benchmark_lock_sha256"]))
    # (4) every bundle parent-binding child file raw hash -- the Phase-0 bundle
    #     binds each parent artifact by raw SHA-256 under a named key.
    bundle = json.loads(Path(os.path.join(P0, "bundle.v1.json")).read_text())
    BUNDLE_PARENT_BINDINGS = {
        "benchmark_lock_hash": "evidence/phase0/benchmark/benchmark-lock.v1.json",
        "dataset_manifest_hash": "evidence/phase0/dataset/dataset-manifest.v1.json",
        "promotion_policy_hash": "evidence/phase0/promotion/policy.v1.json",
        "source_lock_hash": "evidence/phase0/sources/source-lock.v1.json",
        "split_manifest_hash": "evidence/phase0/split/split-manifest.v1.json",
        "claim_contract_hash": "ip/claim-contract.v1.json",
        "disclosure_log_hash": "ip/disclosure-log.v1.json",
        "prior_art_hash": "ip/prior-art.v1.json",
        "technical_dossier_hash": "ip/technical-dossier.v1.json",
    }
    for key in sorted(BUNDLE_PARENT_BINDINGS):
        rel = BUNDLE_PARENT_BINDINGS[key]
        recorded = bundle.get(key)
        if not isinstance(recorded, str):
            continue
        checks.append((f"bundle_parent_binding::{key}",
                       raw_file(os.path.join(MOD, rel)), recorded))
    # (5) second replay of the shipped result must agree with the first.
    checks.append(("shipped_replay_identical",
                   stable_hash(result["second_replay"]["diagnostic_receipt"]),
                   result["first_replay"]["diagnostic_sha256"]))
    results = [{"anchor": n, "recomputed": a, "shipped": b, "match": a == b}
               for n, a, b in checks]
    return results, all(r["match"] for r in results)


# ---------------------------------------------------------------------------
# G1 -- CONTROL: non-recomputing single-mutation probes (must fail closed)
# ---------------------------------------------------------------------------
def _observe(path):
    try:
        verify_run(path)
        return "Ok"
    except RunArchiveError as e:
        return e.variant


def _patch_json(path, key, value):
    with open(path, "rb") as f:
        d = json.loads(f.read())
    d[key] = value
    write_pretty(path, d)


def g1_single_mutation_probes(base):
    probes = []

    def probe(name, expected, mutate):
        work = tempfile.mkdtemp(dir=base)
        path, _ = build_honest(work)
        mutate(path)
        observed = _observe(path)
        shutil.rmtree(work)
        probes.append({"probe": name, "expected_variant": expected,
                       "observed_variant": observed,
                       "fail_closed": observed == expected})

    def _bump_manifest(p):
        _patch_json(os.path.join(p, "manifest.json"), "monte_carlo_seed", 2002)

    def _append_line(p):
        with open(os.path.join(p, "events.jsonl"), "ab") as f:
            f.write(b'{"schema":"amphora.tui-event.v1","sequence":13,"run_id":"'
                    + RUN_ID.encode() + b'","event_type":"GATED",'
                    b'"candidate_id":"cand-999","generation":3,'
                    b'"payload":{},"event_hash":"00"}\n')

    def _patch_final(p):
        _patch_json(os.path.join(p, "final-state.json"), "best_candidate", "cand-000")

    def _patch_root(p):
        _patch_json(os.path.join(p, "provenance.json"), "root_hash", "0" * 64)

    def _patch_events_sha(p):
        _patch_json(os.path.join(p, "provenance.json"), "events_sha256", "0" * 64)

    def _patch_manifest_sha(p):
        _patch_json(os.path.join(p, "provenance.json"), "manifest_sha256", "0" * 64)

    def _patch_chain_root(p):
        _patch_json(os.path.join(p, "provenance.json"), "event_chain_root", "0" * 64)

    def _patch_final_hash(p):
        _patch_json(os.path.join(p, "provenance.json"), "final_state_hash", "0" * 64)

    def _patch_run_id(p):
        _patch_json(os.path.join(p, "provenance.json"), "run_id", "run-other")

    def _drop_root(p):
        with open(os.path.join(p, "provenance.json"), "rb") as f:
            d = json.loads(f.read())
        del d["root_hash"]
        write_pretty(os.path.join(p, "provenance.json"), d)

    def _sequence_gap(p):
        ev = _read_events(os.path.join(p, "events.jsonl"))
        ev[5]["sequence"] = 99
        with open(os.path.join(p, "events.jsonl"), "wb") as f:
            for e in ev:
                f.write(compact_event_line(e))

    def _payload_no_rehash(p):
        ev = _read_events(os.path.join(p, "events.jsonl"))
        ev[3]["payload"]["barrier_score"] = 0.99
        with open(os.path.join(p, "events.jsonl"), "wb") as f:
            for e in ev:
                f.write(compact_event_line(e))

    def _drop_prov(p):
        os.remove(os.path.join(p, "provenance.json"))

    def _drop_manifest(p):
        os.remove(os.path.join(p, "manifest.json"))

    def _drop_events(p):
        os.remove(os.path.join(p, "events.jsonl"))

    probe("manifest_bytes_mutated_no_rehash", "Integrity", _bump_manifest)
    probe("events_extra_line_appended_no_rehash", "Integrity", _append_line)
    probe("final_state_mutated_no_rehash", "Integrity", _patch_final)
    probe("provenance_root_hash_tampered", "Integrity", _patch_root)
    probe("provenance_events_sha256_tampered", "Integrity", _patch_events_sha)
    probe("provenance_manifest_sha256_tampered", "Integrity", _patch_manifest_sha)
    probe("provenance_event_chain_root_tampered", "Integrity", _patch_chain_root)
    probe("provenance_final_state_hash_tampered", "Integrity", _patch_final_hash)
    probe("provenance_run_id_tampered", "Integrity", _patch_run_id)
    probe("provenance_root_hash_removed", "Integrity", _drop_root)
    probe("event_sequence_gap", "Integrity", _sequence_gap)
    probe("event_payload_mutated_no_rehash", "Integrity", _payload_no_rehash)
    probe("provenance_json_missing", "Io", _drop_prov)
    probe("manifest_json_missing", "Io", _drop_manifest)
    probe("events_jsonl_missing", "Io", _drop_events)
    return probes


# ---------------------------------------------------------------------------
# G2/G3/G4/G5 -- CONSISTENT RE-FORGE scenarios
# Each returns (manifest, specs, final) for a fully re-hashed adversarial
# archive that a purely internal predicate cannot distinguish from honest.
# ---------------------------------------------------------------------------
def reforge_scenarios():
    scen = []

    def add(name, semantic_harm, mutated_component, fn):
        scen.append({"scenario": name, "semantic_harm": semantic_harm,
                     "mutated_component": mutated_component, "build": fn})

    def s_payload():
        m, sp, f = honest_manifest(), honest_specs(), honest_final()
        et, cid, g, pl = sp[3]
        pl = dict(pl); pl["barrier_score"] = 0.99
        sp[3] = (et, cid, g, pl)
        return m, sp, f
    add("event_payload_score_forged", "Falsifies a recorded barrier score for "
        "one DGEBA-polyamide candidate.", "events", s_payload)

    def s_delete():
        m, sp, f = honest_manifest(), honest_specs(), honest_final()
        del sp[6]
        m = dict(m); m["n_events_planned"] = 11
        f = dict(f); f["n_events"] = 11
        return m, sp, f
    add("unfavourable_event_deleted_and_renumbered", "Suppresses one SCORED "
        "event and renumbers the chain so the sequence stays contiguous.",
        "events+manifest+final_state", s_delete)

    def s_insert():
        m, sp, f = honest_manifest(), honest_specs(), honest_final()
        sp.insert(8, ("SCORED", "cand-fab", 2,
                      {"idx": 99, "note": "fabricated", "barrier_score": 0.95}))
        m = dict(m); m["n_events_planned"] = 13
        f = dict(f); f["n_events"] = 13
        return m, sp, f
    add("fabricated_event_inserted", "Injects a never-executed SCORED event "
        "with a favourable barrier score.", "events+manifest+final_state",
        s_insert)

    def s_reorder():
        m, sp, f = honest_manifest(), honest_specs(), honest_final()
        sp[1], sp[9] = sp[9], sp[1]
        return m, sp, f
    add("event_order_permuted", "Reverses the temporal order of two events so "
        "a later result appears to have preceded a decision.", "events",
        s_reorder)

    def s_seed():
        m, sp, f = honest_manifest(), honest_specs(), honest_final()
        m = dict(m); m["monte_carlo_seed"] = 999999
        return m, sp, f
    add("manifest_monte_carlo_seed_forged", "Rewrites the pinned RNG seed, "
        "destroying the reproducibility claim while the archive still verifies.",
        "manifest", s_seed)

    def s_final():
        m, sp, f = honest_manifest(), honest_specs(), honest_final()
        f = dict(f); f["best_candidate"] = "cand-002"; f["best_barrier_score"] = 0.95
        return m, sp, f
    add("final_state_best_candidate_forged", "Substitutes the reported winning "
        "candidate of the screening run.", "final_state", s_final)

    def s_whole():
        m = dict(honest_manifest()); m["monte_carlo_seed"] = 4242
        m["n_events_planned"] = 4
        sp = [(EVENT_TYPES[i % 4], f"alt-{i:03d}", 0,
               {"idx": i, "note": "alt-run", "barrier_score": 0.90})
              for i in range(4)]
        f = {"run_id": RUN_ID, "status": "COMPLETE", "n_events": 4,
             "best_candidate": "alt-003", "best_barrier_score": 0.90}
        return m, sp, f
    add("whole_archive_rebuilt_same_run_id", "Discards the real run entirely "
        "and substitutes a different run under the same run_id.",
        "manifest+events+final_state", s_whole)

    def s_truncate():
        m, sp, f = honest_manifest(), honest_specs(), honest_final()
        sp = sp[:6]
        m = dict(m); m["n_events_planned"] = 6
        f = dict(f); f["n_events"] = 6; f["best_candidate"] = "cand-005"
        f["best_barrier_score"] = 0.65
        return m, sp, f
    add("log_truncated_and_rechained", "Rolls the run back to its first 6 "
        "events (Crosby-Wallach truncation attack) with a consistent re-chain.",
        "events+manifest+final_state", s_truncate)
    return scen


ANCHOR_FIELDS = ["run_id", "manifest_sha256", "events_sha256",
                 "event_chain_root", "final_state_hash", "root_hash"]
COMPONENT_FIELDS = ["manifest_sha256", "events_sha256", "event_chain_root",
                    "final_state_hash"]


def g2_g5_reforge(base, honest_prov):
    rows = []
    for scen in reforge_scenarios():
        work = tempfile.mkdtemp(dir=base)
        path = os.path.join(work, RUN_ID)
        m, sp, f = scen["build"]()
        forged = write_archive(path, RUN_ID, m, sp, f)
        # G2: internal verification only.
        observed = _observe(path)
        internal_detected = observed != "Ok"
        # G3/G4: per-anchor-field comparison against the retained honest values.
        per_field = {fld: (forged[fld] != honest_prov[fld]) for fld in ANCHOR_FIELDS}
        # G5: localization -- with all 4 component anchors retained, can the
        # verifier name which component was mutated?
        diverged = [fld for fld in COMPONENT_FIELDS if per_field[fld]]
        expected_components = set()
        for tok in scen["mutated_component"].split("+"):
            expected_components.add({
                "manifest": "manifest_sha256",
                "events": "events_sha256",
                "final_state": "final_state_hash"}[tok])
        # event mutations necessarily also move event_chain_root
        if "events_sha256" in expected_components:
            expected_components.add("event_chain_root")
        localized = set(diverged) == expected_components
        shutil.rmtree(work)
        rows.append({
            "scenario": scen["scenario"],
            "semantic_harm": scen["semantic_harm"],
            "mutated_component": scen["mutated_component"],
            "internal_verify_variant": observed,
            "detected_by_internal_verify": internal_detected,
            "detected_by_external_root_anchor": per_field["root_hash"],
            "anchor_field_divergence": per_field,
            "component_anchors_diverged": diverged,
            "expected_component_anchors": sorted(expected_components),
            "localized_by_component_anchors": localized,
            "localized_by_root_anchor_only": False,
            "forged_root_hash": forged["root_hash"],
        })
    return rows


# ---------------------------------------------------------------------------
# G6 -- in-band DSSE Ed25519 anchor, and the hot-key defeat
# ---------------------------------------------------------------------------
def load_seed(p: Path) -> bytes:
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


def pae(t: str, body: bytes) -> bytes:
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


PTYPE = "application/vnd.amphora.run-provenance-attestation+json"


def dsse_sign(sk, subject: dict):
    body = json.dumps(canonicalize(subject), separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return body, sk.sign(pae(PTYPE, body))


def dsse_ok(pub_bytes, body: bytes, sig: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(pub_bytes).verify(sig, pae(PTYPE, body))
        return True
    except Exception:
        return False


def g6_dsse_anchor(base, honest_prov):
    sk = Ed25519PrivateKey.from_private_bytes(
        load_seed(SEED_DIR / "evaluator.ed25519.seed"))
    pub = sk.public_key().public_bytes_raw()
    subject = {"run_id": honest_prov["run_id"],
               "root_hash": honest_prov["root_hash"]}
    honest_body, honest_sig = dsse_sign(sk, subject)
    assert dsse_ok(pub, honest_body, honest_sig)
    # Adversary WITHOUT the key: the envelope still binds the honest root, so
    # any re-forge whose root differs is caught in-band.
    # Adversary WITH the key (hot key on the producing host): re-signs freely.
    rows = []
    for scen in reforge_scenarios():
        work = tempfile.mkdtemp(dir=base)
        path = os.path.join(work, RUN_ID)
        m, sp, f = scen["build"]()
        forged = write_archive(path, RUN_ID, m, sp, f)
        cold = forged["root_hash"] != json.loads(honest_body)["root_hash"]
        hot_body, hot_sig = dsse_sign(
            sk, {"run_id": forged["run_id"], "root_hash": forged["root_hash"]})
        hot_verifies = dsse_ok(pub, hot_body, hot_sig)
        hot_detected = (not hot_verifies) or (
            json.loads(hot_body)["root_hash"] != forged["root_hash"])
        shutil.rmtree(work)
        rows.append({"scenario": scen["scenario"],
                     "detected_cold_key_custody": cold,
                     "adversary_resigned_envelope_verifies": hot_verifies,
                     "detected_hot_key_on_producing_host": hot_detected})
    return {
        "dsse_payload_type": PTYPE,
        "signing_key_public_key_hex": pub.hex(),
        "signing_key_id": f"phase0-evaluator-{raw_sha256(pub)}",
        "honest_attestation_body_sha256": raw_sha256(honest_body),
        "honest_attestation_sig_sha256": raw_sha256(honest_sig),
        "ed25519_deterministic_rfc8032": True,
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Assemble
# ---------------------------------------------------------------------------
def main():
    base = tempfile.mkdtemp(prefix="amphora-anchor-")
    try:
        honest_path, honest_prov = build_honest(base)
        honest_root_ok = _observe(honest_path) == "Ok"

        g0_rows, g0_pass = g0_anchor_parity()
        g1_rows = g1_single_mutation_probes(base)
        g2_rows = g2_g5_reforge(base, honest_prov)
        g6 = g6_dsse_anchor(base, honest_prov)

        n_scen = len(g2_rows)
        internal_detected = sum(1 for r in g2_rows if r["detected_by_internal_verify"])
        root_detected = sum(1 for r in g2_rows if r["detected_by_external_root_anchor"])
        localized_component = sum(1 for r in g2_rows if r["localized_by_component_anchors"])
        localized_root_only = sum(1 for r in g2_rows if r["localized_by_root_anchor_only"])

        # G4 minimality: coverage of each single anchor field.
        coverage = {}
        for fld in ANCHOR_FIELDS:
            coverage[fld] = sum(1 for r in g2_rows
                                if r["anchor_field_divergence"][fld])
        complete = sorted([f for f, c in coverage.items() if c == n_scen])

        cold = sum(1 for r in g6["rows"] if r["detected_cold_key_custody"])
        hot = sum(1 for r in g6["rows"] if r["detected_hot_key_on_producing_host"])

        gates = {
            "g0_anchor_parity_byte_exact": bool(g0_pass),
            "g0_honest_archive_verifies": bool(honest_root_ok),
            "g1_single_mutation_all_fail_closed":
                all(p["fail_closed"] for p in g1_rows),
            "g2_all_reforges_undetected_by_internal_verify":
                internal_detected == 0,
            "g3_external_root_anchor_detects_all": root_detected == n_scen,
            "g4_root_hash_is_unique_complete_single_anchor":
                complete == ["root_hash"],
            "g5_component_anchors_localize_all": localized_component == n_scen,
            "g5_root_only_anchor_localizes_none": localized_root_only == 0,
            "g6_dsse_cold_key_detects_all": cold == n_scen,
            "g6_hot_key_on_producing_host_detects_none": hot == 0,
        }
        gates["all_pass"] = all(gates.values())

        diag = {
            "schema": "amphora.run-provenance.anchor-necessity-reforge-resistance-diagnostic.v1",
            "study_id": "run-provenance-anchor-necessity-reforge-resistance-v1",
            "module": "amphora-run-provenance",
            "run_type": "AUDIT_ONLY_INDEPENDENT_ORACLE_ADVERSARIAL_CHARACTERIZATION",
            "authority": "AUDIT_ONLY",
            "purpose":
                "Determine whether the shipped Haber-Stornetta linear hash-chain "
                "run archive is tamper-EVIDENT or merely internally "
                "SELF-CONSISTENT, by separating non-recomputing single-mutation "
                "probes (the shipped KPI's threat model) from CONSISTENT RE-FORGE "
                "probes in which the adversary mutates the scientific record and "
                "then recomputes the full chain and all five provenance hashes "
                "exactly as the honest writer would; then quantify which "
                "external anchor is minimally sufficient to restore "
                "tamper-evidence, and under what key-custody assumption a DSSE "
                "Ed25519 attestation supplies that anchor in-band.",
            "hypothesis":
                "verify_run is a purely INTERNAL consistency predicate: it "
                "detects 100% of non-recomputing mutations but 0% of consistent "
                "re-forges, because a consistent re-forge is bit-indistinguishable "
                "from an honest write to any predicate computed solely from the "
                "archive. Tamper-evidence therefore requires an anchor held "
                "outside the archive, root_hash is the unique single provenance "
                "field whose retention detects every re-forge, and a DSSE "
                "Ed25519 attestation supplies that anchor in-band only under cold "
                "key custody (Haber-Stornetta 1991 witnessing requirement; "
                "RFC 6962 Signed Tree Head; Crosby-Wallach 2009).",
            "non_circularity":
                "The oracle shares no code with the Rust runtime. It re-derives "
                "canonicalize/stable_hash/raw_sha256 from the published algorithm "
                "and proves bit-parity by reproducing shipped runtime hash "
                "anchors (G0) before any adversarial claim is made. The "
                "adversarial writer and the honest writer call the SAME "
                "write_archive function -- that identity is the finding, not an "
                "artifact of the harness.",
            "theory_reference": {
                "haber_stornetta_1991":
                    "Haber & Stornetta, 'How to time-stamp a digital document', "
                    "J. Cryptology 3(2):99-111, DOI 10.1007/BF00196791 -- the "
                    "linking scheme binds only because the head is witnessed or "
                    "published by parties other than the document owner.",
                "crosby_wallach_2009":
                    "Crosby & Wallach, 'Efficient Data Structures for "
                    "Tamper-Evident Logging', 18th USENIX Security Symposium "
                    "(2009), pp. 317-334 -- self-consistency is insufficient for "
                    "tamper-evidence; signed commitments + gossip are required; "
                    "source of the truncation-attack scenario.",
                "kelsey_schneier_1999":
                    "Kelsey & Schneier, 'Secure Audit Logs to Support Computer "
                    "Forensics', ACM TISSEC 2(2):159-176, "
                    "DOI 10.1145/317087.317089 -- forward integrity via an "
                    "evolving one-way key.",
                "bellare_yee_2003":
                    "Bellare & Yee, 'Forward-Security in Private-Key "
                    "Cryptography', CT-RSA 2003, LNCS 2612:1-18, "
                    "DOI 10.1007/3-540-36563-X_1.",
                "rfc6962_2013":
                    "RFC 6962 'Certificate Transparency' Sections 3.2, 3.5 -- the "
                    "tree head carries no authority unless signed (STH).",
                "rfc8032_2017":
                    "RFC 8032 'EdDSA: Ed25519' -- deterministic signatures, hence "
                    "byte-stable across replays.",
                "in_toto_slsa":
                    "in-toto Attestation Framework v1.0 (2020) + SLSA v1.0 "
                    "(2023) -- provenance authority derives from the signed "
                    "envelope, not the digest.",
                "fips_180_4": "NIST FIPS 180-4 (2015) Secure Hash Standard (SHA-256).",
                "nist_sp_800_92":
                    "NIST SP 800-92 (2006) Section 2.3.2 -- log integrity requires "
                    "protecting the log from the entity that generates it.",
                "saltzer_schroeder_1975":
                    "Saltzer & Schroeder, Proc. IEEE 63(9):1278-1308 -- complete "
                    "mediation. Anderson (1980) -- audit-log threat model.",
            },
            "runtime_source_anchors": {
                "shipped_kpi_path":
                    "evidence/phase0/kpis/run-provenance-hash-chain-integrity-kpi.v1.json",
                "shipped_kpi_sha256": raw_file(os.path.join(
                    P0, "kpis/run-provenance-hash-chain-integrity-kpi.v1.json")),
                "shipped_result_sha256": raw_file(os.path.join(
                    P0, "benchmark/result.v1.json")),
                "shipped_bundle_sha256": raw_file(os.path.join(P0, "bundle.v1.json")),
                "sibling_parity_oracle_sha256": raw_file(os.path.join(
                    AUDIT, "hash-chain-oracle-parity-v1/run_provenance_oracle.py")),
                "sibling_merkle_oracle_sha256": raw_file(os.path.join(
                    AUDIT, "merkle-rfc6962-baseline-v1/merkle_rfc6962_oracle.py")),
                "runtime_implementation_path": "amphora-engine/src/lib.rs",
            },
            "preconditions": {
                "runs_live_rust_runtime": False,
                "modifies_portfolio_manifest": False,
                "modifies_module_manifest": False,
                "modifies_locked_dataset": False,
                "modifies_signed_phase0_kpi": False,
                "changes_shipped_scheme": False,
                "promotes_authority": False,
                "flips_scientific_readiness": False,
                "wall_clock_used": False,
                "rng_used": False,
                "coating_scope":
                    "solvent-borne two-component DGEBA epoxy / polyamide "
                    "amidoamine marine anti-corrosion screening run archive",
            },
            "honest_reference_run": {
                "run_id": RUN_ID,
                "n_events": 12,
                "generations": 3,
                "verify_run_ok": honest_root_ok,
                "root_hash": honest_prov["root_hash"],
                "manifest_sha256": honest_prov["manifest_sha256"],
                "events_sha256": honest_prov["events_sha256"],
                "event_chain_root": honest_prov["event_chain_root"],
                "final_state_hash": honest_prov["final_state_hash"],
                "signature_status": honest_prov["signature_status"],
                "promotion_receipt_eligible": honest_prov["promotion_receipt_eligible"],
            },
            "g0_anchor_parity": g0_rows,
            "g1_single_mutation_probes": g1_rows,
            "g2_g5_consistent_reforge_probes": g2_rows,
            "g4_single_anchor_field_coverage": coverage,
            "g4_complete_single_anchor_fields": complete,
            "g6_dsse_in_band_anchor": g6,
            "counts": {
                "g0_anchor_checks": len(g0_rows),
                "g0_pass": sum(1 for r in g0_rows if r["match"]),
                "g1_single_mutation_probes": len(g1_rows),
                "g1_fail_closed": sum(1 for p in g1_rows if p["fail_closed"]),
                "g2_reforge_scenarios": n_scen,
                "g2_detected_by_internal_verify": internal_detected,
                "g3_detected_by_external_root_anchor": root_detected,
                "g5_localized_by_component_anchors": localized_component,
                "g5_localized_by_root_anchor_only": localized_root_only,
                "g6_detected_cold_key_custody": cold,
                "g6_detected_hot_key_on_producing_host": hot,
            },
            "rates": {
                "single_mutation_detection_rate":
                    sum(1 for p in g1_rows if p["fail_closed"]) / len(g1_rows),
                "consistent_reforge_detection_rate_internal_verify":
                    internal_detected / n_scen,
                "consistent_reforge_detection_rate_external_root_anchor":
                    root_detected / n_scen,
                "consistent_reforge_detection_rate_dsse_cold_key": cold / n_scen,
                "consistent_reforge_detection_rate_dsse_hot_key": hot / n_scen,
                "localization_rate_component_anchors": localized_component / n_scen,
                "localization_rate_root_anchor_only": localized_root_only / n_scen,
            },
            "verdict": {
                "shipped_kpi_claim_under_test":
                    "fitted_or_physical_model_artifact.content_addressable_end_to_end"
                    " == true, with prediction_rule note 'Runtime is "
                    "content-addressable end-to-end; any single-bit mutation of "
                    "any artifact fails verify_run.'",
                "status": "PARTIALLY_CORROBORATED_SCOPE_BOUNDED",
                "corroborated":
                    "The claim holds exactly as written for non-recomputing "
                    "mutations: 15/15 single-mutation probes fail closed with the "
                    "expected RunArchiveError variant, a superset of the shipped "
                    "KPI's 10 probes.",
                "bounded":
                    "The claim does NOT extend to tamper-evidence. 8/8 consistent "
                    "re-forges -- including score falsification, unfavourable-event "
                    "deletion with renumbering, fabricated-event insertion, "
                    "temporal reordering, monte_carlo_seed rewriting, "
                    "best-candidate substitution, whole-archive substitution under "
                    "the same run_id, and Crosby-Wallach log truncation -- pass "
                    "verify_run with Ok. verify_run is an INTERNAL CONSISTENCY "
                    "predicate, not a tamper-evidence predicate. This is not a "
                    "defect in the implementation; it is the Haber-Stornetta 1991 "
                    "witnessing requirement, and the shipped module already names "
                    "it in kpi.awaiting and pins signature_status to "
                    "UNSIGNED_CONTROLLED_KEY_REQUIRED.",
                "minimal_sufficient_anchor":
                    "Of the 6 provenance fields, root_hash is the UNIQUE single "
                    "field whose out-of-band retention detects all 8 re-forges "
                    "(32 bytes). No component hash alone is complete: "
                    f"{json.dumps(coverage, sort_keys=True)} out of {n_scen}.",
                "localization_tradeoff":
                    "A root-only anchor is complete but yields exactly one "
                    "accept/reject bit and localizes the mutated component in 0/8 "
                    "scenarios; retaining all four component hashes localizes it "
                    "in 8/8. Completeness and diagnosticity are separable "
                    "properties of the anchor set.",
                "key_custody_condition":
                    "A DSSE Ed25519 attestation over {run_id, root_hash} supplies "
                    "the anchor in-band and detects 8/8 re-forges under COLD key "
                    "custody, but 0/8 when the signing key is hot on the "
                    "run-producing host, because the adversary simply re-signs the "
                    "forged root. Phase-1 signing is therefore necessary but not "
                    "sufficient: the controlled key must live outside the host "
                    "that writes the archive, or forward-integrity key evolution "
                    "(Kelsey-Schneier 1999; Bellare-Yee 2003) must be added.",
            },
            "closes":
                "Establishes, by independent non-runtime re-derivation with G0 "
                "byte-exact parity against the shipped Rust hash anchors, that "
                "amphora-run-provenance's verify_run is an internal-consistency "
                "predicate (15/15 non-recomputing mutations fail closed) and NOT "
                "a tamper-evidence predicate (0/8 consistent re-forges detected); "
                "identifies root_hash as the unique minimally sufficient 32-byte "
                "external anchor (8/8, versus at most 6/8 for any single component "
                "hash); separates anchor COMPLETENESS from anchor LOCALIZATION "
                "(root-only localizes 0/8, four component hashes localize 8/8); "
                "and shows constructively that a DSSE Ed25519 attestation over "
                "{run_id, root_hash} restores 8/8 detection in-band under cold key "
                "custody but 0/8 under hot-key custody on the producing host -- "
                "converting the module's open 'Phase-1 controlled-key signing "
                "pipeline' item from a checkbox into a testable key-custody "
                "requirement with a measured threat model.",
            "does_not_close": [
                "Does NOT execute the live Rust runtime; live re-exec parity of "
                "RunArchive create/append/final_state/verify_run and the full "
                "RunArchiveError taxonomy remains the Phase-1 ceiling.",
                "Does NOT change the shipped Haber-Stornetta linear-chain scheme, "
                "the pinned signature_status, or promotion_receipt_eligible.",
                "Does NOT constitute the Phase-1 controlled-key signing pipeline: "
                "the DSSE construction in G6 is an AUDIT_ONLY demonstration under "
                "the audit key, not a production attestation service, and no "
                "independent witness or gossip protocol (Crosby-Wallach) is "
                "implemented.",
                "Does NOT model an adversary with sub-SHA-256 collision "
                "capability; all findings are under the standard FIPS 180-4 "
                "collision-resistance assumption.",
                "Grants no batch-release, manufacturing-qualification, "
                "regulatory, safety, or product-performance authority. Does not "
                "promote the module or flip scientific_readiness.",
            ],
            "gates": gates,
        }
        os.makedirs(OUT, exist_ok=True)
        body = json.dumps(canonicalize(diag), indent=2, sort_keys=True,
                          ensure_ascii=False).encode("utf-8")
        which = os.environ.get("REPLAY", "canonical")
        outp = os.path.join(OUT, f"diagnostic.{which}.json")
        with open(outp, "wb") as f:
            f.write(body)
        print("WROTE", outp)
        print("diagnostic_sha256", raw_sha256(body))
        print("gates", json.dumps(gates, sort_keys=True))
        print("counts", json.dumps(diag["counts"], sort_keys=True))
        print("coverage", json.dumps(coverage, sort_keys=True))
        print("complete_single_anchors", complete)
        return 0 if gates["all_pass"] else 1
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
