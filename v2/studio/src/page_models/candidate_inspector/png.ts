import type {StructureResult} from '../../contracts/candidate.js';
import {requireReply} from '../../transport/scientific/identity.js';
import {active,sha256} from '../../transport/provenance/integrity.js';

type Depiction=Extract<StructureResult['outcome'],{status:'derived'}>['depiction'];
function crc32(bytes:Uint8Array){
 let crc=0xffffffff;
 for(const byte of bytes){crc^=byte;for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}
 return (crc^0xffffffff)>>>0;
}

/** Bounded inert Cairo PNG profile; no external URLs, metadata, animation or SVG. */
export async function verifiedPNG(depiction:Depiction,signal:AbortSignal):Promise<string>{
 active(signal);
 const encoded=depiction.png_base64;
 requireReply(encoded.length<=174764&&encoded.length%4===0&&/^[A-Za-z0-9+/]*={0,2}$/.test(encoded));
 let binary:string;
 try{binary=atob(encoded);}catch{throw Error('invalid_png');}
 requireReply(btoa(binary)===encoded);
 const bytes=Uint8Array.from(binary,c=>c.charCodeAt(0));
 requireReply(bytes.length>=57&&bytes.length<=131072&&await sha256(bytes)===depiction.sha256);
 active(signal);
 requireReply([137,80,78,71,13,10,26,10].every((v,i)=>bytes[i]===v));
 const view=new DataView(bytes.buffer),parts:Uint8Array[]=[];
 let offset=8,channels=0,seenHeader=false,seenEnd=false,seenBackground=false;
 while(offset<bytes.length){
  requireReply(offset+12<=bytes.length&&!seenEnd);
  const length=view.getUint32(offset),end=offset+12+length;
  requireReply(end<=bytes.length);
  const name=String.fromCharCode(...bytes.subarray(offset+4,offset+8));
  requireReply(crc32(bytes.subarray(offset+4,end-4))===view.getUint32(end-4));
  if(name==='IHDR'){
   requireReply(!seenHeader&&offset===8&&length===13);
   const width=view.getUint32(offset+8),height=view.getUint32(offset+12),color=bytes[offset+17];
   requireReply(width===depiction.width&&height===depiction.height&&width>=1&&width<=1024&&height>=1&&height<=768);
   requireReply(bytes[offset+16]===8&&(color===2||color===6)&&bytes[offset+18]===0&&bytes[offset+19]===0&&bytes[offset+20]===0);
   channels=color===2?3:4;seenHeader=true;
  }else if(name==='bKGD'){
   requireReply(seenHeader&&!seenBackground&&parts.length===0&&length===6);seenBackground=true;
  }else if(name==='IDAT'){
   requireReply(seenHeader);parts.push(bytes.slice(offset+8,end-4));
  }else if(name==='IEND'){
   requireReply(seenHeader&&parts.length>0&&length===0&&end===bytes.length);seenEnd=true;
  }else{throw Error('unsupported_png_chunk');}
  offset=end;
 }
 requireReply(seenEnd);
 const stride=depiction.width*channels+1,expected=stride*depiction.height;
 const stream=new Blob(parts as BlobPart[]).stream().pipeThrough(new DecompressionStream('deflate')).getReader();
 let count=0;
 try{
  while(true){
   active(signal);
   const {done,value}=await stream.read();if(done)break;
   requireReply(count+value.length<=expected);
   for(let i=(stride-count%stride)%stride;i<value.length;i+=stride)requireReply(value[i]!<=4);
   count+=value.length;
  }
  requireReply(count===expected);active(signal);
 }finally{await stream.cancel().catch(()=>undefined);}
 return 'data:image/png;base64,'+encoded;
}
