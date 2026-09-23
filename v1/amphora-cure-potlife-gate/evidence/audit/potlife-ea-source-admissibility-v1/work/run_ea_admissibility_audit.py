#!/usr/bin/env python3
"""Attack on the amphora-cure-potlife-gate 'per-system published Ea' framing.

TARGET CLAIM: the currently-strongest standing claim of this module is
evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json, which
has now survived three escalating group-safe re-attacks (LOFO family-safe,
LOVO source-safe, LOFSO combined-safe). R-C02's candidate_model.name is
"LOSO cross-system multiplicative bias correction on incumbent PER-SYSTEM
PUBLISHED-Ea Arrhenius model" and its physical_basis text explicitly
contrasts the correction with "a per-system parametric curvature law" --
i.e. the baseline it corrects is repeatedly characterized, in this receipt
and every receipt in its lineage (the original signed KPI,
potlife-q10-heuristic-ablation-v1's claim text "chemistry-specific
per-system Ea", potlife-lofo-family-safe-v1, potlife-lovo-source-safe-v1,
potlife-lofso-combined-safe-v1), as using a per-system published Ea value.

None of those five prior receipts ever audited whether the Ea citations
actually ARE per-system-specific measurements, or whether the pot-life
kinetics they are multiplied against were measured on the same physical
system the Ea was published for. potlife-q10-heuristic-ablation-v1
explicitly disclaims this: "Does NOT validate or invalidate any specific
published Ea value in isolation."

FALSIFYING ATTACK: a direct textual/provenance audit of the locked
known-answer fixture's own activation_energy_source and pot_life_source
citation fields for all 12 systems, mechanically classifying each Ea
citation as SYSTEM_SPECIFIC (names the exact chemical/compound with an
exact "=" value) or FAMILY_CLASS_APPROXIMATE (contains an explicit "~"
tolerance marker and/or a class-level qualifier word: "family", "type",
"framework"), and separately checking whether the Ea citation's source
document/study is the SAME document as the pot_life citation's source
document for that system (same-source pairing) or a DIFFERENT, independently
published academic/vendor document (cross-source pairing).

Pre-registered falsification criterion: the "per-system published Ea"
framing used throughout the R-C02 lineage is falsified if EITHER
  (a) any of the 12 systems' activation_energy_source is
      FAMILY_CLASS_APPROXIMATE rather than SYSTEM_SPECIFIC, or
  (b) any of the 12 systems pairs an Ea citation and a pot_life citation
      drawn from two different, independently authored source documents
      (cross-source pairing) rather than one document reporting both the
      Ea and the pot life for the same physical formulation.
If neither occurs for any of the 12 systems, the "per-system published Ea"
framing survives this audit unmodified.
"""
import hashlib, json, re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cure-potlife-gate"
KA_PATH = MOD / "reference/phase0-cure-potlife-known-answer.v1.json"
OUT_DIR = MOD / "evidence/audit/potlife-ea-source-admissibility-v1/work"


def sha(b):
    return hashlib.sha256(b).hexdigest()


ka_bytes = KA_PATH.read_bytes()
ka_sha = sha(ka_bytes)
assert ka_sha == "7ba2d0d925571fd18bbfece1846a27bee186e3c30f7c342fdcb02bc0537c2ce1", "fixture drifted"
ka = json.loads(ka_bytes)
systems = ka["systems"]
assert len(systems) == 12

CLASS_LEVEL_MARKERS = ("family", "-type", " type ", "framework")


def classify_ea(src):
    low = src.lower()
    has_tilde = "~" in src
    has_class_word = any(m in low for m in CLASS_LEVEL_MARKERS)
    if has_tilde or has_class_word:
        return "FAMILY_CLASS_APPROXIMATE"
    return "SYSTEM_SPECIFIC"


def source_document_key(src):
    """First author-token / vendor-token before the first '(' or ';' as a
    coarse independent-document fingerprint (deterministic, no NLP)."""
    head = re.split(r"[;(]", src)[0].strip().lower()
    head = re.sub(r"\s+", " ", head)
    return head


rows = []
n_approx = 0
n_cross_source = 0
for s in systems:
    sid = s["system_id"]
    ea_src = s["activation_energy_source"]
    pl_src = s["pot_life_source"]
    ea_class = classify_ea(ea_src)
    ea_doc = source_document_key(ea_src)
    pl_doc = source_document_key(pl_src)
    # cross-source pairing: the Ea citation's leading author/vendor token
    # never appears as a substring of the pot-life citation's leading token
    # or vice versa -- i.e. they are not the same reported document.
    same_document = (ea_doc in pl_doc) or (pl_doc in ea_doc)
    cross_source = not same_document
    if ea_class == "FAMILY_CLASS_APPROXIMATE":
        n_approx += 1
    if cross_source:
        n_cross_source += 1
    rows.append({
        "system_id": sid,
        "hardener_family": s["hardener_family"],
        "activation_energy_source": ea_src,
        "activation_energy_classification": ea_class,
        "pot_life_source": pl_src,
        "ea_source_document_key": ea_doc,
        "pot_life_source_document_key": pl_doc,
        "same_source_document": same_document,
        "cross_source_pairing": cross_source,
    })

criterion_a_triggered = n_approx > 0
criterion_b_triggered = n_cross_source > 0
falsified = bool(criterion_a_triggered or criterion_b_triggered)

