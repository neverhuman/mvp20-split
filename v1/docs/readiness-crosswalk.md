# Readiness, authority, solver-use, and phase crosswalk

These dimensions are independent. No operational label, authority tier, or solver flag promotes a module by itself. Effective authority and solver use are the minimum privilege permitted by the manifest, adapter, model card/receipt, portfolio policy, and emitted envelope.

## Operational readiness

| Status | Operational meaning | Phase implication |
|---|---|---|
| `ROADMAP` | Interface intent only; executable capability is absent or not integrated | Pre-Phase 0 |
| `OPEN` | Work is executable in part, but required integration is incomplete | Pre-Phase 0 |
| `BLOCKED` | A demonstrated correctness, contract, data, or authority defect prevents honest use | Pre-Phase 0 |
| `AUDIT` | Service can inspect evidence/results but cannot drive decisions | At most Phase 0 after its fail-closed gate passes |
| `GATED` | Deterministic constraint service is integrated behind explicit applicability gates | At most Phase 0 without independent scientific evidence |
| `SHADOW` | Service runs for observation and comparison, not live solver use | At most Phase 0 without independent scientific evidence |
| `READY` | Declared runtime interface and regressions pass | Necessary but insufficient for any phase promotion |
| `COMPLETE` | Declared operational scope is implemented and acceptance-tested | Necessary but insufficient for any phase promotion |

## Scientific readiness

| Status | Evidence meaning | Maximum supported phase |
|---|---|---|
| `UNVALIDATED` | No locked independent evaluation supports the hypothesis | Phase 0, and only after usefulness/fail-closed gates pass |
| `LOCKED_INTERNAL` | Reproducible internal benchmark exists, without independent closure | Phase 0 |
| `INDEPENDENTLY_VALIDATED` | Locked independent evaluation meets the declared parity target | Phase 1, if every other Phase-1 gate passes |
| `PROSPECTIVELY_REPLICATED` | Prospective superiority independently repeats with owned provenance | Phase 2, if IP review gates also pass |
| `NOT_APPLICABLE` | Scientific parity is not the right test for this deterministic control service | Phase 0; later assurance claims require their own locked gates |

## Authority tiers

Authority tiers describe kinds of statements, not a universal numeric quality ordering.

| Tier | Permitted statement | Prohibited escalation |
|---|---|---|
| `ROADMAP` | A capability or experiment is proposed | Runtime, evidence, or performance claim |
| `EVIDENCE_ONLY` | Bound evidence exists or is absent under declared intake rules | Scientific prediction, supplier closure, legal or release claim |
| `LIMITED_SANITY` | A bounded heuristic or sanity screen ran inside its domain | Performance, parity, or optimization authority unless separately granted |
| `RULE_CITED` | A cited deterministic rule supports the stated directional/constraint result | Measured performance or broader applicability |
| `MODELED_DIRECTIONAL` | A declared model supports within-domain directional comparison | Absolute performance or qualification |
| `REAL_ARITHMETIC` | Exact arithmetic follows from declared inputs and constants | Formulation fitness or measured performance |
| `CRO_GATED` | Candidate-bound external experimental evidence can support its stated result | Product, batch-release, regulatory, procurement, or legal authority |

## Solver-use ceilings

| Solver use | Permitted behavior | Ranking behavior |
|---|---|---|
| `DISABLED` | Package/report only | Never reaches selection |
| `AUDIT_ONLY` | Observe, log, and compare | Never reaches selection |
| `CONSTRAINT_ONLY` | Apply an authorized hard/soft gate | Cannot become a Pareto objective |
| `OBJECTIVE` | Use exact deterministic arithmetic at the typed objective path | Rankable only when every policy layer agrees |
| `R&D_OBJECTIVE` | Use a validated R&D model at the typed objective path | Rankable only with a current identity-bound receipt and every policy layer agreeing |

## Promotion phases

| Phase | Necessary evidence | Automatic non-authorities |
|---|---|---|
| Pre-Phase 0 | Executable work may exist, but a correctness, contract, or authority defect remains | Not yet an honest useful capability |
| Phase 0 — Useful | Smallest deterministic/evidence-bound capability is reproducible, in-domain, and fails closed | Human parity and experimental superiority |
| Phase 1 — Human parity | Best reproducible expert, standard, or research baseline is matched on a locked independent evaluation with uncertainty | Prospective superiority and defensible IP |
| Phase 2 — Defensible IP | Prospective superiority independently replicates, owned provenance/ablations freeze, and patent-versus-trade-secret review is documented | Product qualification, procurement, batch release, regulatory approval, or legal FTO |

Unknown module identities, missing receipts, policy contradictions, and unknown true claim locks fail closed at both Python and Rust ranking boundaries.
