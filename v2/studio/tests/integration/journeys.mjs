/** Keyboard and viewport assertions shared by the versioned actual-owner scenario pack. */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

export const pack = JSON.parse(await readFile(new URL('./journey_pack.json', import.meta.url), 'utf8'));

export async function keyboardActivate(page, locator) {
  assert.equal(await locator.isEnabled(), true);
  await locator.focus(); await page.keyboard.press('Enter');
}

export async function tabTo(page, start, target, maximum = 24) {
  await start.focus();
  for (let step = 1; step <= maximum; step++) {
    await page.keyboard.press('Tab');
    if (await target.evaluate(element => element === document.activeElement)) return step;
  }
  assert.fail('Essential control was not reachable in the bounded keyboard path');
}

export async function noOverflow(page) {
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
}
