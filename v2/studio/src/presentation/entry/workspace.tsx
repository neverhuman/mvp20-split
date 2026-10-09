import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import type { WorkspaceSession } from '../../page_models/session/model.js';
import type { WorkspaceContext } from '../../transport/session/client.js';
import { ObservationClient } from '../../transport/observations.js';
import { MonitorModel } from '../../page_models/monitor.js';
import { NavigationModel } from '../../page_models/navigation.js';
import { NamedViewsModel } from '../../page_models/named_views.js';
import { EvidenceModel } from '../../page_models/evidence.js';
import { SupervisionClient } from '../../transport/supervision/client.js';
import { SupervisionModel } from '../../page_models/supervision/model.js';
import { FollowupModel } from '../../page_models/followup/model.js';
import { CriterionModel } from '../../page_models/followup/criterion.js';
import { FollowupClient } from '../../transport/followup/client.js';
import { CriterionClient } from '../../transport/followup/criterion.js';
import { MonitorWorkspace } from '../monitor_workspace.js';
import { WorkspaceSelection } from '../../page_models/session/selection.js';
import { WorkspaceFeedbackSelection } from '../../page_models/session/feedback_selection.js';
import { WorkspaceQualityOutputSelection } from '../../page_models/session/quality_output_selection.js';
import { LocalKnowledge } from './knowledge.js';
import { LocalDesign } from './design.js';
import { DraftLibrary } from '../../page_models/design/library.js';
import { AuthoringClient } from '../../transport/authoring.js';
import { workflowView, workflowLink, type WorkflowView } from '../../page_models/session/workflow.js';
import { FeedbackModel } from '../../page_models/feedback/model.js';
import { ResearchRecordClient } from '../../transport/provenance/research.js';
import { FeedbackClient } from '../../transport/feedback/client.js';
import { ResearchQuestion } from './question.js';
import { EvaluationReviewPanel } from '../evaluation_review/panel.js';
import { CampaignFlowModel } from '../../page_models/campaign_flow/model.js';
import { DataProvenanceClient } from '../../transport/provenance/data.js';
import { ConnectedCampaign } from '../campaign_flow.js';
import './style.css';

