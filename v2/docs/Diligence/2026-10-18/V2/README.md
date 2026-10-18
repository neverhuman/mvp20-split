# Amphora | Version 2 investor review

Start with the [critical investor brief](WORKPLAN_V2.md), [findings and disposition](RED_TEAM_FINDINGS.md), [five decision tracks](investment_gates.json), [complete scientific card](SCIENTIFIC_CARD.md), and [V1-to-V2 changelog](CHANGELOG_V1_TO_V2.md). The [review PDF](dist/Amphora_Investor_Red_Team_Workplan_V2_2026-10-18.pdf) presents the brief and all fourteen findings. [Current state](CURRENT_STATE.md) distinguishes implemented preparation from future evidence. The original scientific paper/results are unchanged.

Run from the repository root with Python 3.12. Default checks need no services, provider calls or model fitting. Optional bootstrap needs NumPy; a missing requested dependency returns exit 3, rejected evidence returns 2.

```sh
python3.12 -B v2/dev/diligence/cli.py check-plan
python3.12 -B v2/dev/diligence/cli.py check-decisions
python3.12 -B v2/dev/diligence/cli.py verify-source
python3.12 -B v2/dev/diligence/cli.py verify-source --bootstrap
python3.12 -B v2/dev/diligence/cli.py build-capsule --output /tmp/amphora-new-capsule
```

The capsule output must be a new path outside the checkout. Retain the reported manifest digest independently before using it as an external integrity pin:

```sh
python3.12 -I -B /tmp/amphora-new-capsule/verify.py --expected-manifest-sha256 RECORDED_DIGEST
python3.12 -B v2/dev/diligence/cli.py check-document --pdf v2/docs/Diligence/2026-10-18/V2/dist/Amphora_Investor_Red_Team_Workplan_V2_2026-10-18.pdf --receipt v2/docs/Diligence/2026-10-18/V2/dist/Amphora_Investor_Red_Team_Workplan_V2_2026-10-18.render.json
python3.12 -B -m unittest discover -s v2/dev/tests/diligence -p 'test_*.py'
```

For optional document regeneration, use a separate environment with ReportLab and Matplotlib, and choose a new output path:

```sh
python3 v2/dev/diligence/render_plan.py --output /tmp/amphora-review-v2-new.pdf
```

Renderer dependencies are optional and do not enter the standard-library reviewer path. A freshness pass does not replace visual review of every page. See [actual evidence](evidence/README.md) for 49 targeted tests, code bindings, source checks and the optional arithmetic outcome. The tool is not a hostile-code sandbox, publisher authentication, current service-health test, or scientific/commercial qualification. None of the five decision tracks is met.
