import { ReadFailure } from "./failure.js";

export async function boundedJSON(response: Response, maximum: number): Promise<unknown> {
  if (response.headers.get("content-type")?.split(";")[0]?.trim().toLowerCase() !== "application/json") throw new ReadFailure("invalid_response");
  const declared = response.headers.get("content-length");
  if (declared !== null && Number(declared) > maximum) throw new ReadFailure("invalid_response");
  if (!response.body) throw new ReadFailure("invalid_response");
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let text = "", bytes = 0;
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      bytes += chunk.value.byteLength;
      if (bytes > maximum) throw new ReadFailure("invalid_response");
      try { text += decoder.decode(chunk.value, { stream: true }); }
      catch { throw new ReadFailure("invalid_response"); }
    }
    try { return JSON.parse(text + decoder.decode()) as unknown; }
    catch { throw new ReadFailure("invalid_response"); }
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}
