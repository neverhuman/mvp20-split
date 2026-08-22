#!/usr/bin/env python3
"""Live-runtime per-axis adversarial corpus over the OUTER 23 portfolio-governance
attack axes declared in amphora-redteam-audit's Phase-0 benchmark lock.

Subject under test: the live Rust reference monitor `amphora-phase0-reviewer`
(mvp20-split/amphora-phase0-reviewer/src/main.rs), which is the component that
adjudicates the outer governance block of the module's 46-axis attack lock.

Prior work in this module covered only the INNER meta-audit block (24 axes,
axis-adequacy-subsumption-v1) and the INPUT dispatch allowlist
(dispatch-boundary-fail-closed-v1); both were offline CPython oracles over
shipped bytes. This oracle executes the real binary.

Theory / method anchors:
  Anderson 1972 (Computer Security Technology Planning Study, ESD-TR-73-51):
      reference monitor, complete mediation.
  Saltzer & Schroeder 1975 (Proc. IEEE 63(9):1278-1308): fail-safe defaults,
      separation of privilege (the two-key evaluator/reviewer split).
  DeMillo, Lipton & Sayward 1978 (IEEE Computer 11(4):34-41): mutation
      adequacy - a detector is only evidenced by killed mutants.
  Rapps & Weyuker 1985 (IEEE TSE 11(4):367-375); Zhu, Hall & May 1997
      (ACM CSUR 29(4):366-427): adequacy criteria and subsumption.
  Haber & Stornetta 1991 (J. Cryptology 3(2):99-111): hash-chained parent
      binding.
  NIST SP 800-53r5 CA-8 (penetration testing) / SI-7 (software and
      information integrity).

No portfolio artifact is mutated: every probe runs against a scratch rsync
copy of the workspace. The signed output of this oracle is AUDIT_ONLY.
"""

import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys

WS = "/home/ubuntu/amphora/build/redteam-live-scratch/ws"
PRISTINE = "/home/ubuntu/amphora/build/mvp20-split"
OUT = "/home/ubuntu/amphora/build/redteam-live-scratch/out"
REVIEWER = PRISTINE + "/target/release/amphora-phase0-reviewer"
BENCH = PRISTINE + "/target/release/amphora-tui"
KEYS = "/home/ubuntu/.local/share/amphora/phase0/keys"
EVAL_SEED = KEYS + "/evaluator.ed25519.seed"
REV_SEED = KEYS + "/internal-reviewer.ed25519.seed"
MODULE = "amphora-redteam-audit"
REV_KEYID = ("phase0-internal-reviewer-"
             "47233af18e511a305548d4ee306da018612f5b5aca201f9986504d3d7db3011b")
EVAL_KEYID = ("phase0-evaluator-"
              "3ef6b35cdbbfea74a96a5c9b98a515d57158a09ecaff10acfa1f15990be00178")
EVAL_PT = "application/vnd.amphora.module-phase0-evaluation-receipt.v1+json"

MOD = os.path.join(WS, MODULE)
BUNDLE = "evidence/phase0/bundle.v1.json"
RECEIPT = "evidence/phase0/receipts/evaluation.v1.dsse.json"
RESULT = "evidence/phase0/benchmark/result.v1.json"
POLICY = "evidence/phase0/promotion/policy.v1.json"
SRCLOCK = "evidence/phase0/sources/source-lock.v1.json"
BLOCK = "evidence/phase0/benchmark/benchmark-lock.v1.json"
CONTRACT = "ip/claim-contract.v1.json"
PRIORART = "ip/prior-art.v1.json"
MISSION = "docs/mission.md"
TRUST = "config/phase0-trust-store.v1.json"

# The OUTER portfolio-governance block: benchmark-lock attacks[0:23].
OUTER_AXES = [
    "STALE_PARENT", "SAME_SIGNER_REVIEW", "WRONG_ROLE_SIGNATURE",
    "FORGED_SIGNATURE", "REPOSITORY_LOCAL_PRIVATE_KEY", "FORGED_RIGHTS",
    "MISSING_LICENSE", "STRIPPED_CLAIM_LOCK", "CANDIDATE_SUPPLIED_EVIDENCE",
    "CROSS_MODULE_PATH_SUBSTITUTION", "REPLAY_DRIFT",
    "ALTERED_BENCHMARK_OUTPUT", "FALSE_HUMAN_REVIEW_CLAIM",
    "FALSE_MOVEMENT_CLAIM", "AUTHORITY_ESCALATION",
    "NEGATIVE_RESULT_AUTHORITY_ESCALATION",
    "LEGACY_AMPHORA_RECEIPT_LAUNDERING", "STRIPPED_MISSION_LOCKS",
    "FAILING_DETERMINISTIC_DIAGNOSTIC", "FALSE_BENCHMARK_EXECUTION_COMPLETE",
    "INCOMPLETE_REVIEW_POLICY", "UNKNOWN_REVIEWER_MODULE",
    "SUPERSESSION_ARCHIVE_SUBSTITUTION",
]

