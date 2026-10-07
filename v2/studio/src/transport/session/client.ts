import { boundedJSON } from '../bounded_json.js';

export interface WorkspaceContext {
  readonly actor_id: string;
  readonly scope: { readonly tenant_id: string; readonly project_id: string };
  readonly run_id: string | null;
  readonly synthetic: boolean;
}
export class SessionFailure extends Error {
  constructor(readonly kind: 'denied' | 'failed') { super(kind); }
}
const identifier = (value: unknown): value is string => typeof value === 'string' && /^[A-Za-z0-9_.-]{1,128}$/.test(value);
export function decodeContext(value: unknown): WorkspaceContext {
  if (typeof value !== 'object' || value === null) throw new SessionFailure('failed');
  const item = value as Record<string, unknown>;
  const scope = item.scope as Record<string, unknown> | null;
  if (Object.keys(item).sort().join(',') !== 'actor_id,run_id,scope,synthetic' || !identifier(item.actor_id) ||
      !scope || typeof scope !== 'object' || Object.keys(scope).sort().join(',') !== 'project_id,tenant_id' ||
      !identifier(scope.tenant_id) || !identifier(scope.project_id) ||
      !(item.run_id === null || identifier(item.run_id)) || typeof item.synthetic !== 'boolean') throw new SessionFailure('failed');
  return Object.freeze({ actor_id: item.actor_id, scope: Object.freeze({ tenant_id: scope.tenant_id, project_id: scope.project_id }),
    run_id: item.run_id, synthetic: item.synthetic });
}
export interface SessionSource { open(ticket?: string): Promise<WorkspaceContext>; }
export class SessionClient implements SessionSource {
  constructor(private readonly fetcher: typeof fetch = fetch) {}
  async open(ticket?: string): Promise<WorkspaceContext> {
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 10_000);
    try {
      const response = await this.fetcher.call(globalThis, '/session', { method: ticket ? 'POST' : 'GET',
        credentials: 'same-origin', redirect: 'error', signal: controller.signal,
        ...(ticket ? { headers: { 'Content-Type':'application/json' }, body: JSON.stringify({ ticket }) } : {}) });
      if (response.status === 401 || response.status === 403) { await response.body?.cancel(); throw new SessionFailure('denied'); }
      if (!response.ok) { await response.body?.cancel(); throw new SessionFailure('failed'); }
      return decodeContext(await boundedJSON(response, 8192));
    } catch (error) { if (error instanceof SessionFailure) throw error; throw new SessionFailure('failed'); }
    finally { clearTimeout(timer); }
  }
}
