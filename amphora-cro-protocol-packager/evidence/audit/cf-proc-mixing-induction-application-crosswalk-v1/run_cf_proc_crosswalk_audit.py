#!/usr/bin/env python3
"""CF-PROC mixing/induction/application crosswalk audit (AUDIT_ONLY).

Attack shape (verbatim from docs/directives/2026-08-09-dataset-recon.index.json,
obligation CF-PROC): "Remove the induction-time parameter from a copy and attack
whether the envelope crosswalk fires; walk the envelope's application table and
hunt for an uncovered parameter."

Claim under attack: "The current CF-PROC deliverable state is complete and
accurate for its scope" (finding a miss is CLAIM_REFUTED and is progress).

Refutation criterion (verbatim): "The mixing, induction and application section
or the bench-scale sequence omits a parameter the envelope's WFT, coverage or
cure schedule requires, or a scale-sensitive step is unflagged."

Method: build the CF-PROC deliverable corpus (every document that carries
mixing/induction/application/process content for this candidate formulation
package: amphora-report-packager's blueprint.md, amphora-cro-protocol-packager's
own cro_protocol.md and capture_template.json), extract the envelope's own
process/application requirements from amphora-envelope-gates'
reference/mvp20/charter/v5_requirements.json (performance_envelope +
fixed_constraints), and regex-crosswalk each envelope requirement against the
corpus. Then run a positive control (strip the induction-time parameter from a
copy, per the attack shape) and a discrimination control (a synthetic
fully-patched copy) to prove the checker genuinely discriminates rather than
being hard-wired to one answer.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ENVELOPE_PATH = ROOT / "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json"
BLUEPRINT_PATH = ROOT / "amphora-report-packager/reference/mvp20/out/blueprint.md"
CRO_PROTOCOL_PATH = ROOT / "amphora-cro-protocol-packager/reference/mvp20/out/cro_protocol.md"
CAPTURE_TEMPLATE_PATH = ROOT / "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_corpus():
    parts = {
        "blueprint.md": BLUEPRINT_PATH.read_text(),
        "cro_protocol.md": CRO_PROTOCOL_PATH.read_text(),
        "capture_template.json": CAPTURE_TEMPLATE_PATH.read_text(),
    }
    return parts


# --- envelope-derived required process/application parameters --------------
# Each entry: (key, envelope_source_path, required_value_desc, detection_regex,
#              refuting_clause) -- refuting_clause names which of
#              WFT/coverage/cure-schedule the parameter belongs to, per the
#              pre-committed refutation criterion.
REQUIRED_PARAMS = [
    {
        "key": "induction_min",
        "envelope_path": "performance_envelope.induction_min.target",
        "required_value": "30 min",
        "pattern": r"induction[^.\n]{0,40}?30",
        "criterion_clause": "application",
    },
    {
        "key": "pot_life_h_min",
        "envelope_path": "performance_envelope.pot_life_h.min",
        "required_value": ">=1.5 h @ 73F/50%RH",
        "pattern": r"pot.?life[^.\n]{0,60}?1\.5",
        "criterion_clause": "application",
    },
    {
        "key": "wft_mils",
        "envelope_path": "performance_envelope.wft_mils",
        "required_value": "7-9 mil",
        "pattern": r"7[\s\-–]{1,3}9",
        "criterion_clause": "WFT",
    },
    {
        "key": "coverage_ft2_per_gal",
        "envelope_path": "performance_envelope.coverage_ft2_per_gal",
        "required_value": "175-230 ft2/gal",
        "pattern": r"175[\s\-–]{1,3}230",
        "criterion_clause": "coverage",
    },
    {
        "key": "dft_mils_per_coat",
        "envelope_path": "fixed_constraints.dft_mils_per_coat",
        "required_value": "4.5-6.0 mil",
        "pattern": r"4\.5[\s\-–]{1,3}6",
        "criterion_clause": "coverage",
    },
    {
        "key": "dry_to_touch_h",
        "envelope_path": "performance_envelope.dry_to_touch_h.target",
        "required_value": "2 h (envelope's own dry-to-touch target, distinct from the MIL-cited 3 h set-to-touch)",
        "pattern": r"dry[\s_-]to[\s_-]touch[^.\n]{0,40}?2\b",
        "criterion_clause": "cure schedule",
    },
    {
        "key": "functional_cure_h",
        "envelope_path": "performance_envelope.functional_cure_h.target",
        "required_value": "6 h (envelope's own functional-cure target, stated as such -- not merely numerically-coincident with the MIL dry-hard citation)",
        "pattern": r"functional[\s_]cure[^.\n]{0,40}?6\b",
        "criterion_clause": "cure schedule",
    },
    {
        "key": "recoat_window_h",
        "envelope_path": "fixed_constraints.recoat_window_h.target",
        "required_value": "6 h",
        "pattern": r"recoat[^.\n]{0,40}?6\b",
        "criterion_clause": "cure schedule",
    },
    {
        "key": "mix_ratio_tolerance_pct",
        "envelope_path": "fixed_constraints.mix_ratio_by_volume.engine_tolerance_pct",
        "required_value": "3% engine tolerance band on the 1:1-by-volume mix ratio",
        "pattern": r"mix[^.\n]{0,30}(toleran[a-z]*|3\s?%)|toleran[a-z]*[^.\n]{0,30}mix",
        "criterion_clause": "application",
    },
    {
        "key": "thinning_limit_numeric",
        "envelope_path": "fixed_constraints.voc_g_per_l (max 340, design_to 320) -- the practical thinning ceiling; no field named 'thinning' exists in the envelope, so the deliverable itself must state the derived numeric limit",
        "required_value": "an explicit numeric thinning limit (e.g. max % thinner by volume, max fl oz/gal, or an explicit VOC-headroom-derived cap) -- 'thinning limits' is named verbatim in the CF-PROC done_criteria",
        "pattern": r"thin[a-z]*[^.\n]{0,40}(\d+\s?%|\bfl\.?\s?oz\b|pt/gal|max[^.\n]{0,10}thin)",
        "criterion_clause": "application (done_criteria-named element)",
    },
]

SCALE_SENSITIVE_PATTERN = r"(tip speed|grind temperature|dispersion heat|scale.up|scale.sensitiv)"


def run_crosswalk(corpus_text: str):
    results = []
    for p in REQUIRED_PARAMS:
        m = re.search(p["pattern"], corpus_text, re.IGNORECASE)
        results.append({
            "key": p["key"],
            "envelope_path": p["envelope_path"],
            "required_value": p["required_value"],
            "criterion_clause": p["criterion_clause"],
            "found": bool(m),
            "matched_snippet": m.group(0) if m else None,
        })
    scale_m = re.search(SCALE_SENSITIVE_PATTERN, corpus_text, re.IGNORECASE)
    scale_flagged = bool(scale_m)
    missing = [r for r in results if not r["found"]]
    return {
        "params": results,
        "n_missing": len(missing),
        "missing_keys": [r["key"] for r in missing],
        "scale_sensitive_step_flagged": scale_flagged,
        "scale_sensitive_snippet": scale_m.group(0) if scale_m else None,
        "refuted": (len(missing) > 0) or (not scale_flagged),
    }


def strip_induction_time(corpus_parts):
    """Positive control: delete every induction-time-with-value mention, per
    the attack shape's literal instruction ('remove the induction-time
    parameter from a copy')."""
    out = {}
    strip_pattern = re.compile(r"induction[^.\n]{0,60}?30[^.\n]{0,20}", re.IGNORECASE)
    bare_pattern = re.compile(r"\binduction\b", re.IGNORECASE)
    for name, text in corpus_parts.items():
        t = strip_pattern.sub("[REDACTED]", text)
        t = bare_pattern.sub("[REDACTED]", t)
        out[name] = t
    return out


