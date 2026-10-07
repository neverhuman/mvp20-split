/** Candidate assets in an isolated browser context; every API read uses the live gateway. */
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import assert from 'node:assert/strict';

const input = JSON.parse(await readFile(process.argv[2], 'utf8'));
const assets = resolve(process.argv[3]), output = resolve(process.argv[4]);
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const evidence = { status: 'running', scenarios: [], views: [], errors: [], limits: [
  'Candidate static files intercepted only in this isolated browser; live gateway and owner reads unchanged',
  'No scientific workers, provider calls or campaign writes',
] };
let reviewedPage;
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1100 }, reducedMotion: 'reduce' });
  const page = await context.newPage();
  reviewedPage = page;
  page.on('pageerror', error => evidence.errors.push(error.message));
  const violations = [];
  const fitted = async () => page.waitForFunction(() => {
    const canvas = document.querySelector('.react-flow')?.getBoundingClientRect();
    const nodes = [...document.querySelectorAll('.react-flow__node')];
    return canvas && nodes.length && nodes.every(node => {
      const r = node.getBoundingClientRect();
      return r.width > 0 && r.x >= canvas.x - 1 && r.y >= canvas.y - 1 &&
        r.right <= canvas.right + 1 && r.bottom <= canvas.bottom + 1;
    });
  });
  await page.addInitScript(() => { window.policyViolations = []; document.addEventListener('securitypolicyviolation', e => window.policyViolations.push(e.violatedDirective)); });
  for (const name of ['app.js', 'app.css']) await page.route(input.origin + '/' + name, async route =>
    route.fulfill({ body: await readFile(resolve(assets, name)), contentType: name.endsWith('js') ? 'application/javascript' : 'text/css' }));
  const issued = await context.request.post(input.origin + '/launcher/ticket', { headers: { Authorization: 'Bearer ' + process.env.AMPHORA_BROWSER_LAUNCH_KEY } });
  assert.equal(issued.status(), 200);
  const { ticket } = await issued.json();
  await page.goto(input.origin + '/#view=execution&launch=' + encodeURIComponent(ticket));
  await page.getByRole('heading', { name: 'Follow execution', exact: true }).waitFor();
  // A vertical SVG path has zero bounding-box width, despite its visible stroke.
  // Check attachment here; painted stroke, length, fit and screenshots below own visibility.
  await page.locator('.react-flow__edge-path').first().waitFor({ state: 'attached' });
  await page.waitForFunction(() => document.querySelectorAll('.react-flow__node').length === 9);
  await fitted();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: width === 1440 ? 1100 : 844 });
    await page.getByRole('button', { name: 'Fit graph', exact: true }).click();
    await page.waitForTimeout(250);
    const geometry = await page.evaluate(() => {
      const canvas = document.querySelector('.graph-region').getBoundingClientRect();
      const rect = r => ({ x: r.x, y: r.y, width: r.width, height: r.height });
      return { canvas: rect(canvas), nodes: [...document.querySelectorAll('.react-flow__node')].map(n => ({
        id: n.dataset.id, label: n.textContent, ...rect(n.getBoundingClientRect()) })),
        paths: [...document.querySelectorAll('.react-flow__edge-path')].map(e => ({ d: e.getAttribute('d'), length: e.getTotalLength(), stroke: getComputedStyle(e).stroke })),
        overflow: document.documentElement.scrollWidth > innerWidth };
    });
    assert.equal(geometry.overflow, false);
    assert.ok(geometry.paths.length > 0 && geometry.paths.every(p => p.length > 0 && p.d));
    for (const n of geometry.nodes) {
      assert.ok(n.x >= geometry.canvas.x - 1 && n.y >= geometry.canvas.y - 1);
      assert.ok(n.x + n.width <= geometry.canvas.x + geometry.canvas.width + 1);
      assert.ok(n.y + n.height <= geometry.canvas.y + geometry.canvas.height + 1);
    }
    for (const a of geometry.nodes) for (const b of geometry.nodes) if (a.id !== b.id)
      assert.ok(a.x + a.width <= b.x || b.x + b.width <= a.x || a.y + a.height <= b.y || b.y + b.height <= a.y);
    violations.push(...(await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations.map(v => v.id));
    await page.screenshot({ path: resolve(output, `root-${width}.png`), fullPage: true });
    evidence.views.push({ width, ...geometry });
  }
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.getByRole('button', { name: 'Fit graph', exact: true }).click();
  await page.locator('.react-flow__node[aria-label="seed, succeeded"]').click();
  await page.waitForFunction(() => [...document.querySelectorAll('.react-flow__edge-path')].some(e => getComputedStyle(e).strokeWidth === '3px'));
  await page.getByRole('button', { name: 'Pan right', exact: true }).click();
  await page.waitForTimeout(100);
  const transform = await page.locator('.react-flow__viewport').getAttribute('style');
  await page.getByRole('button', { name: 'Refresh observation', exact: true }).click();
  await page.waitForFunction(() => document.querySelectorAll('.react-flow__node').length === 9);
  await page.waitForTimeout(200);
  assert.equal(await page.locator('.react-flow__viewport').getAttribute('style'), transform);
  await page.getByRole('button', { name: /Open \d+ child groups of evaluate_batch/ }).click();
  await page.getByRole('list', { name: 'Occurrence groups', exact: true }).getByRole('button').first().click();
  await page.waitForFunction(() => document.querySelectorAll('.react-flow__node').length > 0 && document.querySelectorAll('.react-flow__node').length < 9);
  await fitted();
  await page.screenshot({ path: resolve(output, 'parallel-group.png'), fullPage: true });
  await page.getByRole('button', { name: 'Return to root graph', exact: true }).click();
  await page.waitForFunction(() => document.querySelectorAll('.react-flow__node').length === 9);
  await page.getByRole('button', { name: /Open \d+ child groups of generations/ }).click();
  await page.getByRole('list', { name: 'Occurrence groups', exact: true }).getByRole('button').first().click();
  await page.locator('.react-flow__edge-path').first().waitFor({ state: 'attached' });
  await fitted();
  await page.screenshot({ path: resolve(output, 'iteration.png'), fullPage: true });
  evidence.scenarios.push('Selected incident edges emphasized', 'Viewport retained across actual refresh', 'Parallel group and iteration drilldown with root return');
  await page.getByRole('button', { name: 'Activation inventory', exact: true }).click();
  assert.equal(await page.locator('.react-flow').count(), 0);
  await page.getByRole('list', { name: 'Loaded activation list' }).getByRole('button').first().click();
  evidence.scenarios.push('Connected root loads without graph-selection clicks', 'Routed visible edges and nonoverlapping nodes', 'Initial/explicit fit at1440/390', 'Inventory is a secondary list');
  evidence.csp_violations = await page.evaluate(() => window.policyViolations);
  assert.deepEqual(evidence.csp_violations, []);
  assert.deepEqual(violations, []);
  assert.deepEqual(evidence.errors, []);
  evidence.status = 'passed';
} finally {
  if (evidence.status !== 'passed' && reviewedPage) {
    evidence.failureText = await reviewedPage.locator('body').innerText();
    await reviewedPage.screenshot({ path:resolve(output,'failure.png'),fullPage:true });
  }
  if (reviewedPage) await reviewedPage.evaluate(() => fetch('/session/logout', { method:'POST' })).catch(() => {});
  await writeFile(resolve(output, 'evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
  await browser.close();
}
console.log('Actual-owner graph review passed: ' + output);
