import type { GraphInvalidationPage } from "../contracts/observations.js";
import { ReadFailure } from "../transport/failure.js";

/** Bounded replay memory; notifications invalidate data and cannot mutate graph state. */
export class EventPosition {
  constructor(readonly revision: number, readonly cursor: string, private readonly recent = new Map<number, string>()) {}

  accept(page: GraphInvalidationPage) {
    let revision = this.revision;
    const recent = new Map(this.recent);
    for (const entry of page.entries) {
      if (entry.revision <= revision) {
        if (recent.get(entry.revision) !== entry.event_id) throw new ReadFailure("resnapshot");
        continue;
      }
      if (entry.revision !== revision + 1 || [...recent.values()].includes(entry.event_id)) throw new ReadFailure("resnapshot");
      revision = entry.revision;
      recent.set(revision, entry.event_id);
      if (recent.size > 100) recent.delete(recent.keys().next().value!);
    }
    if (page.observed_revision < this.revision) {
      if (!page.entries.length) throw new ReadFailure("resnapshot");
      return this; // Verified old duplicates cannot rewind the cursor.
    }
    if (page.has_more && revision === this.revision) throw new ReadFailure("resnapshot");
    if (revision > page.observed_revision || (!page.has_more && revision !== page.observed_revision) ||
        (page.has_more && revision >= page.observed_revision)) throw new ReadFailure("resnapshot");
    return new EventPosition(revision, page.next_cursor, recent);
  }
}
