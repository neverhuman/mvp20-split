# Planning Research question reads

- Status: BP-07.02/B2.02a.ii verified with actual Research0.33 public reads.
- Owner: Planning. Research owns declarations and assessment; no peer SQL or write interface is used here.

QuestionReader consumes the exact selected ResearchQuestionRefs from an immutable extraction task. ResearchTransport allows only authenticated POST /v1/questions/read through the shared owner-local bounded reader. Its profile caps15 seconds,64 calls,4MiB aggregate and1MiB per body. Returned identity, context scope, criteria uniqueness and predecessor shape must match the selected revision before a record becomes available. No mutable latest-revision selection or automatic retry occurs.

QuestionContext retains byte-owned available records and explicit gaps. Missing exact records do not invent question bodies or erase unrelated usable proposals. Scope/grant denial, owner outage or exhausted read budgets stop further calls and mark remaining selections unavailable with their explicit reason. Other record-specific failures withhold that record. ResearchProposalValidator retains those context findings and withholds dependent items while allowing unrelated local questions to proceed. Partial availability is not permission to register or accept anything.

All network calls are outside SQL, and no durable state or migration is introduced. The immutable owner record is the source of question identity; its public reference has no content digest, so this reader retains exact bytes rather than fabricating a hash-bearing owner reference. Scientific meaning, source rights, executable validation methods and owner registration remain separate gates. Tests belong under tests/research_access, with synthetic protocol cases distinct from actual installed owner proof.

Verified 2026-10-04 07:31:11:70 focused cases,212 shared/read statements28 branches98%;560 regression and542 independent tests. Actual public read proofs passed with8 isolated Planning workers and2 owner hosts per owner. Remaining coverage gaps are defensive socket cleanup and alternate empty-read paths. No migration or scientific acceptance claim.
