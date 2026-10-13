# Durable successor launch

Status: preparation/context and command/recovery implemented; P4.3d journey qualification remains.
Owner: Studio page models. No owner service state is stored here.

SuccessorLaunchModel owns one original launch for a retained curation. Journal
storage is bound to actor/scope/predecessor/curation and occurs before dispatch.
Reload hides cached receipts until live owner reconciliation. A lost response stays
unresolved; retry is explicit and preserves original bytes. Double clicks and
different requests cannot replace a pending original. A second launch requires a
separate curation; this model does not select an alternative graph or mint commands.

SuccessorJournal is an untrusted browser recovery hint, not a cross-tab lock or
execution authority. It stores original request/optional receipt, no credentials.
Storage failure prevents submission; conflicting originals block replacement.
Denial, suspension and disposal clear protected memory and fence late responses.
Reentrant subscribers cannot dispatch after revocation. Returning from a hidden
surface reopens the original journal and requires a live read.

Deployment owns launch/worker readiness. Runtime owns accepted run and execution.
Exact graph review and launch preparation remain separate owners; UI admission
controls may not infer eligibility merely from a saved proposal or cached receipt.
Tests: tests/page_models/successor_launch/model.test.ts. Integrated owner/browser
qualification remains P4.4/P5. Replacement preserves original request identity,
read-only recovery, explicit retries and predecessor/successor separation.

## Reviewed preparation and successor context

PreparedSuccessor requires the reviewed ready draft/validation, the same terminal
predecessor cut with predecessor_ready, and an installed profile covering every
nested invoke. Required root inputs are explicitly mapped to committed run exports
with original value hashes; no matching-by-name or browser type-compatibility claim.
Fresh manual values and node-local carry selection remain outside this initial UI.
Runtime rechecks current eligibility, cut, input types/units and capacity atomically.
SuccessorPreparation owns read cancellation and explicit readiness refresh.

SuccessorPlanningContext binds accepted receipt, exact reviewed draft/plan and new
Runtime snapshot. Future curation reads the exact saved draft and original curation,
preserving all Knowledge heads and Research/artifact selections. They remain requested
context, not a claim of provider/tool consumption. Legacy single-head provenance is
not used to reconstruct successor curation. Tests cover all8 heads and changed pins.

Successor curation retains original artifact selections and adds exact literal dependencies from its verified saved draft plus artifact-valued admission inputs. Shared bounded collection rejects scope/conflict/size violations; this is requested context, not a consumption assertion.
