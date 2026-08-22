# C7 fire 3 of 3 — final reconciliation + signing fix

This directory contains no new science. Fires 1 and 2 both ran genuine,
decisive falsification attacks on the compound claim in
`openpoly-experimental-tg-ml-baseline-kpi.v1.json` ("within-corpus
scaffold-safe performance transfers to out-of-corpus chemistry"), but both
receipts were downgraded by the launcher for a signature-format bug: the
top-level `.signature` field held a bare base64 **string** instead of the
required DSSE envelope **object** `{payloadType, payload, signatures:[...]}`
(a correctly-formed envelope existed alongside it under a separate
`dsse_envelope` key, but the mechanical check only inspects `.signature`).

This fire:
1. Re-verifies both fires' source diagnostics (`diagnostic.canonical.json` in
   each prior fire's directory) are byte-identical to the sha256 their
   receipts recorded — confirming no drift/tampering before reuse.
2. Reproduces fire 1's Tg finding verbatim: **REFUTED**, 6.66x / 16.60x
   degradation (both directions, true independent second corpus, OpenPoly
   <-> Polyuniverse Epoxy), anti-predictive past the training label range.
3. Reconciles the two conflicting density verdicts:
   - Fire 1 (leave-polymer-class-out on RadonPy's own 14 class labels):
     1.80x degradation, **SURVIVED** the 2x bar.
   - Fire 2 (hierarchical macro-chemotype bisection, 16 vs 1061 polymers,
     maximally dissimilar halves of the Tanimoto distance matrix): 13.74x /
     7.59x degradation, **REFUTED**.
   - These are not contradictory findings on the same test — they are two
     different severities of out-of-distribution probe. Leave-class-out
     removes a fine-grained label group whose density neighborhood remains
     densely populated by similar polymers from *other* classes still in
     training (fire 2's own leave-one-Butina-cluster-out dead-end, 0.95x,
     confirms this mechanism directly). Macro-bisection removes an entire
     structurally coherent region of chemical space, which is the closest
     within-corpus analogue to a genuine second-corpus swap available given
     RadonPy PI1070 is the module's only rights-cleared density corpus.
   - Per falsification-first principle, the strongest attack that was
     actually capable of finding a violation governs: density
     transferability is **REFUTED**, superseding fire 1's weaker-probe
     survival (retained as granularity evidence, not the governing verdict).
4. Issues ONE new receipt,
   `c7_final_tg_density_external_validity_verdict_receipt.v1.json`, with the
   correct top-level `.signature` = DSSE envelope object (verified `type ==
   "object"`, independently re-verified against the Ed25519 public key), and
   its own two-replay byte-stability gate over the receipt body itself
   (`receipt_body.canonical.json` == `receipt_body.runB.json`, sha256
   a833ade4...).

## Files
- `reconcile_and_sign.py` — builds, two-replays, and DSSE-signs the final
  verdict receipt from fire 1 and fire 2's already-verified results.
- `receipt_body.canonical.json` / `receipt_body.runB.json` — two independent
  deterministic serializations of the receipt body (pre-signature), byte
  compared before signing.
- `c7_final_tg_density_external_validity_verdict_receipt.v1.json` — the
  signed final verdict receipt. `overall_verdict: CLAIM_REFUTED`,
  `tg_verdict.verdict: REFUTED`, `density_verdict.verdict: REFUTED`.

## Result
Overall verdict: **CLAIM_REFUTED** for both Tg and density. C7's
done_criterion ("Signed external-validation receipts for Tg and density with
explicit within-vs-external degradation factors + ledger entries") is now
met with a correctly-signed receipt.

The density-corpus data-acquisition ask filed by fire 1 remains open in
`/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl` and is unaffected by
this fire — macro-bisection is a proxy escalation within RadonPy PI1070, not
a substitute for a literal second density corpus.
