import { useCallback, useEffect, useState, useSyncExternalStore } from "react";
import type { FeedbackModel } from "../../page_models/feedback/model.js";
import type { ArtifactRef, SourceSpan, ConversionTraceRef } from "../../contracts/scientific/provenance.js";
import { AnswerDetails, FutureDetails } from "./records.js";
import "./style.css";

export interface FeedbackInspection {
  clear(): void;
  artifact(reference: ArtifactRef): void;
  source(span: SourceSpan): void;
  trace(reference: ConversionTraceRef): void;
}
export function FeedbackPanel({ model, inspect }: { model: FeedbackModel; inspect: FeedbackInspection }) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const [step, setStep] = useState<"question" | "need" | "answer" | "future">("question");
  useEffect(() => {
    const check = () => { const visible = document.visibilityState === "visible"; model.visibility(visible); if (visible) void model.refresh(); };
    document.addEventListener("visibilitychange", check); check();
    return () => { document.removeEventListener("visibilitychange", check); model.visibility(false); };
  }, [model]);
  useEffect(() => { setStep("question"); }, [view.context]);
  useEffect(() => { if (view.phase !== "ready") inspect.clear(); }, [view.phase, inspect]);
  const lineage = view.lineage;
  return <section className="feedback-panel" aria-label="Question and feedback lineage">
    <h2>From question to next campaign</h2>
    <p className="muted">Inspect what was learned and what still needs evidence. Corrections apply to future campaigns.</p>
    {!view.context ? <p role="status">Select a research question and evidence need to inspect their lineage.</p> : view.phase !== "ready" ? <p role="status">{{ idle: "Ready to load the selected question.", loading: "Loading selected evidence records…", stale: "This view is stale. Refresh to reread its pinned records.", denied: "Access denied. Evidence details have been cleared.", unavailable: "A selected record is unavailable.", failed: "The selected records could not be verified." }[view.phase]}</p> : lineage && <>
      <nav className="feedback-steps" aria-label="Evidence lineage steps">
        <button aria-pressed={step === "question"} onClick={() => setStep("question")}><span>01</span>Question</button>
        <button aria-pressed={step === "need"} onClick={() => setStep("need")}><span>02</span>Evidence need</button>
        <button aria-pressed={step === "answer"} onClick={() => setStep("answer")}><span>03</span>Scoped answer</button>
        <button aria-pressed={step === "future"} onClick={() => setStep("future")}><span>04</span>Next campaign</button>
      </nav>
      <div className="feedback-detail">
        {step === "question" && <section aria-label="Selected research question"><p className="eyebrow">Research question · revision {lineage.records.question.reference.revision}</p><h3>{lineage.records.question.objective}</h3><ul>{lineage.records.question.criteria.map(c => <li key={c.criterion_id}>{c.description}</li>)}</ul><button onClick={() => inspect.artifact(lineage.records.question.applicability)}>Inspect question applicability</button></section>}
        {step === "need" && <section aria-label="Predeclared evidence need"><p className="eyebrow">Evidence need · revision {lineage.records.need.reference.revision}</p><h3>What would help answer this question?</h3><dl><dt>Declared method</dt><dd>{lineage.records.need.method.schema_id} / {lineage.records.need.method.version}</dd><dt>Criteria addressed</dt><dd>{lineage.records.need.criterion_ids.join(", ")}</dd><dt>Assessment state</dt><dd>{lineage.evidenceState === "gap" ? "Evidence gaps remain" : lineage.evidenceState}</dd></dl><button onClick={() => inspect.artifact(lineage.records.need.required_context)}>Inspect required context</button><p className="muted">The declared method describes the requested evidence. It does not establish that an experiment was performed.</p></section>}
        {step === "answer" && <AnswerDetails lineage={lineage} inspect={inspect} />}
        {step === "future" && <FutureDetails lineage={lineage} inspect={inspect} />}
      </div>
    </>}
  </section>;
}
