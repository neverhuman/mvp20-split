import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { startObservationHost } from './host.mjs';

const output = resolve('../.test-results/studio-emergency', new Date().toISOString().replace(/[:.]/g, '-'));
await mkdir(output, { recursive: true });
const host = await startObservationHost(), browser = await chromium.launch({ headless: true });
const evidence = { verified_at: new Intl.DateTimeFormat('sv-SE', { timeZone: 'America/Chicago', dateStyle: 'short', timeStyle: 'medium' }).format(new Date()),
  timezone: 'America/Chicago', status: 'running', scenarios: [], screenshots: [], limits: ['Scripted HTTP peer using actual Studio transport/models/presentation; no owner cancellation-race or target-host acceptance.'] };
try {
  for (const scenario of ['accepted', 'rejected', 'lost-ack', 'socket-loss', 'denied']) {
    let command, posts = 0, lookups = 0; const bodies = [];
    host.state.revision = 1; host.state.mode = 'ready';
    host.state.hook = async (url, json, req) => {
      if (url.pathname.endsWith('/runs/cancel')) {
        posts++;
        let body = ''; for await (const chunk of req) body += chunk;
        bodies.push(body);
        command = JSON.parse(body);
        assert.equal(command.payload.expected_run_revision, 1);
        assert.equal(command.payload.run_id, 'run-1');
        if (scenario === 'lost-ack') { json(503, { detail: 'receipt unavailable after owner commit' }); return true; }
        if (scenario === 'socket-loss') { req.socket.destroy(); return true; }
        if (scenario === 'denied') { json(403, { detail: 'private emergency diagnostics' }); return true; }
        const binding = { identity: command.identity, operation_id: 'stop', request_sha256: 'a'.repeat(64) };
        json(200, { outcome: scenario === 'rejected' ? { binding, status: 'rejected', reason_code: 'run_revision_conflict' }
          : { binding, status: 'accepted', committed: { kind: 'run', object_id: 'run-1', revision: 2 } } }); return true;
      }
      if (url.pathname.includes('/commands/runtime.cancel/')) {
        lookups++; assert.equal(url.pathname.split('/').at(-1), command.identity.command_id);
        json(200, { outcome: { binding: { identity: command.identity, operation_id: 'stop', request_sha256: 'a'.repeat(64) },
          status: 'accepted', committed: { kind: 'run', object_id: 'run-1', revision: 2 } } }); return true;
      }
      return false;
    };
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    const page = await context.newPage(), errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.goto(host.url + '?emergency=1');
    const region = page.getByRole('region', { name: 'Emergency control', exact: true });
    const button = region.getByRole('button', { name: 'Request emergency stop', exact: true });
    await button.waitFor(); await page.waitForFunction(() => window.observationHarness.emergency.snapshot.revision === 1);
    // Historical inspection must not expose a live stop action.
    await page.getByRole('button', { name: 'Pin loaded inspection', exact: true }).click();
    assert.equal(await button.isDisabled(), true);
    await page.getByLabel('Inspect', { exact: true }).selectOption('');
    await page.getByRole('link', { name: 'Emergency control', exact: true }).click();
    await button.focus(); await page.keyboard.press('Enter');
    const recovery = scenario === 'lost-ack' || scenario === 'socket-loss';
    const expected = recovery ? 'unresolved' : scenario;
    await page.waitForFunction(phase => window.observationHarness.emergency.snapshot.phase === phase, expected);
    assert.equal(await button.isDisabled(), true);
    if (recovery) {
      await region.getByText(/Stop outcome unresolved/).waitFor();
      await region.getByRole('button', { name: 'Check original stop receipt', exact: true }).click();
      await page.waitForFunction(() => window.observationHarness.emergency.snapshot.phase === 'accepted');
      assert.equal(lookups, 1);
    }
    if (scenario === 'socket-loss') { assert.ok(posts >= 1); assert.equal(new Set(bodies).size, 1); }
    else assert.equal(posts, 1);
    assert.equal((await region.textContent()).includes('private emergency diagnostics'), false);
    // Receipt acceptance must not rewrite the read model into a fabricated stopped observation.
    assert.equal(await page.evaluate(() => window.observationHarness.model.snapshot.window.snapshot.status), 'running');
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
      await page.setViewportSize(viewport);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      assert.deepEqual(scan.violations.map(item => item.id), []);
      const filename = `${scenario}-${viewport.width}.png`;
      await page.screenshot({ path: resolve(output, filename), fullPage: true }); evidence.screenshots.push(filename);
    }
    assert.deepEqual(errors, []);
    evidence.scenarios.push({ name: scenario, status: 'passed', posts, lookups, distinct_command_bodies: new Set(bodies).size });
    await context.close();
  }
  evidence.status = 'passed';
} catch (error) { evidence.status = 'failed'; evidence.error = String(error); process.exitCode = 1; }
finally {
  await writeFile(resolve(output, 'manifest.json'), JSON.stringify(evidence, null, 2));
  console.log(JSON.stringify({ status: evidence.status, output, error: evidence.error }));
  await browser.close(); await new Promise(resolve => host.server.close(resolve));
}
