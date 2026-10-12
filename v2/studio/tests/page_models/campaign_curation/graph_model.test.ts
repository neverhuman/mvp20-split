import test from 'node:test';
import assert from 'node:assert/strict';
import {CurationGraphModel} from '../../../src/page_models/campaign_curation/graph_model.js';
import {CurationGraphReview} from '../../../src/page_models/campaign_curation/graph_review.js';
import {graphFixture} from './graph_fixture.js';

test('replacement denial fences an older graph response',async()=>{
  const f=graphFixture(),review=new CurationGraphReview(f.record,f.original,f.saved,f.validation);
  let resolve!:(value:CurationGraphReview)=>void,calls=0;
  const model=new CurationGraphModel({read:async()=>{if(calls++)throw {kind:'denied'};return new Promise(done=>{resolve=done;});}});
  const old=model.load(f.record);await model.load(f.record);
  assert.equal(model.snapshot.phase,'denied');resolve(review);await old;
  assert.equal(model.snapshot.phase,'denied');assert.equal(model.snapshot.review,null);
});

test('subscriber clearing a loading graph prevents its source call',async()=>{
  const f=graphFixture();let calls=0;
  const model=new CurationGraphModel({read:async()=>{calls++;return null;}});
  model.subscribe(()=>{if(model.snapshot.phase==='loading')model.clear();});
  await model.load(f.record);assert.equal(calls,0);assert.equal(model.snapshot.phase,'idle');
});

test('disposal clears a loaded domain review and rejects further reads',async()=>{
  const f=graphFixture(),review=new CurationGraphReview(f.record,f.original,f.saved,f.validation);let calls=0;
  const model=new CurationGraphModel({read:async()=>{calls++;return review;}});
  await model.load(f.record);assert.equal(model.snapshot.review,review);
  model.dispose();await model.load(f.record);assert.equal(calls,1);assert.equal(model.snapshot.review,null);
});
