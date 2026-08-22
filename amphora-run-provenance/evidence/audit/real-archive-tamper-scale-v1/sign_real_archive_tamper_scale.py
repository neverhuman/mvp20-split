#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-run-provenance real-archive-tamper-scale-v1
AUDIT_ONLY receipt.

FIRST adversarial (falsification) test ever recorded for this module
(campaign item T-13 / founder directive T2-13). Runs the real
amphora_core::verify_run against copies of REAL in-tree run archives under
.amphora/runs/ (n=28 of 31 found; 3 skipped as incomplete, reasons
recorded) instead of the shipped n=3 synthetic tempdir fixture, applying
the 4 required tamper probes (truncated chain / mid-point break, reordered
links, substituted intermediate hash, replayed archive) each in a naive
variant (provenance.json left untouched) and a forged variant
(provenance.json recomputed with the REAL stable_hash/raw-SHA-256 formula
so the tampered archive is internally self-consistent -- "root-hash
recompute that reconciles a forged history"), plus a cross-archive splice
divergence probe.

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
BENCH = ROOT / "amphora-run-provenance/evidence/audit/real-archive-tamper-scale-v1"
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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
diag_sha = sha(canon)

harness_main_sha = sha((BENCH / "harness/src/main.rs").read_bytes())
harness_toml_sha = sha((BENCH / "harness/Cargo.toml").read_bytes())
amphora_core_lib_rs_sha256 = sha((ROOT / "amphora-core/src/lib.rs").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

# ---- Derive summary counts straight from the two-replay-verified diagnostic ----
summary = {s["probe_variant"]: s for s in diag["probe_variant_summary"]}


def get(key):
    s = summary[key]
    return {"n": s["n"], "verify_ok": s["verify_ok_count"], "verify_err": s["verify_err_count"]}


truncated_naive = get("truncated_chain::naive_provenance_untouched")
truncated_forged = get("truncated_chain::forged_root_hash_recompute_reconciled")
reorder_naive = get("reordered_links::naive_provenance_untouched")
reorder_forged = get("reordered_links::forged_root_hash_recompute_reconciled")
subst_naive = get("substituted_intermediate_hash::naive_provenance_untouched")
subst_forged = get("substituted_intermediate_hash::forged_root_hash_recompute_reconciled")
replay = get("replayed_archive::verbatim_byte_replay_new_directory")
divergence = diag["divergence_probe_summary"]

# Baseline (zero tampering) verify_run outcomes across the real archives, and
# the field-level root cause for the 4 real-provenance archives that fail
# baseline verify with ZERO tampering (final_state_hash / stable_hash drift).
baseline_fail = [a["archive_id"] for a in diag["per_archive"]
                  if a["baseline_verify_result"] != "Ok"]
baseline_ok = [a["archive_id"] for a in diag["per_archive"]
               if a["baseline_verify_result"] == "Ok"]
n_real_provenance = sum(1 for a in diag["per_archive"] if a["provenance_source"] == "real")

# Any forged/reforged tamper case that verifies Ok is a slip-through of the
# claim "any single-bit mutation of any artifact fails verify_run" and of
# the founder's refutation_criterion.
slip_through_examples = []
for a in diag["per_archive"]:
    for p in a["probes"]:
        if p["variant"] == "forged_root_hash_recompute_reconciled" and p["verify_result"] == "Ok":
            slip_through_examples.append({
                "archive_id": a["archive_id"],
                "probe": p["probe"],
                "detail": p["detail"],
                "verify_result": p["verify_result"],
                "verify_root_hash": p["verify_root_hash"],
            })
    for p in a["probes"]:
        if p["probe"] == "replayed_archive" and p["verify_result"] == "Ok":
            slip_through_examples.append({
                "archive_id": a["archive_id"],
                "probe": p["probe"],
                "detail": p["detail"],
                "verify_result": p["verify_result"],
                "verify_root_hash": p["verify_root_hash"],
            })
for d in diag["divergence_probes"]:
    if d["verify_result"] == "Ok":
        slip_through_examples.append({
            "archive_id": d["host_archive"],
            "probe": d["probe"],
            "detail": d["detail"],
            "verify_result": d["verify_result"],
            "verify_root_hash": d["verify_root_hash"],
        })

forged_total_n = (truncated_forged["n"] + reorder_forged["n"] + subst_forged["n"]
                  + replay["n"] + divergence["n"])
forged_total_ok = (truncated_forged["verify_ok"] + reorder_forged["verify_ok"]
                   + subst_forged["verify_ok"] + replay["verify_ok"] + divergence["verify_ok_count"])

refutation_criterion = "A forged or diverged history verifies as intact."
refutation_observed = forged_total_ok > 0

body_obj = {
    "schema": "amphora.run-provenance.real-archive-tamper-scale-receipt.v1",
    "study_id": "real-archive-tamper-scale-v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-run-provenance",
    "campaign_item_id": "T-13",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_falsification_ledger_in_place": False,
    "runs_live_rust_runtime": True,
    "directive_ref": {
        "doc": "AMPHORA-DIRECTIVE-2026-08-05",
        "section": "A.1",
        "item_id": "T2-13",
        "owner": "LOOP",
        "directive_path": "docs/directives/2026-08-05-closing-the-open-portfolio.md",
        "directive_sha256": "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d",
        "directive_obligation": "T2-13",
    },
    "claim_under_attack": {
        "receipt_path": "amphora-run-provenance/docs/mission.md",
        "claim_text": "amphora-run-provenance has never received an adversarial verdict; its constructive SIGNED_RECEIPT-era receipts are untested claims.",
        "kpi_path": "amphora-run-provenance/evidence/phase0/kpis/run-provenance-hash-chain-integrity-kpi.v1.json",
        "kpi_metrics_attacked": [
            "verify_run_ok_on_untampered_archive_rate (floor 1.0, previously observed 1.0 on n=3 synthetic archives)",
            "integrity_tamper_probes_fail_closed_rate (floor 1.0, previously observed 1.0 on n=10 synthetic tamper probes)",
        ],
    },
    "attack": {
        "description": (
            "FIRST adversarial test of amphora-run-provenance. Ran the REAL "
            "amphora_core::verify_run (not a re-implementation) against copies "
            "of REAL in-tree run archives discovered under "
            ".amphora/runs/ (31 found on disk; 28 had a complete "
            "manifest.json+events.jsonl+final-state.json triple and were "
            "tested; 3 were incomplete/never reached final_state() and are "
            "skipped with reason, listed in skipped_archives). For archives "
            "lacking a real provenance.json (23/28), one was SYNTHESIZED from "
            "the archive's own real manifest/events/final-state bytes using "
            "the exact formula in amphora_core::RunArchive::final_state "
            "(same stable_hash / raw SHA-256 calls), so verify_run could be "
            "exercised; provenance_source is recorded per archive. Applied the "
            "4 required tamper probes to each of the 28 tested archives: "
            "truncated_chain (a mid-point event removed, remaining sequence "
            "renumbered to close the gap), reordered_links (two adjacent "
            "interior events swapped, sequence renumbered), "
            "substituted_intermediate_hash (one interior event's event_hash "
            "field replaced with a garbage value unrelated to its content), "
            "and replayed_archive (the complete, self-consistent archive "
            "copied byte-for-byte into a differently-named directory). Each "
            "of the first three probes was run in a naive variant "
            "(provenance.json left describing the pre-tamper bytes) and a "
            "forged variant (provenance.json RECOMPUTED with the real "
            "stable_hash/raw_sha256 formula against the tampered bytes -- "
            "'root-hash recompute that reconciles a forged history'). "
            "Additionally ran a cross-archive splice-divergence probe "
            "(founder directive's 'diverge a replay input/output pair'): for "
            "14 archive pairs, archive A's events.jsonl was replaced with "
            "archive B's complete, foreign event stream (every line still "
            "carrying B's own run_id), keeping A's manifest.json/"
            "final-state.json, then provenance.json reforged to reconcile."
        ),
        "n_real_archives_found_on_disk": diag["n_archives_found"],
        "n_real_archives_tested": diag["n_archives_tested"],
        "skipped_archives": diag["skipped_archives"],
        "archives_root": diag["archives_root"],
        "n_real_provenance_json_present": n_real_provenance,
        "n_provenance_synthesized_from_real_bytes": diag["n_archives_tested"] - n_real_provenance,
    },
    "results": {
        "baseline_untampered_verify": {
            "n": diag["n_archives_tested"],
            "verify_ok": len(baseline_ok),
            "verify_err": len(baseline_fail),
            "err_archive_ids": baseline_fail,
            "note": (
                "Zero tampering applied by this harness. 4 of the 28 tested "
                "archives are the 4 (of 5 total) real in-tree archives that "
                "carry a GENUINE, runtime-written provenance.json (from "
                "2026-07-17) and STILL fail verify_run today with "
                "'provenance hash mismatch', purely from re-running the "
                "unmodified real bytes through the current build of "
                "verify_run/stable_hash. Field-level isolation on "
                "run-03836b75676e298bc2dd (direct verify_run on the original, "
                "un-copied path, independent of this harness): "
                "manifest_sha256, events_sha256, and event_chain_root all "
                "match the recorded provenance exactly; final_state_hash is "
                "the sole divergent field (recorded "
                "639f25254faf83929b8ec9076adf1c8268aa396de36650857a74f9ad9cc2ce51 "
                "vs recomputed "
                "ca0caec0d5a3a1b5479e2126bb15667d348665bee78002a491899f800502f15b), "
                "which cascades into root_hash. This shows stable_hash's "
                "canonical serialization of final-state.json content (which "
                "carries many floats) is NOT stable across the runtime "
                "versions spanning 2026-07-17 to today, so genuinely "
                "untampered historical archives silently stop verifying -- a "
                "finding independent of, and additional to, the adversarial "
                "probes below."
            ),
        },
        "truncated_chain": {"naive": truncated_naive, "forged_reconciled": truncated_forged},
        "reordered_links": {"naive": reorder_naive, "forged_reconciled": reorder_forged},
        "substituted_intermediate_hash": {"naive": subst_naive, "forged_reconciled": subst_forged},
        "replayed_archive_verbatim": replay,
        "replay_divergence_spliced_input_output": divergence,
        "forged_or_replayed_total": {"n": forged_total_n, "verified_ok_despite_tamper": forged_total_ok},
        "naive_tamper_total_detected": {
            "n": truncated_naive["n"] + reorder_naive["n"] + subst_naive["n"],
            "detected": truncated_naive["verify_err"] + reorder_naive["verify_err"] + subst_naive["verify_err"],
        },
    },
    "slip_through_cases": slip_through_examples,
    "refutation_criterion_verbatim": refutation_criterion,
    "refutation_criterion_observation_occurred": refutation_observed,
    "verdict": "CLAIM_REFUTED",
    "verdict_rationale": (
        f"{forged_total_ok}/{forged_total_n} forged-or-replayed cases across "
        f"{diag['n_archives_tested']} real in-tree run archives caused "
        "verify_run to return Ok (root_hash) -- i.e. the module declared a "
        "tampered, reordered, truncated, substituted, or replayed/foreign "
        "history 'intact'. Root cause read from amphora-core/src/lib.rs: "
        "verify_run never independently recomputes an individual event's "
        "event_hash from stable_hash({schema,sequence,run_id,event_type,"
        "candidate_id,generation,payload,previous_event_hash}) and never "
        "compares it to the stored value; it only (a) checks positional "
        "sequence contiguity, (b) compares raw SHA-256 of the whole "
        "manifest.json/events.jsonl files to the values recorded in "
        "provenance.json, and (c) compares the LAST event's stored "
        "event_hash field to provenance.event_chain_root. All three checks "
        "are satisfied by any attacker who can rewrite provenance.json to "
        "match tampered bytes -- which is exactly what 'root-hash recompute "
        "that reconciles a forged history' does. verify_run also never "
        "compares its own directory path (the run identity under which it "
        "is being checked) to provenance.run_id or to any event's embedded "
        "run_id, so a byte-identical replay of one run's complete archive "
        "into a different run's slot verifies as fully intact. Naive "
        "(non-reforged) tampering IS caught in "
        f"{truncated_naive['verify_err'] + reorder_naive['verify_err'] + subst_naive['verify_err']}/"
        f"{truncated_naive['n'] + reorder_naive['n'] + subst_naive['n']} cases via the coarse "
        "whole-file byte-hash check -- this is real and not nothing -- but "
        "it is not the Haber-Stornetta interior-chain verification the KPI "
        "and mission.md theory section claim ('hash_chain_from_previous_"
        "event_hash_enforced: true'), and it is defeated the moment an "
        "attacker updates provenance.json consistently, which requires no "
        "special access beyond what any process that can write the archive "
        "already has (signature_status is honestly pinned "
        "UNSIGNED_CONTROLLED_KEY_REQUIRED for exactly this reason, but the "
        "KPI's 1.0 tamper-fail-closed-rate and mission.md's "
        "'hash_chain_from_previous_event_hash_enforced' claim lock overstate "
        "what is actually checked at verify time)."
    ),
    "prior_related_evidence": {
        "receipt": "evidence/audit/live-runtime-archive-parity-v1/live-runtime-archive-parity-receipt.v1.dsse.json",
        "relation": (
            "That receipt's G4 probe (hand-built, non-real archives) first "
            "surfaced 'H0b refuted: interior Haber-Stornetta linkage "
            "attested, not re-verified' as a Phase-1 hardening requirement. "
            "This receipt is the first to (a) confirm the same mechanism at "
            "scale (n=28) against REAL in-tree run archives rather than a "
            "hand-built fixture, (b) demonstrate the concrete consequence "
            "as a full forged-history acceptance across 4 named tamper "
            "classes plus replay/divergence, (c) discover the independent "
            "final_state_hash drift on genuine historical archives, and (d) "
            "be the first fire for this module to append a verdict to "
            "logs/falsification-ledger.jsonl -- zero prior entries existed "
            "for amphora-run-provenance."
        ),
    },
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "harness_main_rs_sha256": harness_main_sha,
        "harness_cargo_toml_sha256": harness_toml_sha,
        "amphora_core_lib_rs_sha256": amphora_core_lib_rs_sha256,
        "diagnostic_sha256": diag_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "determinism_basis": (
            "no wall-clock, no RNG in the harness; run twice against two "
            "different scratch directories (/tmp/rp-scale-scratch and "
            "/tmp/rp-scale-scratch-b) and byte-identical stdout was observed "
            "(scratch paths are never written into the emitted JSON); "
            "Ed25519 signatures are deterministic per RFC 8032"
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
ptype = "application/vnd.amphora.run-provenance-real-archive-tamper-scale+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(),
            "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "real-archive-tamper-scale-receipt.v1.dsse.json"
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
print("forged_total_ok", forged_total_ok, "/", forged_total_n)
