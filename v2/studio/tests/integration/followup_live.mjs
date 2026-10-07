/** Actual retained owner records; credentials enter only through controller stdin. */
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import { startSupervisionHost } from "../browser/supervision_host.mjs";
let raw="";for await(const chunk of process.stdin){raw+=chunk;if(Buffer.byteLength(raw)>1048576)throw Error("input_limit");}
const {owners,binding,output}=JSON.parse(raw);raw="";
await mkdir(output,{recursive:true});
const host=await startSupervisionHost({...owners.runtime,binding,peers:{data:owners.data,research:owners.research}});
const browser=await chromium.launch({headless:true});
const evidence={status:"running",tier:"actual isolated owner browser",screenshots:[],scenarios:[],requests:[],limits:["Deterministic proposal; no scientific validity claim","Subsequent adoption is proven separately by controller lineage, not inferred by UI"]};
try {
  const context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),errors=[],authorizations=[];
  page.on("pageerror",error=>errors.push(error.message));page.on("request",request=>{if(request.headers().authorization)authorizations.push(request.url());});page.setDefaultTimeout(15000);
  await page.goto(host.url);const panel=page.getByRole("region",{name:"Campaign checkpoint inspection"});
  await panel.locator(".supervision-records button").first().focus();await page.keyboard.press("Enter");
  await panel.getByRole("button",{name:/Inspect request/}).first().click();await panel.getByRole("button",{name:"Responses",exact:true}).click();
  await panel.getByText("Selected by the committed outcome",{exact:true}).waitFor();
  await panel.getByRole("button",{name:"Inspect recorded proposal"}).click();
  const proposal=page.getByRole("region",{name:"Recorded follow-up proposal"});
  await proposal.getByText("Produce a second bounded observation for comparison.",{exact:true}).waitFor();
  assert.equal(await proposal.getByText("Still unresolved: unknown",{exact:true}).count(),3);
  await proposal.getByRole("button",{name:"Inspect criterion repeatability",exact:true}).first().click();
  await proposal.getByText("Exact referenced records verified.",{exact:true}).waitFor();
  await proposal.getByText("No assessment was selected for this point.",{exact:true}).waitFor();
  for(const width of [1440,390]) {
    await page.setViewportSize({width,height:width===1440?1000:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    assert.deepEqual((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations.map(v=>v.id),[]);
    const path=resolve(output,`actual-followup-${width}.png`);await page.screenshot({path,fullPage:true});evidence.screenshots.push(path);
  }
  await proposal.getByRole("button",{name:"Back to responses"}).click();assert.equal(await proposal.count(),0);
  await panel.getByRole("button",{name:"Refresh checkpoints"}).click();await panel.getByRole("button",{name:"Inspect recorded proposal"}).click();
  await proposal.getByRole("button",{name:"Inspect criterion coverage",exact:true}).click();
  await proposal.getByText("Which observations remain missing?",{exact:true}).waitFor();
  assert.deepEqual(errors,[]);assert.deepEqual(authorizations,[]);
  assert.ok(host.state.calls.filter(call=>call.path.startsWith("/api/research/")).length>=4);
  assert.ok(host.state.calls.filter(call=>"status" in call).every(call=>call.status===200));
  owners.research.token="invalid-acceptance-credential-0000000000000000";
  await proposal.getByRole("button",{name:"Inspect criterion applicability",exact:true}).click();
  await proposal.getByText("Evidence access denied.",{exact:true}).waitFor();
  assert.equal(await proposal.getByText("Which observations remain missing?",{exact:true}).count(),0);
  assert.ok(host.state.calls.some(call=>call.path.startsWith("/api/research/")&&[401,403].includes(call.status)));
  evidence.scenarios.push("Actual Runtime-selected future proposal", "Independent Data metadata/content and hash verification", "Three unresolved points and one intended improvement", "Exact Research criterion records across refresh", "Actual owner credential rejection clears prior evidence", "1440/390 keyboard, accessibility and overflow");evidence.status="passed";
} finally {evidence.requests=host.state.calls;await browser.close();host.server.closeAllConnections();await new Promise(done=>host.server.close(done));await writeFile(resolve(output,"evidence.json"),JSON.stringify(evidence,null,2)+"\n");console.log(output);}