# Independent classification of the reviewer's fail-closed mechanism, derived
# from which predicate family the emitted error belongs to.
MECHANISM = [
    ("unknown field", "SCHEMA_DESERIALIZATION_WALL"),
    ("expected one of", "SCHEMA_DESERIALIZATION_WALL"),
    ("missing field", "SCHEMA_DESERIALIZATION_WALL"),
    ("stale parent hash", "PARENT_HASH_BINDING"),
    ("bundle does not bind", "PARENT_HASH_BINDING"),
    ("trust identities are not distinct", "TRUST_STORE_IDENTITY_SEPARATION"),
    ("trust store must contain exactly", "TRUST_STORE_IDENTITY_SEPARATION"),
    ("does not hold the required", "ROLE_BINDING"),
    ("role", "ROLE_BINDING"),
    ("DSSE", "DSSE_CRYPTOGRAPHIC_BINDING"),
    ("unsigned", "DSSE_CRYPTOGRAPHIC_BINDING"),
    ("repository-local", "KEY_HYGIENE_CONFINEMENT"),
    ("escapes the reviewed module", "PATH_CONFINEMENT"),
    ("unsafe module-relative path", "PATH_CONFINEMENT"),
    ("source rights binding", "RIGHTS_SEMANTIC_PREDICATE"),
    ("source hash claim is stale", "RIGHTS_SEMANTIC_PREDICATE"),
    ("deterministic-control rights policy", "RIGHTS_SEMANTIC_PREDICATE"),
    ("zero-authority claim lock", "CLAIM_LOCK_SEMANTIC_PREDICATE"),
    ("claim contract", "CLAIM_LOCK_SEMANTIC_PREDICATE"),
    ("promotion policy", "POLICY_SEMANTIC_PREDICATE"),
    ("review policy", "POLICY_SEMANTIC_PREDICATE"),
    ("benchmark lock is incomplete", "BENCHMARK_LOCK_SEMANTIC_PREDICATE"),
    ("evaluation receipt does not preserve", "RECEIPT_SEMANTIC_PREDICATE"),
    ("recorded benchmark is not bound", "RECEIPT_RESULT_BINDING"),
    ("replays are altered", "REPLAY_IDENTITY_PREDICATE"),
    ("does not prove complete", "REPLAY_IDENTITY_PREDICATE"),
    ("differs from the evaluated output", "LIVE_RE_EXECUTION"),
    ("locked benchmark did not emit", "LIVE_RE_EXECUTION"),
    ("diagnostic changed between", "LIVE_RE_EXECUTION"),
    ("locked benchmark command failed", "LIVE_RE_EXECUTION"),
    ("registry succession", "REGISTRY_SUCCESSION_CHAIN"),
    ("supersession", "SUPERSESSION_ARCHIVE_INTEGRITY"),
    ("reviewer allowlist", "DISPATCH_ALLOWLIST"),
    ("not confined to the workspace", "DISPATCH_ALLOWLIST"),
]


def classify(msg):
    for needle, mech in MECHANISM:
        if needle in msg:
            return mech
    return "UNCLASSIFIED"


def sha_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()


def stable_hash(value):
    return sha_bytes(canon(value))


def load(rel, base=None):
    with open(os.path.join(base or MOD, rel)) as fh:
        return json.load(fh)


def store(rel, obj, base=None):
    path = os.path.join(base or MOD, rel)
    text = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    with open(path, "w") as fh:
        fh.write(text)


def ed25519_sign(seed_path, payload):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    with open(seed_path, "rb") as fh:
        seed = fh.read()
    key = Ed25519PrivateKey.from_private_bytes(seed)
    return key.sign(payload)


def pae(payload_type, payload):
    return (f"DSSEv1 {len(payload_type)} {payload_type} "
            f"{len(payload)} ").encode() + payload


def sign_receipt(receipt):
    """Re-sign an evaluation receipt with the Phase-0 evaluator identity."""
    unsigned = {k: v for k, v in receipt.items() if k != "signature"}
    payload = canon(unsigned)
    sig = ed25519_sign(EVAL_SEED, pae(EVAL_PT, payload))
    receipt["signature"] = {
        "payload": base64.b64encode(payload).decode(),
        "payloadType": EVAL_PT,
        "signatures": [{"keyid": EVAL_KEYID,
                        "sig": base64.b64encode(sig).decode()}],
    }
    return receipt


