import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { FeedbackModel } from "../../page_models/feedback/model.js";
import type { ArtifactRef, SourceSpan, ConversionTraceRef } from "../../contracts/scientific/provenance.js";
import { AnswerDetails, FutureDetails } from "./records.js";
import { QualityModel } from "../../page_models/quality/model.js";
import { QualityPanel } from "../quality/panel.js";
import type { QualityAttachment } from "../../page_models/quality/attachment.js";
import type { QualityLinkModel } from "../../page_models/quality/runtime_link.js";
import { QualityExecutionDetails } from "../quality/execution.js";
import "./style.css";

export interface FeedbackInspection {
  clear(): void;
  artifact(reference: ArtifactRef): void;
  source(span: SourceSpan): void;
  trace(reference: ConversionTraceRef): void;
}
export function FeedbackPanel({ model, inspect, attachment = null, inspectNode, active = true, runtimeLink }: {
  model: FeedbackModel; inspect: FeedbackInspection; attachment?: QualityAttachment | null;
  inspectNode?: (attachment: QualityAttachment) => void; active?: boolean; runtimeLink?: QualityLinkModel;
}) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const [step, setStep] = useState<"question" | "need" | "answer" | "quality" | "execution" | "future">("question");
  const linkSubscribe = useCallback((notify: () => void) => runtimeLink?.subscribe(notify) ?? (() => {}), [runtimeLink]);
  const link = useSyncExternalStore(linkSubscribe, () => runtimeLink?.snapshot ?? null);
  const quality = useMemo(() => new QualityModel(model), [model]);
  const qualitySubscribe = useCallback((notify: () => void) => quality.subscribe(notify), [quality]);
  const qualityView = useSyncExternalStore(qualitySubscribe, () => quality.snapshot);
  useEffect(() => () => quality.dispose(), [quality]);
  useEffect(() => { quality.attach(link?.attachment ?? attachment); }, [quality, attachment, link?.attachment]);
  useEffect(() => {
    const check = () => { const visible = active && document.visibilityState === "visible"; model.visibility(visible); runtimeLink?.visibility(visible);
      if (visible) { void model.refresh(); void runtimeLink?.refresh(); } };
    document.addEventListener("visibilitychange", check); check();
    return () => { document.removeEventListener("visibilitychange", check); model.visibility(false); runtimeLink?.visibility(false); };
  }, [model, active, runtimeLink]);
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
        <button aria-pressed={step === "quality"} onClick={() => setStep("quality")}>Quality points</button>
        <button aria-pressed={step === "future"} onClick={() => setStep("future")}><span>04</span>Next campaign</button>
      </nav>
      <div className="feedback-detail">
        {step === "question" && <section aria-label="Selected research question"><p className="eyebrow">Research question · revision {lineage.records.question.reference.revision}</p><h3>{lineage.records.question.objective}</h3><ul>{lineage.records.question.criteria.map(c => <li key={c.criterion_id}>{c.description}</li>)}</ul><button onClick={() => inspect.artifact(lineage.records.question.applicability)}>Inspect question applicability</button></section>}
        {step === "need" && <section aria-label="Predeclared evidence need"><p className="eyebrow">Evidence need · revision {lineage.records.need.reference.revision}</p><h3>What would help answer this question?</h3><dl><dt>Declared method</dt><dd>{lineage.records.need.method.schema_id} / {lineage.records.need.method.version}</dd><dt>Criteria addressed</dt><dd>{lineage.records.need.criterion_ids.join(", ")}</dd><dt>Assessment state</dt><dd>{lineage.evidenceState === "gap" ? "Evidence gaps remain" : lineage.evidenceState}</dd></dl><button onClick={() => inspect.artifact(lineage.records.need.required_context)}>Inspect required context</button><p className="muted">The declared method describes the requested evidence. It does not establish that an experiment was performed.</p></section>}
        {step === "answer" && <AnswerDetails lineage={lineage} inspect={inspect} />}
        {step === "quality" && <>{link?.error && <p role="status">The selected execution link is unavailable. Scientific assessment details remain separate.</p>}
          <QualityPanel model={quality} inspectArtifact={reference => inspect.artifact(reference)} inspectNode={value => { inspectNode?.(value); setStep("execution"); }} /></>}
        {step === "execution" && (qualityView.projection?.attachment && !link?.error ? <QualityExecutionDetails attachment={qualityView.projection.attachment} back={() => setStep("quality")} /> : <p role="status">The pinned execution link is no longer available. Return to quality points to refresh the selection.</p>)}
        {step === "future" && <FutureDetails lineage={lineage} inspect={inspect} />}
      </div>
    </>}
  </section>;
}
