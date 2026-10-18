# PLGA prefix forecasting white paper

**Draft author:** Jepson Taylor. **Prepared:** 18 October 2026. This is an Amphora technical white paper in IEEE conference format. No affiliation, funding, ethics approval, submission or acceptance status is asserted.

The complete manuscript is `paper.tex`, with bibliography `references.bib`, compiled `paper.pdf`, and a readable companion in `paper.md`. The paper presents an implemented evaluation protocol and measured representation characterization. It does not claim a statistically established Pareto-specific advantage.

## Scope and result

The paper combines a fixed first-three-record information boundary, joint connected drug/publication grouping, matched kinetic feature/selector ablations, nested configuration choice and exact computational replay. It distinguishes the original exploratory pilot from stage-2 post-pilot internal validation. Every Bao curve was development-exposed before stage 2. No experiments or model searches were run to prepare this manuscript.

The retained cohort contains 320 formulations, 4,870 valid distinct-time observations and 3,910 suffix targets. In 317 formulations the prefix includes the recorded origin. The third recorded time has median 1.928 days; the task is not a fixed 24-hour assay budget. Stage 2 uses 78 joint drug/DOI components and six arms for both RF and LightGBM. All ten planned conditional 95% intervals include zero; none survives Holm correction. The strongest contribution is the auditable evaluation workflow, not confirmed predictive superiority.

## Build and check

An installed TeX Live distribution with IEEEtran, BibTeX, booktabs, tabularx, TikZ, xurl, hyperref and microtype is sufficient. No shell escape is enabled. Poppler (`pdfinfo`, `pdftotext`, `pdftoppm`) and Python 3 standard library support checks/rendering. The included figures and aggregate table source allow building without raw datasets, trained models, network access or the original benchmark environment.

```sh
make all
make check
mkdir -p qa/pages
pdftoppm -r 120 -png paper.pdf qa/pages/page
```

`make check` validates aggregate metric cells, contrast values, cohort facts, reference completeness, author metadata, syntax, branding/private-link scans, absence of overfull boxes and unresolved references, and absence of raw dataset or private report formats. Page images require human/agent visual inspection; the automated check does not substitute for that review. `build_check.json` records the latest compiled PDF/source digests. Compiler logs and QA images are ignored. The generated `paper.bbl` is included to preserve the formatted bibliography.

## Regenerate figures and aggregate claims

`scripts/generate_figures.py` reads only retained audited artifacts. It generates three data/metric figures, `tables.tex`, and `claim_ledger.json`, with **zero model fitting**. The schematic is authored directly in LaTeX. The release examples use the smallest formulation ID within each tertile of third-observation time, with no selection by prediction errors. Their connected lines are visual guides over recorded target times, not interpolated training labels.

On the evidence-owning server, using the recorded scientific Python environment:

```sh
/home/ubuntu/amphora-benchmarks/plga-prefix-20261017-artifacts/env/bin/python \
  scripts/generate_figures.py \
  --pilot-audit /home/ubuntu/amphora-benchmarks/plga-prefix-20261017-independent-audit/independent_audit.json \
  --pilot-artifacts /home/ubuntu/amphora-benchmarks/plga-prefix-20261017-artifacts \
  --stage2-artifacts /home/ubuntu/amphora-benchmarks/plga-strengthening-20261017-artifacts \
  --out .
make all check
```

These paths identify external evidence locations; none of those raw tables, individual prediction files, environment directories or private reports is copied into this manuscript tree. `claim_ledger.json` contains aggregate claims and source digests only. The figures are newly drawn from recorded predictions/metrics; no figures are copied from prior papers.

## Immutable research sources

- Merged research revision: [`879b6d254e10848020635cc2ae2c654968a0cfc1`](https://github.com/neverhuman/mvp20-split/tree/879b6d254e10848020635cc2ae2c654968a0cfc1).
- Pilot source: [`9e4d4afb444d683761078d2a3bbaa151a3d6177c`](https://github.com/neverhuman/mvp20-split/commit/9e4d4afb444d683761078d2a3bbaa151a3d6177c), `v2/benchmarks/plga_prefix/`.
- Stage-2 source: [`dfac76aebc18dcf8b2e021c016f53aaa6b14bd3f`](https://github.com/neverhuman/mvp20-split/commit/dfac76aebc18dcf8b2e021c016f53aaa6b14bd3f), `v2/benchmarks/plga_strengthening/`.
- Official data: Bao et al., Mendeley Data version 2, [doi:10.17632/zzvtdrcy76.2](https://doi.org/10.17632/zzvtdrcy76.2), CC BY 4.0. Source descriptor article: [doi:10.1038/s41597-025-04621-9](https://doi.org/10.1038/s41597-025-04621-9).
- Processed-table derivative: `mdsamad001/Drug_Release_Dynamics_Prediction`, commit `605cd707c47a4379212193560cd332d7a2d973fd`.

Full protocol/code SHA-256 identifiers are printed in the manuscript appendix. The claim ledger retains digests of the independent audits and stage-2 RF prediction file. `reference_verification.json` records primary-source checks for the four principal related-work/data references. Source PDFs/HTML remain outside this tree.

## Interpretation and future validation

Existing early-input and nested-validation work is cited, including Bannigan 2023, Alabsi 2026 and MC-NODE 2026. The paper makes no first-predictor, first-hybrid-kinetics, first-residual or first-grouped-benchmark claim. The Alabsi-inspired comparator is not an exact reproduction, and differences in documentation are not treated as evidence of leakage. Joint drug/DOI separation is not chemical-cluster independence. Computational replay is not independent scientific confirmation, and nonsignificance is not equivalence.

Next scientific work is a frozen representation and fixed sampling schedule on a genuinely unexamined, overlap-screened new-study PLGA panel with assay replicate uncertainty. Ocular transfer would require separate external/prospective evidence. This documentation task does not authorize new model searches or platform-plan work.

## License and local publication boundary

The repository's existing software/documentation license is retained; this draft does not introduce a new open-source license. Dataset-derived figures attribute Bao et al. and the version-2 CC BY 4.0 data. Primary reference metadata and paraphrased discussion are cited in the manuscript; third-party full-text PDFs are not bundled.

This manuscript is prepared on the local branch `docs/ieee-plga-whitepaper-20261018`, based on the merged research revision above. New manuscript changes remain local until separate public push/merge approval. Existing canonical checkout changes are preserved by using a dedicated documentation worktree.
