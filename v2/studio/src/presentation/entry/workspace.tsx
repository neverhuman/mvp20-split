import {CampaignReasoning} from '../campaign_reasoning/panel.js';
import { CampaignCurationEntry } from './curation.js';
import {CampaignSuccessorEntry,CampaignNextCycleEntry,type OpenSuccessor} from './successor.js';
import {SuccessorPlanningContext} from '../../page_models/successor_launch/planning_context.js';
import type {CampaignPlanningContext} from '../../page_models/launch/planning_context.js';
import type { CurationSelection } from '../../transport/campaign_curation/identity.js';
import { CurationPanel } from '../campaign_curation/panel.js';
import { CurationModel } from '../../page_models/campaign_curation/model.js';
import { CurationGraphModel } from '../../page_models/campaign_curation/graph_model.js';
import { CurationGraphReader } from '../../page_models/campaign_curation/graph_review.js';
import { CurationClient } from '../../transport/campaign_curation/client.js';
import { WorkspaceCurationSelection } from '../../page_models/session/curation_selection.js';
import {GenerationModel} from '../../page_models/generation_comparison/model.js';
import {GenerationPanel} from '../generation_comparison/panel.js';
import { useCallback, useEffect, useMemo, useState, useSyncExternalStore, type ReactNode } from 'react';
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
import { CampaignLaunch } from '../../page_models/launch/model.js';
import { LaunchJournal } from '../../page_models/launch/journal.js';
import { LaunchPreparation } from '../../page_models/launch/preparation.js';
import { LaunchPlanningContext } from '../../page_models/launch/planning_context.js';
import { LaunchClient } from '../../transport/launch/client.js';
import { LaunchPanel } from './launch.js';
import { CampaignOriginClient } from '../../transport/campaign_origin/client.js';
import { CampaignOriginModel } from '../../page_models/campaign_origin/model.js';
import { OriginReader } from '../../page_models/campaign_origin/reader.js';
import { OriginResearchReader } from '../../page_models/campaign_origin/research.js';
import { CampaignOriginPanel } from '../campaign_origin/panel.js';
import type { DomainRevisionRef } from '../../contracts/scientific/knowledge.js';
import './style.css';

