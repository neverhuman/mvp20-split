#!/usr/bin/env python3
"""Signs the EHS-REDCHEM done receipt: mechanical audit of whether this
module's regression coverage actually exercises the content-level red-team
axes docs/mission.md's "Red-team dossier" section commits to (malformed
chemistry; mixtures, fragments, polymers; unit ambiguity; zero-mass
ingredients; NaN/Infinity; out-of-domain inputs; group/source/time leakage;
mutated sources; computed-as-measured; spoofed identity; stripped/unknown
claim locks; authority escalation). AUDIT_ONLY. Does not modify any KPI,
gate, or procurement outcome; does not touch mission.md front-matter or the
manifest.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
ITEM_DIR = MOD / "evidence/phase0/audits/EHS-REDCHEM"
WORK = ITEM_DIR / "work"

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = json.loads((ROOT / "config/phase0-trust-store.v1.json").read_text())

OUT_PATH = MOD / "reference/mvp20/data/redchem_regression_coverage_gap_audit_receipt.v1.json"

THIS_FIRE_ID = "20260816T180001-1530423-e67dc03466d4"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pae(t: str, body: bytes) -> bytes:
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


def load_seed(p: Path) -> bytes:
    b = p.read_bytes().strip()
    if len(b) == 64:
        try:
            return bytes.fromhex(b.decode())
        except Exception:
            pass
    return b[:32]


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
tbr = {k.get("role"): k for k in TRUST["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

diag_a_bytes = (WORK / "diagnostic.canonical.json").read_bytes()
diag_b_bytes = (WORK / "diagnostic.runB.json").read_bytes()
diag_a = json.loads(diag_a_bytes)
two_replay_byte_identical = sha(diag_a_bytes) == sha(diag_b_bytes)
assert two_replay_byte_identical, "two-replay byte-stability gate FAILED"
assert diag_a["all_content_variants_ok_and_byte_identical_to_baseline"] is True
assert diag_a["n_cases"] == 14

mission_bytes = (MOD / "docs/mission.md").read_bytes()
lib_rs_bytes = (ROOT / "amphora-assurance-capabilities/src/lib.rs").read_bytes()
test_rs_bytes = (ROOT / "amphora-assurance-capabilities/tests/sourceability_ehs_phase0_kpi.rs").read_bytes()
grep_evidence = (WORK / "coverage_grep_evidence.txt").read_text()
probe_src_bytes = (WORK / "ehs_redchem_probe_main.rs").read_bytes()

# Content-level red-team-dossier axes verbatim from docs/mission.md's
# "Red-team dossier" paragraph, split into DISPATCH-layer (already tested by
# the 3 fail-closed probes in sourceability_ehs_phase0_kpi.rs) and
# CONTENT-layer (never constructed against this module by any .rs file in
# the repo, per coverage_grep_evidence.txt -- the phase0 kpi test file is the
# only caller of AssuranceCapability::new("amphora-sourceability-ehs"), and
# its own 5 scenarios + 3 probes are exhaustively reproduced in the module's
# own source above).
DOSSIER_AXES_DISPATCH_LAYER_TESTED = [
    "unsupported formats (candidate_type mismatch)",
    "unsupported formats (unknown module_id)",
    "unsupported formats (whitespace module_id)",
]
DOSSIER_AXES_CONTENT_LAYER_UNTESTED_BY_EXISTING_SUITE = [
    "malformed chemistry",
    "mixtures, fragments, and polymers",
    "unit ambiguity",
    "zero-mass ingredients",
    "NaN and Infinity",
    "out-of-domain inputs",
    "group/source/time leakage",
    "mutated sources",
    "computed-as-measured records",
    "spoofed identity",
    "authority escalation (content-injected, distinct from the dispatch-layer probes)",
    "stripped or unknown claim locks",
]

body_obj = {
    "schema": "amphora.sourceability-ehs.audit.ehs-redchem.v1",
    "audit_item_id": "EHS-REDCHEM",
    "module": "amphora-sourceability-ehs",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_existing_receipts_or_kpis": False,
    "modifies_procurement_gate_outcome": False,
    "fire_id": THIS_FIRE_ID,
    "date": "2026-08-16",
    "claim_under_attack": {
        "mission_md_path": "amphora-sourceability-ehs/docs/mission.md",
        "mission_md_sha256_at_audit_time": sha(mission_bytes),
        "checked_fixture_path": "amphora-assurance-capabilities/tests/sourceability_ehs_phase0_kpi.rs",
        "checked_fixture_sha256": sha(test_rs_bytes),
        "live_implementation_path": "amphora-assurance-capabilities/src/lib.rs",
        "live_implementation_sha256_at_audit_time": sha(lib_rs_bytes),
        "section": "Red-team dossier",
        "claim_text": (
            "Regression coverage must exercise malformed chemistry; mixtures, fragments, and polymers; "
            "unsupported formats; unit ambiguity; zero-mass ingredients; NaN and Infinity; out-of-domain "
            "inputs; group/source/time leakage; mutated sources; computed-as-measured records; spoofed "
            "identity; authority escalation; stripped or unknown claim locks; fixed-seed replay drift; "
            "and legal, regulatory, supplier, procurement, qualification, or release overclaim. Every "
            "such case must fail closed or remain an explicit evidence gap. Module-focused checked "
            "fixture: amphora-assurance-capabilities/src/lib.rs via rtk cargo test --workspace --locked. "
            "Scenario: Reject stale, wrong-grade, unbound, or hash-mismatched supplier evidence."
        ),
        "why_this_is_the_strongest_untested_standing_claim": (
            "Every prior EHS falsification fire attacked the Python-authored scientific-evidence layer "
            "(VHR temperature envelope, GHS/CLP PubChem CID and H-statement provenance, OSHA Table Z-1/Z-2 "
            "attribution, mixture-additivity non-ideality). None attacked the module's actual live-checked "
            "Rust runtime boundary (evaluate_sourceability, amphora-assurance-capabilities/src/lib.rs) or "
            "its own documented regression-coverage commitment -- the claim this module's Phase-0 gate "
            "status is formally conditioned on (docs/mission.md 'Focused acceptance command: rtk cargo "
            "test --workspace --locked')."
        ),
    },
    "refutation_criterion": (
        "The claim asserts regression coverage 'must exercise' each of 15 named red-team axes against "
        "this module's checked fixture. If a full-repository grep for every .rs call site that invokes "
        "AssuranceCapability::new(\"amphora-sourceability-ehs\") / evaluate() against it shows that N of "
        "those 15 axes have zero corresponding test case anywhere in the repository, the coverage claim "
        "is refuted for those N axes -- regardless of whether the runtime's behavior under those axes "
        "happens to be safe (a separate, non-dispositive question this audit also answers empirically "
        "below, since 'must exercise' is a testing-completeness claim, not a runtime-behavior claim)."
    ),
    "method": {
        "step_1_source_reading": (
            "Read amphora-assurance-capabilities/src/lib.rs:976-1010 (fn evaluate_sourceability). It "
            "takes ZERO candidate-derived arguments -- signature is `fn evaluate_sourceability() -> "
            "ModuleResult`, called from the evaluate() dispatcher (line ~435) as "
            "`SOURCEABILITY_EHS => evaluate_sourceability()`, discarding the `candidate: &CandidateEnvelope` "
            "parameter entirely. It returns a byte-constant ModuleResult built solely from the "
            "compile-time-embedded v5_epoch30_public_bom_sourceability_manifest.json, independent of any "
            "candidate field."
        ),
        "step_2_upstream_check": (
            "Read amphora-core/src/contract.rs:205-247 (CandidateEnvelope::build). Structural validation "
            "only: candidate_id non-empty string, candidate_type in {molecule, formulation, "
            "evidence_package}, required_payload key present and is a JSON object. No semantic chemistry "
            "validation (mass sign, mass magnitude, mixture/polymer well-formedness, unit consistency) "
            "exists at this layer either. JSON's own grammar makes literal NaN/Infinity unrepresentable "
            "(parse_json_strict's visit_f64 explicitly rejects non-finite numbers), so that ONE axis is "
            "structurally guaranteed by the JSON format itself, not by any test -- disclosed, not counted "
            "as a coverage gap below."
        ),
        "step_3_repository_wide_coverage_grep": (
            "grep -rn for every .rs call site invoking AssuranceCapability::new(\"amphora-sourceability-ehs\") "
            "or the SOURCEABILITY_EHS constant, across the entire mvp20-split tree (all modules, not just "
            "amphora-sourceability-ehs). Full output in coverage_grep_evidence.txt. Result: exactly one "
            "call site, amphora-assurance-capabilities/tests/sourceability_ehs_phase0_kpi.rs:205, whose "
            "full content this audit read in full (569 lines). It exercises 5 adversarial-supplier-"
            "declaration-injection scenarios (signed supplier declaration, fake lot CoA, "
            "procurement.declared_ready injection, plus 2 plain formulations) and 3 dispatch-layer "
            "fail-closed probes (wrong candidate_type, unknown module_id, whitespace module_id). None of "
            "the 5 scenarios varies chemistry content in a way that could distinguish malformed from "
            "well-formed input (all use plausible finite positive masses); none constructs a mixture, "
            "polymer, zero/negative-mass, out-of-domain, group/source-leakage, mutated-source, "
            "computed-as-measured, or spoofed-identity case."
        ),
        "step_4_empirical_confirmation": (
            "Built a standalone Rust probe (ehs_redchem_probe_main.rs, checked in beside this receipt; "
            "isolated [workspace] Cargo project depending via path on the real, unmodified "
            "amphora-assurance-capabilities and amphora-core crates -- no other module's source was "
            "edited) constructing 13 adversarial formulation candidates, one per untested content axis "
            "below, plus 1 known-good baseline. Called the real compiled "
            "AssuranceCapability::new(\"amphora-sourceability-ehs\").evaluate() on each, twice "
            "(two-replay), and compared every result byte-for-byte via serde_json canonical (BTreeMap, "
            "sorted-key) serialization."
        ),
    },
    "findings": {
        "dossier_axes_dispatch_layer_already_tested": DOSSIER_AXES_DISPATCH_LAYER_TESTED,
        "dossier_axes_content_layer_untested_by_any_repo_test": DOSSIER_AXES_CONTENT_LAYER_UNTESTED_BY_EXISTING_SUITE,
        "n_content_axes_claimed": len(DOSSIER_AXES_CONTENT_LAYER_UNTESTED_BY_EXISTING_SUITE) + 1,
        "n_content_axes_with_zero_test_coverage": len(DOSSIER_AXES_CONTENT_LAYER_UNTESTED_BY_EXISTING_SUITE),
        "nan_infinity_axis_note": (
            "Excluded from the untested-coverage count above: NaN/Infinity is structurally unrepresentable "
            "in JSON and is rejected at JSON-parse time by amphora-core's own strict deserializer "
            "(contract.rs visit_f64), independent of any test -- the dossier's requirement is met by "
            "construction for this one axis, not by omission."
        ),
        "sole_test_call_site": "amphora-assurance-capabilities/tests/sourceability_ehs_phase0_kpi.rs:205 (only caller in the repository)",
        "coverage_grep_evidence_path": "amphora-sourceability-ehs/evidence/phase0/audits/EHS-REDCHEM/work/coverage_grep_evidence.txt",
        "coverage_grep_evidence_sha256": sha(grep_evidence.encode()),
        "empirical_probe_result": {
            "n_cases": diag_a["n_cases"],
            "n_evaluate_ok": diag_a["n_evaluate_ok"],
            "n_byte_identical_to_baseline": diag_a["n_byte_identical_to_baseline"],
            "n_remains_explicit_evidence_gap": diag_a["n_remains_explicit_evidence_gap"],
            "interpretation": (
                "All 13 adversarial content-level variants (malformed chemistry, mixture/dot-SMILES "
                "fragment, polymer repeat-unit notation with a degree-of-polymerization of 9999999, "
                "conflicting mass units, zero-mass, negative-mass, out-of-domain formulation, spoofed "
                "split_group/source_id, mutated evidence_refs.cited_source.sha256, a value marked "
                "measured:true that is actually computed, a candidate_id colliding with a canonical "
                "fixture id, unrecognised claim_locks keys, and an injected batch_release/qualified "
                "authority-escalation block) produced Ok(ModuleResult) BYTE-IDENTICAL to the known-good "
                "baseline. This confirms by direct execution (not just source reading) that "
                "evaluate_sourceability() is provably content-blind: no chemistry-content mutation, "
                "however adversarial, can change its output at all. The runtime therefore CANNOT be "
                "'tricked' by any of these axes (every case trivially 'remains an explicit evidence gap' "
                "per the dossier's OR-clause) -- but this is because the function never inspects the "
                "content, not because a red-team test suite exercised and confirmed defensive logic. The "
                "dossier's 'must exercise' language commits to the latter; the repository delivers "
                "neither the former as a tested property nor any test construction of these 12 axes at "
                "all."
            ),
        },
        "two_replay_byte_stability": {
            "diagnostic_canonical_sha256": sha(diag_a_bytes),
            "diagnostic_runB_sha256": sha(diag_b_bytes),
            "byte_identical": two_replay_byte_identical,
        },
    },
    "verdict": "CLAIM_REFUTED",
    "verdict_summary": (
        "REFUTED. docs/mission.md's Red-team dossier commits this module's checked fixture "
        "(amphora-assurance-capabilities/src/lib.rs via `rtk cargo test --workspace --locked`) to "
        "exercising malformed chemistry, mixtures/fragments/polymers, unit ambiguity, zero-mass "
        "ingredients, out-of-domain inputs, group/source/time leakage, mutated sources, "
        "computed-as-measured records, spoofed identity, content-level authority escalation, and "
        "stripped/unknown claim locks. A full-repository grep shows exactly one test call site for this "
        "module (sourceability_ehs_phase0_kpi.rs), and it constructs zero cases for any of these 12 "
        "axes -- only 3 dispatch-layer axes (candidate_type/module_id validation) are actually tested. "
        "Source reading plus a fresh, isolated, byte-stable two-replay empirical probe against the real "
        "compiled runtime confirms the root cause: evaluate_sourceability() takes no candidate-derived "
        "argument at all and is provably content-blind (13/13 adversarial variants produced output "
        "byte-identical to a known-good baseline). The regression-coverage claim is therefore false as "
        "written; the runtime's incidental safety under these axes is a side effect of the module being a "
        "content-blind Phase-0 stub, not of tested defensive logic."
    ),
    "does_not_close": [
        "Does not modify evaluate_sourceability(), any KPI, gate, procurement_gate_outcome, or "
        "sourceability_status -- disclosure only. The runtime's actual behavior under every probed axis "
        "is safe (remains an explicit UNRESOLVED/FAILED_GATES evidence gap); only the documented "
        "regression-coverage COMMITMENT is refuted, not the runtime's current safety posture.",
        "Does not add the missing test cases to amphora-assurance-capabilities/tests/ -- that file is "
        "outside this module's subtree (amphora-assurance-capabilities is a shared crate serving 7 other "
        "assurance-capability modules) and editing it is out of this fire's confinement scope; flagged "
        "for a dedicated repair fire with a human-reviewed change to shared test infrastructure.",
        "Does not assert that a future content-sensitive evaluate_sourceability() implementation would be "
        "an improvement -- Phase-0's own honest design intent may be exactly this constant, "
        "content-blind, always-quarantined stub; that design decision is out of scope for this audit, "
        "which addresses only whether the documented coverage claim about it is true.",
        "AUDIT_ONLY: no procurement, regulatory, safety, or scientific-readiness authority.",
    ],
    "artifacts": {
        "probe_source": "amphora-sourceability-ehs/evidence/phase0/audits/EHS-REDCHEM/work/ehs_redchem_probe_main.rs",
        "probe_source_sha256": sha(probe_src_bytes),
        "probe_cargo_toml": "amphora-sourceability-ehs/evidence/phase0/audits/EHS-REDCHEM/work/ehs_redchem_probe_Cargo.toml",
        "diagnostic_canonical": "amphora-sourceability-ehs/evidence/phase0/audits/EHS-REDCHEM/work/diagnostic.canonical.json",
        "diagnostic_runB": "amphora-sourceability-ehs/evidence/phase0/audits/EHS-REDCHEM/work/diagnostic.runB.json",
        "coverage_grep_evidence": "amphora-sourceability-ehs/evidence/phase0/audits/EHS-REDCHEM/work/coverage_grep_evidence.txt",
        "probe_build_note": (
            "Probe crate built and run in an isolated /tmp scratch location on xbabe2 (not committed as a "
            "workspace member) with its own empty [workspace] table (the cargo-fuzz convention) so it "
            "path-depends on, but never edits or joins the workspace of, amphora-core and "
            "amphora-assurance-capabilities. Both dependency crates are byte-identical to the "
            "live_implementation_sha256_at_audit_time / checked_fixture_sha256 values cited above -- no "
            "source in any other module was modified to produce this evidence."
        ),
    },
    "references": [
        "amphora-sourceability-ehs/docs/mission.md, section 'Red-team dossier'.",
        "amphora-assurance-capabilities/src/lib.rs, fn evaluate_sourceability (line ~976).",
        "amphora-assurance-capabilities/tests/sourceability_ehs_phase0_kpi.rs (full file read, 569 lines).",
        "amphora-core/src/contract.rs, CandidateEnvelope::build (line ~205) and parse_json_strict/visit_f64 "
        "(line ~89, non-finite-number rejection).",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.sourceability-ehs-audit-ehs-redchem+json"
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

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
print("WROTE", OUT_PATH)
print("self_verify_signature", True)
print("envelope_sha256", sha(OUT_PATH.read_bytes()))