function Campaign({ context, search }: { context: WorkspaceContext & { run_id: string }; search: string }) {
  const [mode, setMode] = useState<WorkflowView>(() => workflowView(search));
  const [reviewed,setReviewed]=useState(workflowView(search)==='evaluation');
  const [explored, setExplored] = useState(['knowledge','domain'].includes(workflowView(search)));
  const [designed, setDesigned] = useState(workflowView(search) === 'design');
  useEffect(() => { const next = workflowView(search); setMode(next); if(next==='evaluation')setReviewed(true); if (next === 'knowledge' || next === 'domain') setExplored(true); if (next === 'design') setDesigned(true); }, [search]);
  const navigate = (next: WorkflowView) => {
    setMode(next); if(next==='evaluation')setReviewed(true); if (next === 'knowledge' || next === 'domain') setExplored(true); if (next === 'design') setDesigned(true);
    history.replaceState(null, '', location.pathname + location.search + '#' + workflowLink(search, next));
  };
  const selection = useMemo(() => new WorkspaceSelection(search, context.scope), [search, context.scope.tenant_id, context.scope.project_id]);
  const feedbackSelection = useMemo(() => new WorkspaceFeedbackSelection(search, context.scope), [search, context.scope.tenant_id, context.scope.project_id]);
  const outputSelection = useMemo(() => new WorkspaceQualityOutputSelection(search), [search]);
  const owners = useMemo(() => {
    const client = new ObservationClient();
    return { question:new FeedbackModel({ research:new ResearchRecordClient(), feedback:new FeedbackClient() }), model:new MonitorModel(client), navigation:new NavigationModel(client), namedViews:new NamedViewsModel(client), evidence:new EvidenceModel(client), supervision:new SupervisionModel(new SupervisionClient(), new FollowupModel(new FollowupClient()), new CriterionModel(new CriterionClient())), library:new DraftLibrary(context,new AuthoringClient()) };
  }, [context.actor_id, context.scope.tenant_id, context.scope.project_id, context.run_id]);
  useEffect(() => () => { for (const owner of Object.values(owners)) owner.dispose(); }, [owners]);
  const flow=useMemo(()=>new CampaignFlowModel({scope:context.scope,run:context.run_id},new ObservationClient(),new DataProvenanceClient()),[context.scope.tenant_id,context.scope.project_id,context.run_id]);
  const subscribeFlow=useCallback((listener:()=>void)=>flow.subscribe(listener),[flow]);
  const flowView=useSyncExternalStore(subscribeFlow,()=>flow.snapshot);
  const campaignSelection=useMemo(()=>flowView.context?.knowledge?WorkspaceSelection.fromPins(flowView.context.knowledge.pins,context.scope):selection,[flowView.context,selection,context.scope.tenant_id,context.scope.project_id]);
  useEffect(()=>{void flow.refresh();return()=>flow.dispose();},[flow]);
if(flowView.phase==='ready')return <ConnectedCampaign view={flowView} mode={mode} navigate={navigate} refresh={()=>void flow.refresh()} knowledge={explored?<LocalKnowledge embedded selection={campaignSelection} feedbackSelection={feedbackSelection} outputSelection={outputSelection} campaign={{scope:context.scope,run:context.run_id}} active={mode==='domain'} synthetic={context.synthetic}/>:null} technical={<MonitorWorkspace {...owners} compact active={mode==='execution'} context={{scope:context.scope,run:context.run_id}} synthetic={context.synthetic}/>} />;
  if(['loading','idle','denied','failed'].includes(flowView.phase))return <main className="local-entry"><h1>{flowView.phase==='loading'||flowView.phase==='idle'?'Opening the retained campaign':'Campaign context unavailable'}</h1><p>{flowView.message??'Checking the plan and scientific evidence.'}</p>{flowView.phase!=='loading'&&flowView.phase!=='idle'&&<button onClick={()=>void flow.refresh()}>Retry campaign read</button>}</main>;
  return <div className="research-shell">
    <header className="local-workspace-bar"><strong>AMPHORA</strong><span>Research workspace</span><span className="local-access">Local access</span></header>
    <nav className="local-workspace-navigation" aria-label="Research workspace">
      <button aria-pressed={mode === 'question'} onClick={() => navigate('question')}>Question</button>
      <button aria-pressed={mode === 'evaluation'} onClick={() => navigate('evaluation')}>Evaluation design</button>
      <button aria-pressed={mode === 'execution'} onClick={() => navigate('execution')}>Approach and run</button>
      <button aria-pressed={mode === 'knowledge'} onClick={() => navigate('knowledge')}>Results and evidence</button>
      <button aria-pressed={mode === 'design'} onClick={() => navigate('design')}>Next iteration</button>
    </nav>
    <div hidden={mode !== 'question'}><ResearchQuestion model={owners.question} selection={feedbackSelection} active={mode === 'question'} synthetic={context.synthetic} navigate={navigate} /></div>
    {reviewed && <div hidden={mode !== 'evaluation'}><EvaluationReviewPanel synthetic={context.synthetic} /></div>}
    <div hidden={mode !== 'execution'}><MonitorWorkspace {...owners} compact active={mode === 'execution'} context={{ scope:context.scope, run:context.run_id }} synthetic={context.synthetic} /></div>
    {designed && <div hidden={mode !== 'design'}><LocalDesign model={owners.library} synthetic={context.synthetic} /></div>}
    {explored && <div hidden={mode !== 'knowledge' && mode !== 'domain'}><LocalKnowledge selection={selection} feedbackSelection={feedbackSelection} outputSelection={outputSelection} campaign={{ scope: context.scope, run: context.run_id }} active={mode === 'knowledge' || mode === 'domain'} synthetic={context.synthetic} /></div>}
  </div>;
}

export function LocalWorkspace({ session, search = '' }: { session: WorkspaceSession; search?: string }) {
  const subscribe = useCallback((notify: () => void) => session.subscribe(notify), [session]);
  const view = useSyncExternalStore(subscribe, () => session.snapshot);
  return <>
    {!(view.phase === 'ready' && view.context?.run_id) && <header className="local-workspace-bar"><strong>Amphora</strong><span>Research workspace</span><span className="local-access">Local access</span></header>}
    {view.phase === 'ready' && view.context?.run_id ? <Campaign key={[view.context.actor_id, view.context.scope.tenant_id, view.context.scope.project_id, view.context.run_id].join(':')} search={search} context={{ ...view.context, run_id:view.context.run_id }} /> :
      <main className="local-entry" aria-live="polite">
        <h1>{view.phase === 'loading' ? 'Opening your workspace' : view.phase === 'denied' ? 'Open a new workspace session' : view.phase === 'failed' ? 'Workspace unavailable' : 'No campaign selected'}</h1>
        <p>{view.phase === 'loading' ? 'Checking your local session.' : view.phase === 'denied' ? 'Use the local launcher to open this workspace. Existing campaign work is preserved.' : view.phase === 'failed' ? 'The local gateway could not be reached or returned an invalid response.' : 'Your session is ready. No campaign has been selected for this workspace yet.'}</p>
        {view.phase !== 'loading' && <button onClick={() => { void session.open(); }}>Refresh workspace</button>}
      </main>}
  </>;
}
