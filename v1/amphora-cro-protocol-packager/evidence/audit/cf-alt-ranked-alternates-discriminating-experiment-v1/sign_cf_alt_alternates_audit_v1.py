#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-ALT ranked-
alternates / discriminating-experiment audit receipt, fire 1/2 (campaign
item CF-ALT, founder directive AMPHORA-DIRECTIVE-2026-08-09 S7, obligation
CF-ALT, max_fires=2).

AUDIT_ONLY. Finds this module's own carried-candidate corpus
(reference/mvp20/out/capture_template.json) ships THREE evidence-
indistinguishable candidates (M00097/M00101/M00109, all CRO-GATED/
"demoted (card FAIL)" corrosion rank, identical mix ratio/stoichiometry/
solids) with NO named discriminating experiment keyed to any of the three
pairs -- the corpus's one named experiment (key_pairwise: Enhanced-65 >
Envelope-65) is keyed to a different, uncross-walked ID namespace.
CLAIM_REFUTED. Positive control (stripping the resolution for exactly the
M00101/M00109 pair on a synthetic fully-repaired copy) and discrimination
control (the same fully-repaired copy resolving to zero unresolved pairs)
both pass, confirming the checker genuinely discriminates.

Filed into evidence/phase0/repairs/CF-ALT/attempts/ (NOT done/ -- the
done_criterion is not met: no repair has landed this fire).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-alt-ranked-alternates-discriminating-experiment-v1"
ATTEMPTS_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-ALT/attempts"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


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


# --- two-replay gate --------------------------------------------------------
canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["verdict"] == "CLAIM_REFUTED"
assert diag["step_4_discrimination_control"]["discrimination_control_passed"] is True
assert diag["step_5_positive_control"]["detected"] is True
harness_sha = sha((BENCH / "run_cf_alt_alternates_audit_v1.py").read_bytes())

# --- derive public key / key_id from on-host seed ---------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))

