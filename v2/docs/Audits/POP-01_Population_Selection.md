# POP-01 initial whole-pool selection checkpoint

Verified: 2026-10-15 14:54:01 America/Chicago. Search0.17; POP-01.01/E2.2.

select-primary authenticates accepted assembled fitness, verifies the complete
initial pool/evaluation/resolution/observation chain and ranks the entire pool.
Excluded candidates retain their reasons. Initial RNG replays every birth slot.
A single closed Runtime cut counts physical attempts (including the current claim)
and actual materialized graph nodes. Unrelated parallel work rejects; serial
generation-loop ancestors and future control must depend on selection. The cut
is correlation, never a budget grant. Ordinary accepted completion retains proposed
selection/checkpoint outputs; there is no separate Search execution ledger.

prepare-selection emits the existing public request, including generation0's null
predecessor. This explicit typed adapter avoids changing graph scalar formats.
SelectedPrimaryGeneration adds an unambiguous stopped boolean, separate from the
selection receipt's ranking disposition, plus reason/work-cut/source proof.

-355 source and353 independent installed Search checks pass;74 focused workers
 include five closed-cut and five selector checks. Source regressions cover serial
 loops, concurrent work, own-attempt/fence identity, missing finish dependencies,
 complete ranks/exclusions and unaccepted sources.
-13 boundary/ownership checks and dependency guard pass;750 system schemas and
 twelve predecessor tool schema byte pins remain unchanged. Workspace-only frozen
 reuse audit is separately verified against all seven original hashes.
-Independent installation: .test-results/pop01-selection-search-install-20261015a;
 excludes Data/Runtime/Planning/SQLAlchemy/FastAPI.
-Actual success: .test-results/pop01-selection-http-20261015a/population-selection-evidence.json;
 16 selected,22 physical attempts,43 graph nodes,99 retained Artifacts.
-Actual required failure: .test-results/pop01-selection-failure-http-20261015a/population-selection-evidence.json;
 15 selected/one explicit exclusion,22 attempts,43 nodes,98 retained.
-Actual conditional not taken: .test-results/pop01-selection-conditional-http-20261015a/population-selection-evidence.json;
 zero selected/16 exclusions,6 attempts,75 nodes,83 retained. Logical terminal
 evaluations remain16 in each case; counts are not inferred from that logical total.
-All roots confirmed and runs completed. No worker retention grant/provider calls;
 all temporary processes/containers removed, labeled volumes retained.

Bounded drift audit: whole-pool ranking, source/actor authority, explicit unavailable
fitness, RNG continuity and observed counters match the reviewed boundaries.
The legacy no_feasible_survivors disposition here means no eligible scored survivor;
retained exclusions disclose missing evidence, not physical scientific infeasibility.
Actual nested-loop, later-generation parent union and successor preparation remain
unqualified. Whole E2.2 stays0 and E2 stays25%; no serving cutover.
