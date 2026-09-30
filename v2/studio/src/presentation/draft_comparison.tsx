import type { DraftComparison } from "../page_models/design/draft_comparison.js";

export function DraftComparisonView({ comparison }: { comparison: DraftComparison }) {
  const view = comparison.snapshot;
  return <section aria-label="Draft comparison" className="draft-comparison">
    <h2>Changes from saved revision</h2>
    <p>{view.total} structural changes. {view.omitted} omitted from this view.</p>
    {view.warnings.map(text => <p key={text}>{text}</p>)}
    <ol>{view.changes.map((change, index) => <li key={index}>
      <strong>{change.kind} · {change.category}</strong> <span>{change.path}</span>
      <details><summary>Inspect change</summary><pre>{JSON.stringify({ before: change.before, after: change.after }, null, 2)}</pre></details>
    </li>)}</ol>
  </section>;
}
