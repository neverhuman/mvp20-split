#!/usr/bin/env python3
"""Build the diagnostic (twice, byte-stability gate) and DSSE-sign the
amphora-run-provenance run-id-collision-silent-substitution-v1 AUDIT_ONLY
receipt.

ROTATION-mode fire, no campaign item. Attacks the module's mission.md
locked KPI target: "Zero silent acceptance of malformed, unsupported, or
unauthorized inputs before Phase 0." This is the strongest still-standing
(unrefuted) claim in the doc; the other two headline claims (hash-chain
integrity 1.0, and cross-run replay byte-equality) were already refuted
by T-13, W-T-PROV, and the 2026-08-15 fixed-seed-replay-determinism-v1
fire. This study escalates past that last finding: it does not merely
observe that run_id is wall-clock-derived (already known), it exploits
that root cause to force a run_id COLLISION between two DIFFERENT,
legitimate, concurrently-issued requests (different candidate, different
seed) and shows the second request is silently answered with the first
request's stale archive, reported success, and never executed at all.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does not modify
the portfolio manifest, module-manifest.json, any locked dataset, any
signed Phase-0 KPI, mission.md front-matter, or the falsification ledger.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
STUDY = ROOT / "amphora-run-provenance/evidence/audit/run-id-collision-silent-substitution-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
FIRE_ID = "20260817T110001-2327100-8c34d93ee6d1"


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(p.read_bytes())


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


def load_json(p):
    return json.loads(p.read_text())


COLL = STUDY / "archives/collision"
CTRL = STUDY / "archives/control"
HARNESS = STUDY / "harness"

shared_archive = COLL / "shared-archive"
out_B = load_json(COLL / "out_B.json")
out_B_rerun = load_json(COLL / "out_B_rerun.json")

manifest = load_json(shared_archive / "manifest.json")
provenance = load_json(shared_archive / "provenance.json")
events_lines = (shared_archive / "events.jsonl").read_text().strip().splitlines()
first_event = json.loads(events_lines[0])
n_events = len(events_lines)
contains_candidate_b_marker = any("TETA-hardener-B" in line for line in events_lines)

ctrl_manifest_a = load_json(CTRL / "run-A" / "manifest.json")
ctrl_manifest_b = load_json(CTRL / "run-B" / "manifest.json")
ctrl_events_b = (CTRL / "run-B" / "events.jsonl").read_text().strip().splitlines()
ctrl_b_has_seed_222 = any('"seed":222' in line for line in ctrl_events_b)

candidate_a_sha = sha_file(HARNESS / "candidate_A.json")
candidate_b_sha = sha_file(HARNESS / "candidate_B.json")
shim_sha = sha_file(HARNESS / "faketime_shim.c")
shim_so_sha = sha_file(HARNESS / "faketime_shim.so")
amphora_cli_main_rs_sha256 = sha_file(ROOT / "amphora-cli/src/main.rs")
manifest_sha = sha_file(ROOT / "module-manifest.json")
amphora_tui_bin_sha = sha_file(ROOT / "target/release/amphora-tui")

archive_file_sha256 = {
    "collision/shared-archive": {
        f.name: sha_file(f) for f in sorted(shared_archive.iterdir()) if f.is_file()
    },
    "control/run-A": {
        f.name: sha_file(f) for f in sorted((CTRL / "run-A").iterdir()) if f.is_file()
    },
    "control/run-B": {
        f.name: sha_file(f) for f in sorted((CTRL / "run-B").iterdir()) if f.is_file()
    },
}


def build_body():
    return {
        "schema": "amphora.run-provenance.run-id-collision-silent-substitution-receipt.v1",
        "study_id": "run-id-collision-silent-substitution-v1",
        "authority": "AUDIT_ONLY",
        "module": "amphora-run-provenance",
        "campaign_item_id": "",
        "fire_id": FIRE_ID,
        "mode": "ROTATION",
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "modifies_manifest": False,
        "modifies_module_manifest": False,
        "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False,
        "modifies_falsification_ledger_in_place": False,
        "runs_live_rust_runtime": True,
        "claim_under_attack": {
            "receipt_path": "amphora-run-provenance/docs/mission.md",
            "claim_section": "KPI register and promotion gates",
            "claim_text": (
                "Locked target: Zero silent acceptance of malformed, "
                "unsupported, or unauthorized inputs before Phase 0."
            ),
            "note": (
                "This is the module's third headline claim and, as of this "
                "fire, the only one of the three not yet directly tested. "
                "T-13 (2026-08-06) refuted hash-chain-integrity-1.0 "
                "(verify_run is an internal-consistency predicate, not a "
                "tamper-evidence predicate: 0/8 consistent re-forges "
                "detected). W-T-PROV (2026-08-13) refuted the standards-"
                "conformance framing against in-toto/SLSA. The 2026-08-15 "
                "ROTATION fire refuted cross-run replay byte-equality, "
                "root-causing it to production run_id being wall-clock "
                "derived (format!(\"run-{}\", now_ms())) rather than the "
                "already-computed content-derived deterministic_run_id. "
                "That fire observed the divergence but did not exploit it. "
                "This study is the escalation: it uses the SAME root cause "
                "to force two DIFFERENT, legitimate, concurrently-issued "
                "requests to collide on run_id, and tests whether that "
                "collision causes 'silent acceptance' of the second "
                "request under the first request's identity -- the exact "
                "scenario the locked KPI target above claims cannot "
                "happen."
            ),
        },
        "attack": {
            "description": (
                "Built nothing new in Rust; used the existing real "
                "production binary target/release/amphora-tui (bin from "
                "amphora-cli crate, main.rs sha256 pinned below, unchanged "
                "since the 2026-08-15 fire). Wrote a small LD_PRELOAD "
                "shared object (faketime_shim.c, standard black-box time-"
                "interposition technique, same class as libfaketime) that "
                "intercepts glibc clock_gettime(CLOCK_REALTIME, ...) only, "
                "passing CLOCK_MONOTONIC and all other clock ids straight "
                "through to the real libc via dlsym(RTLD_NEXT, ...). It "
                "returns FAKETIME_BASE_MS + (real monotonic elapsed since "
                "process start), so within one process wall-clock deltas "
                "stay real (no div-by-zero / non-finite JSON floats) while "
                "the ABSOLUTE epoch value is deterministically pinned and "
                "reproducible across separate process invocations. No "
                "amphora source file was modified; the technique is purely "
                "external interposition on a real, unmodified binary. "
                "Two experiments, both from the module's live evidence/audit "
                "subtree (no writes outside amphora-run-provenance): "
                "(1) COLLISION: invoked `run` for candidate A (seed 111) "
                "and then, in the SAME working directory, for a genuinely "
                "DIFFERENT candidate B (different candidate_id, different "
                "SMILES, seed 222) with the IDENTICAL FAKETIME_BASE_MS "
                "value, forcing both invocations' run_id to be the string "
                "produced by now_ms() at the very first CLOCK_REALTIME read "
                "of each process (base_ms + 0 elapsed). (2) CONTROL: same "
                "two candidates/seeds, but with FAKETIME_BASE_MS values 5 "
                "seconds apart (no collision), to confirm the harness "
                "itself is discriminating and the shortcut is specific to "
                "the collision, not an artifact of faking the clock."
            ),
            "cli_invocation_template": (
                "FAKETIME_BASE_MS=<T> LD_PRELOAD=harness/faketime_shim.so "
                "target/release/amphora-tui run --candidate <path> "
                "--population 4 --generations 1 --workers 1 --seed <seed> "
                "--headless --jsonl"
            ),
            "collision_case": {
                "shared_faketime_base_ms": 1800000000000,
                "run_A": {"candidate": "candidate_A.json (DGEBA-monomer)", "seed": 111},
                "run_B": {"candidate": "candidate_B.json (TETA-hardener-B, DIFFERENT molecule)", "seed": 222},
                "resulting_run_id_both_requests": "run-1800000000000",
            },
            "control_case": {
                "run_A_faketime_base_ms": 1900000000000,
                "run_B_faketime_base_ms": 1900000005000,
                "run_A": {"candidate": "candidate_A.json (DGEBA-monomer)", "seed": 111},
                "run_B": {"candidate": "candidate_B.json (TETA-hardener-B, DIFFERENT molecule)", "seed": 222},
            },
            "candidate_a_sha256": candidate_a_sha,
            "candidate_b_sha256": candidate_b_sha,
            "amphora_tui_binary_sha256": amphora_tui_bin_sha,
            "faketime_shim_c_sha256": shim_sha,
            "faketime_shim_so_sha256": shim_so_sha,
        },
        "results": {
            "collision_case": {
                "amphora_runs_dirs_created": ["run-1800000000000"],
                "n_distinct_archives_for_2_different_requests": 1,
                "run_B_exit_code": 0,
                "run_B_stdout": out_B,
                "run_B_rerun_stdout_confirms_deterministic_shortcut": out_B_rerun,
                "run_B_reported_immutable_existing_run": out_B.get("immutable_existing_run"),
                "run_B_reported_root_hash": out_B.get("root_hash"),
                "shared_archive_provenance_json_root_hash": provenance.get("root_hash"),
                "root_hash_of_out_B_equals_root_hash_of_run_A_archive": (
                    out_B.get("root_hash") == provenance.get("root_hash")
                ),
                "shared_archive_manifest_candidate_contract_value_hash": manifest["inputs"]["candidate_contract_value_hash"],
                "shared_archive_event_count": n_events,
                "shared_archive_first_event_payload": first_event.get("payload"),
                "shared_archive_first_event_seed_is_run_A_seed_111": first_event.get("payload", {}).get("seed") == 111,
                "shared_archive_contains_any_trace_of_candidate_b_id": contains_candidate_b_marker,
                "request_b_candidate_and_seed_ever_executed": False,
            },
            "control_case": {
                "amphora_runs_dirs_created": ["run-1900000000000", "run-1900000005000"],
                "n_distinct_archives_for_2_different_requests": 2,
                "run_A_candidate_contract_value_hash": ctrl_manifest_a["inputs"]["candidate_contract_value_hash"],
                "run_B_candidate_contract_value_hash": ctrl_manifest_b["inputs"]["candidate_contract_value_hash"],
                "candidate_hashes_differ_as_expected": (
                    ctrl_manifest_a["inputs"]["candidate_contract_value_hash"]
                    != ctrl_manifest_b["inputs"]["candidate_contract_value_hash"]
                ),
                "run_B_archive_contains_seed_222_event": ctrl_b_has_seed_222,
                "run_B_genuinely_executed": ctrl_b_has_seed_222,
            },
        },
        "root_cause_source_read": {
            "file": "amphora-cli/src/main.rs",
            "archive_shortcut_block": {
                "line": 557,
                "src": "let archive_path = Path::new(\".amphora/runs\").join(&run_id);",
            },
            "shortcut_existence_check": {
                "line": 558,
                "src": "if archive_path.exists() {",
            },
            "shortcut_verify_and_return": {
                "lines": "559-570",
                "src": (
                    "let root_hash = verify_run(&archive_path)?; ... "
                    "println!(\"verified immutable run {run_id}: {root_hash}\"); "
                    "return Ok(());"
                ),
            },
            "run_id_source": {
                "line": 501,
                "src": "format!(\"run-{}\", now_ms())",
            },
            "interpretation": (
                "This is the SAME root cause identified by the 2026-08-15 "
                "fire (production run_id keyed to wall-clock now_ms(), not "
                "to the already-computed content-derived scoring_run_id), "
                "but this study demonstrates its downstream consequence for "
                "a DIFFERENT part of the same function: the existence-check "
                "shortcut at line 558 treats path existence under "
                ".amphora/runs/<run_id> as sufficient proof that the CURRENT "
                "request has already been honored. Because run_id carries "
                "no content binding (it is exactly and only now_ms()), path "
                "existence says nothing about whether the archive at that "
                "path corresponds to the CURRENT candidate/seed/population/"
                "generations/workers -- only that SOME earlier request "
                "happened to be issued in the same wall-clock millisecond. "
                "When that happens, verify_run(&archive_path) legitimately "
                "succeeds (it is genuinely checking a self-consistent, "
                "untampered archive -- consistent with T-13's finding that "
                "verify_run is a real internal-consistency predicate), and "
                "the CLI reports success for a request whose actual inputs "
                "were never read past manifest/candidate loading, never "
                "scored, and never archived."
            ),
        },
        "refutation_criterion_verbatim": (
            "Zero silent acceptance of malformed, unsupported, or "
            "unauthorized inputs before Phase 0."
        ),
        "refutation_criterion_observation_occurred": True,
        "refutation_observation": (
            "Request B (candidate_id=TETA-hardener-B, seed=222, a "
            "structurally valid, fully-authorized, non-malformed molecule "
            "request distinct from request A) was answered with exit code "
            "0 and JSON {\"immutable_existing_run\": true, \"root_hash\": "
            f"\"{out_B.get('root_hash')}\", \"run_id\": \"run-1800000000000\", "
            "\"schema\": \"amphora.run-replay.v1\"} without the module ever "
            "reading request B's candidate into a scoring pass, without "
            "creating any archive for request B, and without any warning, "
            "error, or field distinguishing 'this is someone else's cached "
            "result' from 'this is your freshly verified run'. The archive "
            ".amphora/runs/run-1800000000000 that request B's root_hash "
            "refers to contains zero references to candidate_id "
            "TETA-hardener-B or seed 222 anywhere in manifest.json, "
            "events.jsonl (22/22 events), or final-state.json; its sole "
            "content is request A's genuine run (seed 111, DGEBA-monomer). "
            "This is silent acceptance, under a false 'verified' label, of "
            "an unauthorized substitution of one request's output for "
            "another's -- exactly the observation the locked KPI target "
            "above pre-commits to never occurring. The control experiment "
            "(same two candidates/seeds, run_id's 5 seconds apart instead "
            "of colliding) produced two distinct archives with two distinct "
            "candidate_contract_value_hash values, and run B's archive "
            "genuinely contains the seed=222 event -- confirming the "
            "shortcut is specific to the run_id collision, not a harness "
            "artifact or a general miscount."
        ),
        "verdict": "CLAIM_REFUTED",
        "verdict_rationale": (
            "The module's own mission.md, KPI register, locks a promotion "
            "gate stating zero silent acceptance of unauthorized inputs "
            "before Phase 0. Forcing a run_id collision between two "
            "legitimate, differently-seeded, differently-charactered "
            "molecule requests (via external LD_PRELOAD clock "
            "interposition on the real, unmodified production binary -- no "
            "amphora source touched) causes the SECOND request to be "
            "silently and successfully answered with the FIRST request's "
            "stale, unrelated archive: exit 0, "
            "'immutable_existing_run': true, a root_hash that verify_run "
            "legitimately validates (it is a genuinely self-consistent "
            "archive -- this is not a verify_run tamper-detection bug, it "
            "is an identity/binding bug one call frame above verify_run), "
            "and zero trace of the second request's actual candidate or "
            "seed anywhere in the output or the archive. A control run "
            "with non-colliding run_ids behaves correctly (two distinct, "
            "genuinely-executed archives), isolating the defect to the "
            "collision path specifically. This is the third of the "
            "module's three headline KPI claims to fall under direct "
            "testing, and it shares a root cause with the second "
            "(wall-clock-derived run_id) while exposing a more severe "
            "consequence: not merely non-reproducible hashes, but an "
            "unauthorized request answered under someone else's identity "
            "with no error signal, in a portfolio where this very cron "
            "infrastructure runs multiple concurrent automated agents "
            "against xbabe2."
        ),
        "prior_related_evidence": {
            "T-13": "evidence/audit/real-archive-tamper-scale-v1/real-archive-tamper-scale-receipt.v1.dsse.json",
            "W-T-PROV": "evidence/phase0/repairs/W-T-PROV/done/w-t-prov-done-receipt.v1.dsse.json",
            "fixed-seed-replay-determinism-v1": "evidence/audit/fixed-seed-replay-determinism-v1/fixed-seed-replay-determinism-receipt.v1.dsse.json",
            "relation": (
                "T-13 showed verify_run cannot detect reforged tampering "
                "within a single archive. W-T-PROV showed the artifact "
                "meets no external signing/attestation standard. The "
                "2026-08-15 fire showed production run_id is wall-clock, "
                "not content, derived, so two genuinely-identical requests "
                "produce different hashes. This study shows the converse "
                "and more consequential failure mode enabled by the SAME "
                "root cause: two genuinely-DIFFERENT requests that happen "
                "to collide on wall-clock milliseconds produce the SAME "
                "identity, and the second is silently, successfully "
                "answered with the first's result."
            ),
        },
        "proposed_repair": (
            "Use the already-computed content-derived scoring_run_id "
            "(deterministic_run_id over candidate+seed+population+"
            "generations+workers+lane+profile) as the archive path key for "
            "the production `run` subcommand, exactly as `demo` mode "
            "already does at line 499 -- this simultaneously repairs the "
            "2026-08-15 replay-determinism finding (identical requests get "
            "identical, comparable identity) and this collision finding "
            "(only requests with genuinely identical inputs can ever "
            "collide on archive identity, and for those the existing "
            "'verified immutable run' shortcut becomes semantically "
            "correct rather than an unauthorized-substitution hazard)."
        ),
        "provenance": {
            "module_manifest_sha256": manifest_sha,
            "amphora_cli_main_rs_sha256": amphora_cli_main_rs_sha256,
            "amphora_tui_binary_sha256": amphora_tui_bin_sha,
            "faketime_shim_c_sha256": shim_sha,
            "faketime_shim_so_sha256": shim_so_sha,
            "candidate_a_sha256": candidate_a_sha,
            "candidate_b_sha256": candidate_b_sha,
            "archive_file_sha256": archive_file_sha256,
        },
        "reproducibility": {
            "two_replay_sha256_gate": "PASS",
            "determinism_basis": (
                "This diagnostic reads only pinned, already-recorded "
                "artifacts written to evidence/audit/run-id-collision-"
                "silent-substitution-v1/archives/ during the two live CLI "
                "experiments (collision and control), plus the pinned "
                "amphora-cli/src/main.rs and amphora-tui binary already on "
                "disk. No wall-clock, no RNG, no re-invocation of the CLI "
                "occurs inside this builder script, so re-running it twice "
                "against the same recorded archives is byte-identical by "
                "construction. The underlying asymmetry under test -- that "
                "the CLI, when live-invoked under a forced clock collision, "
                "silently substitutes request A for request B -- is the "
                "finding itself, captured once in the recorded archives "
                "and re-derived byte-stably here."
            ),
        },
        "signing_key": {
            "role": "PHASE0_EVALUATOR",
            "key_id": None,
            "public_key_hex": None,
            "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
            "signs_phase0_evaluation_or_review": False,
        },
    }


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha_bytes(eval_pub)}"

body1 = build_body()
body1["signing_key"]["key_id"] = eval_key_id
body1["signing_key"]["public_key_hex"] = eval_pub_hex
canon_bytes = json.dumps(body1, indent=2, sort_keys=True).encode()

body2 = build_body()
body2["signing_key"]["key_id"] = eval_key_id
body2["signing_key"]["public_key_hex"] = eval_pub_hex
runB_bytes = json.dumps(body2, indent=2, sort_keys=True).encode()

assert canon_bytes == runB_bytes, "two-replay byte-stability gate FAILED"

(STUDY / "diagnostic.canonical.json").write_bytes(canon_bytes)
(STUDY / "diagnostic.runB.json").write_bytes(runB_bytes)

diag_sha = sha_bytes(canon_bytes)

ptype = "application/vnd.amphora.run-provenance-run-id-collision-silent-substitution+json"
sig = eval_sk.sign(pae(ptype, canon_bytes))
envelope = {
    "payload": base64.standard_b64encode(canon_bytes).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
out = STUDY / "run-id-collision-silent-substitution-receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("diagnostic_sha256", diag_sha)
print("envelope_sha256", sha_file(out))
print("signature_verified", True)
print("verdict", body1["verdict"])
