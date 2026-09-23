#!/usr/bin/env python3
"""R-A12 anchored re-issue: one reinstatement batch receipt per module for the
fires the launcher verifier downgraded to UNKNOWN solely for
verified_new_signed=0 (declared artifacts DSSE-signed with the unanchored
LOCAL_DEVELOPMENT_AUDIT_ONLY key local-9028773f49591193 instead of the pinned
PHASE0_EVALUATOR key).

Per module: enumerate the downgraded-fire artifacts, diagnose each DSSE defect
live, re-run the science (re-attack), then sign ONE batch receipt with the
trust-anchored evaluator key, replicating the construction of
amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py
(pae(), load_seed(), envelope fields, keyid = phase0-evaluator-<sha256(pub)>).

SUPERSEDE, NEVER REWRITE: no existing file is modified or deleted; before/after
sha256 of every superseded artifact is asserted identical.
"""
import base64
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
os.chdir(ROOT)

SEED = Path.home() / ".local/share/amphora/phase0/keys/evaluator.ed25519.seed"
REVIEWER_SEED = Path.home() / ".local/share/amphora/phase0/keys/internal-reviewer.ed25519.seed"
TRUST = json.loads((ROOT / "config/phase0-trust-store.v1.json").read_text())
LOCAL_PUB_REC = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())
LOCAL_PUB = bytes.fromhex(LOCAL_PUB_REC["public_key_hex"])
RDKIT_PREFIX = "/home/ubuntu/.local/share/amphora/rdkit-2026.03.2"
REPAIR_ITEM = "R-A12"
REPAIR_MODE = "interactive-2026-08-03"
DATE = "2026-08-03"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fsha(rel):
    return sha((ROOT / rel).read_bytes())


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


