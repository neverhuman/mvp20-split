import { forwardRef } from 'react';
import type { RecordedCapability } from '../../page_models/campaign_curation/records.js';
import type { CapabilityRequestView } from '../../contracts/campaign_curation.js';

function Ports({ title, ports }: { title: string; ports: CapabilityRequestView['gap']['inputs'] }) {
  return <section className="curation-ports"><h3>{title}</h3>{ports.length ? <dl>{ports.map(port => <div key={port.name}>
    <dt>{port.name}</dt><dd><strong>{port.representation}</strong>{port.unit ? ` · ${port.unit}` : ' · unit unspecified'}
      <p>{port.description}</p>{port.schema_ref && <small>Schema: {port.schema_ref.schema_id}</small>}</dd>
  </div>)}</dl> : <p>No inputs were specified in this request.</p>}</section>;
}

export const CapabilityDetail = forwardRef<HTMLHeadingElement, { record: RecordedCapability }>(function CapabilityDetail({ record }, ref) {
  const { gap, fulfillment } = record.data;
  return <article className="curation-capability" aria-label="Requested capability detail">
    <div className="curation-detail-heading"><p className="curation-kicker">Requested tool behavior</p>
      <h2 ref={ref} tabIndex={-1}>{gap.purpose}</h2><p>{gap.graph_gap}</p>
      <span className={'curation-state curation-state-' + (fulfillment?.status ?? 'requested')}>{record.fulfillmentStatus}</span>
    </div>
    <section><h3>Where it applies</h3><ul>{gap.applicability.map((item, index) => <li key={index}>{item}</li>)}</ul></section>
    <section><h3>What would demonstrate it works?</h3><p>{gap.evidence_need}</p>
      <ol className="curation-criteria">{gap.acceptance_criteria.map((item, index) => <li key={index}>{item}</li>)}</ol>
    </section>
    <details className="curation-port-detail"><summary>Requested inputs and outputs</summary>
      <Ports title="Inputs" ports={gap.inputs}/><Ports title="Outputs" ports={gap.outputs}/>
    </details>
    <section className="curation-fulfillment"><h3>Fulfillment review</h3>
      {!fulfillment && <p>No owner-submitted release or acceptance evidence is recorded for this request.</p>}
      {fulfillment && <>
        <p><strong>{fulfillment.specification.release.tool.capability_id}</strong> · release {fulfillment.specification.release.tool.release}</p>
        <p>{fulfillment.status === 'verified' ? 'The retained release and reviewed evidence passed the fulfillment checks. This does not establish scientific validity or current execution eligibility.' :
          fulfillment.status === 'pending' ? 'A release and evidence were submitted. Verification is still pending.' :
          fulfillment.status === 'rejected' ? 'The submitted release or evidence did not satisfy the fulfillment review. The capability request remains unresolved.' :
          'The fulfillment outcome is not known. The request remains unresolved.'}</p>
        <details><summary>{record.evidence.length} recorded evidence {record.evidence.length === 1 ? 'reference' : 'references'}</summary>
          <p>References retained with the review. Evidence content is not loaded in this view.</p>
          <ul>{record.evidence.map(item => <li key={item.artifact_id}><strong>{item.artifact_id}</strong><br/>{item.schema_ref.schema_id} · {item.media_type}</li>)}</ul>
        </details>
      </>}
    </section>
    <details className="curation-technical"><summary>Original references and review details</summary><dl>
      <dt>Capability request</dt><dd>{record.data.reference.request_id}</dd>
      <dt>Original proposal digest</dt><dd>{record.data.proposal_sha256}</dd>
      {fulfillment && <><dt>Review recorded</dt><dd>{fulfillment.created_at}</dd>
        <dt>Reason</dt><dd>{fulfillment.reason_code ?? 'No rejection recorded'}</dd>
        <dt>Release descriptor</dt><dd>{fulfillment.specification.release.descriptor_sha256}</dd></>}
    </dl></details>
  </article>;
});
