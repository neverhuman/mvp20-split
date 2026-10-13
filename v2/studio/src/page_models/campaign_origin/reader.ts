import type { CampaignOrigin, OriginDraft } from "../../contracts/campaign_origin.js";
import type { AuthoringClient } from "../../transport/authoring.js";
import type { CampaignOriginClient } from "../../transport/campaign_origin/client.js";
import { verifyOrigin } from "../../transport/campaign_origin/identity.js";
import { Submission } from "../../transport/submission.js";
import { active } from "../../transport/provenance/integrity.js";
import { canonical, requireReply, same } from "../../transport/scientific/identity.js";
import { immutable } from "../explore/context.js";

/** Independent owner reads bind Planning history to the actual saved Runtime draft. */
export class OriginReader {
  constructor(private readonly planning: Pick<CampaignOriginClient, "read">,
    private readonly runtime: Pick<AuthoringClient, "draft" | "receipt">) {}
  async read(expected: OriginDraft, signal: AbortSignal): Promise<CampaignOrigin | null> {
    return (await this.readBound(expected,signal))?.origin??null;
  }
  async readBound(expected: OriginDraft, signal: AbortSignal) {
    const result = await this.planning.read(expected, signal);
    active(signal);
    if (!result) return null;
    await verifyOrigin(result, expected, signal);
    const draft = await this.runtime.draft(expected.draft_id, expected.revision, signal);
    active(signal);
    requireReply(same(draft.scope, expected.scope) && draft.head.draft_id === expected.draft_id &&
      draft.head.revision === expected.revision && draft.head.content_sha256 === expected.content_sha256 &&
      draft.parent_revision === expected.revision - 1);
    const receipt = result.origin.save.receipt;
    const command = new Submission("save", receipt.outcome.binding.identity, { schema_version: "1",
      draft_id: expected.draft_id, expected_revision: draft.parent_revision, title: draft.head.title, definition: draft.definition });
    const retained = await this.runtime.receipt(command, signal);
    active(signal);
    // Compare the owner's canonical command hash, not a JS re-encoding of scientific numbers.
    requireReply(same(retained, receipt));
    const selected = new Map(result.origin.tools.map(use => [canonical(use.node), use.release.tool]));
    requireReply(selected.size === result.origin.tools.length);
    const pending = [{ path: [] as string[], body: draft.definition.body }];
    let nodes = 0, scopes = 0;
    while (pending.length) {
      const current = pending.pop()!;
      requireReply(++scopes <= 1024 && current.path.length <= 16);
      for (const node of current.body.nodes) {
        requireReply(++nodes <= 4096);
        if (node.kind === "invoke") {
          const key = canonical({ scope_path: current.path, node_id: node.node_id });
          requireReply(selected.has(key) && same(selected.get(key), node.tool)); selected.delete(key);
        }
        if (node.kind === "iterate" || node.kind === "scatter") pending.push({ path: [...current.path, node.node_id], body: node.body });
      }
    }
    requireReply(selected.size === 0);
    return immutable({origin:result,draft});
  }
}