def canon_payload(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def try_verify(pub, sig, msg):
    try:
        Ed25519PublicKey.from_public_bytes(pub).verify(sig, msg)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- keys
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
tbr = {k.get("role"): k for k in TRUST["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator seed does not derive the pinned trust-store key id"
EVAL_TRUST_PUB = bytes.fromhex(tbr["PHASE0_EVALUATOR"]["public_key_hex"])
assert eval_pub == EVAL_TRUST_PUB, "derived evaluator pubkey != trust store pubkey"
if REVIEWER_SEED.exists():
    rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
    rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
else:
    rev_pub_hex = tbr["PHASE0_INTERNAL_REVIEWER"]["public_key_hex"]
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))


# ------------------------------------------------- DSSE defect diagnosis
def diagnose(rel):
    """Live DSSE diagnosis of a defectively-signed artifact."""
    raw = (ROOT / rel).read_bytes()
    d = json.loads(raw)
    env = d["signature"] if isinstance(d.get("signature"), dict) else d
    payload = base64.standard_b64decode(env["payload"])
    ptype = env["payloadType"]
    s0 = env["signatures"][0]
    sig = base64.standard_b64decode(s0["sig"])
    m = pae(ptype, payload)
    return {
        "file_sha256": sha(raw),
        "payload_sha256": sha(payload),
        "payloadType": ptype,
        "envelope_location": ("nested_under_.signature" if env is not d
                              else "top_level"),
        "redundant_bare_signature_string_field": (
            isinstance(d.get("signature"), str)),
        "signing_keyid": s0["keyid"],
        "signing_key_authority": LOCAL_PUB_REC["authority"],
        "dsse_pae_wellformed": True,
        "verifies_against_pinned_phase0_evaluator_key": try_verify(
            EVAL_TRUST_PUB, sig, m),
        "verifies_against_local_development_key": try_verify(LOCAL_PUB, sig, m),
        "signed_payload_intact": try_verify(LOCAL_PUB, sig, m),
    }, json.loads(payload)


# ------------------------------------------------- science re-runs (re-attack)
def rerun_harness(workdir):
    bench = ROOT / "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1"
    binp = bench / "harness/target/release/role-live-runtime-domain-probe-harness"
    assert binp.exists(), "harness binary missing (build step must run first)"
    env = dict(os.environ, LD_LIBRARY_PATH=f"{RDKIT_PREFIX}/lib")
    outs = []
    for run in ("runA", "runB"):
        r = subprocess.run([str(binp)], capture_output=True, env=env,
                           check=True, timeout=300)
        (workdir / f"probe_reattack_{run}.json").write_bytes(r.stdout)
        outs.append(r.stdout)
    committed = (bench / "diagnostic.canonical.json").read_bytes()
    diag = json.loads(outs[0])
    return {
        "method": ("rebuilt committed Rust harness (cargo build --release, "
                   "amphora-rdkit-ffi feature=rdkit) against the pinned RDKit "
                   f"2026.03.2 prefix at {RDKIT_PREFIX}; executed the binary "
                   "twice; compared stdout bytes to the committed "
                   "diagnostic.canonical.json"),
        "rerun_runA_sha256": sha(outs[0]),
        "rerun_runB_sha256": sha(outs[1]),
        "rerun_two_replay_byte_equal": outs[0] == outs[1],
        "committed_diagnostic_sha256": sha(committed),
        "rerun_matches_committed_byte_exact": outs[0] == committed,
        "observed_verdict": diag["verdict"],
        "observed_summary": diag["summary"],
        "observed_toolkit_provenance": diag["toolkit_provenance"],
    }


def rerun_reactivity(workdir):
    bench = ROOT / "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1"
    mod = load_module("ra12_reactivity", bench / "run_reactivity_ratio.py")
    d1 = mod.main()
    d2 = mod.main()
    t1 = json.dumps(d1, indent=2, sort_keys=True)
    t2 = json.dumps(d2, indent=2, sort_keys=True)
    (workdir / "reactivity_reattack_runA.json").write_text(t1)
    committed = (bench / "diagnostic.canonical.json").read_text()
    return {
        "method": ("re-imported the committed run_reactivity_ratio.py and "
                   "called main() twice in-process (deterministic seeded "
                   "kinetic Monte Carlo); compared the canonical "
                   "json.dumps(indent=2, sort_keys=True) bytes to the "
                   "committed diagnostic.canonical.json"),
        "rerun_runA_sha256": sha(t1.encode()),
        "rerun_runB_sha256": sha(t2.encode()),
        "rerun_two_replay_byte_equal": t1 == t2,
        "committed_diagnostic_sha256": sha(committed.encode()),
        "rerun_matches_committed_byte_exact": t1 == committed,
        "observed_verdict": d1["verdict"],
        "observed_verdict_detail": d1["verdict_detail"],
    }


def rerun_sourceability(script_rel, committed_rel, workdir, tag, fields):
    mod = load_module(f"ra12_{tag}", ROOT / script_rel)
    d1 = mod.compute()
    d2 = mod.compute()
    b1, b2 = mod.canon(d1), mod.canon(d2)
    (workdir / f"{tag}_reattack_runA.json").write_bytes(b1)
    committed = (ROOT / committed_rel).read_bytes()
    res = {
        "method": (f"re-imported the committed {Path(script_rel).name} and "
                   "called compute() twice in-process; compared canonical "
                   "bytes to the committed diagnostic.canonical.json"),
        "rerun_runA_sha256": sha(b1),
        "rerun_runB_sha256": sha(b2),
        "rerun_two_replay_byte_equal": b1 == b2,
        "committed_diagnostic_sha256": sha(committed),
        "rerun_matches_committed_byte_exact": b1 == committed,
    }
    for label, getter in fields.items():
        res[label] = getter(d1)
    return res


# ----------------------------------------------------------- batch definitions
LOG = "logs/claude-hourly-loop.log"
LEDGER = "logs/falsification-ledger.jsonl"
DEFECT = ("Well-formed DSSE envelope (correct PAE pre-authentication encoding) "
          "but Ed25519-signed by the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key "
          "keyid=local-9028773f49591193 (public key 4b722f4516e035ce3cb95ccecf"
          "fe4638a687d9241e6970f4c1cf5c285b2edf93, .amphora/control/local-"
          "ed25519.pub.json), which is NOT registered in config/phase0-trust-"
          "store.v1.json; the launcher verifier requires a declared artifact "
          "that passes Ed25519 DSSE verification against the pinned "
          "PHASE0_EVALUATOR key (phase0-evaluator-3ef6b35...), so "
          "verified_new_signed=0 and the fire was downgraded to UNKNOWN. "
          "Wrong key, not malformed envelope and not a bare-string-only "
          "signature: the signature cryptographically verifies against the "
          "local development public key over the exact PAE bytes, proving the "
          "payload is intact.")

MODULES = {
    "amphora-molecule-role-ranker": {
        "ptype": "application/vnd.amphora.molecule-role-ranker-ra12-reinstatement-batch+json",
        "fires": [
            {
                "fire_id": "20260802T150002-1413344-9b251899480d",
                "ledger_ts": "2026-08-02T15:26:12+00:00",
                "ledger_line": 34,
                "recorded_verdict": "SURVIVED",
                "downgrade_log_ref": f"{LOG}:5354",
                "downgrade": "[2026-08-02T15:27:08+00:00] DOWNGRADE: CLAIM_SURVIVED->UNKNOWN (verdict CLAIM_SURVIVED not accepted: signing_check=OK, verified_new_signed=0 (must be a DECLARED artifact that passes real Ed25519 DSSE verification against the pinned Phase-0 key), ledger_has_fire_id=true (the ledger line must carry fire_id=20260802T150002-1413344-9b251899480d), protected_check=OK)",
            },
            {
                "fire_id": "20260803T030002-168451-6ef0580e79cf",
                "ledger_ts": "2026-08-03T03:13:18+00:00",
                "ledger_line": 46,
                "recorded_verdict": "SURVIVED",
                "downgrade_log_ref": f"{LOG}:5587",
                "downgrade": "[2026-08-03T03:14:02+00:00] DOWNGRADE: CLAIM_SURVIVED->UNKNOWN (verdict CLAIM_SURVIVED not accepted: signing_check=OK, verified_new_signed=0 (must be a DECLARED artifact that passes real Ed25519 DSSE verification against the pinned Phase-0 key), ledger_has_fire_id=true (the ledger line must carry fire_id=20260803T030002-168451-6ef0580e79cf), protected_check=OK)",
            },
        ],
        "signed_artifacts": [
            {
                "path": "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/replay_receipt.v1.dsse.json",
                "sha_before": "00a146943a4543c92fcb3b35549d79e7046bc6b2b7440d63b99f21a256def2e0",
                "fire_id": "20260802T150002-1413344-9b251899480d",
                "role": "primary replay receipt (live-runtime RDKit-FFI domain probe, verdict SURVIVED)",
                "reattack_key": "role_live_runtime_domain_probe",
            },
            {
                "path": "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/replay_receipt.v1.dsse.json",
                "sha_before": "1ccc3b6c5d0fa90446ad10c12197529a405ac4d247d332aa10be064f90f22784",
                "fire_id": "20260803T030002-168451-6ef0580e79cf",
                "role": "primary replay receipt (non-ideal reactivity-ratio kinetic MC attack on H2 direction rule, verdict SURVIVED)",
                "reattack_key": "role_reactivity_ratio_substitution_effect",
            },
        ],
        "supporting": [
            "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/diagnostic.canonical.json",
            "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/diagnostic.runB.json",
            "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/harness/src/main.rs",
            "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/harness/Cargo.toml",
            "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/sign_domain_probe.py",
            "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/diagnostic.canonical.json",
            "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/diagnostic.runB.json",
            "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/run_reactivity_ratio.py",
            "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/sign_reactivity_ratio.py",
        ],
    },
    "amphora-sourceability-ehs": {
        "ptype": "application/vnd.amphora.sourceability-ehs-ra12-reinstatement-batch+json",
        "fires": [
            {
                "fire_id": "20260802T170001-3280844-63859af6dae2",
                "ledger_ts": "2026-08-02T17:06:27+00:00",
                "ledger_line": 36,
                "recorded_verdict": "REFUTED",
                "downgrade_log_ref": f"{LOG}:5393",
                "downgrade": "[2026-08-02T17:06:41+00:00] DOWNGRADE: CLAIM_REFUTED->UNKNOWN (verdict CLAIM_REFUTED not accepted: signing_check=OK, verified_new_signed=0 (must be a DECLARED artifact that passes real Ed25519 DSSE verification against the pinned Phase-0 key), ledger_has_fire_id=true (the ledger line must carry fire_id=20260802T170001-3280844-63859af6dae2), protected_check=OK)",
            },
            {
                "fire_id": "20260803T050002-2025413-7726cab611c9",
                "ledger_ts": "2026-08-03T05:07:35+00:00",
                "ledger_line": 48,
                "recorded_verdict": "SURVIVED",
                "downgrade_log_ref": f"{LOG}:5622",
                "downgrade": "[2026-08-03T05:07:56+00:00] DOWNGRADE: CLAIM_SURVIVED->UNKNOWN (verdict CLAIM_SURVIVED not accepted: signing_check=OK, verified_new_signed=0 (must be a DECLARED artifact that passes real Ed25519 DSSE verification against the pinned Phase-0 key), ledger_has_fire_id=true (the ledger line must carry fire_id=20260803T050002-2025413-7726cab611c9), protected_check=OK)",
            },
        ],
        "signed_artifacts": [
            {
                "path": "amphora-sourceability-ehs/reference/mvp20/data/osha_table_z1_z2_attribution_audit_receipt.v1.json",
                "sha_before": "1001f14d85dd064e85a3ec57e6b9e4981676720f82c6eb0435bf4695c35547a9",
                "fire_id": "20260802T170001-3280844-63859af6dae2",
                "role": "primary audit receipt (OSHA Table Z-1 vs Z-2 attribution audit, H0 REFUTED: toluene is a Table Z-2 substance)",
                "reattack_key": "osha_table_z1_z2_attribution",
            },
            {
                "path": "amphora-sourceability-ehs/evidence/phase0/kpis/osha-table-z1-z2-attribution-audit-kpi.v1.json",
                "sha_before": "47863834bce63443243660895a1ce83739dc4b2eb3025ed74b0ff7cf2c903611",
                "fire_id": "20260802T170001-3280844-63859af6dae2",
                "role": "companion KPI record for the OSHA Z1/Z2 attribution audit",
                "reattack_key": "osha_table_z1_z2_attribution",
                "kpi_receipt_link": "amphora-sourceability-ehs/reference/mvp20/data/osha_table_z1_z2_attribution_audit_receipt.v1.json",
            },
            {
                "path": "amphora-sourceability-ehs/reference/mvp20/data/vhr_temperature_envelope_crossmethod_audit_receipt.v1.json",
                "sha_before": "d9f34de8c2b10361dd50be1d92e4e3b67530a0703f37b7ea1431e89d8527dde7",
                "fire_id": "20260803T050002-2025413-7726cab611c9",
                "role": "primary audit receipt (independent Clausius-Clapeyron+Watson cross-method temperature-envelope attack, verdict CLAIM_SURVIVED)",
                "reattack_key": "vhr_temperature_envelope_crossmethod",
            },
            {
                "path": "amphora-sourceability-ehs/evidence/phase0/kpis/vhr-temperature-envelope-crossmethod-audit-kpi.v1.json",
                "sha_before": "f3a379ee381c39c298f5f4b1ebaaa5cf20c486908471d64ffd3c42babf3f2cb9",
                "fire_id": "20260803T050002-2025413-7726cab611c9",
                "role": "companion KPI record for the VHR cross-method temperature-envelope audit",
                "reattack_key": "vhr_temperature_envelope_crossmethod",
                "kpi_receipt_link": "amphora-sourceability-ehs/reference/mvp20/data/vhr_temperature_envelope_crossmethod_audit_receipt.v1.json",
            },
        ],
        "supporting": [
            "amphora-sourceability-ehs/benchmarks/osha-table-z1-z2-attribution-audit-v1/diagnostic.canonical.json",
            "amphora-sourceability-ehs/benchmarks/osha-table-z1-z2-attribution-audit-v1/run_table_attribution_audit.py",
            "amphora-sourceability-ehs/benchmarks/vhr-temperature-envelope-crossmethod-audit-v1/diagnostic.canonical.json",
            "amphora-sourceability-ehs/benchmarks/vhr-temperature-envelope-crossmethod-audit-v1/run_crossmethod_temperature_audit.py",
        ],
    },
}


def build_and_sign(module_id, cfg, reattacks, results):
    repair_dir = ROOT / module_id / "evidence/phase0/repairs" / REPAIR_ITEM
    done_dir = repair_dir / "done"
    work_dir = repair_dir / "work"

    artifacts = []
    supersedes = []
    for art in cfg["signed_artifacts"]:
        diag, payload_obj = diagnose(art["path"])
        assert diag["file_sha256"] == art["sha_before"], (
            f"pre-recorded sha mismatch for {art['path']}")
        assert diag["verifies_against_pinned_phase0_evaluator_key"] is False
        assert diag["verifies_against_local_development_key"] is True
        entry = {
            "path": art["path"],
            "sha256": diag["file_sha256"],
            "role": art["role"],
            "fire_id": art["fire_id"],
            "original_defect": DEFECT,
            "observed_dsse_diagnosis": diag,
            "verification_result": reattacks[art["reattack_key"]],
        }
        if "kpi_receipt_link" in art:
            kpi = json.loads((ROOT / art["path"]).read_bytes())
            linked_payload_sha = diagnose(art["kpi_receipt_link"])[0]["payload_sha256"]
            entry["kpi_receipt_binding"] = {
                "kpi_scientific_receipt_body_sha256": kpi.get("scientific_receipt_body_sha256"),
                "linked_receipt_payload_sha256": linked_payload_sha,
                "binding_intact": kpi.get("scientific_receipt_body_sha256") == linked_payload_sha,
                "n_deterministic_gates_defined": kpi.get("n_deterministic_gates_defined"),
                "n_deterministic_gates_passed": kpi.get("n_deterministic_gates_passed"),
            }
            assert entry["kpi_receipt_binding"]["binding_intact"], (
                f"KPI->receipt sha binding broken for {art['path']}")
        artifacts.append(entry)
        supersedes.append({
            "superseded_path": art["path"],
            "superseded_sha256": diag["file_sha256"],
            "superseded_deleted_or_modified": False,
            "reason": ("DSSE signature made with the unanchored "
                       "LOCAL_DEVELOPMENT_AUDIT_ONLY key "
                       "local-9028773f49591193; it cannot verify against the "
                       "pinned PHASE0_EVALUATOR key in "
                       "config/phase0-trust-store.v1.json, so the launcher "
                       "verifier discarded the fire (verified_new_signed=0, "
                       "verdict downgraded to UNKNOWN). This anchored batch "
                       "receipt carries the re-verified science and original "
                       "verdict under the pinned evaluator key. The original "
                       "file is left byte-intact in place as evidence."),
        })

    supporting = {rel: fsha(rel) for rel in cfg["supporting"]}

    def build_payload():
        return {
            "schema": "amphora.repair.reinstatement-batch.v1",
            "repair_item": REPAIR_ITEM,
            "repair_mode": REPAIR_MODE,
            "module_id": module_id,
            "date": DATE,
            "generated_on_host": "xbabe2",
            "authority": "AUDIT_ONLY",
            "authority_ceiling": "EVIDENCE_ONLY",
            "promotes_authority": False,
            "modifies_existing_receipts": False,
            "modifies_manifest": False,
            "flips_scientific_readiness": False,
            "trust_anchored_in_phase0_store": True,
            "human_review_performed": False,
            "organizational_independence_asserted": False,
            "claim": (
                f"Reinstatement of the real falsification work of "
                f"{len(cfg['fires'])} launcher-downgraded fires of "
                f"{module_id}. Each fire's declared artifacts carried a "
                "cryptographically valid DSSE Ed25519 envelope whose only "
                "defect was the signing key: the repo "
                "LOCAL_DEVELOPMENT_AUDIT_ONLY key local-9028773f49591193 "
                "instead of the pinned PHASE0_EVALUATOR key, so the launcher "
                "verifier recorded verified_new_signed=0 and downgraded the "
                "fire verdicts to UNKNOWN. The science of every artifact was "
                "independently re-executed (re-attack) and reproduced the "
                "committed canonical diagnostics BYTE-EXACT, so the original "
                "recorded verdicts stand. This single anchored batch receipt "
                "lists every reinstated artifact with its sha256, its "
                "original defect, and its verification result, signed with "
                "the trust-anchored PHASE0_EVALUATOR key."),
            "root_cause": (
                "Signing-key selection bug in the hourly cron fires: receipts "
                "were signed with .amphora/control/local-ed25519.key "
                "(LOCAL_DEVELOPMENT_AUDIT_ONLY, keyid "
                "local-9028773f49591193) rather than the phase0 evaluator "
                "seed at ~/.local/share/amphora/phase0/keys/"
                "evaluator.ed25519.seed that derives the pinned trust-store "
                "key. Same failure class the loop itself root-caused for "
                "molecule-property W2 fires 1-2 (ledger lines 21-22)."),
            "downgraded_fires": cfg["fires"],
            "ledger_note": (
                f"{LEDGER} is append-only and was not modified by this "
                "repair; the cited ledger lines carry the original fire_ids "
                "and verdicts."),
            "supersedes": supersedes,
            "reinstated_artifacts": artifacts,
            "supporting_evidence_sha256": supporting,
            "reattack": {
                "description": (
                    "Re-ran the exact committed checker of each reinstated "
                    "receipt (rule: re-attack your own fix). Observed results "
                    "are embedded per artifact under verification_result; "
                    "every re-run reproduced the committed "
                    "diagnostic.canonical.json byte-exact and upheld the "
                    "original ledger verdict."),
                "results_by_check": reattacks,
            },
            "reproducibility": {
                "two_replay_sha256_gate": "PASS",
                "payload_canonicalization": (
                    "json.dumps(payload, sort_keys=True, "
                    "separators=(\",\",\":\")) serialized twice from two "
                    "independently constructed payload objects; byte-equality "
                    "asserted before signing; sha256 recorded by the signer "
                    "log and re-derivable from the envelope payload"),
            },
            "signing_key": {
                "role": "PHASE0_EVALUATOR",
                "key_id": eval_key_id,
                "public_key_hex": eval_pub_hex,
                "used_for": "AUDIT_ONLY repair reinstatement batch receipt",
                "signs_phase0_evaluation_or_review": False,
                "derives_pinned_trust_store_key_id": bool(eval_pin),
            },
            "reviewer_reference": {
                "role": "PHASE0_INTERNAL_REVIEWER",
                "key_id": rev_key_id,
                "public_key_hex": rev_pub_hex,
                "derives_pinned_trust_store_key_id": bool(rev_pin),
                "reviewer_signature_present": False,
                "note": ("Reviewer key referenced for provenance only; no "
                         "independent human review performed."),
            },
        }

    body_a = canon_payload(build_payload())
    body_b = canon_payload(build_payload())
    assert body_a == body_b, "two-replay payload serialization mismatch"
    body_sha = sha(body_a)

    ptype = cfg["ptype"]
    sig = eval_sk.sign(pae(ptype, body_a))
    envelope = {
        "payload": base64.standard_b64encode(body_a).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": eval_key_id,
                        "sig": base64.standard_b64encode(sig).decode()}],
    }
    receipt = {
        "evaluator_key_id": eval_key_id,
        "evaluator_public_key_hex": eval_pub_hex,
        "reviewer_public_key_hex": rev_pub_hex,
        "signature": envelope,
    }
    out = done_dir / "ra12_reinstatement_batch_receipt.v1.dsse.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

    # ---- SELF-VERIFY from freshly reloaded disk bytes
    reloaded = json.loads(out.read_bytes())
    renv = reloaded["signature"]
    rpayload = base64.standard_b64decode(renv["payload"])
    rsig = base64.standard_b64decode(renv["signatures"][0]["sig"])
    Ed25519PublicKey.from_public_bytes(eval_pub).verify(
        rsig, pae(renv["payloadType"], rpayload))
    Ed25519PublicKey.from_public_bytes(EVAL_TRUST_PUB).verify(
        rsig, pae(renv["payloadType"], rpayload))
    assert renv["signatures"][0]["keyid"].startswith("phase0-evaluator-3ef6b35"), \
        "keyid does not start with pinned prefix"
    assert sha(rpayload) == body_sha

    results[module_id] = {
        "receipt_path": str(out.relative_to(ROOT)),
        "receipt_sha256": sha(out.read_bytes()),
        "payload_sha256_two_replay": body_sha,
        "self_verified_against_seed_derived_pubkey": True,
        "self_verified_against_trust_store_pubkey": True,
        "keyid": renv["signatures"][0]["keyid"],
        "n_reinstated": len(artifacts),
    }


