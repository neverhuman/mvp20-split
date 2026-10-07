import { useCallback, useSyncExternalStore } from "react";
import type { ArtifactRef } from "../../contracts/observations.js";
import type { QualityModel } from "../../page_models/quality/model.js";
import type { QualityCategory } from "../../page_models/quality/projection.js";
import type { QualityAttachment } from "../../page_models/quality/attachment.js";
import { QualityExecutionGraph } from "./execution.js";
import { FocusEditor, downloadFocus } from "./focus.js";
import "./style.css";

const labels: Record<QualityCategory, string> = { unassessed: "Not assessed", unknown: "Unknown",
  contradictory: "Conflicting evidence", insufficient: "Evidence missing", supported: "Requirement met" };
const reasons: Record<string, string> = {
  missing_answer: "No answer was supplied for this criterion.", answer_unknown: "The supplied answer is unknown.",
  answer_contradicted: "The assessment contradicts the supplied answer.", evidence_contradicted: "The supplied evidence contradicts this criterion.",
  evidence_conflict: "Supporting and contradicting evidence remain in conflict.", no_matching_evidence: "No evidence matches the declared requirement.",
  owner_requirement_met: "The declared evidence requirement is met within this assessment's scope.",
  criterion_not_returned: "This criterion has no decision in the returned assessment.",
  assessment_pending: "Assessment is pending; no scientific conclusion is available.",
  assessment_failed: "Assessment could not complete; this is not a scientific error verdict.",
  assessment_unselected: "No assessment has been selected for this criterion.",
};

export function QualityPanel({ model, inspectArtifact, inspectNode }: {
  model: QualityModel; inspectArtifact(reference: ArtifactRef): void;
  inspectNode?: (attachment: QualityAttachment) => void;
}) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const projection = view.projection, page = view.page;
  const selected = projection?.points.find(point => point.key === view.selected);
  if (!projection || !page) return <section aria-label="Scientific quality points"><h3>Quality points</h3>
    <p role="status">{view.phase === "loading" ? "Loading pinned assessments." : view.phase === "denied" ?
      "Access denied. Quality details have been cleared." : "Quality details are unavailable for this selection."}</p></section>;
  return <section className="quality-panel" aria-label="Scientific quality points">
    <div className="quality-heading"><div><p className="eyebrow">Evidence quality / pinned assessment</p><h3>What needs another look?</h3></div>
      <span className="quality-boundary">Progress, not scientific proof</span></div>
    <p className="muted">Several weak points can remain useful. Review their evidence and target improvements in the next campaign.</p>
    <div className="quality-controls"><span role="status">{view.focus.items.length} points in local focus / {projection.unresolvedCount} unresolved points retained</span>
      <button disabled={!view.focus.items.length} onClick={() => downloadFocus(model)}>Export next-campaign focus</button></div>
    <div className="quality-controls"><label>Show quality <select value={view.category}
      onChange={event => model.filter(event.target.value as QualityCategory | "all")}>
      <option value="all">All points</option>{Object.entries(labels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
    </select></label><span role="status">{page.items.length} of {page.selectedTotal} matching points / {page.total} in this selected need</span></div>
    {projection.missingDecisions > 0 && <p className="quality-notice">Partial assessment: {projection.missingDecisions} criteria have no returned decision.</p>}
    {projection.correction && <p className="quality-notice">A newer correction is available for a future campaign. Historical revision {projection.correction.previous.reference.ordinal} remains separate from revision {projection.correction.next.reference.ordinal}.</p>}
    <div className="quality-layout"><div className="quality-list">
      {page.items.length === 0 ? <p role="status">No points match this filter.</p> : <ul aria-label="Quality point list" tabIndex={0}>{page.items.map(point =>
        <li key={point.key}><button className="quality-point" aria-pressed={view.selected === point.key}
          onClick={() => model.select(point.key)}><span className="quality-marker" data-kind={point.category}>{labels[point.category]}</span>
          <span className="quality-point-title">{point.description}</span><span className="quality-point-reason">{reasons[point.reason] ?? point.reason}</span>
          {view.focus.items.some(item => item.point.key === point.key) && <span>Selected for next-campaign focus</span>}</button></li>)}</ul>}
      <nav className="quality-pages" aria-label="Quality point pages"><button disabled={page.offset === 0}
        onClick={() => model.page(Math.max(0, page.offset - 20))}>Previous points</button><button disabled={page.nextOffset === null}
        onClick={() => model.page(page.nextOffset!)}>Next points</button></nav>
    </div><aside className="quality-inspector" aria-label="Selected quality point">
      {!selected ? <p>Select a point to inspect its requirement and evidence.</p> : <>
        <p className="eyebrow">{labels[selected.category]}</p><h4>{selected.description}</h4>
        <p>{reasons[selected.reason] ?? selected.reason}</p>
        <dl><dt>Question revision</dt><dd>{projection.question.reference.revision}</dd><dt>Evidence need revision</dt><dd>{selected.need.revision}</dd>
          <dt>Declared method</dt><dd>{projection.requirement.method.schema_id} / {projection.requirement.method.version}</dd>
          <dt>Calibrated accuracy</dt><dd>Not provided</dd><dt>Demonstrated error verdict</dt><dd>Not provided</dd></dl>
        <button onClick={() => inspectArtifact(projection.requirement.required_context)}>Inspect applicability context</button>
        <div className="quality-evidence">{selected.supporting.map((reference, index) => <button key={"support-" + index}
          onClick={() => inspectArtifact(reference)}>Supporting evidence {index + 1}</button>)}
          {selected.contradicting.map((reference, index) => <button key={"against-" + index}
            onClick={() => inspectArtifact(reference)}>Contradicting evidence {index + 1}</button>)}</div>
        {selected.supporting.length + selected.contradicting.length === 0 && <p className="muted">No matching evidence references were returned for this point.</p>}
        <FocusEditor key={selected.key} model={model} point={selected}
          saved={view.focus.items.find(item => item.point.key === selected.key)} full={view.focus.items.length >= 32} />
      </>}
      {projection.attachment ? <section className="quality-execution" aria-label="Linked execution quality">
        <QualityExecutionGraph projection={projection} {...(inspectNode ? { inspect: inspectNode } : {})} />
        <p className="eyebrow">Exact output link</p><p>Execution: <strong>{projection.attachment.operationalState}</strong> / pinned revision {projection.attachment.cut.revision}</p>
        <p>Scientific quality remains separate from execution success.</p>
        {!projection.attachment.complete && <p>Only part of this output membership has been loaded.</p>}
        {inspectNode && <button onClick={() => inspectNode(projection.attachment!)}>Inspect linked execution point</button>}
      </section> : <p className="muted">No execution link has been established for this selected assessment. Other consumers have not been searched.</p>}
    </aside></div>
  </section>;
}