NAMED = {
    SRCLOCK: "source_lock_hash",
    "evidence/phase0/dataset/dataset-manifest.v1.json": "dataset_manifest_hash",
    "evidence/phase0/split/split-manifest.v1.json": "split_manifest_hash",
    BLOCK: "benchmark_lock_hash",
    POLICY: "promotion_policy_hash",
    CONTRACT: "claim_contract_hash",
    "ip/technical-dossier.v1.json": "technical_dossier_hash",
    PRIORART: "prior_art_hash",
    "ip/disclosure-log.v1.json": "disclosure_log_hash",
}


def rechain():
    """Model the strongest realistic insider: an actor holding the Phase-0
    evaluator signing identity who re-derives every hash the bundle and the
    evaluation receipt declare, then re-signs.  Only defences that are
    independent of the evaluator's own attestations can survive this."""
    bundle = load(BUNDLE)
    for rel in list(bundle["parents"]):
        path = os.path.normpath(os.path.join(MOD, rel))
        if os.path.isfile(path):
            bundle["parents"][rel] = sha_file(path)
    for rel, field in NAMED.items():
        if rel in bundle["parents"]:
            bundle[field] = bundle["parents"][rel]
    store(BUNDLE, bundle)

    result = load(RESULT)
    result["bundle_sha256"] = sha_file(os.path.join(MOD, BUNDLE))
    store(RESULT, result)

    receipt = load(RECEIPT)
    receipt["bundle_hash"] = sha_file(os.path.join(MOD, BUNDLE))
    receipt["bundle_parent_hashes"] = bundle["parents"]
    receipt["claim_lock_hash"] = stable_hash(bundle["claim_locks"])
    receipt["applicability_domain"] = bundle["applicability_domain"]
    receipt["metrics"]["benchmark_result_sha256"] = sha_file(
        os.path.join(MOD, RESULT))
    receipt["replay_hash"] = stable_hash({"first": result["first_replay"],
                                          "second": result["second_replay"]})
    store(RECEIPT, sign_receipt(receipt))


def run_reviewer(tag, module=MODULE, key_id=REV_KEYID, key=REV_SEED,
                 workspace=WS):
    out = os.path.join(OUT, f"probe-{tag}.json")
    if os.path.exists(out):
        os.remove(out)
    proc = subprocess.run(
        [REVIEWER, "--workspace", workspace, "--module", module,
         "--benchmark-executable", BENCH, "--reviewer-key-id", key_id,
         "--reviewer-key", key, "--output", out],
        capture_output=True, text=True)
    accepted = proc.returncode == 0 and os.path.exists(out)
    msg = ""
    if not accepted:
        msg = (proc.stderr or proc.stdout).strip().splitlines()
        msg = msg[-1] if msg else ""
        msg = msg.replace("Error: ", "", 1)
    return {"accepted": accepted, "error": msg,
            "receipt_sha256": sha_file(out) if accepted else None}


# ---------------------------------------------------------------- snapshot

def snapshot():
    snap = {}
    for base in (MOD, os.path.join(WS, "config")):
        for root, _dirs, files in os.walk(base):
            for name in files:
                path = os.path.join(root, name)
                with open(path, "rb") as fh:
                    snap[path] = fh.read()
    return snap


def changed_paths(snap):
    changed = []
    live = set()
    for base in (MOD, os.path.join(WS, "config")):
        for root, _dirs, files in os.walk(base):
            for name in files:
                path = os.path.join(root, name)
                live.add(path)
                with open(path, "rb") as fh:
                    if fh.read() != snap.get(path):
                        changed.append(os.path.relpath(path, WS))
    changed.extend(os.path.relpath(p, WS) for p in set(snap) - live)
    return sorted(changed)


def live_diagnostic_sha():
    """SHA-256 of the module's live locked-diagnostic line, re-executed now."""
    proc = subprocess.run([BENCH, "benchmark", "run", "--locked", "--all"],
                          cwd=WS, capture_output=True,
                          env=dict(os.environ, AMPHORA_READ_ONLY_COMMAND="1"))
    for raw in proc.stdout.split(b"\n"):
        try:
            row = json.loads(raw)
        except Exception:
            continue
        if row.get("module_id") == MODULE:
            return sha_bytes(raw), row.get("passed")
    return None, None


def restore(snap):
    live = set()
    for base in (MOD, os.path.join(WS, "config")):
        for root, _dirs, files in os.walk(base):
            for name in files:
                live.add(os.path.join(root, name))
    for path in live - set(snap):
        os.remove(path)
    for path, data in snap.items():
        if not os.path.exists(path) or open(path, "rb").read() != data:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(data)


