import { ScientificReadFailure } from "./failure.js";

export async function boundedBytes(response: Response, expectedSize: number, expectedMedia: string): Promise<Uint8Array<ArrayBuffer>> {
  const media = response.headers.get("content-type")?.split(";")[0]?.trim().toLowerCase();
  if (media !== expectedMedia.toLowerCase()) throw new ScientificReadFailure("invalid_response");
  const declared = response.headers.get("content-length");
  if (declared !== null && (!/^\d+$/.test(declared) || Number(declared) !== expectedSize)) throw new ScientificReadFailure("invalid_response");
  if (!response.body) {
    if (expectedSize === 0) return new Uint8Array(0);
    throw new ScientificReadFailure("invalid_response");
  }
  const reader = response.body.getReader(), chunks: Uint8Array[] = [];
  let count = 0;
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      count += chunk.value.byteLength;
      if (count > expectedSize || count > 4194304) throw new ScientificReadFailure("invalid_response");
      chunks.push(chunk.value);
    }
    if (count !== expectedSize) throw new ScientificReadFailure("invalid_response");
    const result = new Uint8Array(count);
    let offset = 0;
    for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.byteLength; }
    return result;
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}
