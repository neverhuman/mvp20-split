#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-run-provenance fixed-seed-replay-determinism-v1
AUDIT_ONLY receipt.

ROTATION-mode fire (no campaign item, no directive_ref). Attacks the
module's own stated Phase-0 falsifiable hypothesis in docs/mission.md:
"fixed-seed replay is byte-identical outside declared wall-clock
telemetry" -- never directly tested by any prior fire for this module
(all five prior audits attacked verify_run's tamper-detection semantics
or standards conformance against a SINGLE archive, not cross-run replay
determinism).

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does not modify
the portfolio manifest, module-manifest.json, any locked dataset, any
signed Phase-0 KPI, mission.md front-matter, or the falsification ledger
(appended separately, never rewritten).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
STUDY = ROOT / "amphora-run-provenance/evidence/audit/fixed-seed-replay-determinism-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"


def sha(b): return hashlib.sha256(b).hexdigest()


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


canon = (STUDY / "diagnostic.canonical.json").read_bytes()
runB = (STUDY / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
diag_sha = sha(canon)

harness_sha = sha((STUDY / "harness_build_diagnostic.py").read_bytes())
amphora_cli_main_rs_sha256 = sha((ROOT / "amphora-cli/src/main.rs").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

prov = diag["results"]["provenance_json_field_compare"]
root_cause = diag["root_cause_source_read"]

body_obj = {
    "schema": "amphora.run-provenance.fixed-seed-replay-determinism-receipt.v1",
    "study_id": "fixed-seed-replay-determinism-v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-run-provenance",
    "campaign_item_id": "",
    "fire_id": "20260815T170001-612230-8379a41d4acd",
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
        "claim_text": diag["hypothesis_under_test"]["text_verbatim"],
        "claim_section": "Decision and falsifiable hypothesis",
        "note": (
            "This is the module's headline Phase-0 falsifiable hypothesis, "
            "stated in the first paragraph of mission.md. No prior fire "
            "(hash-chain-oracle-parity-v1, merkle-rfc6962-baseline-v1, "
            "anchor-necessity-reforge-resistance-v1, "
            "live-runtime-archive-parity-v1, real-archive-tamper-scale-v1/"
            "T-13, W-T-PROV) tested cross-run replay determinism; all "
            "attacked verify_run's tamper-detection semantics or standards "
            "conformance against a single archive."
        ),
    },
    "attack": {
        "description": (
            "Built the real production binary (amphora-cli crate, bin name "
            "amphora-tui) with `cargo build --release -p amphora-cli`, then "
            "invoked it TWICE, minutes apart, with byte-identical CLI "
            "arguments: `run --candidate "
            "amphora-candidate-contract/fixtures/molecule_candidate.json "
            "--population 4 --generations 1 --workers 1 --seed 20260815 "
            "--headless --jsonl`. This is the FIRST use of the real "
            "production `run` code path (not a synthetic unit-test tempdir "
            "fixture, not a hand-built harness calling RunArchive::create "
            "directly, not a historical archive from 2026-07) in this "
            "module's audit history. Compared the two resulting real "
            "archives under .amphora/runs/ field-by-field: manifest.json, "
            "final-state.json, all 22 events in events.jsonl (with run_id "
            "and 5 named timing-field names stripped by hand to isolate "
            "'science' from telemetry), and every field of provenance.json."
        ),
        "run_a_id": diag["inputs"]["run_a_id"],
        "run_b_id": diag["inputs"]["run_b_id"],
        "cli_invocation": diag["inputs"]["cli_invocation"],
        "inputs_equal_precondition_checks": diag["inputs"]["inputs_equal_precondition_checks"],
    },
    "results": {
        "manifest_json_diff_count": diag["results"]["manifest_json_diff_count"],
        "manifest_json_flat_diffs": diag["results"]["manifest_json_flat_diffs"],
        "final_state_json_diff_count": diag["results"]["final_state_json_diff_count"],
        "final_state_json_flat_diffs": diag["results"]["final_state_json_flat_diffs"],
        "events_jsonl_content_diff_count_after_stripping_run_id_and_timing": diag["results"][
            "events_jsonl_content_diff_count_after_stripping"
        ],
        "events_jsonl_n_events": diag["results"]["events_jsonl_n_events"],
        "provenance_json_field_compare": prov,
        "all_five_hash_anchors_differ": diag["results"]["all_five_hash_anchors_differ"],
    },
    "root_cause_source_read": root_cause,
    "declared_wall_clock_telemetry_exemption_search": diag["declared_wall_clock_telemetry_exemption_search"],
    "shipped_replay_command_capability": diag["shipped_replay_command_capability"],
    "positive_finding": diag["positive_finding"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observation_occurred": diag["refutation_criterion_observation_occurred"],
    "verdict": "CLAIM_REFUTED",
    "verdict_rationale": (
        "Two production `run` invocations with identical candidate, seed, "
        "population, generations, workers, lane, and objective profile "
        f"produced DIFFERENT values for every one of the five provenance "
        f"hash anchors: manifest_sha256 ({prov['manifest_sha256']['a'][:16]}... vs "
        f"{prov['manifest_sha256']['b'][:16]}...), events_sha256 "
        f"({prov['events_sha256']['a'][:16]}... vs {prov['events_sha256']['b'][:16]}...), "
        f"event_chain_root ({prov['event_chain_root']['a'][:16]}... vs "
        f"{prov['event_chain_root']['b'][:16]}...), final_state_hash "
        f"({prov['final_state_hash']['a'][:16]}... vs {prov['final_state_hash']['b'][:16]}...), "
        f"and root_hash ({prov['root_hash']['a'][:16]}... vs {prov['root_hash']['b'][:16]}...). "
        "Root cause read from amphora-cli/src/main.rs: the module already "
        "computes a deterministic, seed-derived run identity "
        "(deterministic_run_id -> scoring_run_id, a stable_hash over "
        "candidate+seed+population+generations+workers+lane+profile) but "
        "the production `run` subcommand discards it for archive identity, "
        "using `format!(\"run-{}\", now_ms())` (wall-clock milliseconds) "
        "instead -- only `demo` mode reuses the deterministic id. Because "
        "run_id is embedded byte-for-byte into manifest.json and into "
        "every event line in events.jsonl, this single wall-clock value "
        "cascades into literally every hash the module computes, including "
        "root_hash, the exact anchor mission.md and the shipped KPI hold "
        "out as proof of byte-identical replay. Separately, final-state.json "
        "bakes in real measured average_latency_ms and throughput timestamps "
        "that also vary run to run and also feed final_state_hash/root_hash. "
        "A targeted search of amphora-run-provenance, amphora-core, and "
        "amphora-cli for any allowlist, schema field, or code constant "
        "declaring which fields count as the hypothesis's exempted "
        "'declared wall-clock telemetry' found none -- the phrase exists "
        "nowhere except the hypothesis sentence itself. The hypothesis is "
        "therefore refuted on the plain reading (root_hash is not "
        "byte-identical for a fixed-seed replay) and, independently, is not "
        "mechanically testable as worded because no artifact defines its "
        "exemption clause. This is bounded, not total: after manually "
        "stripping run_id and named timing fields, the real scientific "
        "content of all 22 events -- proposals, mutations, scores, "
        "rankings, result_hash -- IS byte-identical between the two runs, "
        "so the seeded RNG and scoring path genuinely are deterministic; "
        "what fails is the module's own hash-anchor apparatus's ability to "
        "witness that fact."
    ),
    "prior_related_evidence": {
        "T-13": "evidence/audit/real-archive-tamper-scale-v1/real-archive-tamper-scale-receipt.v1.dsse.json (attacked verify_run's tamper-detection semantics against real historical archives; also found unrelated final_state_hash canonicalization drift across code versions)",
        "W-T-PROV": "evidence/phase0/repairs/W-T-PROV/done/w-t-prov-done-receipt.v1.dsse.json (attacked standards conformance vs in-toto/SLSA)",
        "relation": (
            "Both prior refutations concerned what verify_run checks "
            "(internal consistency, not tamper-evidence) or how the "
            "artifact compares to external standards. This study is the "
            "first to test the OTHER half of the module's mission "
            "statement -- the replay-determinism half -- and finds it also "
            "does not hold as stated, for an orthogonal root cause (archive "
            "identity keyed to wall-clock now_ms() in production) that is "
            "independent of both prior findings."
        ),
    },
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "harness_sha256": harness_sha,
        "amphora_cli_main_rs_sha256": amphora_cli_main_rs_sha256,
        "diagnostic_sha256": diag_sha,
        "archive_file_sha256": diag["inputs"]["archive_file_sha256"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "determinism_basis": (
            "The harness itself reads only the two pinned archive "
            "directories (archives/run-A, archives/run-B, copied verbatim "
            "from the two live CLI invocations) and the pinned "
            "amphora-cli/src/main.rs; no wall-clock, no RNG in the harness "
            "itself, so re-running it is byte-identical. The underlying "
            "asymmetry under test -- that the two SOURCE archives differ -- "
            "is precisely the finding, not a harness artifact: both "
            "archives are pinned inputs, read-only, hashed in "
            "provenance.archive_file_sha256."
        ),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.run-provenance-fixed-seed-replay-determinism+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(),
            "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
out = STUDY / "fixed-seed-replay-determinism-receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
print("verdict", body_obj["verdict"])