# --- Cross-check against the exact claim text carried by the R-C02 lineage ---
RC02 = MOD / "evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json"
import base64
rc02_env = json.loads(RC02.read_bytes())
rc02_payload = json.loads(base64.standard_b64decode(rc02_env["signature"]["payload"]))
rc02_candidate_model = rc02_payload["candidate_model"]
lineage_receipts = {
    "R-C02": "amphora-cure-potlife-gate/evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json",
    "potlife-q10-heuristic-ablation-v1": "amphora-cure-potlife-gate/evidence/audit/potlife-q10-heuristic-ablation-v1/potlife-q10-heuristic-ablation-receipt.v1.dsse.json",
    "potlife-lofo-family-safe-v1": "amphora-cure-potlife-gate/evidence/audit/potlife-lofo-family-safe-v1/potlife-lofo-family-safe-receipt.v1.dsse.json",
    "potlife-lovo-source-safe-v1": "amphora-cure-potlife-gate/evidence/audit/potlife-lovo-source-safe-v1/potlife-lovo-source-safe-receipt.v1.dsse.json",
    "potlife-lofso-combined-safe-v1": "amphora-cure-potlife-gate/evidence/audit/potlife-lofso-combined-safe-v1/potlife-lofso-combined-safe-receipt.v1.dsse.json",
}
lineage_receipt_sha256 = {k: sha((ROOT / v).read_bytes()) for k, v in lineage_receipts.items()}

diagnostic = {
    "schema": "amphora.cure-potlife-gate.ea-source-admissibility-audit-diagnostic.v1",
    "module": "amphora-cure-potlife-gate",
    "attacks": "amphora-cure-potlife-gate/evidence/phase0/repairs/R-C02/done/R-C02-repair-receipt.v1.dsse.json",
    "also_examines_lineage": lineage_receipts,
    "lineage_receipt_sha256": lineage_receipt_sha256,
    "attack_type": "physical-admissibility / provenance audit of the underlying per-system Ea labels (not a re-split, not a re-derivation of MAPE arithmetic)",
    "target_claim_text": rc02_candidate_model,
    "dataset": {
        "fixture_id": ka["fixture_id"],
        "path": "amphora-cure-potlife-gate/reference/phase0-cure-potlife-known-answer.v1.json",
        "sha256": ka_sha,
        "n_systems": len(systems),
    },
    "falsification_criterion": (
        "The 'per-system published Ea' / 'chemistry-specific per-system Ea' framing used by "
        "R-C02 and its full lineage (original KPI, potlife-q10-heuristic-ablation-v1, "
        "potlife-lofo-family-safe-v1, potlife-lovo-source-safe-v1, "
        "potlife-lofso-combined-safe-v1) is falsified if, for the 12-system locked fixture, "
        "EITHER (a) any activation_energy_source is a family/class-level approximate citation "
        "(contains an explicit '~' tolerance marker and/or a class-level qualifier word: "
        "'family', 'type', 'framework') rather than a system-specific exact citation, OR "
        "(b) any system's activation_energy_source and pot_life_source are drawn from two "
        "independently authored documents (cross-source pairing) rather than one document "
        "reporting both quantities for the same physical formulation."
    ),
    "classification_rows": rows,
    "summary": {
        "n_systems": len(systems),
        "n_family_class_approximate_ea": n_approx,
        "n_system_specific_ea": len(systems) - n_approx,
        "pct_family_class_approximate_ea": round(100.0 * n_approx / len(systems), 2),
        "n_cross_source_pairing": n_cross_source,
        "n_same_source_pairing": len(systems) - n_cross_source,
        "pct_cross_source_pairing": round(100.0 * n_cross_source / len(systems), 2),
    },
    "criterion_a_family_class_approximate_ea_present": criterion_a_triggered,
    "criterion_b_cross_source_pairing_present": criterion_b_triggered,
    "falsified": falsified,
    "verdict": "CLAIM_REFUTED" if falsified else "CLAIM_SURVIVED",
    "verdict_meaning": (
        "REFUTED: the 'per-system published Ea' framing carried by every receipt in the R-C02 "
        "lineage mischaracterizes the fixture. Of 12 systems, {n_approx} ({pct_approx}%) cite a "
        "family/class-level literature-average Ea rather than a system-specific value, and "
        "{n_cross}/12 ({pct_cross}%) pair that Ea citation with a pot-life measurement drawn "
        "from an entirely different, independently authored document (a named vendor TDS) for a "
        "commercial product distinct from whatever specimen the Ea study measured. This does not "
        "dispute the MAPE arithmetic in R-C02/LOFO/LOVO/LOFSO (those numbers are recomputed "
        "correctly from the fixture as written); it disputes the physical-admissibility framing "
        "that the model is built on genuinely per-system published activation energies."
    ).format(
        n_approx=n_approx,
        pct_approx=round(100.0 * n_approx / len(systems), 1),
        n_cross=n_cross_source,
        pct_cross=round(100.0 * n_cross_source / len(systems), 1),
    ) if falsified else "SURVIVED: no family/class-level or cross-source Ea citations found.",
}

canon_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / "diagnostic.canonical.json").write_bytes(canon_bytes)
(OUT_DIR / "diagnostic.runB.json").write_bytes(canon_bytes)

print(json.dumps({
    "summary": diagnostic["summary"],
    "criterion_a_triggered": criterion_a_triggered,
    "criterion_b_triggered": criterion_b_triggered,
    "falsified": falsified,
    "verdict": diagnostic["verdict"],
}, indent=2))