def synthetic_patch(corpus_parts):
    """Discrimination control: a synthetic fully-repaired copy that adds
    explicit language for the params this audit currently finds missing, to
    prove the checker is not hard-wired to always refute."""
    out = dict(corpus_parts)
    patch = (
        "\n\n## CF-PROC synthetic repair patch (discrimination-control only, "
        "not part of the real deliverable)\n"
        "Dry-to-touch (envelope functional target): 2 h. Functional cure "
        "(envelope functional target): 6 h. Recoat window: 6 h. Mix ratio "
        "tolerance: 3% (engine tolerance band on the 1:1-by-volume mix "
        "ratio) -- do not apply outside a 1:1 +/-3% mixed ratio. Thinning "
        "limit: do not exceed 5% thinner by volume (naphtha/n-butanol "
        "letdown solvent), consistent with the VOC design-to ceiling of "
        "320 g/L against the 340 g/L maximum.\n"
    )
    out["blueprint.md"] = out["blueprint.md"] + patch
    return out


def main():
    envelope = json.loads(ENVELOPE_PATH.read_bytes())
    corpus_parts = load_corpus()
    corpus_sha = {name: sha(text.encode()) for name, text in corpus_parts.items()}
    full_corpus = "\n".join(corpus_parts.values())

    # step A: real crosswalk on the unmodified deliverable
    real_result = run_crosswalk(full_corpus)

    # step B: positive control -- strip induction-time from a copy per the
    # attack shape, confirm the crosswalk now ALSO flags induction_min missing
    stripped_parts = strip_induction_time(corpus_parts)
    stripped_corpus = "\n".join(stripped_parts.values())
    stripped_result = run_crosswalk(stripped_corpus)
    induction_flips_to_missing = (
        "induction_min" in stripped_result["missing_keys"]
        and "induction_min" not in real_result["missing_keys"]
    )

    # step C: discrimination control -- synthetic fully-patched copy should
    # report the previously-missing params as found (checker is not
    # hard-wired to always refute)
    patched_parts = synthetic_patch(corpus_parts)
    patched_corpus = "\n".join(patched_parts.values())
    patched_result = run_crosswalk(patched_corpus)
    real_missing_set = set(real_result["missing_keys"])
    patched_still_missing = [k for k in real_missing_set if k in patched_result["missing_keys"]]
    discrimination_control_passed = (
        len(real_missing_set) > 0 and len(patched_still_missing) == 0
    )

    out = {
        "study_id": "cf-proc-mixing-induction-application-crosswalk-v1",
        "authority": "AUDIT_ONLY",
        "module": "amphora-cro-protocol-packager",
        "campaign_item_id": "CF-PROC",
        "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
        "directive_sha256": "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207",
        "directive_obligation": "CF-PROC",
        "claim_under_attack": "The current CF-PROC deliverable state is complete and accurate for its scope",
        "refutation_criterion_verbatim": (
            "The mixing, induction and application section or the bench-scale "
            "sequence omits a parameter the envelope's WFT, coverage or cure "
            "schedule requires, or a scale-sensitive step is unflagged."
        ),
        "attack_shape_verbatim": (
            "Remove the induction-time parameter from a copy and attack whether "
            "the envelope crosswalk fires; walk the envelope's application "
            "table and hunt for an uncovered parameter."
        ),
        "deliverable_under_test": {
            "amphora-report-packager/reference/mvp20/out/blueprint.md": corpus_sha["blueprint.md"],
            "amphora-cro-protocol-packager/reference/mvp20/out/cro_protocol.md": corpus_sha["cro_protocol.md"],
            "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json": corpus_sha["capture_template.json"],
        },
        "envelope_source": {
            "path": "amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json",
            "sha256": sha(ENVELOPE_PATH.read_bytes()),
        },
        "step_a_real_crosswalk": real_result,
        "step_b_positive_control": {
            "planted_defect": "deleted every induction-time-with-value mention (and bare 'induction' token) from a copy of the full corpus, per the attack shape's literal instruction",
            "how_planted": "regex-substituted 'induction ... 30 ...' occurrences and bare 'induction' tokens with '[REDACTED]' across blueprint.md / cro_protocol.md / capture_template.json copies",
            "detected": induction_flips_to_missing,
            "evidence": stripped_result,
        },
        "step_c_discrimination_control": {
            "patch_description": "synthetic fully-repaired copy adding explicit dry-to-touch/functional-cure/mix-ratio-tolerance/thinning-limit language to a copy of blueprint.md",
            "real_missing_keys": sorted(real_missing_set),
            "still_missing_after_patch": patched_still_missing,
            "discrimination_control_passed": discrimination_control_passed,
            "evidence": patched_result,
        },
        "verdict": "CLAIM_REFUTED" if real_result["refuted"] else "CLAIM_SURVIVED",
    }
    return out


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2, sort_keys=True))
