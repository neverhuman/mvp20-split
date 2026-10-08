import compiled from './validators.js';
import type {ArtifactRef} from '../../contracts/observations.js';
import {RequestLane} from '../request_lane.js';
import {scientificSchemas} from './schemas.js';

type Method=keyof typeof scientificSchemas;
export type ScientificResult=Readonly<{method:Method;candidate:string;parameters:Readonly<Record<string,unknown>>;
  quantities:readonly {name:string;value:number|string;unit:string}[];procedure:readonly string[];limitation:string}>;
const validators:Record<string,(value:unknown)=>boolean>={'materials.hansen-solvency.output':compiled.hansen_solvency,'materials.arrhenius-viscosity.output':compiled.arrhenius_viscosity};
export function supported(reference:ArtifactRef):boolean {
  const profile=scientificSchemas[reference.schema_ref.schema_id as Method];
  return !!profile&&reference.schema_ref.version==='1'&&reference.schema_ref.sha256===profile.sha256;
}
export function scientificResult(reference:ArtifactRef,value:unknown):ScientificResult {
  if(!supported(reference)||!validators[reference.schema_ref.schema_id]!(value))throw Error('Scientific output schema mismatch');
  const d=value as Record<string,unknown>,method=reference.schema_ref.schema_id as Method;
  const parameters=JSON.parse(JSON.stringify(d.input_parameters)) as Record<string,unknown>;
  if(d.candidate_id!==parameters.candidate_id)throw Error('Scientific candidate identity mismatch');
  const fields=method==='materials.hansen-solvency.output'?
    [['distance_squared','MPa'],['distance','MPa^0.5'],['relative_energy_difference','dimensionless'],['sphere_position','declared sphere']]:
    [['reference_temperature_k','K'],['temperature_k','K'],['exponent','dimensionless'],['viscosity_pa_s','Pa.s']];
  return Object.freeze({method,candidate:String(d.candidate_id),parameters:Object.freeze(parameters),
    quantities:Object.freeze(fields.map(([name,unit])=>Object.freeze({name:name!,unit:unit!,value:d[name!] as number|string}))),
    procedure:Object.freeze([...(d.procedure as string[])]),limitation:String(d.limitation)});
}
interface Source{jsonArtifact(reference:ArtifactRef,signal:AbortSignal):Promise<unknown>}
type View=Readonly<{phase:'idle'|'loading'|'ready'|'failed'|'denied';result:ScientificResult|null;error:string|null}>;
export class ScientificOutputModel {
  private lane=new RequestLane();private listeners=new Set<()=>void>();private disposed=false;
  private view:View={phase:'idle',result:null,error:null};
  constructor(private source:Source){}
  get snapshot(){return this.view;}
  subscribe(listener:()=>void){this.listeners.add(listener);return()=>{this.listeners.delete(listener);};}
  private patch(view:View){if(this.disposed)return;this.view=Object.freeze(view);for(const l of this.listeners)l();}
  async read(reference:ArtifactRef|null){this.lane.cancel();if(this.disposed)return;
    if(!reference||!supported(reference)){this.patch({phase:'idle',result:null,error:null});return;}
    const pinned=JSON.parse(JSON.stringify(reference)) as ArtifactRef,ticket=this.lane.begin();this.patch({phase:'loading',result:null,error:null});
    try{const raw=await this.source.jsonArtifact(pinned,ticket.signal);if(ticket.current())this.patch({phase:'ready',result:scientificResult(pinned,raw),error:null});}
    catch(error){if(ticket.current())this.patch({phase:(error as {kind?:string})?.kind==='denied'?'denied':'failed',result:null,error:'Scientific result could not be verified. No result is displayed.'});}
  }
  dispose(){this.lane.cancel();this.listeners.clear();this.disposed=true;this.view={phase:'idle',result:null,error:null};}
}