function Campaign({ context, search, launchControl, planning,openSuccessor }: { context: WorkspaceContext & { run_id: string }; search: string; launchControl: ReactNode; planning?: CampaignPlanningContext;openSuccessor:OpenSuccessor }) {
  const [selectedCuration,setSelectedCuration]=useState<CurationSelection|null>(null);
  const [originKnowledge, setOriginKnowledge] = useState<DomainRevisionRef | null>(null);
  const [mode, setMode] = useState<WorkflowView>(() => workflowView(search));
  const [reviewed,setReviewed]=useState(workflowView(search)==='evaluation');
  const [explored, setExplored] = useState(['knowledge','domain'].includes(workflowView(search)));
  const [designed, setDesigned] = useState(workflowView(search) === 'design');
  useEffect(() => { const next = workflowView(search); setMode(next); if(next==='evaluation')setReviewed(true); if (next === 'knowledge' || next === 'domain') setExplored(true); if (next === 'design') setDesigned(true); }, [search]);
  const navigate = (next: WorkflowView) => {
    setMode(next); if(next==='evaluation')setReviewed(true); if (next === 'knowledge' || next === 'domain') setExplored(true); if (next === 'design') setDesigned(true);
    const params=new URLSearchParams(workflowLink(search,next));
    if(selectedCuration)params.set('curation',selectedCuration.reference.curation_id);
    history.replaceState(null, '', location.pathname + location.search + '#' + params.toString());
  };
  const selection = useMemo(() => new WorkspaceSelection(search, context.scope), [search, context.scope.tenant_id, context.scope.project_id]);
  const feedbackSelection = useMemo(() => new WorkspaceFeedbackSelection(search, context.scope), [search, context.scope.tenant_id, context.scope.project_id]);
  const outputSelection = useMemo(() => new WorkspaceQualityOutputSelection(search), [search]);
  const curationSelection = useMemo(() => new WorkspaceCurationSelection(search, context), [search, context.actor_id, context.run_id, context.scope.tenant_id, context.scope.project_id]);
  const curation = useMemo(() => new CurationModel(new CurationClient()), [context.actor_id, context.run_id, context.scope.tenant_id, context.scope.project_id]);
  useEffect(() => () => curation.dispose(), [curation]);
  const curationGraphs=useMemo(()=>new CurationGraphModel(new CurationGraphReader(new AuthoringClient())),[context.actor_id,context.run_id,context.scope.tenant_id,context.scope.project_id]);
  useEffect(()=>()=>curationGraphs.dispose(),[curationGraphs]);
  const curationLink = selectedCuration || curationSelection.phase !== 'missing' ? <button onClick={() => navigate('curation')}>Review proposed revision</button> : null;
  const owners = useMemo(() => {
    const client = new ObservationClient();
    return { reasoning:new SupervisionModel(new SupervisionClient(),new FollowupModel(new FollowupClient()),new CriterionModel(new CriterionClient())), question:new FeedbackModel({ research:new ResearchRecordClient(), feedback:new FeedbackClient() }), model:new MonitorModel(client), navigation:new NavigationModel(client), namedViews:new NamedViewsModel(client), evidence:new EvidenceModel(client), supervision:new SupervisionModel(new SupervisionClient(), new FollowupModel(new FollowupClient()), new CriterionModel(new CriterionClient())), library:new DraftLibrary(context,new AuthoringClient()) };
  }, [context.actor_id, context.scope.tenant_id, context.scope.project_id, context.run_id]);
  useEffect(() => () => { for (const owner of Object.values(owners)) owner.dispose(); }, [owners]);
  const generations=useMemo(()=>new GenerationModel({scope:context.scope,run:context.run_id},new ObservationClient(),new DataProvenanceClient()),[context.scope.tenant_id,context.scope.project_id,context.run_id]);
  useEffect(()=>()=>generations.dispose(),[generations]);
  const flow=useMemo(()=>new CampaignFlowModel({scope:context.scope,run:context.run_id},new ObservationClient(),new DataProvenanceClient(),planning),[context.scope.tenant_id,context.scope.project_id,context.run_id,planning]);
  const subscribeFlow=useCallback((listener:()=>void)=>flow.subscribe(listener),[flow]);
  const flowView=useSyncExternalStore(subscribeFlow,()=>flow.snapshot);
  const campaignSelection=useMemo(()=>originKnowledge?WorkspaceSelection.fromPins({graph:originKnowledge,experiment:null,observations:[]},context.scope):flowView.context?.knowledge?WorkspaceSelection.fromPins(flowView.context.knowledge.pins,context.scope):selection,[originKnowledge,flowView.context,selection,context.scope.tenant_id,context.scope.project_id]);
  useEffect(()=>{void flow.refresh();return()=>flow.dispose();},[flow]);
  const originModel=useMemo(()=>new CampaignOriginModel(new OriginReader(new CampaignOriginClient(),new AuthoringClient()),new OriginResearchReader(new ResearchRecordClient())),[context.scope.tenant_id,context.scope.project_id,context.run_id,planning]);
  useEffect(()=>()=>originModel.dispose(),[originModel]);
  const originSelection=useMemo(()=>{if(!planning||!flowView.snapshot)return null;try{return planning.selection(flowView.snapshot);}catch{return null;}},[planning,flowView.snapshot]);
  const curationControl=<CampaignCurationEntry context={context} {...(planning?{planning}:{})} review={selection=>{
    setSelectedCuration(selection);setMode('curation');
    const params=new URLSearchParams(workflowLink(search,'curation'));params.set('curation',selection.reference.curation_id);
    history.replaceState(null,'',location.pathname+location.search+'#'+params.toString());
  }}/>;
  const reasoning=<CampaignReasoning model={owners.reasoning} context={{scope:context.scope,run:context.run_id}} back={()=>navigate('knowledge')}/>;
  const provenance=<CampaignOriginPanel model={originModel} selection={originSelection} openKnowledge={revision=>{setOriginKnowledge(revision);navigate('domain');}}/>;
  useEffect(()=>{
    if(mode!=='execution'||!(flowView.snapshot?.status==='running'||flowView.retrySnapshot))return;
    let stopped=false;let timer:ReturnType<typeof setTimeout>;
    const tick=async()=>{if(!document.hidden)await flow.refresh(true);if(!stopped)timer=setTimeout(()=>void tick(),2000);};
    timer=setTimeout(()=>void tick(),2000);return()=>{stopped=true;clearTimeout(timer);};
  },[flow,mode,flowView.snapshot?.status,flowView.retrySnapshot]);
if(mode==='curation')return <CurationPanel graphs={curationGraphs} model={curation} selection={selectedCuration??curationSelection.selection} invalid={!selectedCuration&&curationSelection.phase==='invalid'} synthetic={context.synthetic} back={()=>navigate('design')}
  successor={review=><CampaignSuccessorEntry review={review} open={openSuccessor}/>}
  nextCycle={record=><CampaignNextCycleEntry record={record} ready={()=>navigate('design')}/>}/>;
if(flowView.phase==='ready')return <ConnectedCampaign curationControl={curationControl} curationLink={curationLink} reasoning={reasoning} generations={mode==='knowledge'?<details><summary>Evolutionary search history</summary><GenerationPanel model={generations}/></details>:null} provenance={provenance} launchControl={launchControl} view={flowView} mode={mode} navigate={navigate} refresh={()=>void flow.refresh()} knowledge={explored?<LocalKnowledge embedded selection={campaignSelection} feedbackSelection={feedbackSelection} outputSelection={outputSelection} campaign={{scope:context.scope,run:context.run_id}} active={mode==='domain'} synthetic={context.synthetic}/>:null} technical={<MonitorWorkspace {...owners} compact active={mode==='execution'} context={{scope:context.scope,run:context.run_id}} synthetic={context.synthetic}/>} />;
  if(['loading','idle','denied','failed'].includes(flowView.phase))return <main className="local-entry">{launchControl}<h1>{flowView.phase==='loading'||flowView.phase==='idle'?'Opening the retained campaign':'Campaign context unavailable'}</h1><p>{flowView.message??'Checking the plan and scientific evidence.'}</p>{flowView.phase!=='loading'&&flowView.phase!=='idle'&&<button onClick={()=>void flow.refresh()}>Retry campaign read</button>}</main>;
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
    {mode==='reasoning'&&reasoning}
    <div hidden={mode !== 'execution'}>{mode==='execution'&&<button onClick={()=>navigate('reasoning')}>Inspect model decisions</button>}{launchControl}<MonitorWorkspace {...owners} compact active={mode === 'execution'} context={{ scope:context.scope, run:context.run_id }} synthetic={context.synthetic} /></div>
    {designed && <div hidden={mode !== 'design'}>{curationLink}{curationControl}<LocalDesign model={owners.library} synthetic={context.synthetic} /></div>}
    {explored && <div hidden={mode !== 'knowledge' && mode !== 'domain'}>{mode==='knowledge'&&<><button onClick={()=>navigate('reasoning')}>Inspect model decisions</button><GenerationPanel model={generations}/></>}<LocalKnowledge selection={selection} feedbackSelection={feedbackSelection} outputSelection={outputSelection} campaign={{ scope: context.scope, run: context.run_id }} active={mode === 'knowledge' || mode === 'domain'} synthetic={context.synthetic} /></div>}
  </div>;
}

