import { useEffect, useMemo } from 'react';
import { ExploreModel } from '../../page_models/explore/model.js';
import type { WorkspaceSelection } from '../../page_models/session/selection.js';
import { KnowledgeClient } from '../../transport/scientific/knowledge.js';
import { ResearchClient } from '../../transport/scientific/research.js';
import { ResearchRecordClient } from '../../transport/provenance/research.js';
import { DataProvenanceClient } from '../../transport/provenance/data.js';
import { ExploreWorkspace } from '../explore/workspace.js';
import { FeedbackModel } from '../../page_models/feedback/model.js';
import { FeedbackClient } from '../../transport/feedback/client.js';
import type { WorkspaceFeedbackSelection } from '../../page_models/session/feedback_selection.js';
import type { WorkspaceQualityOutputSelection } from '../../page_models/session/quality_output_selection.js';
import type { RunContext } from '../../page_models/graph_window.js';
import { QualityLinkModel } from '../../page_models/quality/runtime_link.js';
import { ObservationClient } from '../../transport/observations.js';

export function LocalKnowledge({ selection, feedbackSelection, outputSelection, campaign, active, synthetic }: {
  selection: WorkspaceSelection; feedbackSelection?: WorkspaceFeedbackSelection; outputSelection: WorkspaceQualityOutputSelection;
  campaign: RunContext; active: boolean; synthetic: boolean;
}) {
  const model = useMemo(() => new ExploreModel({ knowledge:new KnowledgeClient(), research:new ResearchClient(), records:new ResearchRecordClient(), data:new DataProvenanceClient() }), [selection]);
  const feedback = useMemo(() => new FeedbackModel({ research:new ResearchRecordClient(), feedback:new FeedbackClient() }), [feedbackSelection]);
  const qualityLink = useMemo(() => new QualityLinkModel(new ObservationClient()), []);
  useEffect(() => { model.bind(selection.pins); return () => model.dispose(); }, [model, selection]);
  useEffect(() => { feedback.bind(feedbackSelection?.pins ?? null); return () => feedback.dispose(); }, [feedback, feedbackSelection]);
  useEffect(() => { if (!active) feedback.visibility(false); }, [feedback, active]);
  useEffect(() => { qualityLink.bind(campaign, outputSelection.pins); }, [qualityLink, campaign.scope.tenant_id, campaign.scope.project_id, campaign.run, outputSelection]);
  useEffect(() => () => qualityLink.dispose(), [qualityLink]);
  if (selection.phase !== 'ready') return <main className="local-entry">
    <h1>{selection.phase === 'invalid' ? 'Research context unavailable' : 'No research context selected'}</h1>
    <p>{selection.phase === 'invalid' ? 'This link does not contain a valid research selection for your workspace. Execution history remains available.' : 'Open a workspace link with an explicit domain graph or experiment selection to inspect its evidence.'}</p>
  </main>;
  return <>{feedbackSelection?.phase === 'invalid' && <p role="status">The selected question link is invalid for this workspace. Other research views remain available.</p>}
    {outputSelection.phase === 'invalid' && <p role="status">The selected execution output link is invalid. No affected consumer has been inferred.</p>}
    <ExploreWorkspace model={model} active={active} synthetic={synthetic} qualityLink={qualityLink} {...(feedbackSelection?.phase === 'ready' ? { feedback } : {})} /></>;
}
