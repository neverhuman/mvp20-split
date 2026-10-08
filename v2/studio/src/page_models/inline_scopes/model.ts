import type { GraphSnapshotPage, GraphTopologyPage } from '../../contracts/observations.js';
import type { NavigationSource } from '../../transport/observations.js';
import { ReadFailure, asReadFailure } from '../../transport/failure.js';
import { cutKey } from '../graph_window.js';
import { RequestLane } from '../request_lane.js';
import { TopologyWindow } from '../topology_window.js';

type Anchor = GraphSnapshotPage['snapshot'];
export type InlineGroup = Readonly<{ phase:'loading'|'ready'|'failed'; total:number;
  pages:readonly GraphTopologyPage[]; error:string|null }>;

/** Bounded sibling reads at exactly the Monitor cut. No competing snapshot or execution writes. */
export class InlineScopes {
  private anchor: Anchor|null = null;
  private identity:string|null=null;
  private desired=new Map<string,boolean>();
  private lanes = new Map<string,RequestLane>();
  private listeners = new Set<() => void>();
  private state: Readonly<Record<string,InlineGroup>> = Object.freeze({});
  constructor(private readonly source:NavigationSource, private readonly reject:(error:ReadFailure)=>void) {}
  get snapshot() { return this.state; }
  subscribe(listener:()=>void) { this.listeners.add(listener); return ()=>{this.listeners.delete(listener);}; }
  private publish(id:string, value:InlineGroup) { this.state=Object.freeze({...this.state,[id]:Object.freeze(value)}); this.notify(); }
  private notify() { for(const listener of this.listeners) listener(); }
  bind(anchor:Anchor|null) {
    if(anchor && this.anchor && cutKey(anchor.cut)===cutKey(this.anchor.cut) && anchor.snapshot_token===this.anchor.snapshot_token) return;
    for(const lane of this.lanes.values()) lane.cancel(); this.lanes.clear();
    if(anchor) {
      const identity=JSON.stringify([anchor.cut.scope,anchor.cut.run_id,anchor.cut.plan_sha256]);
      if(identity!==this.identity)this.desired.clear();this.identity=identity;
    }
    this.anchor=anchor ? structuredClone(anchor) : null; this.state=Object.freeze({}); this.notify();
  }
  restore(records:readonly GraphTopologyPage['nodes'][number][], autoRoot:boolean) {
    for(const record of records) {
      const id=record.activation.activation_id,preference=this.desired.get(id);
      if(record.child_scope_count && !this.state[id] && (preference===true || preference===undefined && autoRoot &&
        record.activation.kind==='scatter' && !(record.activation.path.occurrences?.length))) void this.expand(record);
    }
  }
  reset() {this.desired.clear();this.identity=null;this.bind(null);}
  collapse(id:string) {
    this.desired.set(id,false);
    const next={...this.state};
    const remove=(key:string)=>{
      for(const page of next[key]?.pages??[]) for(const node of page.nodes) if(next[node.activation.activation_id]) remove(node.activation.activation_id);
      this.lanes.get(key)?.cancel();this.lanes.delete(key);delete next[key];
    };
    remove(id);this.state=Object.freeze(next);this.notify();
  }
  async expand(parent:GraphTopologyPage['nodes'][number]) {
    const anchor=this.anchor,id=parent.activation.activation_id;
    if(!anchor || !['scatter','iterate'].includes(parent.activation.kind) || !parent.child_scope_count || this.state[id]?.phase==='loading') return;
    if(Object.keys(this.state).length>=8 && !this.state[id]) return;
    this.desired.set(id,true);
    const lane=this.lanes.get(id)??new RequestLane();this.lanes.set(id,lane);const request=lane.begin();
    this.publish(id,{phase:'loading',total:parent.child_scope_count,pages:[],error:null});
    try {
      const groups=await this.source.scopes(anchor.cut.run_id,anchor.snapshot_token,id,undefined,request.signal);
      if(!request.current()) return;
      if(cutKey(groups.cut)!==cutKey(anchor.cut)) throw new ReadFailure('resnapshot');
      if(groups.parent_activation_id!==id || groups.scope_count!==parent.child_scope_count ||
        groups.scopes.length>groups.scope_count || new Set(groups.scopes.map(s=>s.scope_key)).size!==groups.scopes.length ||
        groups.scopes.some(s=>s.parent_activation_id!==id) || (!groups.next_cursor && groups.scopes.length!==groups.scope_count) ||
        (!!groups.next_cursor && (!groups.scopes.length || groups.scopes.length>=groups.scope_count)))
        throw new ReadFailure('invalid_response');
      // At most four siblings per expansion. More remain explicitly omitted, not silently complete.
      const selected=groups.scopes.slice(0,4);
      const pages=await Promise.all(selected.map(async scope=> {
        const raw=await this.source.topology(anchor.cut.run_id,scope.scope_key,anchor.snapshot_token,{},undefined,request.signal);
        const page=TopologyWindow.open(anchor.cut,scope.scope_key,{},raw).page;
        if(JSON.stringify(page.graph_scope)!==JSON.stringify(scope)) {
          // DTO property order is not an identity; compare semantic fields instead.
          if(page.graph_scope.parent_activation_id!==id || page.graph_scope.status!==scope.status ||
            page.graph_scope.node_count!==scope.node_count || JSON.stringify(page.graph_scope.occurrences)!==JSON.stringify(scope.occurrences) ||
            JSON.stringify(page.graph_scope.definition_path)!==JSON.stringify(scope.definition_path)) throw new ReadFailure('invalid_response');
        }
        const occurrence=page.graph_scope.occurrences.at(-1);
        if(!occurrence || occurrence.node_id!==parent.activation.path.node_id ||
          occurrence.kind!==(parent.activation.kind==='scatter'?'scatter':'loop') ||
          JSON.stringify(page.graph_scope.occurrences.slice(0,-1))!==JSON.stringify(parent.activation.path.occurrences??[])) throw new ReadFailure('invalid_response');
        if(page.nodes.some(n=>JSON.stringify(n.activation.path.occurrences??[])!==JSON.stringify(page.graph_scope.occurrences)))
          throw new ReadFailure('invalid_response');
        return page;
      }));
      const ids=pages.flatMap(p=>p.nodes.map(n=>n.activation.activation_id));
      if(new Set(ids).size!==ids.length || ids.includes(id)) throw new ReadFailure('invalid_response');
      if(request.current()) this.publish(id,{phase:'ready',total:groups.scope_count,pages,error:null});
    } catch(raw) {
      if(!request.current()) return;
      lane.cancel(); const error=asReadFailure(raw);
      if(error.kind==='denied'||error.kind==='resnapshot') { if(error.kind==='denied')this.reset();else this.bind(null);this.reject(error); }
      else this.publish(id,{phase:'failed',total:parent.child_scope_count,pages:[],error:error.kind});
    }
  }
  dispose() { this.reset();this.listeners.clear(); }
}