# ---------------------------------------------------------- repaired base

def build_repaired_baseline():
    """The shipped evidence halts the live reviewer for every module in the
    workspace (receipt-declared benchmark_result_sha256 no longer matches the
    on-disk result, and the recorded result predates three reviewer-required
    fields).  To expose the axes whose detectors sit downstream of that halt,
    the scratch copy is repaired into a state the live reviewer accepts."""
    proc = subprocess.run([BENCH, "benchmark", "run", "--locked", "--all"],
                          cwd=WS, capture_output=True,
                          env=dict(os.environ, AMPHORA_READ_ONLY_COMMAND="1"))
    line = None
    for raw in proc.stdout.split(b"\n"):
        try:
            row = json.loads(raw)
        except Exception:
            continue
        if row.get("module_id") == MODULE:
            line, diag = raw, row
    if line is None:
        raise SystemExit("live diagnostic for the module was not emitted")
    replay = {"diagnostic_receipt": diag, "diagnostic_sha256": sha_bytes(line),
              "execution_passed": True, "scientific_passed": True}
    result = load(RESULT)
    result.update({
        "schema": "amphora.module-phase0-benchmark-result.v1",
        "module_id": MODULE,
        "replay_identical": True,
        "scientific_outcome": "NOT_APPLICABLE",
        "benchmark_execution_complete": True,
        "first_replay": replay,
        "second_replay": json.loads(json.dumps(replay)),
    })
    store(RESULT, result)
    rechain()
    return sha_bytes(line)


# --------------------------------------------------------------- mutators

def m_stale_parent():
    path = os.path.join(MOD, PRIORART)
    with open(path, "ab") as fh:
        fh.write(b"\n")


def m_same_signer():
    trust = load(TRUST, base=WS)
    ev = [k for k in trust["keys"] if k["role"] == "PHASE0_EVALUATOR"][0]
    for row in trust["keys"]:
        if row["role"] == "PHASE0_INTERNAL_REVIEWER":
            row["public_key_hex"] = ev["public_key_hex"]
            row["key_id"] = ("phase0-internal-reviewer-" +
                             sha_bytes(bytes.fromhex(ev["public_key_hex"])))
    store(TRUST, trust, base=WS)


def m_forged_signature():
    receipt = load(RECEIPT)
    sig = receipt["signature"]["signatures"][0]["sig"]
    raw = bytearray(base64.b64decode(sig))
    raw[0] ^= 0x01
    receipt["signature"]["signatures"][0]["sig"] = base64.b64encode(
        bytes(raw)).decode()
    store(RECEIPT, receipt)


def m_repo_local_key():
    d = os.path.join(WS, ".phase0-keys")
    os.makedirs(d, exist_ok=True)
    os.chmod(d, 0o700)
    dst = os.path.join(d, "internal-reviewer.ed25519.seed")
    shutil.copyfile(REV_SEED, dst)
    os.chmod(dst, 0o600)


def m_forged_rights():
    lock = load(SRCLOCK)
    lock["sources"][0]["rights_status"] = "   "
    store(SRCLOCK, lock)


def m_missing_license():
    lock = load(SRCLOCK)
    lock["sources"][0]["rights_evidence_path"] = None
    lock["sources"][0]["license_present"] = True
    store(SRCLOCK, lock)


def m_stripped_claim_lock():
    bundle = load(BUNDLE)
    del bundle["claim_locks"]["no_release_authority"]
    store(BUNDLE, bundle)
    contract = load(CONTRACT)
    contract["claim_locks"].pop("no_release_authority", None)
    store(CONTRACT, contract)


def m_candidate_evidence():
    lock = load(SRCLOCK)
    lock["candidate_supplied_evidence_allowed"] = True
    store(SRCLOCK, lock)


def m_cross_module_path():
    bundle = load(BUNDLE)
    bundle["parents"]["../amphora-report-packager/ip/prior-art.v1.json"] = \
        sha_file(os.path.join(WS, "amphora-report-packager/ip/prior-art.v1.json"))
    store(BUNDLE, bundle)


def m_replay_drift():
    result = load(RESULT)
    result["second_replay"]["diagnostic_receipt"]["passed"] = True
    result["second_replay"]["diagnostic_sha256"] = "0" * 64
    store(RESULT, result)


def m_altered_benchmark_output():
    """Rewrite the recorded diagnostic that the evaluation receipt attests to,
    keeping both replays byte-identical, so that only live re-execution can
    expose the divergence."""
    result = load(RESULT)
    for key in ("first_replay", "second_replay"):
        diag = result[key]["diagnostic_receipt"]
        records = diag.get("records")
        if isinstance(records, list) and records:
            diag["records"] = records[:-1]
        else:
            diag["forged_axis_evidence"] = True
        result[key]["diagnostic_sha256"] = sha_bytes(canon(diag))
    store(RESULT, result)


