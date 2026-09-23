#!/usr/bin/env python3
"""Fix-up: correct the confidence_interval_summary / interpretation text in
power_analysis.json (and its mirror in capture_template.json) to match the
ACTUAL computed achieved_power_and_confidence_interval_table -- the first
draft mis-stated n=6 as under-powered at sigma=0.5 when the real numbers
show n=6 clears 80% power (93.37%) at every assumed sigma up to 0.5; only
the n=3 MINIMUM FLOOR dips below 80% power (68.78%) at sigma=0.5. Recomputes
and re-locks nothing else. Idempotent-safe: only rewrites these two text
fields plus recomputes locked_gates_hash is untouched (gate content did not
change in this pass).
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-cro-protocol-packager"
OUT = MOD / "reference/mvp20/out"
CAPTURE = OUT / "capture_template.json"
POWER = OUT / "power_analysis.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


power = json.loads(POWER.read_bytes())
capture = json.loads(CAPTURE.read_bytes())

table = power["achieved_power_and_confidence_interval_table"]


def lookup(sigma, n):
    for row in table:
        if row["assumed_sigma_log10_abs_z"] == sigma and row["n_per_track_per_arm"] == n:
            return row
    raise KeyError((sigma, n))


r6_01 = lookup(0.1, 6)
r6_05 = lookup(0.5, 6)
r3_05 = lookup(0.5, 3)

new_summary = (
    "At the pre-registered DEFAULT of 6 panels/track/arm, achieved power to detect the pre-registered "
    f"1.0 log10|Z| gap stays >=93% across the entire assumed sigma range 0.1-0.5 (e.g. {r6_01['achieved_power_to_detect_delta_1p0']*100:.1f}% "
    f"at sigma=0.1, {r6_05['achieved_power_to_detect_delta_1p0']*100:.1f}% at sigma=0.5), with 95% CI half-width on the measured gap "
    f"ranging {r6_01['ci95_halfwidth_log10_abs_z']}-{r6_05['ci95_halfwidth_log10_abs_z']} log10 ohm-cm2 over that same sigma range. "
    f"The pre-registered MINIMUM FLOOR of 3 panels/track/arm is materially weaker: at the pessimistic end of the assumed range "
    f"(sigma=0.5) it achieves only {r3_05['achieved_power_to_detect_delta_1p0']*100:.1f}% power (below the conventional 80% threshold) with a "
    f"{r3_05['ci95_halfwidth_log10_abs_z']} log10 CI half-width -- i.e. the plan's own stated preference for 6 panels/track/arm "
    "'if budget allows' over the 3-panel floor is exactly the difference between adequately-powered and under-powered at the "
    "pessimistic end of the literature-cited sigma range. Stated honestly, not oversold: this is a risk the 3-panel floor "
    "carries, not a guarantee the default avoids it, since the true sigma is unmeasured until bench data exists."
)

new_interpretation = (
    "This is NOT a claim that MVP20's true EIS replicate sigma is known -- no EIS has been run on any MVP20 track or "
    "candidate. It is a pre-registered sensitivity table: across the full sigma range plausibly implied by Floyd et al. "
    "2009's documented EIS log-resistance replicate scatter, the pre-registered DEFAULT panel count (6/track/arm) keeps "
    "power >=80% at every assumed sigma tested here, while the MINIMUM FLOOR (3/track/arm) drops below 80% power at the "
    "pessimistic end (sigma=0.5). This quantifies the actual statistical stakes of the pre-registered 'default vs "
    "minimum-floor' panel-count choice before any panel is cut, rather than asserting a single point uncertainty value. "
    "Once EIS is run, sigma becomes measurable from the bench's own replicate data and this a priori table should be "
    "superseded by a post-hoc calibrated interval, not before."
)

power["confidence_interval_summary"] = new_summary
power["interpretation"] = new_interpretation
capture["statistical_decision_rules"]["confidence_interval_summary"] = new_summary

POWER.write_text(json.dumps(power, indent=2, sort_keys=True))
capture_bytes = json.dumps(capture, indent=2, sort_keys=True).encode()
CAPTURE.write_bytes(capture_bytes)

print(json.dumps({
    "power_analysis_json_sha256": sha(POWER.read_bytes()),
    "capture_template_json_sha256": sha(capture_bytes),
    "new_summary": new_summary,
}, indent=2))
