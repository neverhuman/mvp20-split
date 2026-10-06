import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import { startSupervisionHost } from "./supervision_host.mjs";
const output=resolve("../.test-results/studio-supervision-browser",new Date().toISOString().replaceAll(/[:.]/g,"-"));await mkdir(output,{recursive:true});
const actual=process.env.SUPERVISION_BROWSER_ENDPOINT ? {endpoint:process.env.SUPERVISION_BROWSER_ENDPOINT,token:process.env.SUPERVISION_BROWSER_TOKEN,binding:JSON.parse(process.env.SUPERVISION_BROWSER_BINDING)}:null;
const host=await startSupervisionHost(actual),browser=await chromium.launch({headless:true});
const evidence={status:"running",tier:actual?"installed-owner browser":"scripted public HTTP browser",scenarios:[],screenshots:[],limits:["No live-model efficacy, production gateway or scientific validity claim"]};
const errors=[];
try {
  const browserContext=await browser.newContext({viewport:{width:1440,height:1000}});const page=await browserContext.newPage();page.setDefaultTimeout(10000);page.on("pageerror",error=>errors.push(error.message));
  await page.goto(host.url);const panel=page.getByRole("region",{name:"Campaign checkpoint inspection"});
  await panel.locator(".supervision-records button").first().focus();await page.keyboard.press("Enter");
  await panel.getByRole("button",{name:/Inspect request/}).first().click();
  await panel.getByRole("button",{name:"Responses",exact:true}).click();
  await panel.locator(".supervision-records li").first().waitFor();
  evidence.scenarios.push("keyboard checkpoint selection -> original request -> response versus committed outcome");
  for(const width of [1440,390]) {
    await page.setViewportSize({width,height:width===1440?1000:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    const axe=await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze();assert.deepEqual(axe.violations.map(v=>v.id),[]);
    const screenshot=resolve(output,`responses-${width}.png`);await page.screenshot({path:screenshot,fullPage:true});evidence.screenshots.push(screenshot);
  }
  await panel.getByRole("button",{name:"Refresh checkpoints"}).click();await panel.locator(".supervision-records li").first().waitFor();
  assert.equal(await panel.getByRole("button",{name:"Responses",exact:true}).getAttribute("aria-pressed"),"true");
  await panel.getByRole("button",{name:"Context",exact:true}).click();await panel.locator(".supervision-records li").first().waitFor();
  if(!actual) {
    await panel.getByText("Omitted: budget",{exact:true}).waitFor();evidence.scenarios.push("included versus budget-omitted metadata; selection survives refresh");
    host.state.mode="partial";await panel.getByRole("button",{name:"Refresh checkpoints"}).click();await panel.getByText(/Not observed here; the evidence view is partial/).waitFor();
    for(const [mode,text] of [["stale","Checkpoint evidence changed."],["denied","Checkpoint access denied."],["failed","Checkpoint evidence could not be loaded."],["empty","No retained records in this view."]]) {
      host.state.mode=mode;await panel.getByRole("button",{name:"Refresh checkpoints"}).click();await panel.getByRole("status").filter({hasText:text}).waitFor();
    }
    host.state.mode="ready";let release;host.state.held=new Promise(r=>{release=r;});
    await panel.getByRole("button",{name:"Refresh checkpoints"}).click();await panel.getByText("Loading checkpoint evidence...",{exact:true}).waitFor();release();host.state.held=null;
    await panel.locator(".supervision-records button").first().waitFor();
    host.state.mode="paged";await panel.getByRole("button",{name:"Refresh checkpoints"}).click();await panel.getByText("Showing 10 of 11 checkpoints.",{exact:true}).waitFor();
    await panel.getByRole("button",{name:"Next checkpoints"}).click();await panel.getByRole("button",{name:"checkpoint-11",exact:true}).waitFor();
    assert.equal(await panel.locator(".supervision-records li").count(),1);
    evidence.scenarios.push("partial, stale, denied, failed, empty, loading and bounded replacement pagination");
  }
  assert.deepEqual(errors,[]);assert.ok(host.state.calls.every(call=>call.method==="GET"&&!call.ownerAuthorization));
  evidence.status="passed";evidence.calls=host.state.calls.length;
} finally {await browser.close();await new Promise(done=>host.server.close(done));await writeFile(resolve(output,"evidence.json"),JSON.stringify(evidence,null,2)+"\n");console.log(output);}
