import { useCallback, useEffect, useState, useSyncExternalStore } from "react";
import type { OriginDraft } from "../../contracts/campaign_origin.js";
import type { DomainRevisionRef } from "../../contracts/scientific/knowledge.js";
import type { CampaignOriginModel } from "../../page_models/campaign_origin/model.js";
import "./style.css";

export function CampaignOriginPanel({ model, selection, openKnowledge }: {
  model: CampaignOriginModel; selection: OriginDraft | null; openKnowledge: (revision: DomainRevisionRef) => void;
}) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const [toolLimit, setToolLimit] = useState(20);
  const origin = view.origin?.origin;
  useEffect(() => {
    if (view.phase !== "ready" || !origin || view.detail.phase !== "idle") return;
    const first = origin.research.records.findIndex(row => row.kind === "question" && row.unavailable === null);
    if (first >= 0) void model.inspect(first);
  }, [model, view.phase, origin, view.detail.phase]);
  return <details className="campaign-origin" onToggle={event => {
    if (event.currentTarget.open && selection && view.phase === "idle") void model.load(selection);
  }}>
    <summary>Why this campaign? <span>Proposal, criteria and Knowledge context</span></summary>
    <div className="campaign-origin-body">
      {!selection && <p>This run has no verified saved-draft link in this browser. New campaigns launched here retain that link for provenance inspection.</p>}
      {selection && <>
        {view.phase === "loading" && <p role="status">Checking Planning history and the original Runtime save…</p>}
        {view.phase === "not_recorded" && <p role="status">No Planning origin is recorded for this exact draft. This does not establish who authored it.</p>}
        {view.phase === "denied" && <p role="status">Campaign provenance is not available to this session.</p>}
        {view.phase === "failed" && <p role="status">{view.reason === "limit" ? "The retained provenance exceeds this bounded view." :
          view.reason === "invalid_response" ? "The campaign provenance could not be verified." : "Campaign provenance is temporarily unavailable."}</p>}
        {["not_recorded", "denied", "failed"].includes(view.phase) && <button onClick={() => void model.load(selection)}>Retry provenance read</button>}
      </>}
      {origin && <>
        <h2>Recorded Planning proposal</h2>
        <p className="origin-rationale">{origin.proposal.rationale}</p>
        <p className="origin-attribution">Provider {origin.proposal.context.model.provider_id} · Model {origin.proposal.context.model.model_id} · Revision {origin.proposal.context.model.model_revision}</p>
        <p>Historical proposal and save verified. Scientific validity is not established by compilation.</p>
        <h3>Research criteria</h3>
        {origin.research.records.some(row => row.kind !== "assessment") ? <label className="origin-choice">Inspect retained Research context
          <select value={view.detail.index ?? ""} onChange={event => void model.inspect(Number(event.target.value))}>
            <option value="" disabled>Choose a question or evidence need</option>
            {origin.research.records.map((row, index) => row.kind !== "assessment" && <option key={index} value={index} disabled={row.unavailable !== null}>
              {row.kind === "question" ? "Question" : "Evidence need"} {index + 1} · {row.criterion_ids.length} {row.criterion_ids.length === 1 ? "criterion" : "criteria"}{row.unavailable ? " · context unavailable" : ""}
            </option>)}
          </select>
        </label> : <p>No Research question or criterion context was retained with this proposal.</p>}
        {origin.research.records.some(row => row.unavailable !== null) && <p>Some selected Research records were unavailable in the retained Planning context.</p>}
        {view.detail.phase === "loading" && <p role="status">Verifying the exact Research record…</p>}
        {(view.detail.phase === "failed" || view.detail.phase === "denied") && <p role="status">{view.detail.phase === "denied" ? "Research detail access is denied." : "This Research record or its criterion membership could not be verified."}</p>}
        {view.detail.value && <section className="origin-criteria" aria-label="Verified Research criteria">
          <h4>{view.detail.value.question.objective}</h4>
          <ul>{view.detail.value.question.criteria.filter(criterion => !view.detail.value?.need || view.detail.value.need.criterion_ids.includes(criterion.criterion_id))
            .map(criterion => <li key={criterion.criterion_id}>{criterion.description}</li>)}</ul>
          <p>Exact Research revision {view.detail.value.question.reference.revision}. These are criteria present in the retained context; they are not measured results.</p>
        </section>}
        <h3>Knowledge used in planning</h3>
        {origin.knowledge?.status === "available" ? <>
          <p>{origin.knowledge.entities.length} selected entities · {origin.knowledge.assertions.length} selected assertions{origin.knowledge.head ? ` · graph revision ${origin.knowledge.head.snapshot.revision}` : " · genesis context"}</p>
          {origin.knowledge.head && <button onClick={() => openKnowledge(origin.knowledge!.head!.snapshot)}>Inspect the consumed Knowledge graph</button>}
        </> : <p>{origin.knowledge ? "The selected Knowledge graph was unavailable in the retained Planning context." : "No separate Knowledge graph selection was retained."}</p>}
        <details><summary>{origin.tools.length} executable tool {origin.tools.length === 1 ? "binding" : "bindings"}</summary>
          <div className="origin-tools"><table><thead><tr><th>Step</th><th>Tool</th><th>Version</th></tr></thead>
            <tbody>{origin.tools.slice(0, toolLimit).map(use => <tr key={[...use.node.scope_path, use.node.node_id].join("/")}>
              <td>{[...use.node.scope_path, use.node.node_id].join(" / ")}</td><td>{use.release.tool.capability_id}</td><td>{use.release.tool.release}</td>
            </tr>)}</tbody></table></div>
          {toolLimit < origin.tools.length && <button onClick={() => setToolLimit(value => value + 20)}>Show 20 more tools</button>}
        </details>
        <details><summary>Original identities and recorded usage</summary><dl>
          <dt>Producer</dt><dd>{origin.proposal.actor_id}</dd>
          <dt>Proposal attempt</dt><dd>{origin.proposal.attempt.engagement.engagement_id} / {origin.proposal.attempt.ordinal}</dd>
          <dt>Draft</dt><dd>{origin.draft.draft_id} / revision {origin.draft.revision}</dd>
          <dt>Input / output tokens</dt><dd>{origin.proposal.usage.input_tokens ?? "not recorded"} / {origin.proposal.usage.output_tokens ?? "not recorded"}</dd>
          <dt>Origin digest</dt><dd><code>{view.origin!.origin_sha256}</code></dd>
        </dl><p>Provider capture content has no public link in this compiler association. Source and graph reads retain their separate permissions.</p></details>
        <button className="origin-refresh" onClick={() => selection && void model.load(selection)}>Refresh verified provenance</button>
      </>}
    </div>
  </details>;
}
