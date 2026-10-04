# Synthetic extraction evaluation corpus

Version1, reviewed2026-10-04 04:18:00 (America/Chicago), BP-07.02/B1.03c.

Eighteen manually authored synthetic passages cover nine semantic categories,
one calibration and one held-out case per category. The oracles were specified
as expected meanings, required context, permitted alternatives and hard
rejections, separately from any adapter outputs. No model responses or gold
scientific measurements were used. Review is by the coding agent against the
literal synthetic passages; it is not independent human or domain-expert review.

Only source files are model input. Oracle files and split labels must never enter
the extraction prompt. Calibration cases may inform prompt development; freeze
the prompt/profile before evaluating held-out cases. Held-out here denotes the
evaluation split, not a claim that a developer or pretrained model never saw the
text. New tuning against those cases requires a new held-out corpus version.

The manifest pins exact UTF-8 source and oracle bytes. Source identities/digests
are disjoint between splits. Preserve LF on checkout. Changing a pinned passage,
oracle, category or split requires a deliberate corpus version and review;
do not regenerate expected meanings from implementation outputs.

Review checks: negative claims stay bounded to measured conditions; species,
dose, route, time and method do not default; correlation does not become proven
causation; alias collisions do not merge identities; contradictory reports remain
separately attributed; retraction prose without an exact accepted assertion
target stays unresolved; missing context remains missing; opinions are distinct
question/answer/evidence-need proposals; source instructions grant no authority.

B3 owns executable per-category candidate evaluation and precision/recall/
abstention reporting. This corpus checkpoint verifies integrity and evaluation
separation, not extraction quality or live prompt-injection resistance. The hard
gate remains zero unauthorized accepted changes or fabricated accepted citations.
Real model thresholds and scientific validation remain BP-07.05.
