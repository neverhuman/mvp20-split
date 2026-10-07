import { useCallback, useSyncExternalStore } from "react";
import type { FollowupModel } from "../../page_models/followup/model.js";
import type { CriterionModel } from "../../page_models/followup/criterion.js";

function CriterionDetail({ model }: { model: CriterionModel }) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot), records = view.records;
  if (view.phase === "idle") return null;
  return <section aria-label="Selected criterion evidence" className="supervision-outcome">
    <button onClick={() => model.clear()}>Close evidence</button>
    <p role="status">{view.phase === "loading" ? "Reading exact owner evidence…" : view.phase === "denied" ? "Evidence access denied." :
      view.phase !== "ready" ? "The referenced evidence could not be verified. No newer assessment has been substituted." : "Exact referenced records verified."}</p>
    {records && <><h3>{records.question.criteria.find(point => point.criterion_id === records.criterion.criterion_id)?.description}</h3>
      <p>{records.question.objective}</p><p>Question revision {records.question.reference.revision} · Evidence need revision {records.need.reference.revision}</p>
      <p>{!records.assessment ? "No assessment was selected for this point." : `Assessment: ${records.assessment.outcome.status}`}</p>
      {records.assessment?.outcome.status === "assessed" && <p>{records.assessment.outcome.assessment.sufficient ? "The selected assessment reports sufficient evidence for its scope." : "The selected assessment retains evidence gaps."}</p>}
      <details><summary>Exact record identities</summary><p className="identity">Question: {records.question.reference.question_id}; need: {records.need.reference.need_id}; criterion: {records.criterion.criterion_id}</p>
        {records.criterion.assessment && <p className="identity">Assessment digest: {records.criterion.assessment.status_sha256}</p>}</details></>}
  </section>;
}
export function FollowupRegion({ model, criterion, close }: { model: FollowupModel; criterion: CriterionModel; close: () => void }) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot), projection = view.projection, page = view.page;
  if (view.phase === "idle") return null;
  return <section aria-label="Recorded follow-up proposal">
    <div className="toolbar"><h3>What could improve next?</h3><button onClick={close}>Back to responses</button></div>
    <p role="status">{view.phase === "loading" ? "Verifying the recorded proposal…" : view.phase === "denied" ? "Proposal content access denied." :
      view.phase === "unsupported" ? "This proposal profile does not yet have a supported detail view." : view.phase !== "ready" ? "This proposal could not be verified." : "Recorded intent · Subsequent campaign adoption not verified"}</p>
    {projection && page && <><p>{projection.document.draft.rationale}</p>
      <p>{projection.document.draft.action === "abstain" ? "The model abstained. Unresolved points remain useful for future work." : "This is a proposal for future work; scientific validity is not established."}</p>
      {!projection.criterionTargetingAvailable && <p>This older proposal records evidence intent without exact criterion targets.</p>}
      <div className="supervision-records"><ul>{page.rows.map((row, index) => <li key={page.offset + index}>
        <strong>{row.kind === "target" ? "Intended improvement" : row.kind === "evidence" ? "Evidence to seek" : `Still unresolved: ${row.posture}`}</strong>
        <p>{row.kind === "target" ? row.improvement : row.description}</p>
        {row.kind === "target" && <p><strong>What we might learn: </strong>{row.learning}</p>}
        {row.kind === "evidence" && <p>{row.uncertainty}</p>}
        {row.criterion && <button onClick={() => void criterion.select(row.criterion!)}>Inspect criterion {row.criterion.criterion_id}</button>}
      </li>)}</ul>{page.total === 0 && <p>No follow-up points were recorded.</p>}</div>
      <div className="toolbar"><button disabled={page.offset === 0} onClick={() => { criterion.clear(); model.page(page.offset - 20); }}>Previous points</button>
        <span>{page.total === 0 ? "0 points" : `${page.offset + 1}–${page.offset + page.rows.length} of ${page.total} points`}</span>
        <button disabled={!page.hasNext} onClick={() => { criterion.clear(); model.page(page.offset + 20); }}>Next points</button></div>
      <CriterionDetail model={criterion}/></>}
  </section>;
}
