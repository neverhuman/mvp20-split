/** Actual-owner acceptance driver. Secrets arrive on stdin and never enter evidence. */
import assert from 'node:assert/strict';
import { DataProvenanceClient } from '../dist/src/transport/provenance/data.js';
import { ResearchRecordClient } from '../dist/src/transport/provenance/research.js';
import { KnowledgeClient } from '../dist/src/transport/scientific/knowledge.js';
import { ResearchClient } from '../dist/src/transport/scientific/research.js';
import { ExploreModel } from '../dist/src/page_models/explore/model.js';
import { FeedbackClient } from '../dist/src/transport/feedback/client.js';
import { FeedbackModel } from '../dist/src/page_models/feedback/model.js';

let raw = '';
for await (const chunk of process.stdin) {
  raw += chunk;
  if (Buffer.byteLength(raw) > 1048576) throw new Error('probe_input_limit');
}
const { owners, records } = JSON.parse(raw);
const fetcher = (path, options) => {
  const match = /^\/api\/(data|research|knowledge)(\/v1\/.*)$/.exec(String(path));
  if (!match) throw new Error('probe_route');
  const owner = owners[match[1]], origin = new URL(owner.endpoint);
  if (origin.protocol !== 'http:' || origin.hostname !== '127.0.0.1') throw new Error('probe_origin');
  return fetch(owner.endpoint + match[2], { ...options, headers: { ...options.headers, Authorization: 'Bearer ' + owner.token } });
};
const signal = () => new AbortController().signal;
const data = new DataProvenanceClient(fetcher), research = new ResearchRecordClient(fetcher);
const knowledge = new KnowledgeClient(fetcher), views = new ResearchClient(fetcher);
const text = await data.span(records.span, signal());
assert.equal(text.text, 'Synthetic claims are not scientifically accepted.');
await data.trace(records.trace, signal());
assert.deepEqual(await data.derivation(records.publication.outcome.derivation.artifact, signal()), records.publication.outcome.derivation);
assert.deepEqual(await research.question(records.question.reference, signal()), records.question);
assert.deepEqual(await research.need(records.need.reference, signal()), records.need);
for (const [method, key] of [['material', 'material-state-revision'], ['experiment', 'experiment-definition'], ['observation', 'observation-revision']]) {
  assert.deepEqual(await research[method](records.specimens[key].reference, signal()), records.specimens[key]);
}
assert.deepEqual(await knowledge.catalog(records.head.snapshot, signal()), records.knowledge_views.catalog);
assert.deepEqual(await knowledge.search(records.knowledge_views.entities.request, signal()), records.knowledge_views.entities);
assert.deepEqual(await views.catalog(records.specimens['experiment-definition'].reference, signal()), records.research_views.catalog);
assert.deepEqual(await views.specimens(records.research_views.specimens.request, signal()), records.research_views.specimens);
assert.deepEqual(await views.properties(records.research_views.properties.request, signal()), records.research_views.properties);
const model = new ExploreModel({ knowledge, research: views, records: research, data });
model.bind({ graph: records.head.snapshot, experiment: records.specimens['experiment-definition'].reference,
  observations: records.research_views.properties.request.observations });
await Promise.all([model.search(records.knowledge_views.entities.request), model.specimens(records.research_views.specimens.request),
  model.properties(records.research_views.properties.request), model.source(records.span)]);
await Promise.all([model.trace(records.trace), model.artifact(records.publication.outcome.derivation.artifact),
  model.derivation(records.publication.outcome.derivation.artifact)]);
assert.deepEqual(model.snapshot.regions.search.value, records.knowledge_views.entities);
assert.deepEqual(model.snapshot.regions.properties.value, records.research_views.properties);
assert.equal(model.snapshot.regions.source.value.text, text.text);
assert.equal(model.snapshot.regions.trace.value.trace_id, records.trace.trace_id);
assert.deepEqual(model.snapshot.regions.derivation.value, records.publication.outcome.derivation);
model.visibility(false);
assert.ok(Object.values(model.snapshot.regions).every(region => region.phase === 'stale' && region.value === null));
model.dispose();
if (records.feedback) {
  const feedback = new FeedbackModel({ research, feedback: new FeedbackClient(fetcher) });
  feedback.bind({ ...records.feedback.pins, assessment: records.feedback.unmet.request, publication: null, proposal: null, corrections: null });
  await feedback.refresh();
  assert.equal(feedback.snapshot.phase, 'ready');
  assert.equal(feedback.snapshot.lineage.evidenceState, 'gap');
  feedback.bind(records.feedback.pins);
  await feedback.refresh();
  assert.equal(feedback.snapshot.phase, 'ready', feedback.snapshot.error?.kind);
  assert.deepEqual(feedback.snapshot.lineage.records.proposal, records.feedback.proposal);
  assert.deepEqual(feedback.snapshot.lineage.records.change, records.feedback.change);
  assert.deepEqual(feedback.snapshot.lineage.records.corrections.previous, records.feedback.root);
  assert.deepEqual(feedback.snapshot.lineage.records.corrections.next, records.feedback.next);
  assert.equal(feedback.snapshot.lineage.evidenceState, 'sufficient');
  assert.equal(feedback.snapshot.lineage.futureOnly, true);
  const provenance = await data.derivation(records.feedback.second.evidence, signal());
  assert.ok(provenance.declaration.inputs.some(ref => ref.artifact_id === records.feedback.second.report.artifact_id));
  assert.ok(records.feedback.proposal.proposal.grounding.interpretation_artifacts.some(ref => ref.artifact_id === records.feedback.second.report.artifact_id));
  assert.deepEqual(await research.observationCorrection(records.feedback.observation_correction.after.reference, signal()), records.feedback.observation_correction);
  feedback.dispose();
}
process.stdout.write(JSON.stringify({ status: 'verified', artifact_sha256: text.artifact_sha256, span_sha256: text.span_sha256,
  boundary: 'actual owner HTTP through compiled Studio clients and Explore model', browser_claim: false }));
