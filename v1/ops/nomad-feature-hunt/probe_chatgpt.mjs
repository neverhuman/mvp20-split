#!/usr/bin/env node
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

function argument(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
}

const expected = argument('--expected', 'GPT-5.6');
const minimumCapacity = Number(argument('--minimum-capacity', '10'));
const registryPath = process.env.JAILGUN_BROWSER_PROFILE_REGISTRY
  || path.join(os.homedir(), '.jailgun', 'browser-profiles.json');

async function cdpEvaluate(webSocketUrl) {
  const socket = new WebSocket(webSocketUrl);
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('CDP websocket open timeout')), 8000);
    socket.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
    socket.addEventListener('error', () => { clearTimeout(timer); reject(new Error('CDP websocket error')); }, { once: true });
  });
  const expression = `(() => {
    const visible = (element) => {
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
    };
    const texts = [...document.querySelectorAll('button,[role="button"],[aria-label],[data-testid]')]
      .filter(visible)
      .flatMap((element) => [element.innerText, element.getAttribute('aria-label')])
      .filter(Boolean)
      .map((text) => text.trim());
    return { title: document.title, url: location.href, visible_controls: [...new Set(texts)] };
  })()`;
  const id = 1;
  socket.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression, returnByValue: true } }));
  const response = await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('CDP evaluate timeout')), 8000);
    socket.addEventListener('message', (event) => {
      const parsed = JSON.parse(String(event.data));
      if (parsed.id === id) { clearTimeout(timer); resolve(parsed); }
    });
  });
  socket.close();
  if (response.error || response.result?.exceptionDetails) throw new Error('CDP evaluation failed');
  return response.result.result.value;
}

const registry = JSON.parse(await fs.readFile(registryPath, 'utf8'));
const accounts = registry.accounts.filter((account) => account.status === 'ready');
const capacity = accounts.reduce((sum, account) => sum + Math.max(Number(account.max_tabs || 1), 1), 0);
if (capacity < minimumCapacity) throw new Error(`ready account capacity ${capacity} is below ${minimumCapacity}`);

const receipts = [];
for (const account of accounts) {
  const response = await fetch(`http://127.0.0.1:${account.cdp_port}/json/list`);
  if (!response.ok) throw new Error(`cannot query CDP for account ${account.id}`);
  const targets = (await response.json()).filter((target) => target.type === 'page' && target.url.includes('chatgpt.com'));
  if (targets.length === 0) throw new Error(`account ${account.id} has no visible ChatGPT page`);
  const pages = [];
  for (const target of targets) {
    const view = await cdpEvaluate(target.webSocketDebuggerUrl);
    const matches = view.visible_controls.filter((text) => text === expected || text.startsWith(`${expected} `));
    pages.push({ target_id: target.id, title: view.title, url: view.url, visible_model_matches: matches });
  }
  if (!pages.some((page) => page.visible_model_matches.length > 0)) {
    const visibleModels = [...new Set(pages.flatMap((page) => page.visible_controls)
      .filter((text) => /GPT|o[1-9]/i.test(text)))].slice(0, 20);
    throw new Error(`account ${account.id} does not visibly show exact model ${expected}; visible model controls=${JSON.stringify(visibleModels)}`);
  }
  receipts.push({ account_id: account.id, cdp_port: account.cdp_port, max_tabs: account.max_tabs, pages });
}

const conversationIds = receipts.flatMap((receipt) => receipt.pages.map((page) => {
  const match = page.url.match(/chatgpt\.com\/c\/([^/?#]+)/);
  return match ? match[1] : null;
}).filter(Boolean));

process.stdout.write(`${JSON.stringify({
  probed_at: new Date().toISOString(),
  expected_visible_model: expected,
  ready_account_capacity: capacity,
  accounts: receipts,
  conversation_ids: [...new Set(conversationIds)].sort(),
})}\n`);
