> For public, fresh-clone reproduction and model-free evidence checks, use the [outside-review guide](../../../docs/OUTSIDE_REVIEW.md). The original retained-archive instructions below preserve the historical execution record; private archives are not required by the public guide.

# Reproduce the frozen stage-2 campaign

This is post-pilot internal validation on development-exposed Bao data, not an untouched external confirmation. Preserve the original pilot and report every arm. No model search follows these results.

The archived `code/` contains the four model/protocol files hashed before stage-2 scoring. Its sibling `plga_prefix/` retains the original adapter, exact ranking module and software license. `raw/` contains the pinned Bao files and official metadata; `sources.json` retains public source URLs, the derivative commit and data checksums. Bao data v2 are CC BY 4.0, doi:10.17632/zzvtdrcy76.2; cite Bao et al., Scientific Data 12, 364 (2025), doi:10.1038/s41597-025-04621-9.

To verify retained outputs with the recorded Python/package environment:

```sh
python code/campaign.py summarize --artifacts .
python audit/independent_audit.py --artifacts .
python audit/feature_replay.py --artifacts .
```

These commands read existing predictions, verify full replay, recompute metrics/uncertainty and check prefix-only feature invariance. They fit no global models. Exact replay is established for the recorded Linux environment, not every operating system or library version.

For a full fresh reproduction, create a NEW artifact directory, copy raw data and publication_mapping.csv into it, then run `code/campaign.py prepare --artifacts NEW_DIR`. Only then run the locked learner grids with `code/launch.py --artifacts NEW_DIR`. The launcher pins CPUs 113/114 and assumes those CPUs exist on xbabe1; it caps address space/CPU/wall time and uses nice 10 and one scientific thread per process. No dependency installation, credential change or network service is invoked. Do not run prepare or model fits over the retained original main/replay directories.

The model grid has 780 fits; a full fresh-process replay doubles that to 1,560. `main/` and `replay/` each contain all predictions, all inner search scores, chosen configurations and timings. `exact_replay.json`, `independent_audit.json`, and `audit/feature_replay_proof.json` retain verification. No model pickle was created or loaded.

A desktop disconnect occurred during the replay, but the remote workers continued and finished. Both complete saved matrices were retained; no fits were restarted. The launcher exited before final summary postprocessing. After recovery, only the frozen summarize step and independent audit/plotting were run. `completion_record.json` records this recovery. Supplementary audit/report scripts and this README were added after the model/protocol lock and cannot change its archived hashes.

The new brief and archive are separate from the original audited pilot. All ten planned conditional intervals include zero and no comparison passes Holm correction. A specific Pareto advantage is not established. Full-text verification of the reviewer-supplied 2026 articles and a genuinely unexamined external panel remain outside the completed validation evidence.
