import { useState } from "react";
import type { ExploreModel } from "../../page_models/explore/model.js";
import type { ExploreState } from "../../page_models/explore/projection.js";
import { domainScene, entityKey } from "../../page_models/explore/scene.js";
import type { GraphNeighborhoodRequest } from "../../contracts/scientific/knowledge.js";
import { GraphCanvas } from "../graph_canvas.js";
import { RegionStatus } from "./status.js";

export function DomainView({ model, view }: { model: ExploreModel; view: ExploreState }) {
  const [text, setText] = useState("");
  const revision = view.context?.graph, search = view.regions.search.value, neighborhood = view.regions.neighborhood.value;
  if (!revision) return <p>No domain graph is selected.</p>;
  const select = (reference: GraphNeighborhoodRequest["focus"]) => {
    void model.detail({ wire_version: "1", revision, selection: { kind: "entity", reference } });
    void model.neighborhood({ wire_version: "1", revision, focus: reference, radius: 1 });
  };
  const scene = neighborhood ? domainScene(neighborhood) : null;
  const detail = view.regions.detail.value?.detail;
  return <section className="explore-domain" aria-label="Domain knowledge">
    <form className="explore-search" onSubmit={event => { event.preventDefault(); void model.search({ wire_version: "1", revision, text, limit: 20 }); }}>
      <label htmlFor="knowledge-search">Find a concept</label><input id="knowledge-search" value={text} onChange={event => setText(event.target.value)} maxLength={256} placeholder="Name or identifier" />
      <button type="submit" disabled={view.regions.search.phase === "loading"}>Search</button>
    </form>
    <RegionStatus region={view.regions.search} label="concepts" />
    {search && <div className="explore-results"><p>{search.entities.length} of {search.total} matching concepts shown</p>
      <ul className="explore-concepts">{search.entities.map(entity => <li key={entityKey(entity.reference)}><button onClick={() => select(entity.reference)}>{entity.label}</button><span>{entity.entity_type}{entity.alias_target ? " / alias" : ""}</span></li>)}</ul>
      {search.next_position && <button onClick={() => void model.search({ ...search.request, position: search.next_position })}>Next concepts</button>}
    </div>}
    <RegionStatus region={view.regions.neighborhood} label="neighborhood" />
    {scene && neighborhood ? <>
      <div className="explore-caption"><h2>Connected knowledge</h2><span>{scene.nodes.length} concepts / {scene.edges.length} relationships</span></div>
      <GraphCanvas nodes={scene.nodes} edges={scene.edges} selection={detail?.kind === "entity" ? entityKey(detail.record.reference) : null}
        label="Domain graph neighborhood" select={id => { const row = neighborhood.entities.find(entity => entityKey(entity.reference) === id); if (row) select(row.reference); }} />
      <p>{scene.omittedEntities} concepts and {scene.omittedAssertions} relationships omitted from this graph window. Pan or zoom to reach offscreen concepts. Arrows show declared relationships, not proven causation.</p>
      <details><summary>Concept list for this neighborhood</summary><ul>{neighborhood.entities.map(entity => <li key={entityKey(entity.reference)}><button onClick={() => select(entity.reference)}>{entity.label}</button></li>)}</ul></details>
      <h3>Claims in this neighborhood</h3><ul className="explore-claims">{neighborhood.assertions.map(assertion => <li key={assertion.reference.assertion_id + assertion.reference.revision}>
        <button onClick={() => void model.detail({ wire_version: "1", revision, selection: { kind: "assertion", reference: assertion.reference } })}>
          {neighborhood.entities.find(entity => entityKey(entity.reference) === entityKey(assertion.subject))?.label ?? assertion.subject.entity_id} {assertion.predicate.replaceAll("_", " ")} {neighborhood.entities.find(entity => entityKey(entity.reference) === entityKey(assertion.object))?.label ?? assertion.object.entity_id}
        </button><span>{assertion.posture} / {assertion.polarity}{assertion.retracted ? " / retracted" : ""}</span>
      </li>)}</ul>
      {neighborhood.next_position && <button onClick={() => void model.neighborhood({ ...neighborhood.request, position: neighborhood.next_position })}>Next neighborhood window</button>}
    </> : <div className="explore-empty"><h2>Follow an idea to its evidence</h2><p>Select a concept to open its local graph, then choose a claim to inspect its sources.</p></div>}
  </section>;
}
