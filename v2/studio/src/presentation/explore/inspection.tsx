import type { ExploreModel } from "../../page_models/explore/model.js";
import type { ExploreState } from "../../page_models/explore/projection.js";
import { RegionStatus } from "./status.js";

export function ExploreInspection({ model, view }: { model: ExploreModel; view: ExploreState }) {
  const detail = view.regions.detail.value?.detail, source = view.regions.source.value, trace = view.regions.trace.value;
  const artifact = view.regions.artifact.value, derivation = view.regions.derivation.value;
  return <aside className="explore-inspector" aria-label="Scientific evidence inspector">
    <p className="eyebrow">Selected evidence</p><h2>{detail?.kind === "entity" ? detail.record.label : detail?.kind === "assertion" ? "Claim and grounding" : "Inspect the context"}</h2>
    <RegionStatus region={view.regions.detail} label="selected object" />
    {detail?.kind === "entity" && <><p>{detail.record.entity_type} / revision {detail.record.reference.revision}</p><p>{detail.is_latest ? "Latest entity within this pinned graph" : "Retained entity revision"}</p><button onClick={() => void model.artifact(detail.record.context)}>Inspect entity context</button></>}
    {detail?.kind === "assertion" && <>
      <p className="explore-posture">{detail.record.posture} / {detail.record.polarity}{detail.retracted ? " / retracted" : ""}</p>
      <p className="explore-statement">{detail.record.statement}</p><p>This claim remains qualified by its source and applicability.</p>
      <button onClick={() => void model.artifact(detail.record.applicability)}>Inspect applicability</button>
      <h3>Source passages</h3><ul>{detail.record.grounding.spans.map((span, index) => <li key={index}><button onClick={() => void model.source(span)}>Read source passage {index + 1}</button><span> bytes {span.start}–{span.end}</span></li>)}</ul>
      <h3>Conversion history</h3><ul>{detail.record.grounding.conversion_traces.map((ref, index) => <li key={ref.trace_id}><button onClick={() => void model.trace(ref)}>Inspect conversion {index + 1}</button></li>)}</ul>
      {detail.record.research_links.length > 0 && <p>{detail.record.research_links.length} declared research links; a proposed answer is not scientific acceptance.</p>}
    </>}
    <RegionStatus region={view.regions.source} label="source passage" />
    {source && <section aria-label="Verified source passage"><h3>Verified source passage</h3><p>Exact retained byte range / {source.span.source.revision_id}</p><pre className="source-text">{source.text || "(Empty byte range)"}</pre><details><summary>Integrity details</summary><p>Whole artifact and selected span SHA-256 verified.</p><code>{source.span_sha256}</code></details></section>}
    <RegionStatus region={view.regions.trace} label="conversion history" />
    {trace && <section aria-label="Conversion history"><h3>Conversion history</h3><p>{trace.converter_id} / {trace.converter_version}</p><p>Conversion disposition: {trace.disposition}. This describes conversion, not scientific validity.</p><ol>{trace.transforms.map((step, index) => <li key={index}>{step.transform_id} / {step.kind} / {step.version}</li>)}</ol><p>{trace.fields.length} mapped fields / {trace.warnings.length} warnings</p><button onClick={() => void model.artifact(trace.output)}>Inspect converted artifact</button></section>}
    <RegionStatus region={view.regions.artifact} label="artifact metadata" />
    {artifact && <section aria-label="Verified artifact"><h3>Verified artifact</h3><p>{artifact.media_type} / {artifact.size_bytes} bytes</p><details><summary>Artifact identity</summary><p>{artifact.artifact_id}</p><code>{artifact.sha256}</code></details><button onClick={() => void model.derivation(artifact)}>Inspect derivation</button></section>}
    <RegionStatus region={view.regions.derivation} label="derivation" />
    {derivation && <section aria-label="Artifact derivation"><h3>Artifact derivation</h3><p>{derivation.declaration.transformation.transformation_id} / {derivation.declaration.transformation.version}</p><ul>{derivation.declaration.inputs.map((input, index) => <li key={input.artifact_id}><button onClick={() => void model.artifact(input)}>Inspect input {index + 1}</button></li>)}</ul></section>}
    {!detail && !source && !artifact && <p>Select a concept, claim or measured result to follow its exact retained evidence.</p>}
  </aside>;
}
