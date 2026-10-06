import { useCallback, useSyncExternalStore } from "react";
import type { SupervisionModel } from "../../page_models/supervision/model.js";
import type { SupervisionWire } from "../../contracts/supervision.js";
import "./style.css";
const label = (value: string) => value.replaceAll("_", " ");
const status = (value: string) => value === "unavailable" ? "Provider unavailable" : value === "abstained" ? "Scientific abstention" : label(value);
export function SupervisionInspector({ model }: { model: SupervisionModel }) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const ready = view.phase === "ready" || view.phase === "empty";
  const outcome = view.decision?.outcome;
  return <section className="supervision-inspector" aria-label="Campaign checkpoint inspection">
    <div className="toolbar"><h2>Checkpoint reasoning</h2><button onClick={() => void model.refresh()} disabled={view.phase === "loading"}>Refresh checkpoints</button></div>
    <p>Inspect what the campaign considered and changed. Improvements inform the next campaign.</p>
    <nav aria-label="Checkpoint detail"><button onClick={() => void model.checkpoints()}>Checkpoints</button>
      {view.checkpoint && <button disabled={!ready} onClick={() => void model.requests()}>Requests for {view.checkpoint.checkpoint_id}</button>}
      {view.request && <><button disabled={!ready} aria-pressed={view.tab === "context"} onClick={() => void model.tab("context")}>Context</button>
        <button disabled={!ready} aria-pressed={view.tab === "responses"} onClick={() => void model.tab("responses")}>Responses</button></>}
    </nav>
    <p role="status">{view.phase === "loading" ? "Loading checkpoint evidence..." : view.phase === "stale" ? "Checkpoint evidence changed. Refresh to inspect a coherent snapshot." :
      view.phase === "denied" ? "Checkpoint access denied." : view.phase === "failed" ? "Checkpoint evidence could not be loaded." :
      view.phase === "unavailable" ? "This checkpoint is unavailable." : view.phase === "empty" ? "No retained records in this view." : view.phase === "idle" ? "Open checkpoint evidence to begin." :
      `Showing ${view.page?.items.length} of ${view.page?.total} ${view.tab}.`}</p>
    {ready && view.checkpoint && <div className="supervision-outcome" aria-label="Authoritative checkpoint outcome">
      <strong>Authoritative outcome: </strong>{!outcome ? (view.decisionUnavailable ? "Not observed here; the evidence view is partial." : "Pending") :
        outcome.kind === "model_accepted" ? <>Model accepted: {label(outcome.effect.kind)}{'changes' in outcome.effect && <ul>{outcome.effect.changes.map((change, i) => <li key={i}>{change.field_name}: {String(change.value.value)}</li>)}</ul>}</> :
        outcome.kind === "pending" ? "Pending" : <>{label(outcome.kind)}: {label(outcome.reason_code)}</>}
      <small>Read separately from the paged evidence snapshot. Execution acceptance does not establish scientific accuracy.</small>
    </div>}
    {ready && view.request && <details><summary>Request {view.request.lineage.ordinal}: model and attempt history</summary>
      <p>{view.request.model.provider_id} / {view.request.model.model_id} / {view.request.model.model_revision}</p>
      <p>{view.request.context_entries} included; {view.request.context_omissions} omitted. {view.request.report_stop_reason ? label(view.request.report_stop_reason) : "Execution report not observed here; a call may have occurred."}</p>
      <p>{view.request.disposition ? `Runtime ${label(view.request.disposition)}: ${label(view.request.disposition_reason ?? "unspecified")}` : "No repair or fallback disposition observed."}</p>
      <ul>{view.request.attempts.map(item => <li key={item.ordinal}>Attempt {item.ordinal}: {status(item.status)}</li>)}</ul>
      <p className="identity">Request {view.request.request_sha256}</p><p className="identity">Parent {view.request.lineage.parent_request_sha256 ?? "Original request"}</p>
    </details>}
    {ready && view.page && <div className="supervision-records">
      {view.tab === "checkpoints" && <ul>{(view.page as SupervisionWire["checkpoints"]).items.map(item => <li key={item.reference.decision_id}><button onClick={() => void model.selectCheckpoint(item)}>{item.checkpoint_id}</button><span>{item.winner_kind ? label(item.winner_kind) : "Pending"}: {item.requests} requests</span></li>)}</ul>}
      {view.tab === "requests" && <ul>{(view.page as SupervisionWire["requests"]).items.map(item => <li key={item.request_sha256}><button onClick={() => void model.selectRequest(item)}>Inspect request {item.lineage.ordinal}</button><span>{item.report_stop_reason ? label(item.report_stop_reason) : "Report unobserved"}{item.disposition ? ` : ${label(item.disposition)}` : ""}</span></li>)}</ul>}
      {view.tab === "context" && <ul>{(view.page as SupervisionWire["context"]).items.map((item, index) => <li key={index}><strong>{item.kind === "included" ? `Included: ${item.entry.role}` : `Omitted: ${label(item.omission.reason)}`}</strong><details><summary>Artifact metadata {index + 1}</summary><p className="identity">{item.kind === "included" ? item.entry.artifact.artifact_id : item.omission.artifact.artifact_id}</p><p>Source content requires its owning service's permission.</p></details></li>)}</ul>}
      {view.tab === "responses" && <ul>{(view.page as SupervisionWire["responses"]).items.map(item => <li key={item.response_sha256}><strong>Attempt {item.attempt_ordinal}: {status(item.status)}</strong><p>{item.selected_by_winner ? "Selected by the committed outcome" : "Retained observation; not selected by the committed outcome"}</p><p>{item.reason_code && label(item.reason_code)}</p><details><summary>Response metadata</summary><p className="identity">{item.response_sha256}</p><p>{item.captured_bytes} captured bytes: {item.output_complete ? "complete capture" : "partial capture"}</p></details></li>)}</ul>}
    </div>}
    <button disabled={!ready || !view.page?.next_cursor} onClick={() => void model.next()}>Next {view.tab}</button>
  </section>;
}
