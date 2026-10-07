import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { build } from "esbuild";
import { allowedRoute } from "../../dist/src/transport/scientific/routes.js";
export async function startSupervisionHost(actual = null, followup = null) {
  await build({ entryPoints: ["tests/browser/supervision_entry.tsx"], bundle: true, outdir: "dist/supervision-browser", format: "esm", jsx: "automatic" });
  const fixtures = Object.fromEntries(await Promise.all(["checkpoints","requests","context","responses"].map(async k => [k,JSON.parse(await readFile(`tests/fixtures/supervision/${k}.json`,"utf8"))])));
  const state = { mode: "ready", calls: [], held: null };
  if (followup) fixtures.responses.items = [followup.selection.response];
  const server = createServer(async (req,res) => {
    const url = new URL(req.url,"http://local"), path=url.pathname;
    const reply = (code,value) => { res.writeHead(code,{"content-type":"application/json","cache-control":"no-store"});res.end(JSON.stringify(value)); };
    try {
      if(path==="/binding") { reply(200,{synthetic:!actual,binding:actual?.binding ?? {run:fixtures.checkpoints.snapshot.cut.run_id,scope:fixtures.checkpoints.snapshot.cut.scope}});return; }
      if (actual?.peers && (path.startsWith("/api/data/") || path.startsWith("/api/research/"))) {
        if (url.search || req.headers.authorization || !allowedRoute(req.method,path)) { reply(403,{}); return; }
        const name=path.split("/")[2], peer=actual.peers[name], origin=new URL(peer.endpoint);
        if(origin.protocol!=="http:" || origin.hostname!=="127.0.0.1" || origin.pathname!=="/") throw Error("owner_origin");
        const chunks=[];let size=0;
        for await(const chunk of req) {size+=chunk.length;if(size>262144)throw Error("input_limit");chunks.push(chunk);}
        const upstream=await fetch(peer.endpoint+req.url.slice(("/api/"+name).length),{method:req.method,redirect:"error",
          headers:{Authorization:"Bearer "+peer.token,"Content-Type":"application/json"},
          ...(req.method==="POST"?{body:Buffer.concat(chunks)}:{}),signal:AbortSignal.timeout(15000)});
        const parts=[];size=0;
        for await(const chunk of upstream.body) {size+=chunk.length;if(size>4194304)throw Error("output_limit");parts.push(chunk);}
        state.calls.push({path,method:req.method,ownerAuthorization:false,status:upstream.status});
        res.writeHead(upstream.status,{"content-type":upstream.headers.get("content-type")??"application/json","cache-control":"no-store"});res.end(Buffer.concat(parts));return;
      }
      if (followup && (path.startsWith("/api/data/") || path.startsWith("/api/research/"))) {
        state.calls.push({path,method:req.method,ownerAuthorization:!!req.headers.authorization});
        if (state.mode === "content-denied") { reply(403,{}); return; }
        if (path.endsWith("/content")) { reply(200, followup.document); return; }
        if (path.startsWith("/api/data/")) { reply(200,followup.record.capture); return; }
        if (path.endsWith("/questions/read")) { reply(200,followup.question); return; }
        if (path.endsWith("/evidence-needs/read")) { reply(200,followup.need); return; }
        reply(404,{}); return;
      }
      if(path.startsWith("/api/runtime/v1/supervision/")) {
        state.calls.push({path,method:req.method,ownerAuthorization:!!req.headers.authorization});
        if(req.method!=="GET") {reply(405,{});return;}
        if(actual) {
          const response=await fetch(actual.endpoint+req.url.slice("/api/runtime".length),{headers:{Authorization:"Bearer "+actual.token},redirect:"error"});
          const bytes=await response.arrayBuffer();if(bytes.byteLength>262144)throw new Error("limit");
          res.writeHead(response.status,{"content-type":"application/json","cache-control":"no-store"});res.end(Buffer.from(bytes));return;
        }
        if(state.held) await state.held;
        if(state.mode==="denied") {reply(403,{});return;}
        if(state.mode==="stale") {reply(409,{});return;}
        if(state.mode==="failed") {reply(503,{});return;}
        if (followup && path === "/api/runtime/v1/supervision/responses/" + followup.record.response_id) { reply(200,followup.record); return; }
        if(path.includes("/decisions/")) {
          if(state.mode==="partial") {reply(404,{});return;}
          reply(200,{schema_version:"1",profile:"checkpoint-decision.v1",reference:fixtures.requests.reference,revision:1,checkpoint_seed_sha256:"a".repeat(64),outcome:{kind:"fallback",action:"continue_unchanged",reason_code:"checkpoint_provider_unconfigured"}});return;
        }
        const kind=path.split("/").at(-1);if(!fixtures[kind]) {reply(404,{});return;}
        const page=structuredClone(fixtures[kind]);
        if(state.mode==="empty") {page.total=0;page.items=[];page.next_cursor=null;}
        if(state.mode==="paged" && kind==="checkpoints") {
          page.total=11;page.items=Array.from({length:url.searchParams.has("cursor")?1:10},(_,i)=>({...page.items[0],checkpoint_id:"checkpoint-"+(url.searchParams.has("cursor")?11:i+1),reference:{...page.items[0].reference,decision_id:"decision-"+(i+1)}}));
          page.next_cursor=url.searchParams.has("cursor")?null:"next-page";
        }
        reply(200,page);return;
      }
      if(path==="/") {res.setHeader("content-type","text/html");res.end('<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Checkpoint inspection</title><link rel="stylesheet" href="/supervision_entry.css"></head><body><div id="root"></div><script type="module" src="/supervision_entry.js"></script></body></html>');return;}
      if(!["/supervision_entry.js","/supervision_entry.css"].includes(path)) {reply(404,{});return;}
      res.setHeader("content-type",path.endsWith("css")?"text/css":"text/javascript");res.end(await readFile(resolve("dist/supervision-browser",path.slice(1))));
    } catch {if(!res.headersSent)res.writeHead(500);res.end();}
  });
  await new Promise(done=>server.listen(0,"127.0.0.1",done));
  return {state,server,url:`http://127.0.0.1:${server.address().port}`};
}
