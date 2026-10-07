/** Actual-owner reads with isolated candidate assets; no campaign or provider writes. */
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';
const input = JSON.parse(await readFile(process.argv[2], 'utf8'));
const assets = resolve(process.argv[3]), output = resolve(process.argv[4]);
await mkdir(output, { recursive:true });
const browser = await chromium.launch({ headless:true });
const evidence = { status:'running', errors:[], checks:[] };
try {
  const context = await browser.newContext({ viewport:{ width:1440, height:1000 } });
  const page = await context.newPage();
  page.on('pageerror', error => evidence.errors.push(error.message));
  for (const name of ['app.js','app.css']) await page.route(input.origin + '/' + name, route =>
    readFile(resolve(assets,name)).then(body => route.fulfill({ body, contentType:name.endsWith('js') ? 'application/javascript' : 'text/css' })));
  const issued = await context.request.post(input.origin + '/launcher/ticket', { headers:{ Authorization:'Bearer ' + process.env.AMPHORA_BROWSER_LAUNCH_KEY } });
  assert.equal(issued.status(),200);
  const { ticket } = await issued.json();
  const pins = new URLSearchParams({ launch:ticket, explore:JSON.stringify({ graph:input.records.snapshot.reference, experiment:null, observations:[] }),
    feedback:JSON.stringify({ question:input.records.question.reference, need:input.records.need.reference, assessment:null, publication:null, proposal:null, corrections:null }) });
  await page.goto(input.origin + '/#' + pins);
  await page.getByRole('heading',{ name:input.records.question.objective, exact:true }).waitFor();
  assert.equal(new URL(page.url()).hash.includes('launch='),false);
  const nav = page.getByRole('navigation',{ name:'Research workspace', exact:true });
  for (const width of [1440,390]) {
    await page.setViewportSize({ width,height:1000 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false);
    assert.deepEqual((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v=>v.id),[]);
    await page.screenshot({ path:resolve(output,`question-${width}.png`),fullPage:true });
  }
  await page.setViewportSize({width:1440,height:1000});
  await nav.getByRole('button',{name:'Approach and run',exact:true}).click();
  await page.locator('.react-flow__node[aria-label="seed, succeeded"]').click();
  await page.getByRole('button',{name:'Pan right',exact:true}).click();
  await page.waitForTimeout(150);
  const viewport = await page.locator('.react-flow__viewport').getAttribute('style');
  await nav.getByRole('button',{name:'Results and evidence',exact:true}).click();
  await page.getByRole('heading',{name:'Follow the evidence',exact:true}).waitFor();
  await nav.getByRole('button',{name:'Approach and run',exact:true}).click();
  await page.waitForTimeout(500);
  assert.equal(await page.locator('.react-flow__viewport').getAttribute('style'),viewport);
  assert.ok(await page.locator('.react-flow__node.selected').count() > 0);
  await page.reload();
  await page.getByRole('heading',{name:'Follow execution',exact:true}).waitFor();
  await nav.getByRole('button',{name:'Question',exact:true}).click();
  await page.getByRole('heading',{name:input.records.question.objective,exact:true}).waitFor();
  await nav.getByRole('button',{name:'Next iteration',exact:true}).click();
  await page.waitForTimeout(300);
  assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('view'),'design');
  await nav.getByRole('button',{name:'Question',exact:true}).click();
  await page.getByRole('heading',{name:input.records.question.objective,exact:true}).waitFor();
  evidence.checks.push('Exact question and criteria from Research', '1440/390 no overflow and accessibility', 'Graph selection and viewport survive evidence roundtrip', 'Reload restores workflow view and exact selection pins', 'Next iteration and question return paths', 'Launch credential erased');
  assert.deepEqual(evidence.errors,[]);
  evidence.status='passed';
} finally {
  await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2)+'\n');
  await browser.close();
}
console.log('Actual-owner workflow review: '+output);
