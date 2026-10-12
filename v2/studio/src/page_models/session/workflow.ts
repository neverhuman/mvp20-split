export type WorkflowView = 'question' | 'evaluation' | 'execution' | 'knowledge' | 'domain' | 'design' | 'reasoning' | 'curation';
const views: readonly string[] = ['question', 'evaluation', 'execution', 'knowledge', 'domain', 'design', 'reasoning', 'curation'];

/** Navigation is a bounded hint. It neither selects owner records nor grants access. */
export function workflowView(search: string): WorkflowView {
  const values = new URLSearchParams(search).getAll('view');
  return values.length === 1 && views.includes(values[0]!) ? values[0] as WorkflowView : 'question';
}
export function workflowLink(search: string, view: WorkflowView): string {
  const source = new URLSearchParams(search), result = new URLSearchParams();
  for (const key of ['explore', 'feedback', 'quality_output', 'curation'])
    for (const value of source.getAll(key)) result.append(key, value);
  result.set('view', view);
  return result.toString();
}
