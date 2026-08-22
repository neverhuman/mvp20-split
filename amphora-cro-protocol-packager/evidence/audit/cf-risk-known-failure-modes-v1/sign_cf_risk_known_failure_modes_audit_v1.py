#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-RISK known-
failure-modes/application-limits/mitigations audit receipt, fire 1/2
(campaign item CF-RISK, founder directive AMPHORA-DIRECTIVE-2026-08-09 S7,
obligation CF-RISK, max_fires=2).

AUDIT_ONLY. Verdict CLAIM_REFUTED: no dedicated known-failure-modes /
application-limits / mitigations section exists anywhere in this module
for any of the 4 required risks (pinholing, wetting, film_build,
pot_life); the CRO test plan's own kill/acceptance gates mention pot life
and pinhole only as lab reject-rules, not as application-limit-parameter
+ mitigation guidance. Filed into evidence/phase0/repairs/CF-RISK/attempts/
(NOT done/ -- the done_criterion is not met).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-risk-known-failure-modes-v1"
ATTEMPTS_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-RISK/attempts"
WORK_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-RISK/work"
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
assert diag["refutation_criterion_observed"] is True
assert diag["part2_checker_discriminating_power_control"]["checker_detects_dropped_pot_life_mitigation"] is True
harness_sha = sha((BENCH / "run_cf_risk_known_failure_modes_audit_v1.py").read_bytes())

# --- derive public key / key_id from on-host seed ---------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.cro-protocol-packager.cf-risk-known-failure-modes-audit-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-RISK",
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
    "modifies_mission_prose": True,
    "claim_under_attack": diag["claim_under_attack"],
    "attack_shape_verbatim": diag["attack_shape_verbatim"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observed": diag["refutation_criterion_observed"],
    "deliverable_under_test": diag["deliverable_under_test"],
    "part1_real_corpus_scan": diag["part1_real_corpus_scan"],
    "part2_checker_discriminating_power_control": diag["part2_checker_discriminating_power_control"],
    "finding": diag["finding"],
    "notes_on_related_but_distinct_material": diag["notes_on_related_but_distinct_material"],
    "verdict": "CLAIM_REFUTED",
    "repair_status": "in_progress",
    "campaign_item_status": "pending",
    "campaign_item_disposition": (
        "Fire 1/2 for CF-RISK. Zero of the 4 required failure-mode entries "
        "(pinholing, wetting, film_build, pot_life) exist anywhere in the "
        "module as an application-limit-parameter + mitigation pair; only "
        "the CRO test plan's own lab kill/acceptance gates mention pot "
        "life and pinhole, and those are reject-rules for the screening "
        "study, not field application guidance. Repair for a future "
        "CF-RISK fire (max_fires=2): add a real 'Known failure modes, "
        "application limits, mitigations' section (e.g. to "
        "reference/mvp20/out/cro_protocol.md, this module's own write "
        "scope) with one entry per required risk carrying: (a) the "
        "application-limit parameter of THIS RECIPE most likely to be "
        "exceeded, with a cited numeric threshold and its physical "
        "rationale; (b) a concrete field mitigation an applicator would "
        "act on; and (c) for any element the engine genuinely cannot "
        "defend from existing evidence, an honest 'cannot defend' flag "
        "plus a named resolving experiment instead of a guessed "
        "mitigation. The synthetic_compliant_section in this receipt's "
        "part2 is a starting draft, not a citation-backed final answer -- "
        "the repair fire must ground each parameter/threshold in a real "
        "citation (envelope v5_requirements.json, MIL-DTL-24441/38A, "
        "ASTM/SSPC method, or an honestly-flagged assumption) the way "
        "cro_protocol.md's existing MEASURED/MODELED/ASSUMED tagging "
        "does, not restate this receipt's placeholder text verbatim."
    ),
    "does_not_close": (
        "This receipt does not repair the deliverable. It establishes the "
        "truthful current state: no known-failure-modes/application-"
        "limits/mitigations section exists for CF-RISK's 4 required "
        "risks, and demonstrates (via a synthetic compliant section plus "
        "the literal drop-the-pot-life-mitigation attack) that the "
        "checker built to evaluate such a section, once it exists, has "
        "real discriminating power."
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
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/ and evidence/phase0/repairs/CF-RISK/attempts/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cro-protocol-packager-cf-risk-known-failure-modes-audit+json"
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

out = BENCH / "cf-risk-known-failure-modes-audit-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
attempts_out = ATTEMPTS_DIR / "cf-risk-known-failure-modes-audit-receipt.v1.dsse.json"
attempts_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

WORK_DIR.mkdir(parents=True, exist_ok=True)
state = {
    "campaign_item_id": "CF-RISK",
    "last_fire_sequence": 1,
    "last_verdict": "CLAIM_REFUTED",
    "max_fires": 2,
    "missing_or_unqualified_risks": diag["part1_real_corpus_scan"]["missing_or_unqualified_risks"],
    "next_fire_should": (
        "REPAIR MODE for fire 2/2: add a real 'Known failure modes, "
        "application limits, mitigations' section to "
        "reference/mvp20/out/cro_protocol.md (in-scope write target) "
        "covering pinholing, wetting, film_build and pot_life, each with "
        "a cited application-limit parameter + numeric threshold + "
        "mitigation, OR an honest cannot-defend flag + named resolving "
        "experiment where the engine genuinely lacks evidence. Ground "
        "every parameter in a real citation (envelope v5_requirements.json, "
        "MIL-DTL-24441/38A, cited ASTM/SSPC method) using the same "
        "MEASURED/MODELED/ASSUMED confidence tagging already used "
        "elsewhere in cro_protocol.md -- do not restate this fire's "
        "synthetic_compliant_section placeholder text verbatim, it is a "
        "structural draft only. Then RE-RUN this exact checker (same "
        "script sha256 below, same command) as the acceptance test -- "
        "verdict = truthful CURRENT state, CLAIM_SURVIVED only if all 4 "
        "risks pass, else CLAIM_REFUTED with repair_status reflecting "
        "partial progress. Do NOT repeat this fire's byte-identical "
        "reconfirm with no new information."
    ),
    "harness_script_sha256": harness_sha,
    "deliverable_shas_at_this_fire": diag["deliverable_under_test"],
}
(WORK_DIR / "STATE.json").write_text(json.dumps(state, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
pk.verify(base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["payload"])))

print("WROTE", out)
print("WROTE", attempts_out)
print("WROTE", WORK_DIR / "STATE.json")
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
