import { decodeCampaignOrigin, type OriginDraft } from "../../contracts/campaign_origin.js";
import { boundedJSON } from "../bounded_json.js";
import { ScientificReadFailure } from "../scientific/failure.js";
import { verifyOrigin } from "./identity.js";

/** A scoped GET, with no provider key, write method or latest-head fallback. */
export class CampaignOriginClient {
  constructor(private readonly fetcher: typeof fetch = fetch, private readonly timeoutMs = 15_000) {
    if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1) throw Error("invalid_transport_configuration");
  }
  async read(expected: OriginDraft, signal: AbortSignal) {
    if (!/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(expected.draft_id) ||
      !Number.isSafeInteger(expected.revision) || expected.revision < 1 || !/^[0-9a-f]{64}$/.test(expected.content_sha256))
      throw new ScientificReadFailure("invalid_request");
    const controller = new AbortController();
    let timedOut = false;
    const abort = () => controller.abort();
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, this.timeoutMs);
    try {
      if (controller.signal.aborted) throw new ScientificReadFailure("aborted");
      const path = "/api/planning/v1/campaign-origins/" + encodeURIComponent(expected.draft_id) +
        "?revision=" + expected.revision + "&content_sha256=" + expected.content_sha256;
      const response = await this.fetcher.call(globalThis, path, { method: "GET", signal: controller.signal,
        credentials: "same-origin", redirect: "error", headers: { Accept: "application/json" } });
      if (response.status === 401 || response.status === 403) {
        await response.body?.cancel(); throw new ScientificReadFailure("denied");
      }
      if (!response.ok) {
        let reason: unknown;
        try { reason = (await boundedJSON(response, 4096) as { reason_code?: unknown }).reason_code; }
        catch { throw new ScientificReadFailure("unavailable"); }
        if (controller.signal.aborted) throw new ScientificReadFailure("aborted");
        if (response.status === 404 && reason === "campaign_origin_not_recorded") return null;
        if (response.status === 422 && reason === "campaign_origin_response_limit") throw new ScientificReadFailure("limit");
        if (response.status === 409 && reason === "campaign_origin_inconsistent") throw new ScientificReadFailure("invalid_response");
        throw new ScientificReadFailure("unavailable");
      }
      let result;
      try { result = decodeCampaignOrigin(await boundedJSON(response, 262144)); }
      catch { throw new ScientificReadFailure("invalid_response"); }
      await verifyOrigin(result, expected, controller.signal);
      return result;
    } catch (error) {
      if (timedOut) throw new ScientificReadFailure("timeout");
      if (signal.aborted) throw new ScientificReadFailure("aborted");
      if (error instanceof ScientificReadFailure) throw error;
      throw new ScientificReadFailure("network");
    } finally { clearTimeout(timer); signal.removeEventListener("abort", abort); controller.abort(); }
  }
}