def main():
    results = {}
    # working dirs first (needed by re-attack runs)
    workdirs = {}
    for module_id in MODULES:
        repair_dir = ROOT / module_id / "evidence/phase0/repairs" / REPAIR_ITEM
        (repair_dir / "done").mkdir(parents=True, exist_ok=True)
        (repair_dir / "work").mkdir(parents=True, exist_ok=True)
        workdirs[module_id] = repair_dir / "work"

    # ---------- re-attacks (synchronous)
    rr_work = workdirs["amphora-molecule-role-ranker"]
    se_work = workdirs["amphora-sourceability-ehs"]
    reattacks_role = {
        "role_live_runtime_domain_probe": rerun_harness(rr_work),
        "role_reactivity_ratio_substitution_effect": rerun_reactivity(rr_work),
    }
    reattacks_ehs = {
        "osha_table_z1_z2_attribution": rerun_sourceability(
            "amphora-sourceability-ehs/benchmarks/osha-table-z1-z2-attribution-audit-v1/run_table_attribution_audit.py",
            "amphora-sourceability-ehs/benchmarks/osha-table-z1-z2-attribution-audit-v1/diagnostic.canonical.json",
            se_work, "osha", {
                "observed_h0_refuted": lambda d: d["h0_refuted"],
                "observed_misattributed_solvents": lambda d: d["misattributed_solvents"],
                "observed_n_misattributed_to_z1": lambda d: d["n_misattributed_to_z1"],
                "observed_matcher_trustworthy": lambda d: d["matcher_selfcheck"]["matcher_trustworthy"],
            }),
        "vhr_temperature_envelope_crossmethod": rerun_sourceability(
            "amphora-sourceability-ehs/benchmarks/vhr-temperature-envelope-crossmethod-audit-v1/run_crossmethod_temperature_audit.py",
            "amphora-sourceability-ehs/benchmarks/vhr-temperature-envelope-crossmethod-audit-v1/diagnostic.canonical.json",
            se_work, "vhr", {
                "observed_band_migrators": lambda d: d["hybrid_panel_result"]["band_migrators"],
                "observed_worst_actor_temperature_invariant": lambda d: d["hybrid_panel_result"]["worst_actor_temperature_invariant"],
                "observed_rank_order_25C": lambda d: d["hybrid_panel_result"]["rank_order_25C"],
                "observed_no_independent_anchor": lambda d: d["no_independent_anchor"],
            }),
    }

    # sanity: re-attacks all reproduce byte-exact and uphold verdicts
    for k, v in {**reattacks_role, **reattacks_ehs}.items():
        assert v["rerun_two_replay_byte_equal"], k
        assert v["rerun_matches_committed_byte_exact"], k

    build_and_sign("amphora-molecule-role-ranker",
                   MODULES["amphora-molecule-role-ranker"],
                   reattacks_role, results)
    build_and_sign("amphora-sourceability-ehs",
                   MODULES["amphora-sourceability-ehs"],
                   reattacks_ehs, results)

    # ---------- AFTER: superseded files byte-intact
    after = {}
    for cfg in MODULES.values():
        for art in cfg["signed_artifacts"]:
            now = fsha(art["path"])
            after[art["path"]] = {
                "sha256_before": art["sha_before"],
                "sha256_after": now,
                "intact": now == art["sha_before"],
            }
            assert now == art["sha_before"], f"SUPERSEDED FILE CHANGED: {art['path']}"

    # copy signer into work dirs for provenance
    for module_id, wd in workdirs.items():
        shutil.copy2(__file__, wd / "ra12_reissue.py")

    print(json.dumps({"results": results, "superseded_after_check": after},
                     indent=2))


if __name__ == "__main__":
    main()
