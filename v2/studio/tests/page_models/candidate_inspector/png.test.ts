import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {verifiedPNG} from '../../../src/page_models/candidate_inspector/png.js';
import {fixture} from './fixture.js';
const signal=()=>new AbortController().signal;
function picture(){const f=fixture();if(f.result.outcome.status!=='derived')throw Error('fixture');return f.result.outcome.depiction;}
function altered(bytes:Buffer){return {...picture(),png_base64:bytes.toString('base64'),sha256:createHash('sha256').update(bytes).digest('hex')};}
test('actual Cairo PNG passes bounded full stream validation',async()=>{assert.ok((await verifiedPNG(picture(),signal())).startsWith('data:image/png;base64,'));});
test('image digest, dimensions, CRC, trailing data, SVG and truncation are rejected',async()=>{
 const p=picture(),raw=Buffer.from(p.png_base64,'base64'),crc=Buffer.from(raw);crc[29]=crc[29]!^1;
 for(const invalid of [{...p,sha256:'0'.repeat(64)},{...p,width:p.width+1},altered(crc),altered(Buffer.concat([raw,Buffer.from('tail')])),altered(raw.subarray(0,raw.length-12)),altered(Buffer.from('<svg xmlns="http://www.w3.org/2000/svg"/>'))])await assert.rejects(()=>verifiedPNG(invalid,signal()));
});
test('aborted image validation publishes no data URL',async()=>{const controller=new AbortController();controller.abort();await assert.rejects(()=>verifiedPNG(picture(),controller.signal));});
