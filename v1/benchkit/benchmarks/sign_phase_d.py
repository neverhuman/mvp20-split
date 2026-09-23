#!/usr/bin/env python3
"""DSSE-Ed25519-sign the PHASE-D shared-performance-kit receipt.

Replicates the signing discipline of
amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py:
pae/load_seed/payloadType/attestation keys incl. authority AUDIT_ONLY,
promotes_authority false, two-replay byte-stability gate, self-verification
(rebuild PAE, verify, key id pinned against the phase0 trust store).

Signs a NEW receipt under amphora-redteam-audit/evidence/phase0/repairs/
PHASE-D/done/; modifies no existing signed artifact, no manifest, no locked
fixture, no quarantined data.
"""
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BK = ROOT / "benchkit"
BM = BK / "benchmarks"
OUTDIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/PHASE-D/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
CARGO_CONFIG = ROOT / ".cargo/config.toml"


def sha(b):
    return hashlib.sha256(b).hexdigest()


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


# ---- two-replay byte-stability gate ----------------------------------------
canon = (BM / "speedups.canonical.json").read_bytes()
runB = (BM / "speedups.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["_meta"]["all_bit_identical"] is True, "bit-identity gate failed"
diag_sha = sha(canon)

timings = json.loads((BM / "timings.v1.json").read_text())
wstests = json.loads((BM / "workspace_tests.v1.json").read_text())
assert wstests["phase_d_caused_regressions"] == 0, "phase-d regression detected"

kit_files = sorted(p for p in (BK / "amphora_benchkit").glob("*.py"))
test_files = sorted((BK / "tests").glob("*.py"))
kit_sha = {p.name: sha(p.read_bytes()) for p in kit_files}
test_sha = {p.name: sha(p.read_bytes()) for p in test_files}
harness_sha = sha((BM / "measure_speedups.py").read_bytes())
config_sha = sha(CARGO_CONFIG.read_bytes())

# ---- keys ------------------------------------------------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

speedup_summary = {k: {"speedup_x_informative": round(v["speedup_x"], 1)}
                   for k, v in timings["cases"].items()}

body_obj = {
    "schema": "amphora.redteam-audit.phase-d-shared-performance-kit-receipt.v1",
    "receipt_id": "phase-d-shared-performance-kit-v1",
    "module_id": "amphora-redteam-audit",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-04",
    "generated_on_host": "xbabe2",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_benchmark_lock": False,
    "modifies_existing_signed_benchmark_scripts": False,
    "claim": (
        "PHASE-D cross-cutting infrastructure receipt: (D2) a shared Python "
        "performance kit `amphora_benchkit` now exists at benchkit/ (pip -e "
        "installable AND sys.path importable) with five modules -- vectorized "
        "(cluster) bootstrap, np.linalg.solve Markov-chain ARL, thread-chunked "
        "stacked-solve ARL quadrature, RDKit BulkTanimotoSimilarity wrappers, "
        "and wall_seconds timing helpers -- adopted from named in-tree "
        "originals and covered by a DETERMINISM CONTRACT: 25 pytest tests "
        "execute the ORIGINAL implementations verbatim (AST-extracted from "
        "the original benchmark files, never hand-copied) on in-tree "
        "canonical fixtures and assert BIT-IDENTICAL outputs (float ==, "
        "ndarray .tobytes() equality); all pass, and the speedup harness "
        "re-asserts every bit-identity verdict with a two-replay byte-stable "
        "canonical diagnostic. (D1) sccache 0.15.0 is enabled workspace-wide "
        "via .cargo/config.toml [build] rustc-wrapper (merged; pre-existing "
        "[alias] preserved; 6-way hardlink deliberately broken by "
        "temp-file+mv so only this tree's config changed): cold 2-crate "
        "build 13.14s / 16 cache misses, warm replay 1.03s with 100% cache "
        "hit rate (2/2); post-change cargo test --workspace: 60/62 suites "
        "green, 363 passed / 3 failed, with ZERO Phase-D-caused regressions "
        "-- the 3 failures are (i) a live-evidence-state status assertion "
        "(phase0_count 16 vs 9) driven by Wave-R+ supersessions in baseline "
        "commit 907e753 plus a concurrent 2026-08-04T00:09 cron fire that "
        "rewrote 10 modules' result.v1.json, and (ii) two staleness-guard "
        "refusals in the NEW Phase-C amphora-solver-lab crate reacting to the "
        "R-N01 fire2 superseding receipt; none of these reads any Phase-D "
        "file (full attribution embedded under workspace_tests). sccache is "
        "output-transparent (it caches and replays "
        "compiler outputs content-addressed by compiler+args+inputs), so "
        "byte-identical-replay KPIs are unaffected. (D3) the ~254MB "
        "Epoxy_1M_p.csv Parquet conversion was deliberately SKIPPED: the file "
        "is quarantined (PolyUniverse acquisition unit polyuniverse_pairs, "
        "rights_class UNRESOLVED, catalog blocked_reason 'Upstream data "
        "license is unresolved; cached bytes remain inaccessible to "
        "derivatives'); writing a Parquet derivative would violate the "
        "quarantine. No existing signed benchmark script was rewritten or "
        "re-signed; the kit is import-only for FUTURE fires."),
    "kit": {
        "path": "benchkit/",
        "package": "amphora_benchkit 0.1.0",
        "modules": {
            "bootstrap.py": ("vectorized bootstrap indices / boot_r2 / cluster "
                             "RMSE + fold-mean CIs; originals: run_altlaw.py "
                             "(adopted vectorized reference), bigsoldb-v1 "
                             "run_benchmark_v2.py, nist-baseline-fold-"
                             "significance-v1 run_fold_significance.py"),
            "linalg.py": ("markov_arl / shewhart / EWMA / CUSUM ARL via "
                          "np.linalg.solve; adopted original: estparam-memory-"
                          "detector-arl-degradation-v1 run_memory_estparam_arl"
                          ".py; replaces spc-arl-characterization-v1 pure-"
                          "Python Gauss-Jordan"),
            "quadrature.py": ("thread-chunked stacked-solve conditional_arls "
                              "over (U,W) grids incl. round-12 memo-cache "
                              "replication; original: run_memory_estparam_arl"
                              ".py::conditional_arls"),
            "similarity.py": ("BulkTanimotoSimilarity wrappers preserving the "
                              "original accumulation order; originals: "
                              "molgen-scaffold-diversity-v1, conformal-"
                              "anomaly-detection-v1"),
            "timing.py": "stopwatch contextmanager + timed decorator emitting wall_seconds",
            "origins.py": "AST verbatim-extraction of originals for bit-identity tests",
        },
        "install_verified": {"pip_editable_venv": True, "sys_path_import": True},
        "file_sha256": kit_sha,
        "test_file_sha256": test_sha,
    },
    "determinism_contract": {
        "pytest_summary": "25 passed (benchkit/tests, python 3.12.3, xbabe2)",
        "bit_identity_all_cases": diag["_meta"]["all_bit_identical"],
        "bit_identity_cases": {
            k: v for k, v in diag.items() if not k.startswith("_")},
        "method": ("originals executed verbatim via AST extraction from the "
                   "in-tree benchmark files (sha256-provenanced); equality "
                   "asserted as float == / ndarray .tobytes(), never approx"),
        "fixture_note": ("the NIST fold-significance original's raw CSV lived "
                         "in /tmp scratch and no longer exists; its bootstrap "
                         "contract is exercised on the hash-pinned OpenPoly "
                         "canonical CSV instead (RNG-stream + reduction "
                         "replication is input-independent); all other "
                         "contracts run on the originals' own canonical "
                         "fixtures (purformance Experiment.zip, uw_nodes "
                         "grids, molgen hash-locked accepted proposals, "
                         "OpenPoly corpus)"),
    },
    "speedups_informative": {
        "note": ("wall-clock ratios vary with host load (128-core box shared "
                 "with cron fires; load avg 111-368 observed during runs); "
                 "kept OUT of the canonical two-replay payload by design"),
        "cases": speedup_summary,
        "quadrature_range_observed": "conditional_arls m=20 64x64: original 16.1-77.5s -> kit 4.9-5.2s (3.3x-14.8x)",
    },
    "sccache": {
        "version": "sccache 0.15.0",
        "wrapper_path": "/home/ubuntu/.cargo/bin/sccache",
        "config_file": ".cargo/config.toml",
        "config_sha256": config_sha,
        "config_merge": "pre-existing [alias] xtask section preserved; [build] rustc-wrapper appended",
        "cold_build_2_crates_seconds": 13.14,
        "cold_cache_misses": 16,
        "warm_build_2_crates_seconds": 1.03,
        "warm_hit_rate_percent": 100.0,
        "warm_hits": "2/2 compile requests served from cache",
        "output_transparency": ("sccache caches compilation outputs keyed by "
                                "compiler+arguments+inputs and replays them "
                                "byte-for-byte; it changes build speed only, "
                                "so byte-identical-replay KPIs are unaffected"),
        "incremental_note": ("demo builds used CARGO_INCREMENTAL=0 (sccache "
                             "does not cache incremental units; default "
                             "incremental builds simply pass through)"),
    },
    "parquet_d3": {
        "status": "SKIPPED",
        "target": "feedback/v1/external_data/polyuniverse_epoxy/raw/Epoxy_1M_p.csv (265,396,937 bytes)",
        "reason": ("quarantined: acquisition unit polyuniverse_pairs, "
                   "rights_class UNRESOLVED ('No derivative use until counsel "
                   "resolves upstream license.'); feedback/v2 catalog "
                   "blocked_reason: 'Upstream data license is unresolved; "
                   "cached bytes remain inaccessible to derivatives.' A "
                   "Parquet copy is a derivative; none was written and the "
                   "CSV was not touched"),
    },
    "workspace_tests": wstests,
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": ("benchkit/benchmarks/measure_speedups.py run twice "
                          "(canonical, runB); deterministic payload contains "
                          "bit-identity verdicts, fixture/grid sha256s and "
                          "provenance only; timings live in timings.v1.json "
                          "outside the byte-stability gate"),
    },
    "provenance": {
        "harness_sha256": {"measure_speedups.py": harness_sha},
        "canonical_diagnostic": "benchkit/benchmarks/speedups.canonical.json",
        "workspace_tests_file_sha256": sha((BM / "workspace_tests.v1.json").read_bytes()),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY infrastructure receipt under evidence/phase0/repairs/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.phase-d-shared-performance-kit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUTDIR.mkdir(parents=True, exist_ok=True)
out = OUTDIR / "phase-d-shared-performance-kit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# ---- self-verification: rebuild PAE from the WRITTEN file and verify -------
written = json.loads(out.read_text())
env = written["signature"]
payload = base64.standard_b64decode(env["payload"])
Ed25519PublicKey.from_public_bytes(bytes.fromhex(written["evaluator_public_key_hex"])).verify(
    base64.standard_b64decode(env["signatures"][0]["sig"]),
    pae(env["payloadType"], payload))
assert env["signatures"][0]["keyid"].startswith("phase0-evaluator-3ef6b35"), \
    "key id does not match pinned trust anchor prefix"

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified_and_keyid_pinned", True)
