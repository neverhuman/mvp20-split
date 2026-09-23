# schemas/

JSON Schema definitions for the contracts the Amphora runtime and evidence tree exchange.
These are the authority on shape; the prose in `docs/mission.md` is the authority on meaning.

Roughly three families:

- **Module contracts** — `module-manifest`, `module-capability-profile`,
  `module-claim-contract.v1`, `module-dataset-lock.v2`, `module-evidence-inventory`.
- **Phase-0 evidence** — `module-phase0-bundle.v1`, `module-phase0-evaluation-receipt.v1`,
  `module-phase0-review-receipt.v1`, `module-phase0-supersession.v1`,
  `module-movement-event.v1`.
- **Data rights and provenance** — `rights-decision.v2`, `rights-review-receipt`,
  `rights-review-trust-store`, `source-intent.v2`, `normalized-dataset-manifest.v2`,
  `acquisition-unit.v2`.

`engine-result.schema.json` covers the engine's output envelope.

Hand-edited. Changing a schema is a reviewed act: `xtask audit` validates real artifacts
against these, so a loosened pattern silently widens what the gate accepts.
