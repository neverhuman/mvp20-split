#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-RISK repair
receipt, fire 2/2 (campaign item CF-RISK, founder directive
AMPHORA-DIRECTIVE-2026-08-09 S7, obligation CF-RISK, max_fires=2, final
fire for this item).

Fire 1 (CLAIM_REFUTED) found zero of the 4 required known-failure-mode
entries (pinholing, wetting, film_build, pot_life) anywhere in the module.
This fire adds a real 'Known failure modes and application limits'
section to reference/mvp20/out/cro_protocol.md (this module's own write
scope) -- one entry per required risk, each citing a real published
standard/law or this document's own already-cited envelope/MIL values,
using MEASURED/MODELED/ASSUMED confidence tagging consistent with the
rest of the document, and explicitly flagging (with a named resolving
experiment) the two sub-parameters the engine cannot fully defend from
existing evidence (the recipe-specific pinhole WFT threshold, and the
recipe-specific soluble-salt tolerance) rather than guessing a number.

Then re-runs the SAME unmodified checker fire 1 used
(run_cf_risk_known_failure_modes_audit_v1.py, sha256
252f3566092b024b2299d670423ad37cd3b831f035c1af12b4fa52522994c673) against
the repaired corpus as the acceptance test, per REPAIR MODE rule 2.

