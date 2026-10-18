# Amphora: outside review

For the separate systems/investor assessment, see [Version 2 critical review](../v2/docs/Diligence/2026-10-18/V2/WORKPLAN_V2.md) and its [findings](../v2/docs/Diligence/2026-10-18/V2/RED_TEAM_FINDINGS.md). It distinguishes historical software evidence, the separately executed PLGA study and still-open integration/value/validation decisions.

This review package documents a retrospective PLGA drug-release forecasting benchmark and its limitations. Start with the manuscript, then inspect the protocols and run the model-free evidence checks.

| Review item | Entry point |
|---|---|
| IEEE-format white paper, 8 pages | [Compiled PDF](whitepapers/plga-prefix-forecasting/paper.pdf) |
| Readable manuscript | [Markdown companion](whitepapers/plga-prefix-forecasting/paper.md) |
| LaTeX, bibliography, figures and build instructions | [Manuscript source directory](whitepapers/plga-prefix-forecasting/README.md) |
| Compact public evidence and fresh-clone reproduction | [Review guide](review/plga/README.md) |
| Original exploratory pilot | [Protocol](../v2/benchmarks/plga_prefix/protocol.json) and [source](../v2/benchmarks/plga_prefix/benchmark.py) |
| Joint drug/publication sensitivity | [Protocol](../v2/benchmarks/plga_prefix/joint/protocol.json) and [source](../v2/benchmarks/plga_prefix/joint/joint_sensitivity.py) |
| Stage-2 matched ablations and nested selection | [Protocol](../v2/benchmarks/plga_strengthening/protocol.json) and [source](../v2/benchmarks/plga_strengthening/campaign.py) |
| Data provenance and attribution | [Public source pins](review/plga/evidence/SOURCE_DATA.json) and [notice](review/plga/NOTICE.md) |

## What the evidence supports

The evaluation predicts later release from the first three valid recorded observations and static formulation descriptors. The retained Bao cohort contains 320 formulations, 4,870 observations and 3,910 suffix targets. The third observation is not a fixed 24-hour sampling budget. Stage 2 separates 78 joint drug/DOI components and evaluates six representations with both random forests and LightGBM, with configuration selection inside each outer training fold.

All ten planned stage-2 conditional 95% intervals include zero, and none survives Holm correction. The paper therefore characterizes an inspectable evaluation workflow; it does not establish a Pareto-specific predictive gain. Stage 2 is post-pilot internal validation on a development-exposed corpus. Drug/DOI grouping is not chemical-cluster independence, computational replay is not independent scientific confirmation, and nonsignificance is not equivalence. There is no external/prospective ocular or clinical validation in this package.

## Review without training models

From a full clone of this repository:

```sh
python3 docs/review/plga/verify_evidence.py
```

This checks the published content hashes, all 28 aggregate result cells, group consistency and recorded replay receipts using only the Python standard library. The [review guide](review/plga/README.md) adds an independent NumPy bootstrap/Holm calculation and explicit, separate commands for optional full model reproduction. The setup was checked against cached public source files and reconstructed all three frozen split files exactly, without fitting global learners.

The manuscript builds offline from the included source, figures and aggregate tables. With TeX Live/IEEEtran, BibTeX and Poppler installed:

```sh
cd docs/whitepapers/plga-prefix-forecasting
make -B all check
```

## Publication scope

The repository contains the manuscript source, compiled PDF, original research code/protocols, derived per-formulation error tables, public data pins and verification scripts. Original raw tables, per-timepoint prediction archives, private diligence, emails, credentials, private Drive files and third-party full-text papers are not bundled. Obtain source measurements from the checksum-pinned public downloads and use an external work directory as described in the guide.

The manuscript is a technical draft by Jepson Taylor, prepared 18 October 2026; no submission, acceptance, affiliation or funding status is asserted. Dataset-derived metrics and figures attribute Bao et al.'s version-2 CC BY 4.0 data. The repository's existing license remains in [v1/LICENSE](../v1/LICENSE); publication does not grant a new blanket open-source license or resolve historical third-party rights elsewhere in the repository.

The broader repository also preserves historical implementation and planning materials. This research package does not establish the readiness or validation of every Amphora module. The [root README](../README.md) describes that repository layout.
