import { useEffect, useMemo } from 'react';
import { ExploreModel } from '../../page_models/explore/model.js';
import type { WorkspaceSelection } from '../../page_models/session/selection.js';
import { KnowledgeClient } from '../../transport/scientific/knowledge.js';
import { ResearchClient } from '../../transport/scientific/research.js';
import { ResearchRecordClient } from '../../transport/provenance/research.js';
import { DataProvenanceClient } from '../../transport/provenance/data.js';
import { ExploreWorkspace } from '../explore/workspace.js';

export function LocalKnowledge({ selection, active, synthetic }: { selection: WorkspaceSelection; active: boolean; synthetic: boolean }) {
  const model = useMemo(() => new ExploreModel({ knowledge:new KnowledgeClient(), research:new ResearchClient(), records:new ResearchRecordClient(), data:new DataProvenanceClient() }), [selection]);
  useEffect(() => { model.bind(selection.pins); return () => model.dispose(); }, [model, selection]);
  if (selection.phase !== 'ready') return <main className="local-entry">
    <h1>{selection.phase === 'invalid' ? 'Research context unavailable' : 'No research context selected'}</h1>
    <p>{selection.phase === 'invalid' ? 'This link does not contain a valid research selection for your workspace. Execution history remains available.' : 'Open a workspace link with an explicit domain graph or experiment selection to inspect its evidence.'}</p>
  </main>;
  return <ExploreWorkspace model={model} active={active} synthetic={synthetic} />;
}
