import { useState } from "react";
import type { FeedbackLineage } from "../../page_models/feedback/lineage.js";
import type { FeedbackInspection } from "./panel.js";

export function AnswerDetails({ lineage, inspect }: { lineage: FeedbackLineage; inspect: FeedbackInspection }) {
  const [page, setPage] = useState(0);
  const { assessment, publication } = lineage.records;
  if (!assessment) return <p role="status">No assessment is selected. The question and evidence need remain available for exploration.</p>;
  if (assessment.outcome.status !== "assessed") return <p role="status">Assessment {assessment.outcome.status}. No completed answer is being claimed.</p>;
  const answer = assessment.outcome.assessment, start = Math.min(page * 20, Math.max(0, Math.ceil(answer.needs.length / 20) - 1) * 20);
  return <section aria-label="Scoped evidence assessment"><p className="eyebrow">Synthetic assessment / not scientifically established</p><h3>{answer.sufficient ? "Sufficient for this synthetic assessment" : "Evidence gaps remain"}</h3><p>Answer disposition: <strong>{answer.disposition}</strong>. {answer.answered ? "An answer is recorded." : "The question is not yet answered."}</p>
    <div className="explore-table-wrap"><table className="explore-table" aria-label="Evidence need decisions"><thead><tr><th>Criterion</th><th>Evidence status</th><th>Supporting / contradicting</th></tr></thead><tbody>{answer.needs.slice(start, start + 20).map((n, i) => <tr key={start + i}><td>{n.criterion_id}</td><td>{n.gap ? n.gap.reason.replaceAll("_", " ") : "No gap recorded"}</td><td>{n.supporting.length} / {n.contradicting.length}{[...n.supporting, ...n.contradicting].slice(0, 4).map((a, j) => <button key={j} onClick={() => inspect.artifact(a)}>Inspect evidence {j + 1}</button>)}{n.supporting.length + n.contradicting.length > 4 && <span>First 4 evidence links shown</span>}</td></tr>)}</tbody></table></div>
    <div className="explore-caption"><span>{start + 1}–{Math.min(start + 20, answer.needs.length)} of {answer.needs.length} need decisions</span><button disabled={start === 0} onClick={() => setPage(Math.max(0, page - 1))}>Previous decisions</button><button disabled={start + 20 >= answer.needs.length} onClick={() => setPage(page + 1)}>Next decisions</button></div>
    {publication?.outcome.status === "published" ? <><p>Published receipt: <strong>{publication.outcome.receipt.outcome.status}</strong>. Runtime decides whether a campaign can consume it.</p><button onClick={() => inspect.artifact(publication.outcome.status === "published" ? publication.outcome.derivation.artifact : answer.subject)}>Inspect published assessment</button></> : <p className="muted">{publication ? `Publication ${publication.outcome.status}.` : "No publication selected."} This assessment remains inspectable.</p>}
  </section>;
}

export function FutureDetails({ lineage, inspect }: { lineage: FeedbackLineage; inspect: FeedbackInspection }) {
  const { proposal, change, corrections } = lineage.records;
  return <section aria-label="Future campaign feedback"><p className="eyebrow">For a later campaign</p><h3>Carry improvements forward</h3><p>Current campaign pins and committed history stay unchanged. A later campaign must explicitly select revised inputs.</p>
    {corrections ? <div className="explore-table-wrap"><table className="explore-table" aria-label="Historical and corrected receipts"><thead><tr><th>Receipt</th><th>Revision</th><th>Outcome</th></tr></thead><tbody><tr><td>Historical selection</td><td>{corrections.previous.reference.ordinal}</td><td>{corrections.previous.record.receipt.outcome.status}</td></tr><tr><td>Later correction</td><td>{corrections.next.reference.ordinal}</td><td>{corrections.next.record.receipt.outcome.status}</td></tr></tbody></table><p>Correction reason: {corrections.next.record.reason_code.replaceAll("_", " ")}</p></div> : <p className="muted">No adjacent correction pair selected.</p>}
    {proposal ? <><h4>{proposal.proposal.description}</h4><p>{proposal.proposal.rationale}</p><p>Graph proposal: <strong>{lineage.proposalState}</strong>{lineage.proposalState === "accepted" ? " for graph structure. This does not prove the claim scientifically." : "."}</p>{change && <p>Resulting domain revision: {change.content.resulting_snapshot.revision}. Campaign adoption is separate.</p>}
      <div className="feedback-evidence">{proposal.proposal.grounding.spans.slice(0, 8).map((span, i) => <button key={i} onClick={() => inspect.source(span)}>Read feedback source {i + 1}</button>)}{proposal.proposal.grounding.conversion_traces.slice(0, 8).map((trace, i) => <button key={i} onClick={() => inspect.trace(trace)}>Inspect feedback conversion {i + 1}</button>)}</div><p className="muted">{proposal.proposal.operations.length} proposed graph operations. Up to 8 source and conversion links shown.</p></> : <p className="muted">No graph feedback proposal selected. A missing proposal does not block further exploration.</p>}
  </section>;
}