function ReadyWorkspace({context,search}:{context:WorkspaceContext;search:string}) {
  const [successors,setSuccessors]=useState<SuccessorPlanningContext[]>([]),[selectedSuccessor,setSelectedSuccessor]=useState<number|null>(null);
  const [journeySearch,setJourneySearch]=useState<string|null>(null);
  const owners=useMemo(()=>{
    const client=new LaunchClient();
    const journal=new LaunchJournal(context,{getItem:key=>localStorage.getItem(key),setItem:(key,value)=>localStorage.setItem(key,value)});
    return {launch:new CampaignLaunch(client,journal),preparation:new LaunchPreparation(context,new AuthoringClient(),client)};
  },[context.actor_id,context.scope.tenant_id,context.scope.project_id]);
  const listen=useCallback((notify:()=>void)=>owners.launch.subscribe(notify),[owners]);
  const view=useSyncExternalStore(listen,()=>owners.launch.snapshot);
  useEffect(()=>()=>{owners.launch.dispose();owners.preparation.dispose();},[owners]);
  useEffect(()=>{
    let stopped=false;let timer:ReturnType<typeof setTimeout>;
    const tick=async()=>{
      const current=owners.launch.snapshot;
      if(!document.hidden&&owners.launch.canReconcile&&!["released","rejected"].includes(current.receipt?.phase??""))await owners.launch.reconcile();
      if(!stopped)timer=setTimeout(()=>void tick(),2000);
    };
    void tick();return()=>{stopped=true;clearTimeout(timer);};
  },[owners]);
  const launchedRun=view.receipt?.run_id??null;
  const selected=selectedSuccessor===null?undefined:successors[selectedSuccessor];
  const run=selected?.receipt.run_id??launchedRun??context.run_id;
  const planning=useMemo(()=>launchedRun&&owners.launch.submission&&owners.launch.snapshot.receipt
    ?new LaunchPlanningContext(owners.launch.submission,owners.launch.snapshot.receipt,new AuthoringClient()):undefined,[owners,launchedRun]);
  const control=<LaunchPanel launch={owners.launch} preparation={owners.preparation}/>;
  const choose=(index:number|null)=>{
    setSelectedSuccessor(index);const params=new URLSearchParams();params.set('view','execution');
    setJourneySearch(params.toString());history.replaceState(null,'',location.pathname+location.search+'#'+params.toString());
  };
  const open:OpenSuccessor=(review,command,receipt)=>{
    const next=new SuccessorPlanningContext(review,command,receipt,new AuthoringClient(),new CurationClient());
    const found=successors.findIndex(item=>item.receipt.run_id===next.receipt.run_id);
    if(found>=0){choose(found);return;}
    const retained=[...successors,next].slice(-32);setSuccessors(retained);choose(retained.length-1);
  };
  const currentPlanning=selected??planning;
  return run?<><nav className="campaign-journey" aria-label="Campaign iteration history" hidden={!successors.length}>
    <label>Inspect campaign<select value={selectedSuccessor??'original'} onChange={event=>choose(event.target.value==='original'?null:Number(event.target.value))}>
      <option value="original">Original campaign</option>{successors.map((item,index)=><option key={item.receipt.run_id} value={index}>{item.review.proposed.title} · {item.receipt.run_id}</option>)}</select></label>
    <span>Most recent 32 opened successors in this workspace. Reload returns to the original campaign; reopen a successor from its retained proposal.</span>
    </nav><Campaign key={run} context={{...context,run_id:run}} search={journeySearch??search} launchControl={selected?null:control} openSuccessor={open} {...(currentPlanning?{planning:currentPlanning}:{})}/></>
    :<main className="local-entry"><h1>Prepare your first campaign</h1>{control}</main>;
}

