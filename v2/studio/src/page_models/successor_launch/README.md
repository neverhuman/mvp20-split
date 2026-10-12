# Durable successor launch

Status: implemented command/recovery foundation; controls remain UI-01.08 P4.3c.
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
