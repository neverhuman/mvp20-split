# governance-axis-live-corpus-v1

**Live-runtime per-axis adversarial corpus over the OUTER 23 portfolio-governance
attack axes** declared in `amphora-redteam-audit`'s Phase-0 benchmark lock.

Status: AUDIT_ONLY. No Phase-0 promotion, no manifest change (portfolio stays at
66 receipts / 11 modules), no shipped artifact mutated.

## Why this oracle exists

`axis-adequacy-subsumption-v1` showed the module's benchmark lock declares **46**
attack axes while its own KPI cross-checks only the contiguous inner suffix of
**24** (the meta-audit block). The remaining **23 outer portfolio-governance
axes** (`attacks[0:23]`: `STALE_PARENT` … `SUPERSESSION_ARCHIVE_SUBSTITUTION`)
had **no oracle at all** — they were DECLARED_ONLY. This oracle closes that gap,
and does so against the live binary rather than shipped bytes.

Subject under test: the real Rust reference monitor `amphora-phase0-reviewer`
(release build), which is the component that adjudicates the outer block. Prior
oracles in this module (`meta-integrity-oracle-parity-v1`,
`dispatch-boundary-fail-closed-v1`, `axis-adequacy-subsumption-v1`) were offline
CPython over shipped evidence; this is the module's **first live-runtime
harness**.

## Method

Every probe runs against an `rsync` scratch copy of the workspace
(`redteam-live-scratch/ws`), verified byte-identical to the portfolio tree for
`amphora-redteam-audit/`, `config/` and `registry/` before the run. Nothing under
`mvp20-split/` is mutated.

Gates:

- **G1 shipped-state characterisation** — the live reviewer's verdict on the
  shipped evidence, for this module and three sibling deterministic controls.
- **G2 signing parity** — independently re-derive the shipped evaluator DSSE
  signature. Ed25519 is deterministic, so a byte match proves the Python
  canonical form equals the Rust one and that the re-chaining adversary below is
  faithfully modelled.
- **G3 repaired accepting baseline** — because the shipped evidence halts the
  reviewer for *every* module (see Findings), the scratch copy is repaired into a
  state the live reviewer accepts, so per-axis rejections are attributable to the
  probe rather than to pre-existing drift. The control accepts, and the signed
  review receipt is byte-stable across two reviewer replays.
- **G4/G5 per-axis corpus** — 24 probes covering 23/23 outer axes, each restored
  to the accepting baseline first, each instrumented with the exact set of files
  it changed (so a surviving mutant cannot be confused with an ineffective one).
  Two adversary models:
  - `NAIVE_CONTENT_TAMPER` — edits an artifact and nothing else.
  - `RECHAINED_EVALUATOR_KEY_HOLDER` — the strongest realistic insider: holds the
    Phase-0 **evaluator** signing identity, re-derives every hash the bundle and
    evaluation receipt declare, and re-signs. Only defences independent of the
    evaluator's own attestations survive this.
- **G7 re-execution root binding** — diagnosis of the surviving live-re-execution
  axis.
- **G6 residue control** — the corpus leaves no state behind (the post-corpus
  control review reproduces the baseline receipt hash exactly).

Theory anchors: Anderson 1972 (ESD-TR-73-51, reference monitor / complete
mediation); Saltzer & Schroeder 1975 (Proc. IEEE 63(9):1278-1308, fail-safe
defaults, separation of privilege); DeMillo, Lipton & Sayward 1978 (IEEE Computer
11(4):34-41, mutation adequacy); Rapps & Weyuker 1985 (IEEE TSE 11(4):367-375);
Zhu, Hall & May 1997 (ACM CSUR 29(4):366-427); Haber & Stornetta 1991 (J.
Cryptology 3(2):99-111); NIST SP 800-53r5 CA-8 / SI-7.

## Verdict: HYPOTHESIS_PARTIALLY_REFUTED

**20 of 24 mutants killed; 23/23 outer axes probed; 19 axes have a live,
fail-closed detector**, with detection mechanisms independently classified
(rights predicates x4, policy x2, claim-lock x2, replay-identity x2, plus
parent-hash binding, DSSE crypto, path confinement, trust-store identity
separation, role binding, dispatch allowlist, schema wall, live re-execution).
The re-chained evaluator-key holder is stopped on **14 of 18** attempts.

Four axes are **not** mediated as declared:

1. `STALE_PARENT` (structural) — parent hash binding is an evaluator
   self-attestation. It kills the naive tamper, but an evaluator-key holder who
   re-declares hashes and re-signs is accepted. No external anchor exists.
2. `FALSE_MOVEMENT_CLAIM` — `movement/ledger.v1.json` is outside the reviewer's
   read surface entirely; a forged head is accepted.
3. `STRIPPED_MISSION_LOCKS` — `docs/mission.md` front-matter locks are never read
   by the reviewer. Setting `authority_ceiling` to `RELEASE` and deleting
   `solver_use_ceiling` is accepted, even though this axis is a *lock-required*
   attack for current deterministic controls.
4. `FAILING_DETERMINISTIC_DIAGNOSTIC` — the reviewer re-executes the locked
   benchmark with `current_dir(root)`, but the benchmark resolves its workspace
   from `env!("CARGO_MANIFEST_DIR")` (`amphora-cli/src/main.rs`, `fn
   workspace_root`). G7 shows the emitted diagnostic is byte-identical after
   tampering with `config/benchmark-lock.v1.json` inside the reviewed workspace,
   still declares the pristine hash for that path, and is emitted even with the
   working directory outside any workspace. **Live re-execution is bound to the
   compile-time tree, not the tree under review.**

## Independent finding (G1): portfolio-wide evidence drift

The live reviewer rejects the **shipped** evidence of all four modules tested
(`amphora-redteam-audit`, `-source-ledger`, `-report-packager`,
`-evidence-intake-validator`) with `recorded benchmark is not bound to the
evaluation receipt`. For this module the signed receipt declares
`benchmark_result_sha256 = 2bba87aa…` while the on-disk
`evidence/phase0/benchmark/result.v1.json` hashes to `701482a2…`, and the
recorded result predates three reviewer-required fields (`bundle_sha256`,
`replay_identical`, `scientific_outcome`). The shipped Phase-0 review receipts
therefore cannot be reproduced by today's reviewer. This is reported as-is; no
shipped artifact was repaired.

## Files

- `oracle_governance_axis_corpus.py` — the harness (executes the real reviewer).
- `result.v1.json` — full result, byte-identical across two independent replays.
- `sign_governance_axis_corpus.py` — DSSE Ed25519 AUDIT_ONLY signer.
- `../../evidence/phase0/independent/governance-axis-live-corpus-v1.dsse.json` —
  the signed receipt.

## Ceiling

The corpus is bounded by what the reviewer reads. Mutating the compiled Rust
diagnostic itself (rebuilding `amphora-assurance-capabilities` with a subverted
corpus generator) and per-axis error-taxonomy parity against a second independent
reviewer implementation remain out of scope; those are Phase-1 work.

## Reproducing

The scratch workspace is disposable and is rebuilt with:

```
rsync -a --exclude target/ /home/ubuntu/amphora/build/mvp20-split/ \
      /home/ubuntu/amphora/build/redteam-live-scratch/ws/
cargo build -p amphora-cli --release        # provides target/release/amphora-tui
python3 oracle_governance_axis_corpus.py    # prints result.v1.json to stdout
```

The signed receipt binds `oracle_script_sha256` and `oracle_result_sha256`; this
README is documentation and is not covered by the signature.
