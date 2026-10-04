import { useState } from "react";
import type { MaterialStateRevision } from "../../contracts/scientific/provenance.js";
import type { ExploreModel } from "../../page_models/explore/model.js";

export function MaterialInspection({ record, model }: { record: MaterialStateRevision; model: ExploreModel }) {
  const [page, setPage] = useState(0), start = page * 8;
  return <section aria-label="Prepared material state"><h3>{record.reference.material_state_id}</h3><p>Revision {record.reference.revision} / candidate {record.candidate.candidate_id}</p><p>{record.preparation.length} preparation steps; {record.features.length} retained material features.</p>
    {record.preparation.length === 0 ? <p>No processing history declared.</p> : <><ol className="material-preparation" start={start + 1}>{record.preparation.slice(start, start + 8).map(event => <li key={event.event_id}><strong>{event.event_id}</strong><p>{event.attribution.basis} / {event.context.method.schema_id} / {event.context.method.version}</p>{event.context.duration && <p>Duration: {event.context.duration.value} {event.context.duration.unit}</p>}<p>Atmosphere: {event.context.atmosphere ?? "not reported"}</p><details><summary>{event.context.conditions.length} processing conditions</summary><dl>{event.context.conditions.map(c => <div key={c.name}><dt>{c.name}</dt><dd>{c.quantity.value} {c.quantity.unit}</dd></div>)}</dl></details><button onClick={() => void model.artifact(event.attribution.source)}>Inspect preparation source</button></li>)}</ol><div className="explore-caption"><button disabled={page === 0} onClick={() => setPage(page - 1)}>Previous preparation</button><button disabled={start + 8 >= record.preparation.length} onClick={() => setPage(page + 1)}>Next preparation</button></div></>}
  </section>;
}