def m_false_human_review():
    policy = load(POLICY)
    policy["human_review_performed"] = True
    store(POLICY, policy)


def m_false_movement_claim():
    ledger = load("movement/ledger.v1.json")
    for key in ("head", "head_event_sha256", "head_sha256"):
        if key in ledger and isinstance(ledger[key], str):
            ledger[key] = "0" * 64
            break
    else:
        ledger["fabricated_movement_claim"] = True
    store("movement/ledger.v1.json", ledger)


def m_authority_escalation():
    contract = load(CONTRACT)
    contract["prohibited_authorities"] = [
        a for a in contract["prohibited_authorities"] if a != "RELEASE"]
    store(CONTRACT, contract)


def m_negative_result_authority():
    lock = load(BLOCK)
    lock["negative_result_authority"] = "RELEASE"
    store(BLOCK, lock)


def m_legacy_laundering():
    lock = load(SRCLOCK)
    lock["legacy_amphora_receipt_authority"] = "AUTHORITATIVE"
    store(SRCLOCK, lock)


def m_stripped_mission_locks():
    path = os.path.join(MOD, MISSION)
    text = open(path).read()
    front, rest = text.split("\n", 2)[1], text
    meta = json.loads(front)
    meta.pop("solver_use_ceiling", None)
    meta["authority_ceiling"] = "RELEASE"
    lines = rest.split("\n")
    lines[1] = json.dumps(meta, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False)
    with open(path, "w") as fh:
        fh.write("\n".join(lines))


def m_failing_diagnostic():
    """Tamper with a workspace artifact the live diagnostic hashes into its own
    receipt (config/benchmark-lock.v1.json), so the locked control diagnostic
    must stop passing."""
    path = os.path.join(WS, "config/benchmark-lock.v1.json")
    lock = json.load(open(path))
    lock["fabricated_gate_relaxation"] = True
    with open(path, "w") as fh:
        fh.write(json.dumps(lock, sort_keys=True, indent=2,
                            ensure_ascii=False) + "\n")


def m_false_execution_complete():
    result = load(RESULT)
    result["benchmark_execution_complete"] = False
    store(RESULT, result)
    receipt = load(RECEIPT)
    receipt["benchmark_execution_complete"] = True
    store(RECEIPT, receipt)


def m_incomplete_policy():
    policy = load(POLICY)
    policy["required_gates"] = [g for g in policy["required_gates"]
                                if g != "INDEPENDENT_REVIEW_SIGNATURE"]
    store(POLICY, policy)


def m_supersession_substitution():
    root = os.path.join(MOD, "evidence/superseded")
    victim = None
    for base, _dirs, files in os.walk(root):
        for name in files:
            if name.endswith(".json"):
                victim = os.path.join(base, name)
                break
        if victim:
            break
    donor = os.path.join(WS, "amphora-report-packager/ip/prior-art.v1.json")
    shutil.copyfile(donor, victim)
    return victim


