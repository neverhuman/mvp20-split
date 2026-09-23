# density-butina-cluster-external-validity-c7-v2

CAMPAIGN C7, fire 2 of 3. Escalates fire 1
(`amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v1`),
which left the density half of the attacked claim (`openpoly-experimental-tg-ml-baseline-kpi.v1.json`,
"Within-corpus scaffold-safe performance ... transfers to out-of-corpus
chemistry") **SURVIVED** under the hardest proxy then available
(leave-polymer-class-out on RadonPy PI1070's curated labels, 1.80x < 2x bar)
and explicitly flagged density for revisit once a harder proxy or a second
corpus became available. No second rights-cleared polymer-density corpus has
been acquired since (re-verified: the fire-1 acquisition-queue entry is still
open), so a literal cross-corpus swap remains BLOCKED_DATA. This fire instead
escalates the within-corpus proxy methodology.

Two designs were run, both fully reported (no silent discard):

1. **Leave-one-Butina-cluster-out** (Butina 1999, Tanimoto dist_thresh=0.4 on
   the production Morgan r=2/512-bit fingerprints): a documented dead end.
   Degradation = **0.95x** (i.e. no degradation at all) -- fine chemical
   islands (median eligible-cluster size ~14, 411 clusters total, 277
   singletons) remain densely surrounded by highly similar training
   neighbors from adjacent clusters, so holding one out barely perturbs
   local interpolation. This is a *weaker* proxy than fire 1's leave-class-out
   and cannot serve as a falsification attempt on its own.

2. **Hierarchical macro-bisection** (average-linkage agglomerative clustering
   on the full 1077x1077 Tanimoto distance matrix, cut to 2 macro-chemotypes)
   -- the fire's primary, pre-registered attack. This groups the entire
   corpus into two large, internally-diverse regions that are collectively
   as mutually dissimilar as the clustering can make them: the closest
   within-corpus analogue to a genuine second-corpus split. The bisection is
   naturally imbalanced (16 vs 1061 polymers) -- itself a finding: RadonPy
   PI1070 contains one coherent minority macro-chemotype of 16 polymers in
   the upper density tail (1.277-1.914 g/cm3) that is structurally distinct
   from the rest.

   Both directions blow through the pre-registered 2x refute bar:
   - Train on the 16-polymer macro-chemotype, cold-predict the other 1061:
     MAE 0.5604 g/cm3 = **13.74x** within-corpus MAE (0.0408), R2 = -12.15.
   - Train on the 1061-polymer bulk, cold-predict the 16-polymer outlier
     macro-chemotype: MAE 0.3098 g/cm3 = **7.59x** within-corpus MAE, R2 = -5.01.

**Verdict: REFUTED** (density). Combined with fire 1's outright Tg refutation
(true second corpus, 6.66x/16.60x), the compound claim is now refuted for
BOTH named properties via genuinely falsifying attacks.

Run:
```
python3 compute_density_cluster_external_validity.py   # writes diagnostic.out.json
cp diagnostic.out.json diagnostic.canonical.json        # first replay
python3 compute_density_cluster_external_validity.py
cp diagnostic.out.json diagnostic.runB.json              # second replay
diff diagnostic.canonical.json diagnostic.runB.json       # byte-identical
python3 sign_density_cluster_external_validity.py
```
