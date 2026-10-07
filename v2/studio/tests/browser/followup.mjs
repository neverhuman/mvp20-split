import assert from "node:assert/strict";
import { mkdir, writeFile, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import { startSupervisionHost } from "./supervision_host.mjs";
import { fixture, draft } from "../../dist/tests/fixtures/followup.js";
const document = draft(21), criterion = document.unresolved[0].criterion;
document.action = "request_evidence";
document.targets = [{ criterion, improvement: "Resolve the uncertain response", expected_learning: "Learn whether the effect is reproducible under the selected conditions" }];
document.evidence_requests = [{ question: criterion.question, needs: [criterion.need], assessments: [], producer: null, expected_evidence: "A repeat measurement", uncertainty: "Reproducibility remains unknown" }];
const f = fixture(document), records = JSON.parse(await readFile("tests/fixtures/scientific/provenance-question.json", "utf8"));
f.question = { ...records.question, reference: criterion.question, criteria: document.unresolved.map(point => ({ criterion_id: point.criterion.criterion_id, description: "Reproducibility under selected conditions" })) };
f.need = { ...records.need, reference: criterion.need, question: criterion.question, criterion_ids: document.unresolved.map(point => point.criterion.criterion_id) };
f.question.applicability.scope = criterion.question.scope; f.need.required_context.scope = criterion.question.scope;
const output = resolve("../.test-results/studio-followup-browser", new Date().toISOString().replaceAll(/[:.]/g,"-")); await mkdir(output,{recursive:true});
const host = await startSupervisionHost(null, f), browser = await chromium.launch({headless:true});
const evidence = { status: "running", tier: "scripted public HTTP browser", screenshots: [], scenarios: [], limits: ["Actual owner journey and independent Studio replacement remain SQ-01/V1", "Frozen demo assets unchanged"] };
try {
  const context = await browser.newContext({viewport:{width:1440,height:1000}}), page = await context.newPage(), errors = []; page.on("pageerror",error=>errors.push(error.message)); page.setDefaultTimeout(10000);
  await page.goto(host.url); const panel=page.getByRole("region",{name:"Campaign checkpoint inspection"});
  await panel.locator(".supervision-records button").first().click(); await panel.getByRole("button",{name:/Inspect request/}).click(); await panel.getByRole("button",{name:"Responses",exact:true}).click();
  await panel.getByRole("button",{name:"Inspect recorded proposal"}).focus(); await page.keyboard.press("Enter");
  const proposal=page.getByRole("region",{name:"Recorded follow-up proposal"});
  await proposal.getByText("Resolve the uncertain response",{exact:true}).waitFor();
  await proposal.getByText(/Subsequent campaign adoption not verified/).waitFor();
  assert.equal(await proposal.locator(".supervision-records li").count(),20);
  await proposal.getByRole("button",{name:"Next points",exact:true}).click(); assert.equal(await proposal.locator(".supervision-records li").count(),3);
  await proposal.getByRole("button",{name:"Previous points",exact:true}).click();
  await proposal.getByRole("button",{name:"Inspect criterion criterion-0",exact:true}).first().click();
  await proposal.getByText("Exact referenced records verified.",{exact:true}).waitFor();
  for (const width of [1440,390]) {
    await page.setViewportSize({width,height:width===1440?1000:844});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    assert.deepEqual((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations.map(v=>v.id),[]);
    const path=resolve(output,`followup-${width}.png`); await page.screenshot({path,fullPage:true}); evidence.screenshots.push(path);
  }
  await proposal.getByRole("button",{name:"Back to responses"}).click(); assert.equal(await proposal.count(),0);
  host.state.mode="content-denied"; await panel.getByRole("button",{name:"Inspect recorded proposal"}).click(); await proposal.getByText("Proposal content access denied.",{exact:true}).waitFor();
  assert.equal(await proposal.getByText("Resolve the uncertain response",{exact:true}).count(),0);
  host.state.mode="ready"; await proposal.getByRole("button",{name:"Back to responses"}).click();
  let release; host.state.held=new Promise(resolve=>{release=resolve;});
  await panel.getByRole("button",{name:"Inspect recorded proposal"}).click(); await proposal.getByText("Verifying the recorded proposal…",{exact:true}).waitFor();
  await panel.getByRole("button",{name:"Context",exact:true}).click(); release(); host.state.held=null;
  await panel.getByText("Omitted: budget",{exact:true}).waitFor(); assert.equal(await proposal.count(),0);
  assert.deepEqual(errors,[]); assert.ok(host.state.calls.every(call=>!call.ownerAuthorization));
  evidence.scenarios.push("Keyboard proposal selection", "20-row replacement pagination", "Exact criterion owner read", "1440/390 accessibility and overflow", "Content denial clears intent", "Navigation fences delayed reply"); evidence.status="passed";
} finally { await browser.close(); await new Promise(done=>host.server.close(done)); await writeFile(resolve(output,"evidence.json"),JSON.stringify(evidence,null,2)+"\n"); console.log(output); }
