import { useMemo, useState } from "react";
import type { ExploreModel } from "../../page_models/explore/model.js";
import type { ExploreState } from "../../page_models/explore/projection.js";
import { ScientificComparison } from "../../page_models/explore/comparison.js";
import { measurementText } from "../../page_models/explore/measurement.js";
import { RegionStatus } from "./status.js";

export function ComparisonView({ model, view }: { model: ExploreModel; view: ExploreState }) {
  const specimens = view.regions.specimens.value, properties = view.regions.properties.value;
  const comparison = useMemo(() => {
    if (!specimens || !properties) return null;
    try { return new ScientificComparison(specimens, properties); } catch { return "invalid"; }
  }, [specimens, properties]);
  return <section aria-label="Prepared specimen comparison"><h2>Compare specimens</h2><p>Compare reported observations while keeping preparation, method and applicability explicit.</p>
    <RegionStatus region={view.regions.specimens} label="specimens" /><RegionStatus region={view.regions.properties} label="observations" />
    {comparison === "invalid" ? <p role="status">These pages do not have a coherent comparison context. Refresh the selected view.</p> : comparison && <>
      <p>{comparison.rows.length} observations loaded; {comparison.omittedObservations} observations and {comparison.omittedSpecimens} specimens outside these windows.</p>
      {comparison.rows.length ? <PairSelection key={properties!.query_sha256 + ":" + (properties!.request.position?.offset ?? 0) + ":" + (specimens!.request.position?.offset ?? 0)} comparison={comparison} model={model} /> : <p>No observations selected for comparison.</p>}
      <div className="explore-caption">{specimens!.next_position && <button onClick={() => { model.clearInspection(); void model.specimens({ ...specimens!.request, position: specimens!.next_position }); }}>Next comparison specimens</button>}{properties!.next_position && <button onClick={() => { model.clearInspection(); void model.properties({ ...properties!.request, position: properties!.next_position }); }}>Next comparison observations</button>}</div>
    </>}
  </section>;
}

function PairSelection({ comparison, model }: { comparison: ScientificComparison; model: ExploreModel }) {
  const [left, setLeft] = useState(comparison.rows[0]!.identity), [right, setRight] = useState(comparison.rows[1]?.identity ?? comparison.rows[0]!.identity);
  const pair = comparison.pair(left, right);
  return <>
    <div className="comparison-selectors"><label>First observation<select aria-label="First observation" value={left} onChange={e => { model.clearInspection(); setLeft(e.target.value); }}>{comparison.rows.map(row => <option key={row.identity} value={row.identity}>{row.observation.reference.observation_id} / revision {row.observation.reference.revision}</option>)}</select></label><label>Second observation<select aria-label="Second observation" value={right} onChange={e => { model.clearInspection(); setRight(e.target.value); }}>{comparison.rows.map(row => <option key={row.identity} value={row.identity}>{row.observation.reference.observation_id} / revision {row.observation.reference.revision}</option>)}</select></label></div>
    <div className="explore-table"><table><caption>Selected observations and preparation</caption><thead><tr><th>Context</th><th>First observation</th><th>Second observation</th></tr></thead><tbody>
      <tr><th scope="row">Reported result</th>{[pair.left, pair.right].map((r, i) => <td key={i}>{measurementText(r.observation.value)}</td>)}</tr>
      <tr><th scope="row">Nominal candidate</th>{[pair.left, pair.right].map((r, i) => <td key={i}>{r.specimenContext === "exact" ? r.specimen!.sample.candidate.candidate_id : "Unresolved specimen"}</td>)}</tr>
      <tr><th scope="row">Sample</th>{[pair.left, pair.right].map((r, i) => <td key={i}>{r.observation.binding.specimen.sample?.sample_id ?? "Not bound"}<small>{r.specimenContext.replaceAll("_", " ")}</small></td>)}</tr>
      <tr><th scope="row">Prepared state</th>{[pair.left, pair.right].map((r, i) => <td key={i}>{r.observation.binding.specimen.material_state ? <>{r.observation.binding.specimen.material_state.material_state_id}<small>revision {r.observation.binding.specimen.material_state.revision}</small><button onClick={() => void model.material(r.observation.binding.specimen.material_state!)}>Inspect preparation {i + 1}</button></> : "Not declared"}</td>)}</tr>
      <tr><th scope="row">Method</th>{[pair.left, pair.right].map((r, i) => <td key={i}>{r.observation.binding.measurement.method ? `${r.observation.binding.measurement.method.schema_id} / ${r.observation.binding.measurement.method.version}` : "Not declared"}</td>)}</tr>
      <tr><th scope="row">Quality</th>{[pair.left, pair.right].map((r, i) => <td key={i}>Controls: {r.observation.quality.controls}<small>{r.observation.quality.flags.join(", ") || "No flags reported"}</small></td>)}</tr>
      <tr><th scope="row">Evidence</th>{[pair.left, pair.right].map((r, i) => <td key={i}><button onClick={() => void model.artifact(r.observation.source, true)}>Inspect compared evidence {i + 1}</button></td>)}</tr>
    </tbody></table></div>
    <h3>Context identity: {pair.contextIdentity}</h3><p>{pair.evidenceIdentity === "same_pinned_record" ? "Both selections refer to the same pinned evidence record." : "These are distinct evidence records."} Reuse eligibility belongs to the owning tool or Research policy.</p>
    <dl className="comparison-differences">{pair.differences.map(d => <div key={d.field}><dt>{d.field.replaceAll("_", " ")}</dt><dd>{d.relationship}</dd></div>)}</dl>
  </>;
}
