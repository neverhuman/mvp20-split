# The showcase demo

`demo/founder-showcase` (tip `e8e3acd`, unmerged) carries a terminal UI that runs four
worked examples against the real engine and pinned data. It is the fastest way to see what
this system actually does, and it is deliberately honest about what it is not: throughput
panels are engineering metrics, never novelty, ranking, or validated science.

```bash
git fetch origin demo/founder-showcase
git switch demo/founder-showcase
ops/restore-datasets.sh --apply --only feedback/v1/derived/
cargo run --release -- showcase
```

## The four examples

**E1 — live VOC-minimising solver.** Searches a real formulation grid (billions of cells)
under the envelope constraints, showing the optimal blend update in real time. This is the
one that makes the scale legible.

**E2 — hazard-constrained hardener selection.** Applies the EHS and hazard constraints to
hardener choice and returns an **empty feasible set**, honestly, rather than relaxing a
constraint to produce an answer. The most characteristic thing in the repository: the system
is built to say "no admissible candidate" and mean it.

**E3 — 2⁴ factorial process screen.** A full factorial over four process factors, scored
through the same gates as any other candidate.

**E4 — live compounds/second molecule screening.** Streams molecule candidates through the
design gate and reports sustained throughput.

Plus a **red-team board** summarising the adversarial probes and their verdicts.

## Why it is not on `main`

The branch also carries three security-hardening commits:

| Commit | Item | What it fixes |
|---|---|---|
| `78d9ab48` | R1 / T-01B | A caller-supplied `canonical_structure_hash` could reach the typed field, the result echo, export report, and provenance root. An equivalent fix is now on `main` as `acf268f6`. |
| `30c2ae93` | R2 / T-13 | Recomputes the event-hash chain and binds run identity in `verify_run`. |
| `403e0ccc` | R3 / T-05 | Attests molecule facts by recomputation before the equivalent balance. |

`R2` and `R3` have **declared breaking effects**: legacy run archives written under the
superseded event-hash format fail loudly against them. Merging is therefore a reviewed
decision about how to treat historical archives, not a cleanup — which is why the branch was
published rather than merged.

`R1` was separable and is already on `main`; R2/R3 still require the historical-archive
decision above. See [BACKLOG.md](BACKLOG.md).

## Also on the branch

`e38892fa` caches the novelty corpus fingerprints — bit-identical results with roughly 5×
fewer RDKit calls.