Beyond that checker's own built-in Part-2 self-test (which validates its
own discriminating power against an ISOLATED synthetic dict, not the real
document), this fire runs a STRONGER positive control directly against
the actual repaired reference/mvp20/out/cro_protocol.md: it deletes each
of the 4 risks' own real mitigation sentence, one at a time, from a copy
of the real on-disk text, and re-applies the checker's own regex-window
scan logic to confirm detection localizes correctly (only the deleted
risk fails; the other 3 remain passing). This was necessary because an
early draft of this section passed the checker's synthetic self-test but
FAILED this real-document control (adjacent-section text leaked into the
±400-char detection window, letting 3 of 4 risks silently survive their
own mitigation being deleted) -- the final section text below was
restructured (explicit inter-entry boundaries, a second risk-name mention
directly beside each mitigation sentence) specifically to close that gap
before this receipt was signed.
"""
import base64, copy, hashlib, json, re
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cro-protocol-packager"
BENCH = MOD / "evidence/audit/cf-risk-known-failure-modes-v1"
DONE_DIR = MOD / "evidence/phase0/repairs/CF-RISK/done"
ATTEMPTS_DIR = MOD / "evidence/phase0/repairs/CF-RISK/attempts"
WORK_DIR = MOD / "evidence/phase0/repairs/CF-RISK/work"
OUT = MOD / "reference/mvp20/out"
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


# --- two-replay gate (post-repair re-run of the UNCHANGED v1 checker) -------
canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["verdict"] == "CLAIM_SURVIVED"
assert diag["refutation_criterion_observed"] is False
assert diag["part1_real_corpus_scan"]["missing_or_unqualified_risks"] == []
assert diag["part2_checker_discriminating_power_control"]["checker_detects_dropped_pot_life_mitigation"] is True
harness_sha = sha((BENCH / "run_cf_risk_known_failure_modes_audit_v1.py").read_bytes())
assert harness_sha == "252f3566092b024b2299d670423ad37cd3b831f035c1af12b4fa52522994c673", \
    "checker script changed -- not the same acceptance test as fire 1"

# --- STRONGER positive control: run the checker's own regex-window logic
# directly against the REAL repaired cro_protocol.md, deleting each risk's
# own real mitigation sentence one at a time from a copy, and confirming
# detection localizes correctly (only that risk fails; the other 3 hold).
RISK_WORD_RE = {
    "pinholing": re.compile(r"pinhol", re.IGNORECASE),
    "wetting": re.compile(r"\bwetting\b|non-?wetting|dewetting", re.IGNORECASE),
    "film_build": re.compile(r"film[ _-]?build", re.IGNORECASE),
    "pot_life": re.compile(r"pot[ _-]life", re.IGNORECASE),
}
MITIGATION_WORD_RE = re.compile(r"\bmitigat", re.IGNORECASE)
PARAM_FRAMING_RE = re.compile(
    r"exceed|threshold|application[- ]limit|\bmax(imum)?\b|\bmin(imum)?\b|"
    r"\d+(\.\d+)?\s*(mil|h|min|%|°?[FC]|g/L)",
    re.IGNORECASE,
)


def structured_entries_in_text(text):
    found = {}
    for risk, word_re in RISK_WORD_RE.items():
        found[risk] = {"present": False, "has_param_framing": False, "has_mitigation": False}
        for m in word_re.finditer(text):
            lo, hi = max(0, m.start() - 400), min(len(text), m.end() + 400)
            window = text[lo:hi]
            found[risk]["present"] = True
            if PARAM_FRAMING_RE.search(window):
                found[risk]["has_param_framing"] = True
            if MITIGATION_WORD_RE.search(window):
                found[risk]["has_mitigation"] = True
    return found


def qualifies(scan, risk):
    e = scan[risk]
    return bool(e["present"] and e["has_param_framing"] and e["has_mitigation"])


real_text = (OUT / "cro_protocol.md").read_text()

MITIGATION_SENTENCES = {
    "pinholing": "Mitigation for pinholing meanwhile: hold WFT in the 7-9 mil band via gauge checks every pass, "
                 "avoid thin trailing edges, allow inter-coat flash-off.",
    "wetting": "Mitigation for wetting meanwhile: verify >=3C dew-point margin and a salt-test pass before "
               "coating; stop-work (DEV-PREP) on either failure.",
    "film_build": "Mitigation for film build: verify DFT per panel via SSPC-PA 2 style grid; split heavy builds "
                  "into multiple passes on vertical/overhead runs to stay inside the sag envelope.",
    "pot_life": "Mitigation for pot life: batch mixed material to the 90-min window at the FIELD temperature "
                "actually measured, not an assumed 73F; use smaller kits in hot conditions; discard on KU "
                "stop-rule breach rather than force-apply over-pot material.",
}

real_doc_scan = structured_entries_in_text(real_text)
real_doc_all_pass = all(qualifies(real_doc_scan, r) for r in RISK_WORD_RE)
assert real_doc_all_pass, "real repaired document does not pass 4/4 on its own -- do not sign"

per_risk_deletion_results = {}
for risk, sent in MITIGATION_SENTENCES.items():
    assert sent in real_text, f"mitigation sentence for {risk} not found verbatim in real document"
    mutated = real_text.replace(sent, "")
    assert mutated != real_text
    scan = structured_entries_in_text(mutated)
    per_risk = {r: qualifies(scan, r) for r in RISK_WORD_RE}
    localized_correctly = (per_risk[risk] is False) and all(per_risk[r] is True for r in RISK_WORD_RE if r != risk)
    per_risk_deletion_results[risk] = {
        "deleted_sentence": sent,
        "per_risk_pass_after_deletion": per_risk,
        "target_risk_now_fails": per_risk[risk] is False,
        "other_3_risks_unaffected": all(per_risk[r] is True for r in RISK_WORD_RE if r != risk),
        "localized_correctly": localized_correctly,
    }
    assert localized_correctly, f"deleting {risk}'s mitigation did not localize correctly -- do not sign"

real_document_positive_control_passed = all(v["localized_correctly"] for v in per_risk_deletion_results.values())

positive_control = {
    "planted_defect": "deleted the pot-life mitigation sentence from a copy of the REAL, repaired "
                       "reference/mvp20/out/cro_protocol.md (the literal attack shape the directive names: "
                       "'drop the pot-life mitigation from a copy and attack whether the check fires')",
    "how_planted": "cro_protocol.md text, exact-string removal of: "
                   f"\"{MITIGATION_SENTENCES['pot_life']}\"",
    "detected": bool(per_risk_deletion_results["pot_life"]["target_risk_now_fails"]),
    "evidence": (
        "Re-applying the checker's own risk-word/param-framing/mitigation-word regex-window scan (±400 chars "
        "per occurrence) to the mutated copy: pot_life now fails "
        f"(present={per_risk_deletion_results['pot_life']['per_risk_pass_after_deletion']['pot_life']}) while "
        "pinholing, wetting and film_build all remain passing "
        f"({per_risk_deletion_results['pot_life']['per_risk_pass_after_deletion']}), i.e. the attack fires on "
        "the planted defect and localizes to exactly the risk it was planted in. On the REAL unmutated document "
        f"all 4 risks pass (no false fire): {real_doc_scan and {r: qualifies(real_doc_scan, r) for r in RISK_WORD_RE}}."
    ),
    "extended_verification": (
        "The same real-document deletion test was independently repeated for the other 3 risks "
        "(pinholing, wetting, film_build), each deleted one at a time from its own copy of the real document: "
        "in every case only the targeted risk fails and the other 3 remain passing "
        "(see repair_actions[1].per_risk_real_document_deletion_results below). This is a stronger control than "
        "the checker's own built-in Part-2 self-test, which only validates its regex logic against an isolated "
        "synthetic dict with no surrounding prose -- an earlier draft of this section passed that synthetic "
        "self-test while FAILING this real-document control (adjacent-section text leaked into the detection "
        "window), which is why the section text below was restructured before this receipt was signed."
    ),
}

repair_actions = [
    {
        "action": "added a 'Known failure modes and application limits' section to "
                  "reference/mvp20/out/cro_protocol.md with one entry per required risk "
                  "(pinholing, wetting, film_build, pot_life)",
        "citations_used": [
            "SSPC-PA 2 (Procedure for Determining Conformance to Dry Coating Thickness Requirements) / "
            "ASTM D4414 (WFT gauge) -- same methods already cited in this document's own acceptance matrix",
            "SSPC-PA 1 / ASTM D3276 (painting-inspection dew-point/substrate-condition guidance) -- published, "
            "recipe-independent industry standard",
            "NACE SP0508 / ISO 8502-6 (soluble-salt test methods)",
            "Crank, J. (1975). The Mathematics of Diffusion, 2nd ed., Oxford University Press. "
            "ISBN 0-19-853411-6 -- Fickian diffusion law grounding the film-build under-cure/barrier-thickness "
            "relationship",
            "This document's own already-cited MIL-DTL-24441/38A Formula 160 pot-life value and D562 KU-vs-time "
            "test (self-citation, not a new source)",
        ],
        "honest_holes_flagged": [
            {
                "risk": "pinholing",
                "cannot_defend": "the exact WFT value at which pinhole-defect probability becomes unacceptable "
                                  "for THIS specific resin/solvent/pigment blend -- no defect-rate-vs-WFT panel "
                                  "study exists in the receipt corpus; the ~6 mil figure used is a generic "
                                  "SSPC-PA 2 rule-of-thumb, not a recipe-specific measurement",
                "resolving_experiment": "bench-scale WFT ramp panel series (5 levels spanning 4-11 mil, "
                                         "triplicate panels, blind raking-light pinhole count) to fit an "
                                         "empirical defect-rate curve",
            },
            {
                "risk": "wetting",
                "cannot_defend": "the numeric soluble-salt threshold for THIS recipe's service environment -- "
                                  "the ~50 mg/m^2 figure sometimes quoted in informal field guidance for "
                                  "critical-immersion service is not independently validated against this "
                                  "recipe's own blister-onset data",
                "resolving_experiment": "commissioned blister-onset panel series at 3-4 residual-chloride "
                                         "levels (Bresle-patch dosed panels, cyclic B117/D1654 exposure); "
                                         "until measured, any nonzero soluble-salt failure is treated as a "
                                         "stop-work deviation (DEV-PREP) rather than a numeric pass/fail gate",
            },
        ],
        "per_risk_real_document_deletion_results": per_risk_deletion_results,
    },
]

# --- derive public key / key_id from on-host seed ---------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))

# --- receipt body -------------------------------------------------------------
body_obj = {
    "schema": "amphora.cro-protocol-packager.cf-risk-known-failure-modes-repair-receipt.v2",
    "study_id": "cf-risk-known-failure-modes-audit-v1-fire2",
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-RISK",
    "run_type": "repair_and_reverify",
    "fire_sequence": 2,
    "final_fire_for_item": True,
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207",
    "directive_obligation": "CF-RISK",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_front_matter": False,
    "modifies_mission_prose": True,
    "claim_under_attack": (
        "The current CF-RISK deliverable state is complete and accurate for its scope "
        "(finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "attack_shape_verbatim": (
        "Drop the pot-life mitigation from a copy and attack whether the check fires; hunt for a named risk "
        "with no exceeded-parameter or no mitigation."
    ),
    "refutation_criterion_verbatim": (
        "No failure-mode entry exists for pinholing, wetting, film-build or pot-life, or a named risk lacks "
        "the application-limit parameter most likely exceeded and its mitigation."
    ),
    "refutation_criterion_observed": diag["refutation_criterion_observed"],
    "prior_fire": {
        "fire_sequence": 1,
        "verdict": "CLAIM_REFUTED",
        "receipt": "amphora-cro-protocol-packager/evidence/audit/cf-risk-known-failure-modes-v1/"
                   "cf-risk-known-failure-modes-audit-receipt.v1.dsse.json",
        "missing_or_unqualified_risks_found": ["pinholing", "wetting", "film_build", "pot_life"],
        "status": "remains the true historical record of the pre-repair state; NOT superseded, only built upon "
                   "(the deliverable itself changed, not the fact that fire 1's finding was correct when made)",
    },
    "repair_mode": {
        "rule_applied": "REPAIR MODE (objective explicitly invokes it despite item id not carrying an R-/V- "
                        "prefix): supersede-never-rewrite (n/a here -- no signed artifact was rewritten, only "
                        "the underlying deliverable file cro_protocol.md the item's done_criterion is about, "
                        "which is this module's own write scope); re-attack own fix with SAME script sha256, "
                        "same command; done receipt filed into done/ because the acceptance criterion is met.",
        "acceptance_test": "re-ran evidence/audit/cf-risk-known-failure-modes-v1/"
                           "run_cf_risk_known_failure_modes_audit_v1.py UNCHANGED (sha256 verified equal to "
                           "fire 1's pinned harness sha256) against the repaired corpus, twice, byte-identical "
                           "both times",
        "acceptance_test_script_sha256": harness_sha,
    },
    "repair_actions": repair_actions,
    "positive_control": positive_control,
    "deliverable_under_test": {
        **diag["deliverable_under_test"],
    },
    "part1_real_corpus_scan": diag["part1_real_corpus_scan"],
    "part2_checker_discriminating_power_control": diag["part2_checker_discriminating_power_control"],
    "finding": (
        "CLAIM_SURVIVED (repaired). A real 'Known failure modes and application limits' section now exists in "
        "reference/mvp20/out/cro_protocol.md with a fully-qualifying entry (application-limit parameter most "
        "likely exceeded + numeric threshold + mitigation) for all 4 required risks (pinholing, wetting, "
        "film_build, pot_life); re-running the SAME unmodified fire-1 checker confirms "
        "missing_or_unqualified_risks=[] and refutation_criterion_observed=false, byte-identical across two "
        "independent runs. Beyond the checker's own synthetic self-test, this fire's positive_control ran the "
        "literal directive attack (delete the pot-life mitigation from a copy) directly against the REAL "
        "repaired document, and separately repeated the same deletion for the other 3 risks: in every case "
        "detection localizes correctly to exactly the risk whose mitigation was deleted, with no false fire on "
        "the other 3 and no false pass on the real, unmutated document. Two sub-parameters (the recipe-specific "
        "pinhole WFT threshold and the recipe-specific soluble-salt tolerance) are explicitly flagged as "
        "CANNOT FULLY DEFEND with a named resolving experiment, per the done_criterion's own instruction that "
        "an honest hole is compliant and a confident-looking guess is not."
    ),
    "verdict": "CLAIM_SURVIVED",
    "repair_status": "fix_landed_survived",
    "campaign_item_status": "done",
    "campaign_item_disposition": (
        "Fire 2/2 (final fire, max_fires=2) for CF-RISK. All 4 required risks now carry a fully-qualifying "
        "known-failure-mode entry, grounded in real citations (SSPC-PA 1/2, ASTM D3276/D4414, NACE SP0508/ISO "
        "8502-6, Crank 1975, and this document's own already-cited MIL-DTL-24441/38A + D562 values) with "
        "MEASURED/MODELED/ASSUMED confidence tagging consistent with the rest of cro_protocol.md. Two "
        "sub-parameters are honestly flagged as undefended with named resolving experiments rather than guessed. "
        "done_criterion met: signed receipt filed to evidence/phase0/repairs/CF-RISK/done/."
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
        "used_for": "AUDIT_ONLY repair receipt under evidence/audit/ and evidence/phase0/repairs/CF-RISK/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cro-protocol-packager-cf-risk-known-failure-modes-repair-receipt+json"
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

out = BENCH / "cf-risk-known-failure-modes-repair-receipt.v2.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

DONE_DIR.mkdir(parents=True, exist_ok=True)
done_out = DONE_DIR / "cf-risk-known-failure-modes-repair-receipt.v2.dsse.json"
done_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
attempts_out = ATTEMPTS_DIR / "cf-risk-known-failure-modes-repair-receipt.v2.dsse.json"
attempts_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

WORK_DIR.mkdir(parents=True, exist_ok=True)
state = {
    "campaign_item_id": "CF-RISK",
    "last_fire_sequence": 2,
    "last_verdict": "CLAIM_SURVIVED",
    "max_fires": 2,
    "final_fire_for_item": True,
    "missing_or_unqualified_risks": [],
    "harness_script_sha256": harness_sha,
    "deliverable_shas_at_this_fire": {
        str(p.relative_to(MOD)): sha(p.read_bytes())
        for p in [
            MOD / "README.md", MOD / "docs/capability-profile.json", MOD / "docs/mission.md",
            MOD / "docs/moonshot.md", MOD / "reference/mvp20/out/capture_template.json",
            MOD / "reference/mvp20/out/cro_protocol.md", MOD / "reference/mvp20/out/falsification_protocol.json",
            MOD / "reference/mvp20/out/power_analysis.json",
        ] if p.exists()
    },
    "done_receipt": "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-RISK/done/"
                    "cf-risk-known-failure-modes-repair-receipt.v2.dsse.json",
    "next_fire_should": "none -- done_criterion met, item closed",
}
(WORK_DIR / "STATE.json").write_text(json.dumps(state, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
pk.verify(base64.standard_b64decode(json.loads(done_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(done_out.read_text())["signature"]["payload"])))
pk.verify(base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["payload"])))

print("WROTE", out)
print("WROTE", done_out)
print("WROTE", attempts_out)
print("WROTE", WORK_DIR / "STATE.json")
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
print("real_document_positive_control_passed", real_document_positive_control_passed)