export function LocalWorkspace({ session, search = '' }: { session: WorkspaceSession; search?: string }) {
  const subscribe = useCallback((notify: () => void) => session.subscribe(notify), [session]);
  const view = useSyncExternalStore(subscribe, () => session.snapshot);
  return <>
    {!(view.phase === 'ready' && view.context) && <header className="local-workspace-bar"><strong>Amphora</strong><span>Research workspace</span><span className="local-access">Local access</span></header>}
    {view.phase === 'ready' && view.context ? <ReadyWorkspace key={[view.context.actor_id,view.context.scope.tenant_id,view.context.scope.project_id].join(':')} search={search} context={view.context} /> :
      <main className="local-entry" aria-live="polite">
        <h1>{view.phase === 'loading' ? 'Opening your workspace' : view.phase === 'denied' ? 'Open a new workspace session' : view.phase === 'failed' ? 'Workspace unavailable' : 'No campaign selected'}</h1>
        <p>{view.phase === 'loading' ? 'Checking your local session.' : view.phase === 'denied' ? 'Use the local launcher to open this workspace. Existing campaign work is preserved.' : view.phase === 'failed' ? 'The local gateway could not be reached or returned an invalid response.' : 'Your session is ready. No campaign has been selected for this workspace yet.'}</p>
        {view.phase !== 'loading' && <button onClick={() => { void session.open(); }}>Refresh workspace</button>}
      </main>}
  </>;
}
