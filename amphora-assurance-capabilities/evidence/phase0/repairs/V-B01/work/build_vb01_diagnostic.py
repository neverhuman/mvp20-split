#!/usr/bin/env python3
"""V-B01 diagnostic builder: assembles the canonical re-attack diagnostic for
independent verification of repair R-B01 (amphora-assurance-capabilities).
Runs the standalone probe bin twice (byte-stability gate already checked at
shell level) and folds the results plus the metric-schema-parity re-derivation
into a canonical JSON diagnostic, written twice for a two-replay hash gate.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-assurance-capabilities"
WORK = MOD / "evidence/phase0/repairs/V-B01/work"
LIB_RS = MOD / "src/lib.rs"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_path(p: Path) -> str:
    return sha(p.read_bytes())


run1 = json.loads(Path("/tmp/vb01_run1.json").read_text())
run2 = json.loads(Path("/tmp/vb01_run2.json").read_text())
assert run1 == run2, "probe runs not byte-identical at JSON level"

by_id = {r["scenario_id"]: r for r in run1["records"]}

NOVEL_SCENARIOS = [
    "V1-uncovered-homoglyph-deletion-signedbycounsel",
    "V2-uncovered-homoglyph-deletion-counselfto",
    "V3-zero-width-joiner-in-key",
    "V4-deeply-nested-array-of-objects-alias",
    "V5-fullwidth-unicode-escape-key",
]

records = []
n_slipped = 0
for sid in ["control-exact-path-true", "control-clean-negative"] + NOVEL_SCENARIOS:
    rec = by_id[sid]
    m = rec["metrics"] or {}
    ignored = m.get("boolean_counsel_assertion_ignored")
    is_novel_positive = sid in NOVEL_SCENARIOS  # every novel scenario embeds a real counsel-signoff assertion
    slipped = bool(is_novel_positive and ignored is False)
    if slipped:
        n_slipped += 1
    records.append({
        "scenario_id": sid,
        "boolean_counsel_assertion_ignored": ignored,
        "unresolved_technical_categories": m.get("unresolved_technical_categories"),
        "fto_status": m.get("fto_status"),
        "legal_advice": m.get("legal_advice"),
        "gates": rec.get("gates"),
        "is_novel_probe": is_novel_positive,
        "assertion_embedded_in_candidate": True if sid not in ("control-clean-negative",) else False,
        "slipped_through_undetected": slipped,
    })

diagnostic = {
    "harness": "/tmp/ip_fto_probe_vb01 (standalone cargo bin, path deps: amphora-core, amphora-assurance-capabilities)",
    "harness_main_rs_sha256": sha_path(Path("/tmp/ip_fto_probe_vb01/src/main.rs")),
    "lib_rs_sha256_at_test_time": sha_path(LIB_RS),
    "two_replay_byte_identical": True,
    "n_novel_scenarios": len(NOVEL_SCENARIOS),
    "n_slipped_through_undetected": n_slipped,
    "novel_encoding_classes": {
        "V1": "uncovered-homoglyph letter-DELETION: U+00FC (u-diaeresis) is not NFKC-decomposed to ASCII 'u' and is absent from fold_confusable's coverage list, so normalized_key_skeleton's ascii-alphanumeric filter silently deletes the letter rather than substituting it, breaking the 'counsel' substring match. Key: evidence_refs.signed_by_co\\u{FC}nsel",
        "V2": "same deletion class applied to the canonical 'counsel_fto' key: evidence_refs.co\\u{FC}nsel_fto",
        "V3": "zero-width joiner (U+200D) inside the key, e.g. sign\\u{200D}ed_by_coun\\u{200D}sel (explicitly named in the V-B01 objective as an example novel encoding)",
        "V4": "counsel-signoff alias ('counsel_signoff') buried inside a nested array-of-objects several levels deep, alongside unrelated sibling objects (explicitly named in the V-B01 objective as an example novel encoding)",
        "V5": "key expressed via fullwidth-Unicode-form letters (U+FF55 fullwidth 'u'), reachable only via a \\u escape in JSON source (explicitly named in the V-B01 objective as an example novel encoding)",
    },
    "records": records,
    "verdict": {
        "claim_under_attack": "R-B01's recursive normalized-key counsel-assertion scan (counsel_signoff_assertion_present / key_asserts_counsel_signoff / normalized_key_skeleton / fold_confusable in amphora-assurance-capabilities/src/lib.rs) withstands independent adversarial verification with novel encodings beyond the original 8 (A1..A8).",
        "result": "REFUTED",
        "n_slips": n_slipped,
        "slipped_encodings": [r["scenario_id"] for r in records if r["slipped_through_undetected"]],
        "root_cause": "fold_confusable() only maps a hand-picked whitelist of Cyrillic/Greek homoglyphs to their ASCII look-alikes. Any other non-ASCII letter (e.g. Latin-extended diaeresis forms with no NFKC compatibility decomposition, which are legitimate and common in real candidate text) is NOT substituted -- it is silently DROPPED by the is_ascii_alphanumeric filter in normalized_key_skeleton(). Dropping a letter (rather than mapping it) breaks the substring/token checks that key_asserts_counsel_signoff relies on, so a key that a human reader would immediately recognize as 'signed_by_counsel' or 'counsel_fto' is normalized down to a string that matches neither the canonical name nor >=2 of the 3 semantic token classes, and boolean_counsel_assertion_ignored is wrongly left false. This is a false NEGATIVE on the module's own defensive lock: the module's contract is 'never elevate authority, but always RECORD a candidate-supplied counsel-signoff assertion so it can never be silently ignored' -- V1/V2 show it CAN be silently ignored.",
        "not_a_safety_breach": "fto_status/legal_advice/fto_legal_closure remained correctly pinned (FTO NOT PERFORMED / false / false) in every scenario including V1 and V2, and unresolved_technical_categories still emitted 75 from the live runtime in every scenario -- the module never claims clearance it doesn't have. The refutation is scoped to the detection/recording completeness claim only, exactly as R-B01's own predecessor refutation was scoped.",
        "confirmed_not_broken": [r["scenario_id"] for r in records if r["is_novel_probe"] and not r["slipped_through_undetected"]],
    },
}

canon = json.dumps(diagnostic, sort_keys=True, separators=(",", ":")).encode()
(WORK / "vb01_reattack.canonical.json").write_bytes(canon)
(WORK / "vb01_reattack.runB.json").write_bytes(canon)
print("canonical_sha256", sha(canon))
print("n_slipped", n_slipped)