PROBES = [
    ("STALE_PARENT", m_stale_parent, False, {}),
    ("STALE_PARENT", m_stale_parent, True, {}),
    ("SAME_SIGNER_REVIEW", m_same_signer, False,
     {"key_id": EVAL_KEYID, "key": EVAL_SEED}),
    ("WRONG_ROLE_SIGNATURE", None, False,
     {"key_id": EVAL_KEYID, "key": EVAL_SEED}),
    ("FORGED_SIGNATURE", m_forged_signature, False, {}),
    ("REPOSITORY_LOCAL_PRIVATE_KEY", m_repo_local_key, False,
     {"key": WS + "/.phase0-keys/internal-reviewer.ed25519.seed"}),
    ("FORGED_RIGHTS", m_forged_rights, True, {}),
    ("MISSING_LICENSE", m_missing_license, True, {}),
    ("STRIPPED_CLAIM_LOCK", m_stripped_claim_lock, True, {}),
    ("CANDIDATE_SUPPLIED_EVIDENCE", m_candidate_evidence, True, {}),
    ("CROSS_MODULE_PATH_SUBSTITUTION", m_cross_module_path, True, {}),
    ("REPLAY_DRIFT", m_replay_drift, True, {}),
    ("ALTERED_BENCHMARK_OUTPUT", m_altered_benchmark_output, True, {}),
    ("FALSE_HUMAN_REVIEW_CLAIM", m_false_human_review, True, {}),
    ("FALSE_MOVEMENT_CLAIM", m_false_movement_claim, True, {}),
    ("AUTHORITY_ESCALATION", m_authority_escalation, True, {}),
    ("NEGATIVE_RESULT_AUTHORITY_ESCALATION", m_negative_result_authority, True, {}),
    ("LEGACY_AMPHORA_RECEIPT_LAUNDERING", m_legacy_laundering, True, {}),
    ("STRIPPED_MISSION_LOCKS", m_stripped_mission_locks, True, {}),
    ("FAILING_DETERMINISTIC_DIAGNOSTIC", m_failing_diagnostic, True, {}),
    ("FALSE_BENCHMARK_EXECUTION_COMPLETE", m_false_execution_complete, True, {}),
    ("INCOMPLETE_REVIEW_POLICY", m_incomplete_policy, True, {}),
    ("UNKNOWN_REVIEWER_MODULE", None, False,
     {"module": "amphora-redteam-audit-v2"}),
    ("SUPERSESSION_ARCHIVE_SUBSTITUTION", m_supersession_substitution, True, {}),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {}

    # G1 - shipped-state characterisation of the live reference monitor.
    shipped = {}
    for module in (MODULE, "amphora-source-ledger", "amphora-report-packager",
                   "amphora-evidence-intake-validator"):
        shipped[module] = run_reviewer("shipped-" + module, module=module,
                                       workspace=PRISTINE)
    receipt = load(RECEIPT, base=os.path.join(PRISTINE, MODULE))
    declared = receipt["metrics"]["benchmark_result_sha256"]
    observed = sha_file(os.path.join(PRISTINE, MODULE, RESULT))
    report["g1_shipped_state"] = {
        "reviewer_verdicts": shipped,
        "any_shipped_module_accepted": any(v["accepted"] for v in shipped.values()),
        "receipt_declared_benchmark_result_sha256": declared,
        "on_disk_benchmark_result_sha256": observed,
        "declared_equals_on_disk": declared == observed,
        "recorded_result_missing_reviewer_required_fields": sorted(
            f for f in ("bundle_sha256", "replay_identical", "scientific_outcome")
            if f not in load(RESULT, base=os.path.join(PRISTINE, MODULE))),
    }

    # G2 - canonicalisation + signing parity: independently re-derive the
    # shipped evaluator DSSE signature byte-for-byte (Ed25519 is
    # deterministic, so a match proves canonical-form parity with the Rust
    # implementation and that the re-chaining adversary is faithfully modelled).
    unsigned = {k: v for k, v in receipt.items() if k != "signature"}
    payload = canon(unsigned)
    resign = base64.b64encode(ed25519_sign(EVAL_SEED, pae(EVAL_PT, payload))).decode()
    report["g2_signing_parity"] = {
        "payload_b64_matches_shipped":
            base64.b64encode(payload).decode() == receipt["signature"]["payload"],
        "signature_matches_shipped":
            resign == receipt["signature"]["signatures"][0]["sig"],
        "keyid": EVAL_KEYID,
    }

    # G3 - repaired accepting baseline in the scratch workspace.
    base_snap = snapshot()
    live_sha = build_repaired_baseline()
    control_a = run_reviewer("control-a")
    control_b = run_reviewer("control-b")
    report["g3_repaired_baseline"] = {
        "live_diagnostic_line_sha256": live_sha,
        "control_a": control_a,
        "control_b": control_b,
        "accepted": control_a["accepted"],
        "review_receipt_byte_stable_across_replays":
            control_a["receipt_sha256"] == control_b["receipt_sha256"],
    }
    if not control_a["accepted"]:
        report["g3_repaired_baseline"]["fatal"] = (
            "no accepting baseline; per-axis corpus is not interpretable")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    accepted_snap = snapshot()

    # G4/G5 - per-axis adversarial corpus against the accepting baseline.
    probes = []
    for index, (axis, mutator, rechained, args) in enumerate(PROBES):
        restore(accepted_snap)
        if mutator is not None:
            mutator()
            if rechained:
                rechain()
        touched = changed_paths(accepted_snap)
        diag_sha, diag_passed = live_diagnostic_sha()
        tag = f"{index:02d}-{axis.lower()}" + ("-rechained" if rechained else "-naive")
        verdict = run_reviewer(
            tag,
            module=args.get("module", MODULE),
            key_id=args.get("key_id", REV_KEYID),
            key=args.get("key", REV_SEED))
        probes.append({
            "index": index,
            "axis": axis,
            "adversary": ("RECHAINED_EVALUATOR_KEY_HOLDER" if rechained
                          else "NAIVE_CONTENT_TAMPER"),
            "mutation_applied": mutator is not None,
            "mutation_effective": bool(touched) or mutator is None,
            "artifacts_touched": touched,
            "live_diagnostic_sha256": diag_sha,
            "live_diagnostic_changed": diag_sha != live_sha,
            "live_diagnostic_passed": diag_passed,
            "reviewer_accepted": verdict["accepted"],
            "fail_closed": not verdict["accepted"],
            "error": verdict["error"],
            "detection_mechanism": (None if verdict["accepted"]
                                    else classify(verdict["error"])),
        })
    restore(accepted_snap)

    covered = {p["axis"] for p in probes}
    killed = {p["axis"] for p in probes if p["fail_closed"]}
    survived = sorted({p["axis"] for p in probes if p["reviewer_accepted"]})
    report["g4_axis_corpus"] = {
        "outer_axis_block": OUTER_AXES,
        "outer_axis_count": len(OUTER_AXES),
        "axes_probed": sorted(covered),
        "axes_probed_count": len(covered),
        "coverage_complete": covered == set(OUTER_AXES),
        "probe_count": len(probes),
        "probes": probes,
    }
    report["g5_mutation_adequacy"] = {
        "mutants_killed": sum(1 for p in probes if p["fail_closed"]),
        "mutants_survived": sum(1 for p in probes if p["reviewer_accepted"]),
        "ineffective_probes": [p["axis"] for p in probes
                               if not p["mutation_effective"]],
        "surviving_effective_mutants": [
            {"axis": p["axis"], "adversary": p["adversary"],
             "artifacts_touched": p["artifacts_touched"],
             "live_diagnostic_changed": p["live_diagnostic_changed"]}
            for p in probes
            if p["reviewer_accepted"] and p["mutation_effective"]],
        "axes_killed_count": len(killed),
        "axes_survived": survived,
        "rechained_adversary_kill_rate": [
            sum(1 for p in probes
                if p["adversary"] == "RECHAINED_EVALUATOR_KEY_HOLDER"
                and p["fail_closed"]),
            sum(1 for p in probes
                if p["adversary"] == "RECHAINED_EVALUATOR_KEY_HOLDER"),
        ],
        "mechanism_histogram": {
            mech: sum(1 for p in probes if p["detection_mechanism"] == mech)
            for mech in sorted({p["detection_mechanism"] for p in probes
                                if p["detection_mechanism"]})
        },
    }

    # G7 - diagnosis of the surviving live-re-execution axis: is the locked
    # diagnostic that the reviewer re-executes actually bound to the workspace
    # under review, or to the tree the benchmark binary was compiled in?
    target = os.path.join(WS, "config/benchmark-lock.v1.json")
    with open(target, "rb") as fh:
        pristine = fh.read()
    lock = json.loads(pristine)
    lock["probe_marker_not_shipped"] = True
    with open(target, "w") as fh:
        fh.write(json.dumps(lock, sort_keys=True, indent=2,
                            ensure_ascii=False) + "\n")
    tampered_file_sha = sha_file(target)
    diag_after, _passed = live_diagnostic_sha()
    declared = None
    proc = subprocess.run([BENCH, "benchmark", "run", "--locked", "--all"],
                          cwd=WS, capture_output=True,
                          env=dict(os.environ, AMPHORA_READ_ONLY_COMMAND="1"))
    for raw in proc.stdout.split(b"\n"):
        try:
            row = json.loads(raw)
        except Exception:
            continue
        if row.get("module_id") == MODULE:
            declared = (row.get("artifact_hashes") or {}).get(
                "config/benchmark-lock.v1.json")
    with open(target, "wb") as fh:
        fh.write(pristine)
    outside = subprocess.run([BENCH, "benchmark", "run", "--locked", "--all"],
                             cwd="/tmp", capture_output=True,
                             env=dict(os.environ,
                                      AMPHORA_READ_ONLY_COMMAND="1"))
    emitted_outside = any(
        json.loads(raw).get("module_id") == MODULE
        for raw in outside.stdout.split(b"\n")
        if raw.strip().startswith(b"{"))
    with open(os.path.join(PRISTINE, "amphora-cli/src/main.rs")) as fh:
        source = fh.read()
    marker = 'PathBuf::from(env!("CARGO_MANIFEST_DIR"))'
    report["g7_reexecution_root_binding"] = {
        "reviewed_workspace": WS,
        "compiled_in_workspace": PRISTINE,
        "tampered_config_file_sha256": tampered_file_sha,
        "diagnostic_declared_config_sha256": declared,
        "declared_hash_tracks_reviewed_workspace": declared == tampered_file_sha,
        "diagnostic_line_changed_after_tamper": diag_after != live_sha,
        "diagnostic_emitted_with_cwd_outside_any_workspace": emitted_outside,
        "workspace_root_is_compile_time_constant": marker in source,
        "source_citation": "amphora-cli/src/main.rs fn workspace_root()",
    }

    # G6 - residue control: the corpus leaves no state behind.
    residue = run_reviewer("control-residue")
    report["g6_residue_control"] = {
        "accepted": residue["accepted"],
        "receipt_sha256_matches_control_a":
            residue["receipt_sha256"] == control_a["receipt_sha256"],
        "error": residue["error"],
    }

    restore(base_snap)
    killed_n = report["g5_mutation_adequacy"]["mutants_killed"]
    report["hypothesis"] = (
        "H0: the outer 23-axis portfolio-governance attack block declared in "
        "amphora-redteam-audit's Phase-0 benchmark lock is completely mediated "
        "and fail-closed under the live Phase-0 reference monitor, including "
        "against an adversary holding the evaluator signing identity.")
    report["verdict"] = ("HYPOTHESIS_PARTIALLY_REFUTED"
                         if report["g5_mutation_adequacy"]["surviving_effective_mutants"]
                         else "HYPOTHESIS_CORROBORATED")
    report["verdict_basis"] = {
        "mutants_killed_of_total": [killed_n, len(probes)],
        "axes_with_a_live_fail_closed_detector":
            report["g5_mutation_adequacy"]["axes_killed_count"],
        "axes_unmediated_or_structurally_limited":
            report["g5_mutation_adequacy"]["axes_survived"],
        "root_causes": {
            "STALE_PARENT": "parent hash binding is an evaluator self-attestation; "
                            "it detects third-party tampering but not an "
                            "evaluator-key holder who re-declares the hashes",
            "FALSE_MOVEMENT_CLAIM": "movement/ledger.v1.json is outside the "
                                    "reviewer's read surface entirely",
            "STRIPPED_MISSION_LOCKS": "docs/mission.md front-matter locks are "
                                      "never read by the reviewer even though "
                                      "the axis is a lock-required attack",
            "FAILING_DETERMINISTIC_DIAGNOSTIC":
                "the re-executed benchmark resolves its workspace from a "
                "compile-time constant, so the live diagnostic does not "
                "reflect the workspace under review (see g7)",
        },
    }
    report["remediation_non_authoritative"] = [
        "resolve the benchmark workspace from the reviewer-supplied root "
        "(argument or environment) instead of env!(\"CARGO_MANIFEST_DIR\"), so "
        "live re-execution is bound to the reviewed tree",
        "add mission front-matter lock and movement-ledger head predicates to "
        "the reviewer, or drop STRIPPED_MISSION_LOCKS / FALSE_MOVEMENT_CLAIM "
        "from the lock's declared axis set",
        "anchor bundle parents outside the evaluator's own attestation "
        "(second-party signature or external timestamp) if STALE_PARENT is to "
        "hold against a key-holding insider",
        "re-issue the stale evidence: every shipped module's evaluation "
        "receipt declares a benchmark_result_sha256 that no longer matches "
        "the on-disk result (g1)",
    ]
    report["schema"] = "amphora.redteam-audit-governance-axis-corpus-result.v1"
    report["module_id"] = MODULE
    report["subject_under_test"] = ("amphora-phase0-reviewer (live Rust "
                                    "reference monitor, release build)")
    report["audit_date"] = "2026-07-31"
    report["decision_use_ceiling"] = "AUDIT_ONLY"
    report["theory_anchors"] = [
        "Anderson 1972, ESD-TR-73-51 (reference monitor, complete mediation)",
        "Saltzer & Schroeder 1975, Proc. IEEE 63(9):1278-1308 "
        "(fail-safe defaults, separation of privilege)",
        "DeMillo, Lipton & Sayward 1978, IEEE Computer 11(4):34-41 "
        "(mutation adequacy)",
        "Rapps & Weyuker 1985, IEEE TSE 11(4):367-375 (adequacy subsumption)",
        "Zhu, Hall & May 1997, ACM CSUR 29(4):366-427 (adequacy criteria)",
        "Haber & Stornetta 1991, J. Cryptology 3(2):99-111 (hash chaining)",
        "NIST SP 800-53r5 CA-8 / SI-7",
    ]
    report["claim_locks"] = {
        "pre_phase_0_research_only": True,
        "no_phase_1_or_phase_2_claim": True,
        "no_release_authority": True,
        "no_qualification_authority": True,
        "no_product_performance_authority": True,
        "audit_only": True,
        "no_portfolio_artifact_mutated": True,
        "scratch_workspace_only": True,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
