import { useCallback, useEffect, useSyncExternalStore } from 'react';
import type { FeedbackModel } from '../../page_models/feedback/model.js';
import type { WorkspaceFeedbackSelection } from '../../page_models/session/feedback_selection.js';
import type { WorkflowView } from '../../page_models/session/workflow.js';

export function ResearchQuestion({ model, selection, active, synthetic, navigate }: {
  model: FeedbackModel; selection: WorkspaceFeedbackSelection; active: boolean; synthetic: boolean;
  navigate: (view: WorkflowView) => void;
}) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  useEffect(() => {
    // Overview depends only on the question and need, not optional downstream reads.
    const pins = selection.pins;
    model.bind(pins ? { ...pins, assessment: null, publication: null, proposal: null, corrections: null } : null);
  }, [model, selection]);
  useEffect(() => {
    const visibility = () => { model.visibility(active && !document.hidden); if (active && !document.hidden) void model.refresh(); };
    visibility(); document.addEventListener('visibilitychange', visibility);
    return () => { document.removeEventListener('visibilitychange', visibility); model.visibility(false); };
  }, [model, selection, active]);
  const question = view.phase === 'ready' ? view.lineage?.records.question : null;
  return <main className="research-overview">
    <p className="eyebrow">Research workspace {synthetic && '/ Synthetic demonstration'}</p>
    <h1>What are we trying to learn?</h1>
    <section className="research-purpose" aria-label="Research purpose">
      {question ? <><h2>{question.objective}</h2><p>What a useful answer needs to address</p>
        <ul>{question.criteria.map(c => <li key={c.criterion_id}>{c.description}</li>)}</ul>
        <p className="muted">These are the selected research criteria. Open the evidence view to inspect assessments and remaining uncertainty.</p>
      </> : <div role="status"><h2>{selection.phase === 'missing' ? 'No research question selected' : selection.phase === 'invalid' ? 'Research question link is invalid' : view.phase === 'loading' ? 'Loading the research question' : view.phase === 'denied' ? 'Research access unavailable' : 'Research question unavailable'}</h2>
        <p>{selection.phase === 'missing' ? 'This campaign link contains execution history without a selected research question. You can still inspect its approach and run.' : 'The campaign remains accessible. Research details appear only after their exact records can be read.'}</p>
        {selection.phase === 'ready' && view.phase !== 'loading' && <button onClick={() => void model.refresh()}>Retry research question</button>}
      </div>}
    </section>
    {synthetic && <section className="research-purpose"><h2>Review the evaluation strategy</h2><p>Inspect a separate polymer design proposal: criteria, proposed scientific methods, assumptions and selection rules. Record what an SME would change next campaign.</p><button onClick={() => navigate('evaluation')}>Review evaluation design</button><p className="muted">Codex-authored design proposal; not executed or linked to the numerical history below.</p></section>}
    <div className="research-steps" aria-label="Research workflow">
      <section><span className="step-number">01</span><h2>Understand the approach</h2><p>Follow the connected campaign graph, its tools and repeated work.</p><button onClick={() => navigate('execution')}>Explore approach and run</button></section>
      <section><span className="step-number">02</span><h2>Inspect the evidence</h2><p>Explore the selected domain context, observations and evidence quality.</p><button onClick={() => navigate('knowledge')}>Open results and evidence</button></section>
      <section><span className="step-number">03</span><h2>Prepare another iteration</h2><p>Review saved campaign drafts. Changes belong to a future campaign.</p><button onClick={() => navigate('design')}>Review next campaign</button></section>
    </div>
    {synthetic && <p className="research-limit">This demonstration uses synthetic research records. Completed execution does not establish scientific validity.</p>}
  </main>;
}
