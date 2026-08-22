#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-candidate-contract shadow-run-live-reachability
AUDIT_ONLY receipt.

Closes the specific `does_not_close` item left open by
evidence/audit/normalized-formulation-shadow-consumer-v1 (2026-08-15, REFUTED):
"shadow_run() -> signed_receipt() -> persist_receipt() was not independently
re-run live in this fire ... reachability is established by exact source
citation only." This study independently re-runs it live, twice, against a
throwaway isolated workspace (never against shared production .amphora/ state).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-candidate-contract/benchmarks/shadow-run-live-reachability-v1"
AUDIT_DIR = ROOT / "amphora-candidate-contract/evidence/audit/shadow-run-live-reachability-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(path):
    return sha(path.read_bytes())


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(path):
    raw = path.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = json.loads((BENCH / "diagnostic.canonical.json").read_bytes())
runB = json.loads((BENCH / "diagnostic.runB.json").read_bytes())
two_replay = json.loads((BENCH / "two_replay_comparison.json").read_bytes())
assert two_replay["two_replay_payload_identical_excl_local_dev_identity"] is True
assert canon["leak_confirmed"] is True and runB["leak_confirmed"] is True
assert canon["both_receipts_ed25519_verified"] is True and runB["both_receipts_ed25519_verified"] is True

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_derives_pin = (rev_key_id == trust_by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.candidate-contract.shadow-run-live-reachability-receipt.v1",
    "study_id": "shadow-run-live-reachability-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "AUDIT_ONLY",
    "module": "amphora-candidate-contract",
    "campaign_item_id": "",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_or_capability_profile": False,

    "axis": (
        "Directly closes the sole `does_not_close` item of "
        "evidence/audit/normalized-formulation-shadow-consumer-v1 (2026-08-15T06:13:26Z, REFUTED, "
        "amphora-candidate-contract/evidence/audit/normalized-formulation-shadow-consumer-v1/"
        "normalized-formulation-shadow-consumer-receipt.v1.dsse.json): "
        "'shadow_run() -> signed_receipt() -> persist_receipt() was not independently re-run live "
        "in this fire (would write a real signed receipt into shared production .amphora/ state); "
        "reachability is established by exact source citation only.' That study proved by source "
        "citation that `amphora-tui shadow run --candidate <file>` (amphora-cli/src/control.rs "
        "ShadowRunArgs / shadow_run, no lane/candidate_type gate) calls the identical unmediated "
        "amphora_engine::EnginePool::score_many() this whole audit chain (T-01, T-01B, "
        "normalized-formulation-shadow-consumer-v1) has repeatedly shown echoes attacker-controlled "
        "top-level candidate keys verbatim, then folds the result into a real signed "
        "EvaluationReceiptV1 via control_receipt() -> signed_receipt() -> persist_receipt(). This "
        "study builds a fully isolated, symlink-based copy of the workspace (amphora-cli rebuilt "
        "from a real, non-symlinked directory inside the isolated root so that "
        "workspace_root() -- env!(\"CARGO_MANIFEST_DIR\").parent(), baked in at Rust compile time -- "
        "resolves to the isolated root, not the shared production tree; every other crate/module dir "
        "is a plain read-only symlink; `.amphora/` is never symlinked, so all writes -- fresh local "
        "Ed25519 dev-identity keygen, receipt persistence -- land only inside the throwaway isolated "
        "root and never touch the shared production `.amphora/receipts`, `.amphora/control`, or "
        "`.amphora/runs`), and runs the real, unmodified, compiled `amphora-tui shadow run` binary "
        "against it end-to-end, twice independently (two separate isolated roots, two separate fresh "
        "local dev identities), on a clean and a poisoned formulation candidate."
    ),

    "claim_under_attack": (
        "does_not_close item (verbatim, from normalized-formulation-shadow-consumer-v1): "
        "'shadow_run() -> signed_receipt() -> persist_receipt() was not independently re-run live in "
        "this fire (would write a real signed receipt into shared production .amphora/ state); "
        "reachability is established by exact source citation only, in the same style T-01B used for "
        "control.rs:4337-4359.'"
    ),

    "refutation_criterion_verbatim": (
        "The prior study's reachability claim (that shadow_run persists a real signed "
        "EvaluationReceiptV1 carrying an attacker-injected candidate value) was source-cited but NOT "
        "independently live-reproduced. REFUTATION of the open item = live end-to-end execution of the "
        "real compiled `amphora-tui shadow run` binary (not a harness reimplementation) on a clean vs. "
        "poisoned formulation candidate (candidate_id held constant) shows: (i) a real DSSE-enveloped, "
        "Ed25519-signed EvaluationReceiptV1 is persisted to disk via the exact production "
        "signed_receipt()/persist_receipt() call chain with no confirmation gate; (ii) its signature "
        "cryptographically verifies against the declared local identity key; (iii) the receipt's "
        "artifact_hashes/result_hash differs between clean and poison runs, i.e. the attacker-injected "
        "top-level key is baked into the signed artifact's content; and (iv) this reproduces "
        "byte-identically (payload-for-payload) across two fully independent isolated-workspace "
        "replays. SURVIVAL of the open item would instead require either shadow_run failing to run "
        "end-to-end, failing to sign/persist, producing a signature that does not verify, or producing "
        "identical artifact_hashes for clean vs. poison."
    ),
    "refutation_criterion_observed": True,
    "refutation_criterion_statement": (
        "REFUTATION OF THE OPEN ITEM OCCURRED -- reachability is now LIVE-PROVEN, not merely "
        "source-cited. Built and ran the real, unmodified `amphora-tui shadow run` binary "
        "(compiled from the workspace's real amphora-cli/amphora-core/amphora-engine sources via a "
        "symlink-isolated root so workspace_root() resolves off-tree) against a clean and a poisoned "
        "formulation candidate (candidate_id constant: 'Envelope-65-black-leaktest', the same "
        "candidate pair normalized-formulation-shadow-consumer-v1 used, injected key "
        "canonical_structure_hash). Both runs (i) completed with exit 0 and no confirmation prompt; "
        "(ii) each persisted a real DSSE EvaluationReceiptV1 to <isolated_root>/.amphora/receipts/ via "
        "the production signed_receipt()->persist_receipt() call chain (schema "
        "amphora.evaluation-receipt.v1, module_id 'amphora-optimizer-orchestrator', evidence_tier "
        "SYNTHETIC_DIAGNOSTIC, decision_use_ceiling SHADOW, passed=true); (iii) both receipts' Ed25519 "
        "signatures independently verify against their declared local-<hex> identity public key "
        "(PAE = DSSEv1 SP len(type) SP type SP len(body) SP body, matching amphora-core::crypto::pae); "
        "(iv) clean artifact_hashes['result:Envelope-65-black-leaktest'] = "
        "c5c85f0bcc3bb63bb8d5533f2e42f57dcb94208589ade7f5fc404c7bca16ed9f, poison = "
        "e8b7d40e030217faad944cd701ab5c88d7001aaf1b57e9a2dfb1f93601da613d -- DIFFERENT, sole input "
        "delta being the presence of the injected top-level key, candidate_id held constant; (v) a "
        "SECOND, fully independent isolated-root replay (fresh symlink scaffold, fresh cargo build, "
        "fresh random local dev-identity keypair) reproduced byte-identical receipt PAYLOADS for both "
        "clean (payload sha256 665c76343237dce5a6f9e57f42f21945ff4c436816a255280654b755ac47fb8b, both "
        "runs) and poison (payload sha256 afc1bd4108145652c55acad7c8ecf812da6d0e8d9f86a6631aedc4c2bad0"
        "2050, both runs) -- the only per-replay difference is the local dev-identity signing keyid "
        "itself (a fresh /dev/urandom key minted per throwaway isolated root by "
        "ensure_local_identity(), not attacker-controlled data), confirming the leaked content is "
        "deterministic and reproducible, not an artifact of one run. Zero writes to shared production "
        "root/.amphora/ occurred (verified: no new files under the real "
        "/home/ubuntu/amphora/build/mvp20-split/.amphora/receipts or /control during this study)."
    ),

    "mitigating_context": (
        "This does NOT establish that the leaked content can reach Ranking/production decision "
        "authority through this specific receipt. amphora-core/src/artifacts.rs "
        "EvaluationReceiptV1::validate() rejects evidence_tier SyntheticDiagnostic combined with "
        "decision_use_ceiling==Ranking outright, and PromotionPolicyV1::authority_for() computes "
        "policy_ceiling.minimum(receipt.decision_use_ceiling) -- with decision_use_ceiling fixed to "
        "Shadow for every shadow_run receipt, any consumer that correctly calls authority_for() is "
        "mechanically capped at Shadow regardless of policy, and cannot elevate this receipt to "
        "Ranking authority. authority_for() is confirmed load-bearing (consumed by "
        "amphora-core/src/molecule_evidence.rs, not dead code). What THIS study establishes is "
        "strictly the data-integrity claim T-01/T-01B/normalized-formulation-shadow-consumer-v1 have "
        "each tested: that attacker-supplied candidate content survives verbatim into a real signed "
        "artifact via an unmediated, currently-shipped CLI path -- a Saltzer&Schroeder complete-"
        "mediation failure at the DATA layer, independent of whatever AUTHORITY ceiling that artifact "
        "carries. Whether any downstream consumer reads shadow-tier receipt CONTENT (as opposed to "
        "its authority ceiling) without going through authority_for() is not evaluated here and is "
        "flagged in does_not_close."
    ),

    "theory_reference": [
        "J. H. Saltzer and M. D. Schroeder (1975), 'The Protection of Information in Computer "
        "Systems', Proceedings of the IEEE 63(9):1278-1308, DOI 10.1109/PROC.1975.9939 -- complete "
        "mediation requires every access path to a protected resource to be checked; shadow_run is a "
        "second, unmediated access path to the same signing/persistence machinery as the gated "
        "run_solver path.",
    ],

    "non_circularity": (
        "The real, unmodified `amphora-tui` binary is built from the workspace's actual "
        "amphora-cli/amphora-core/amphora-engine source (via `cargo build --bin amphora-tui`, no code "
        "changes) and executed as a subprocess via its real CLI (`shadow run --candidate <file>`), not "
        "called as a library function or reimplemented. The isolation is purely a symlink scaffold "
        "plus a fresh root-relative `.amphora/`; every source file cargo compiles is the real, "
        "unmodified file (symlinked, byte-identical, hashes below). Signature verification uses an "
        "independent Python Ed25519 implementation (cryptography library), not the Rust verifier, "
        "against the PAE construction copied verbatim from amphora-core/src/crypto.rs."
    ),

    "live_reproduction": {
        "isolation_method": (
            "amphora-cli/{Cargo.toml,src} placed under a real (non-symlinked) directory inside the "
            "isolated root so env!(\"CARGO_MANIFEST_DIR\") -- baked in at compile time by "
            "workspace_root() in amphora-cli/src/main.rs -- resolves inside the isolated root; every "
            "other top-level workspace entry symlinked read-only; `.amphora/` intentionally absent so "
            "ensure_local_identity()/persist_receipt() create it fresh, isolated. Setup script: "
            "shadow_isolation_setup.sh."
        ),
        "cli_binary": "amphora-tui (package amphora-cli, [[bin]] name amphora-tui, default-run)",
        "cli_invocation": "amphora-tui shadow run --candidate <file.json> --workers 2 --seed 42",
        "engine_entry_point": "amphora_engine::EnginePool::score_many, called from amphora-cli/src/control.rs fn shadow_run with no candidate_type/lane filter",
        "signing_chain": "amphora-cli/src/control.rs shadow_run -> control_receipt() -> signed_receipt() -> EvaluationReceiptV1::sign() (amphora-core/src/artifacts.rs, Ed25519 via amphora-core::crypto::sign_dsse/pae) -> persist_receipt()",
        "writes_to_shared_state": False,
        "writes_to_shared_state_note": "Verified no new files appeared under the real /home/ubuntu/amphora/build/mvp20-split/.amphora/{receipts,control} during this study; both isolated roots (runA, runB) live entirely under /tmp and are scratch, not part of the tracked repository.",
        "candidate_id_held_constant": "Envelope-65-black-leaktest",
        "injected_key": "canonical_structure_hash",
        "runA": canon,
        "runB": runB,
        "two_replay_comparison": two_replay,
    },

    "does_not_close": [
        "Whether any downstream consumer reads shadow-tier receipt PAYLOAD/CONTENT (candidate_id, "
        "artifact_hashes, or embedded metrics) directly -- bypassing PromotionPolicyV1::authority_for() "
        "-- for any purpose (dashboards, provenance indexing, dedup) is not evaluated; only the "
        "authority-ceiling clamp mechanism itself was confirmed load-bearing by call-site grep "
        "(amphora-core/src/molecule_evidence.rs), not by tracing every consumer of persisted receipts.",
        "Only the single top-level-key vector (canonical_structure_hash) was tested here, chosen for "
        "direct comparability with T-01B and normalized-formulation-shadow-consumer-v1; the other 7 of "
        "T-01's original 8 vector shapes were not re-run against shadow_run specifically.",
        "Repair is out of scope for this AUDIT_ONLY receipt: amphora-cli/src/control.rs shadow_run "
        "remains unpatched.",
        "No promotion, no manifest edit, no scientific_readiness flip, no wet-lab, qualification, or "
        "release authority.",
    ],

    "founder_directive_done_criteria_verbatim": "All eight vectors rejected or ignored; identity recomputed from host graph; no candidate value reaches a typed downstream field.",
    "founder_directive_done_criteria_met": False,
    "founder_directive_done_criteria_met_note": (
        "FALSE for the shadow_run path: a candidate-injected top-level key (canonical_structure_hash) "
        "reaches the artifact_hashes/result_hash of a real, persisted, Ed25519-signed "
        "EvaluationReceiptV1, live-reproduced end-to-end via the actual production CLI binary, "
        "byte-stable across two independent replays."
    ),

    "results": {
        "leak_confirmed_runA": canon["leak_confirmed"],
        "leak_confirmed_runB": runB["leak_confirmed"],
        "both_receipts_ed25519_verified_runA": canon["both_receipts_ed25519_verified"],
        "both_receipts_ed25519_verified_runB": runB["both_receipts_ed25519_verified"],
        "candidate_id_held_constant": True,
        "two_replay_payload_identical_excl_local_dev_identity": two_replay["two_replay_payload_identical_excl_local_dev_identity"],
    },

    "reproducibility": {
        "byte_identical": True,
        "scope": "Receipt DSSE payload (all content except the per-isolated-root random local dev-identity signing key) is byte-identical across two fully independent isolated-workspace replays.",
        "canonical_diagnostic_sha256": sha_file(BENCH / "diagnostic.canonical.json"),
        "runB_diagnostic_sha256": sha_file(BENCH / "diagnostic.runB.json"),
        "two_replay_sha256_gate": "PASS",
        "replay_method": "Run shadow_isolation_setup.sh twice against two fresh /tmp roots (fresh cargo build, fresh /dev/urandom local dev-identity each time), run `amphora-tui shadow run` on the same clean/poison candidate files in each, diff the persisted receipts' DSSE payload bytes.",
    },

    "source_hashes": {
        "amphora-cli/src/control.rs": sha_file(ROOT / "amphora-cli/src/control.rs"),
        "amphora-cli/src/main.rs": sha_file(ROOT / "amphora-cli/src/main.rs"),
        "amphora-core/src/artifacts.rs": sha_file(ROOT / "amphora-core/src/artifacts.rs"),
        "amphora-core/src/crypto.rs": sha_file(ROOT / "amphora-core/src/crypto.rs"),
        "amphora-engine/src/lib.rs": sha_file(ROOT / "amphora-engine/src/lib.rs"),
    },
    "harness_sha256": {
        "shadow_isolation_setup.sh": sha_file(BENCH / "shadow_isolation_setup.sh"),
    },

    "finding": (
        "The remaining does_not_close item of normalized-formulation-shadow-consumer-v1 is closed: "
        "`amphora-tui shadow run`, a real, currently-shipped, lane-unrestricted CLI path, was "
        "independently, live, end-to-end re-run (not merely source-cited) against a fully isolated "
        "workspace and confirmed to persist a real Ed25519-signed EvaluationReceiptV1 whose content "
        "(artifact_hashes/result_hash) is altered by an attacker-injected top-level candidate key, "
        "reproducibly across two independent replays, with candidate_id held constant. This graduates "
        "the prior fire's citation-only reachability claim to a live-proven one. Separately, the "
        "receipt's decision_use_ceiling=SHADOW / evidence_tier=SYNTHETIC_DIAGNOSTIC fields mechanically "
        "cap its authority via PromotionPolicyV1::authority_for() (confirmed load-bearing, not dead "
        "code) -- so this is a confirmed data-integrity leak into a real signed artifact, not a "
        "confirmed authority-escalation path."
    ),
    "verdict": "REFUTED",

    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_derives_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.candidate-contract-shadow-run-live-reachability+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

AUDIT_DIR.mkdir(parents=True, exist_ok=True)
out = AUDIT_DIR / "shadow-run-live-reachability-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
