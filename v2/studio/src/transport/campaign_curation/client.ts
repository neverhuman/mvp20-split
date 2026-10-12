import { decodeCapability, decodeCuration } from "../../contracts/campaign_curation.js";
import { boundedJSON } from "../bounded_json.js";
import { ScientificReadFailure } from "../scientific/failure.js";
import { bindCapability, bindCuration, validSelection, validCapabilitySelection, type CapabilitySelection, type CurationSelection } from "./identity.js";

const MISSING = Symbol('named_missing_record');

/** Only exact scoped reads; no writes, model calls, credentials or catalog refresh. */
export class CurationClient {
  constructor(private readonly fetcher: typeof fetch = fetch, private readonly timeoutMs = 15_000) {
    if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1) throw Error('invalid_transport_configuration');
  }
  async curation(expected: CurationSelection, signal: AbortSignal) {
    validSelection(expected);
    const value = await this.read('/campaign-curations/' + encodeURIComponent(expected.reference.curation_id),
      'curation_not_recorded', signal);
    if (value === MISSING) return null;
    try { return bindCuration(decodeCuration(value), expected); }
    catch { throw new ScientificReadFailure('invalid_response'); }
  }
  async capability(expected: CapabilitySelection, signal: AbortSignal) {
    validCapabilitySelection(expected);
    const value = await this.read('/capability-requests/' + encodeURIComponent(expected.reference.request_id),
      'capability_request_not_recorded', signal);
    if (value === MISSING) return null;
    try { return bindCapability(decodeCapability(value), expected); }
    catch { throw new ScientificReadFailure('invalid_response'); }
  }
  private async read(path: string, missing: string, signal: AbortSignal): Promise<unknown> {
    const controller = new AbortController();
    let timedOut = false;
    const abort = () => controller.abort();
    signal.addEventListener('abort', abort, { once: true });
    if (signal.aborted) abort();
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, this.timeoutMs);
    try {
      if (controller.signal.aborted) throw new ScientificReadFailure('aborted');
      const response = await this.fetcher.call(globalThis, '/api/planning/v1' + path, { method: 'GET',
        signal: controller.signal, credentials: 'same-origin', redirect: 'error', headers: { Accept: 'application/json' } });
      if (response.status === 401 || response.status === 403) {
        await response.body?.cancel(); throw new ScientificReadFailure('denied');
      }
      if (!response.ok) {
        let reason: unknown;
        try { reason = (await boundedJSON(response, 4096) as { reason_code?: unknown }).reason_code; }
        catch { throw new ScientificReadFailure('unavailable'); }
        if (controller.signal.aborted) throw new ScientificReadFailure('aborted');
        if (response.status === 404 && reason === missing) return MISSING;
        if (response.status === 409) throw new ScientificReadFailure('invalid_response');
        throw new ScientificReadFailure('unavailable');
      }
      let value: unknown;
      try { value = await boundedJSON(response, 1048576); }
      catch { throw new ScientificReadFailure('invalid_response'); }
      if (controller.signal.aborted) throw new ScientificReadFailure('aborted');
      return value;
    } catch (error) {
      if (timedOut) throw new ScientificReadFailure('timeout');
      if (signal.aborted) throw new ScientificReadFailure('aborted');
      if (error instanceof ScientificReadFailure) throw error;
      throw new ScientificReadFailure('network');
    } finally { clearTimeout(timer); signal.removeEventListener('abort', abort); controller.abort(); }
  }
}