unresolved = diag["step_3_real_corpus_unresolved_pairs"]["unresolved_evidence_indistinguishable_pairs"]
n_unresolved = diag["step_3_real_corpus_unresolved_pairs"]["n_unresolved"]

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.cro-protocol-packager.cf-alt-alternates-audit-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-ALT",
    "run_type": "falsification_attack",
    "fire_sequence": 1,
    "final_fire_for_item": False,
    "directive_path": diag["directive_path"],
    "directive_sha256": diag["directive_sha256"],
    "directive_obligation": diag["directive_obligation"],
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_front_matter": False,
    "modifies_mission_prose": False,
    "claim_under_attack": diag["claim_under_attack"],
    "deliverable_under_test": diag["deliverable_under_test"],
    "deliverable_sha256": diag["deliverable_sha256"],
    "cross_module_context_read_only": diag["cross_module_context_read_only"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "attack_shape_verbatim": diag["attack_shape_verbatim"],
    "step_1_carried_candidates": diag["step_1_carried_candidates"],
    "step_2_named_discriminating_experiments_in_real_corpus": diag["step_2_named_discriminating_experiments_in_real_corpus"],
    "step_3_real_corpus_unresolved_pairs": diag["step_3_real_corpus_unresolved_pairs"],
    "step_4_discrimination_control": diag["step_4_discrimination_control"],
    "step_5_positive_control": diag["step_5_positive_control"],
    "refutation_criterion_observed": (
        f"OBSERVED: {n_unresolved} pair(s) of evidence-indistinguishable "
        "candidates ship without ranked alternates and a named "
        "discriminating experiment: " + json.dumps(unresolved) + ". This "
        "directly instantiates the pre-committed refutation criterion "
        "verbatim ('" + diag["refutation_criterion_verbatim"] + "')."
    ),
    "finding": (
        "CLAIM_REFUTED (fire 1/2): this module's own carried-candidate "
        "corpus (reference/mvp20/out/capture_template.json, sha256 "
        + diag["deliverable_sha256"] + ") lists three candidates in its "
        "top-level 'candidates' array -- M00097, M00101, M00109 -- and by "
        "the corpus's OWN tier labels all three share an identical "
        "CRO-GATED / 'demoted (card FAIL)' corrosion-rank tier (i.e. the "
        "corpus itself asserts no validated model can rank any pair of "
        "them) plus identical mix_ratio_by_volume (1.0), stoichiometric_"
        "ratio (0.7) and volume_solids_pct (65.0), with pvc_pct differing "
        "by well under 1 percentage point across all three pairs -- this "
        "module's own operational definition of 'evidence cannot "
        "distinguish'. The corpus DOES name one discriminating experiment "
        "(statistical_decision_rules.key_pairwise: 'the Enhanced-65 > "
        "Envelope-65 non-obvious call', mirrored in falsification_protocol"
        ".json's key_pairwise_bet), but it is keyed to a different ID "
        "namespace (Lineage-60/Envelope-65/Enhanced-65/CRO-Robust-65 track "
        "names) than the M00-series ids this module's own candidates list "
        "uses, and no structured, machine-checkable crosswalk file exists "
        "anywhere in the repo connecting the two namespaces -- only one "
        "prose sentence in amphora-report-packager's blueprint.md ties "
        "M00097 to 'Envelope-65'. M00101 and M00109 are never tied to any "
        "track name anywhere in the four files searched, so the named "
        "experiment cannot be verified to resolve the M00101-vs-M00109 "
        "pair, and it does not resolve the M00097-vs-M00101 or M00097-vs-"
        "M00109 pairs either since neither of those alternates is named as "
        "a track. Separately, the zinc-phosphate 'functional variant' "
        "M00098 (which blueprint prose implies IS the Enhanced-65 track) "
        "is entirely ABSENT from this module's own candidates list and "
        "prediction_ledger -- an internal inconsistency in this module's "
        "own carried-candidate bookkeeping, independent of the cross-"
        "module ownership question. Additionally, two further companion "
        "files this module's own capture_template.json cites by relative "
        "path (falsification_protocol_path -- present; power_analysis_path "
        "-- ABSENT) and blueprint.md cites for the alternates themselves "
        "(funnel_results.json -- ABSENT anywhere in the repo, consistent "
        "with CF-BOM's prior independent finding of the same gap) do not "
        "exist, so even the informal alternates ranking blueprint.md "
        "gestures at (M00101, M00109, functional variant M00098) has no "
        "backing file at all. Positive control: stripping the named-"
        "experiment resolution for exactly the M00101-vs-M00109 pair on a "
        "synthetic fully-repaired copy causes the SAME checker to re-flag "
        "exactly that pair and only that pair (detected="
        + str(diag["step_5_positive_control"]["detected"]) + "). "
        "Discrimination control: the same fully-repaired copy (every "
        "evidence-indistinguishable pair given an explicit pair-keyed "
        "named discriminating experiment) causes the SAME checker to "
        "report zero unresolved pairs (discrimination_control_passed="
        + str(diag["step_4_discrimination_control"]["discrimination_control_passed"])
        + "), so the checker genuinely discriminates rather than being "
        "hard-wired to always refute."
    ),
    "verdict": "CLAIM_REFUTED",
    "repair_status": "not_attempted",
    "campaign_item_status": "pending",
    "campaign_item_disposition": (
        "Fire 1/2 for CF-ALT. Unlike CF-BOM, the core gap identified here "
        "(no pair-keyed M00-series crosswalk to a named discriminating "
        "experiment; M00098 missing from this module's own candidates "
        "list) is at least partially repairable from WITHIN amphora-cro-"
        "protocol-packager's own write scope, since capture_template.json "
        "is this module's own file (unlike blueprint.md/funnel_results.json "
        "which remain owned by amphora-report-packager). A fire-2 repair "
        "attempt should: (a) add an explicit, structured id-to-track-name "
        "crosswalk section to capture_template.json; (b) add pair-keyed "
        "discriminating-experiment entries for the M00097/M00101/M00109 "
        "pairs, reusing falsification_protocol.json's existing decisive-"
        "pair protocol construction where the track mapping allows, and "
        "naming a new pairwise test explicitly where it does not; (c) "
        "resolve the M00098-in-candidates-list inconsistency (either add "
        "it with its own tier entry, or state explicitly why it is "
        "excluded from the CRO capture round); (d) re-run this fire's "
        "checker (script sha256 below) as the acceptance test, superseding "
        "-- never rewriting -- this receipt if it changes verdict. The "
        "funnel_results.json / power_analysis.json absence remains a "
        "cross-module or genuinely-not-yet-produced gap outside this "
        "module's sole authority to close."
    ),
    "does_not_close": (
        "This receipt does not repair the deliverable. It establishes, "
        "with a positive control and a discrimination control, that this "
        "module's own carried-candidate corpus currently ships an evidence-"
        "indistinguishable candidate set without a pair-keyed named "
        "discriminating experiment, which directly instantiates CF-ALT's "
        "pre-committed refutation criterion."
    ),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "diagnostic_script_sha256": harness_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/ and evidence/phase0/repairs/CF-ALT/attempts/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cro-protocol-packager-cf-alt-alternates-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}

out = BENCH / "cf-alt-ranked-alternates-discriminating-experiment-audit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
attempts_out = ATTEMPTS_DIR / "cf-alt-ranked-alternates-discriminating-experiment-audit-receipt.v1.dsse.json"
attempts_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
pk.verify(base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["payload"])))

print("WROTE", out)
print("WROTE", attempts_out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
