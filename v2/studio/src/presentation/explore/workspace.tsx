import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { ExploreModel } from "../../page_models/explore/model.js";
import type { FeedbackModel } from "../../page_models/feedback/model.js";
import type { QualityLinkModel } from "../../page_models/quality/runtime_link.js";
import { FeedbackPanel } from "../feedback/panel.js";
import type { FeedbackInspection } from "../feedback/panel.js";
import { DomainView } from "./domain.js";
import { ExploreInspection } from "./inspection.js";
import { ComparisonView } from "./comparison.js";
import { LaboratoryView } from "./laboratory.js";
import "../style.css";
import "./style.css";

export function ExploreWorkspace({ model, feedback, qualityLink, synthetic = false, active = true, embedded=false }: { model: ExploreModel; feedback?: FeedbackModel; qualityLink?: QualityLinkModel; synthetic?: boolean; active?: boolean; embedded?:boolean }) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const [mode, setMode] = useState<"domain" | "specimens" | "properties" | "feedback" | "comparison">("domain");
  const context = view.context;
  const feedbackInspection = useMemo<FeedbackInspection>(() => ({ clear: () => model.clearInspection(), artifact: ref => { void model.artifact(ref, true); }, source: span => { void model.source(span); }, trace: ref => { void model.trace(ref); } }), [model]);
  useEffect(() => {
    const check = () => model.visibility(active && document.visibilityState === "visible");
    document.addEventListener("visibilitychange", check); check();
    return () => { document.removeEventListener("visibilitychange", check); model.visibility(false); };
  }, [model, active]);
  const refresh = useCallback(() => {
    if (!context) return;
    if (mode === "feedback") { void feedback?.refresh(); void qualityLink?.refresh(); return; }
    if (mode === "comparison" && context.experiment) { void model.specimens({ wire_version: "1", experiment: context.experiment }); void model.properties({ wire_version: "1", experiment: context.experiment, observations: context.observations }); return; }
    if (mode === "domain" && context.graph) void model.search({ wire_version: "1", revision: context.graph, limit: 20 });
    if (mode === "specimens" && context.experiment) void model.specimens({ wire_version: "1", experiment: context.experiment });
    if (mode === "properties" && context.experiment) void model.properties({ wire_version: "1", experiment: context.experiment, observations: context.observations });
  }, [model, feedback, qualityLink, context, mode]);
  useEffect(() => {
    if (mode === "feedback" || mode === "comparison") model.clearInspection();
    model.suspend(mode === "comparison" ? ["search", "neighborhood", "series"] : mode === "feedback" ? ["search", "neighborhood", "specimens", "properties", "series"] : mode === "domain" ? ["specimens", "properties", "series"] : mode === "specimens" ? ["search", "neighborhood", "properties", "series"] : ["search", "neighborhood", "specimens"]);
    if (view.visible && mode !== "feedback") refresh();
  }, [model, mode, refresh, view.visible]);
  useEffect(() => { if (context && !context.graph && mode === "domain") setMode("specimens"); }, [context, mode]);
  const Content=embedded?'section':'main';
  return <div className={'workspace explore-workspace'+(embedded?' explore-embedded':'')}>
    {!embedded&&<header><span className="brand">AMPHORA<span>research studio</span></span><div className="mode">Explore</div><span className="fixture">{synthetic ? "Synthetic research fixture" : "Pinned research context"}</span></header>}
    <Content><div className="context"><div><p className="eyebrow">Knowledge / laboratory evidence</p><h1>Follow the evidence</h1></div><p>Read-only / improvements belong to the next campaign</p></div>
      {!context ? <p role="status">Choose a graph or experiment from your research context to begin.</p> : <>
        <div className="explore-context"><span>{context.graph ? `Domain graph revision ${context.graph.revision}` : "No domain graph selected"}</span><span>{context.experiment ? `Experiment ${context.experiment.experiment_id} / revision ${context.experiment.revision}` : "No experiment selected"}</span></div>
        <nav className="explore-tabs" aria-label="Research views"><button aria-pressed={mode === "domain"} disabled={!context.graph} onClick={() => setMode("domain")}>Knowledge graph</button><button aria-pressed={mode === "specimens"} disabled={!context.experiment} onClick={() => setMode("specimens")}>Specimens</button><button aria-pressed={mode === "properties"} disabled={!context.experiment} onClick={() => setMode("properties")}>Properties</button><button aria-pressed={mode === "comparison"} disabled={!context.experiment} onClick={() => setMode("comparison")}>Compare specimens</button>{feedback && <button aria-pressed={mode === "feedback"} onClick={() => setMode("feedback")}>Question &amp; feedback</button>}<button onClick={refresh}>{mode === "feedback" ? "Refresh feedback" : "Refresh selected view"}</button></nav>
        <div className="explore-area">{mode === "comparison" ? <ComparisonView model={model} view={view} /> : mode === "feedback" && feedback ? <FeedbackPanel model={feedback} inspect={feedbackInspection} active={active} {...(qualityLink ? { runtimeLink: qualityLink } : {})} /> : mode === "domain" ? <DomainView model={model} view={view} /> : <LaboratoryView model={model} view={view} mode={mode === "properties" ? "properties" : "specimens"} />}<ExploreInspection model={model} view={view} /></div>
      </>}
    </Content>
  </div>;
}
