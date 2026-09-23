# amphora-dataset-recon

Evidence module for **AMPHORA-DIRECTIVE-2026-08-09** (Dataset Reconnaissance,
Multilingual Literature & Candidate Formulation — Mandate A). AUDIT-ONLY:
discovery and recommendation, **no acquisition** — nothing in this module ever
downloads, caches, or bulk-scrapes a candidate dataset. It reads enough to
evaluate (abstracts, data descriptors, license pages) and records what it
found, in the language it found it.

Lightweight module on the `amphora-solver-lab` precedent: no
`module-manifest.json` entry and no `docs/mission.md` — `unknown_module_policy:
REJECT` governs engine runtime loading, and nothing here is engine-loadable.
This directory is an evidence tree only.

## Layout

- `evidence/ledgers/` — the four deliverable ledgers plus the quarantined annex,
  all append-only JSONL/JSON:
  - `dataset-ledger.v1.jsonl` — one entry per recommended source: the
    portfolio's 8-key data-ask schema extended with `language`,
    `native_citation` (native script preserved), `custodian`,
    `standard_mapping{published_standard, astm_iso_equiv, comparability_rating}`,
    `translation_confidence`, `integrity_risks`, `coverage`, `rank`,
    `serves{module_gaps[], recipe_elements[]}`, `disposition{verdict, reason}`,
    `confidence_flag`, `snapshot_date`, `run_id`, `fire_id`,
    `framing:"AUDIT-ONLY"`.
  - `disposition-ledger.v1.jsonl` — every candidate ever evaluated gets exactly
    one of RECOMMENDED / CONDITIONAL / REJECTED with a stated reason; its first
    entry is the sha256-pinned candidate-intake manifest of every
    previously-furnished source.
  - `coverage-map.v1.json` — gap × best source; a gap with no public source is
    converted to a commissioned-measurement candidate, never left blank.
  - `search-record.v1.jsonl` — languages, repository classes, and the
    native-language query forms actually used, so the next run extends rather
    than repeats.
  - `discovery-annex.v1.jsonl` — quarantined (directive §9): superior
    non-conforming chemistries and adjacent finds live here and may never be
    cited by the primary recipe or ledger.
- `evidence/phase0/repairs/<ITEM>/…` — campaign-item output contract
  (`done/` receipts, `attempts/` checkpoints, `work/STATE.json`).
- `evidence/audit/<slug>/` — falsification receipts.

## Integrity

Ledgers are `.jsonl` and therefore invisible to the module content-hash scan
(it hashes `.json` only) — so **every fire's credited artifact is a DSSE
`.json` receipt whose payload content-binds the ledger state**:
`{ledger_path, appended_line_range, sha256_of_appended_lines,
prior_prefix_sha256}`. That gives each ledger an append-only chain the next
audit fire re-verifies. Signing uses the standard pinned Phase-0 evaluator key;
receipts carry the directive citation (path, sha256, obligation id, and the
refutation criterion restated verbatim) like every other module.
