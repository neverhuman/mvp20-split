import type {DraftRevision} from '../../contracts/authoring.js';
import type {ArtifactRef} from '../../contracts/observations.js';
import {same} from '../../transport/scientific/identity.js';
import {immutable} from '../explore/context.js';

/** Exact declared tool/child-scope inputs, not inferred outputs or fetched content. */
export class CurationArtifactInputs {
  static collect(definition:DraftRevision['definition'],inherited:readonly ArtifactRef[]=[]):ArtifactRef[]{
    const refs=new Map<string,ArtifactRef>();
    const add=(ref:ArtifactRef)=>{
      if(!same(ref.scope,definition.scope))throw Error('curation_artifact_scope');
      const previous=refs.get(ref.artifact_id);
      if(previous&&!same(previous,ref))throw Error('curation_artifact_conflict');
      refs.set(ref.artifact_id,ref);
      if(refs.size>16)throw Error('curation_artifact_limit');
    };
    inherited.forEach(add);
    const pending=[{body:definition.body,depth:0}];let nodes=0,scopes=0;
    while(pending.length){
      const current=pending.pop()!;
      if(++scopes>1024||current.depth>16)throw Error('curation_artifact_graph_limit');
      for(const node of current.body.nodes){
        if(++nodes>4096)throw Error('curation_artifact_graph_limit');
        if('inputs' in node)for(const binding of node.inputs)if(binding.source.kind==='artifact')add(binding.source.artifact);
        if(node.kind==='invoke'&&node.checkpoint?.kind==='artifact')add(node.checkpoint.artifact);
        if(node.kind==='iterate'||node.kind==='scatter')pending.push({body:node.body,depth:current.depth+1});
      }
    }
    return immutable([...refs.values()].sort((a,b)=>a.artifact_id.localeCompare(b.artifact_id)));
  }
}
