import type { CurationClient } from '../../transport/campaign_curation/client.js';
import { validSelection, type CurationSelection } from '../../transport/campaign_curation/identity.js';
import { ScientificReadFailure } from '../../transport/scientific/failure.js';
import { immutable } from '../explore/context.js';
import { RequestLane } from '../request_lane.js';
import { RecordedCapability, RecordedCuration, sameValue } from './records.js';

type Phase = 'idle' | 'hidden' | 'loading' | 'ready' | 'missing' | 'denied' | 'stale' | 'failed';
interface Detail { phase: Phase; index: number | null; record: RecordedCapability | null; reason: string | null }
interface State { phase: Phase; record: RecordedCuration | null; reason: string | null; detail: Readonly<Detail> }
const emptyDetail = (): Readonly<Detail> => Object.freeze({ phase: 'idle', index: null, record: null, reason: null });

/** One visible curation owner and one lazy, independently fenced detail lane. */
export class CurationModel {
  private readonly lane = new RequestLane();
  private readonly detailLane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private state: Readonly<State> = Object.freeze({ phase: 'idle', record: null, reason: null, detail: emptyDetail() });
  private selection: CurationSelection | null = null;
  private baseline: RecordedCuration | null = null;
  private readonly capabilityBaselines = new Map<string, RecordedCapability>();
  private bookmark: number | null = null;
  private visible = true;
  private disposed = false;
  constructor(private readonly source: Pick<CurationClient, 'curation' | 'capability'>) {}
  get snapshot() { return this.state; }
  subscribe(listener: () => void) { if (!this.disposed) this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private publish(state: State) {
    if (this.disposed) return;
    this.state = Object.freeze({ ...state, detail: Object.freeze(state.detail) });
    for (const listener of this.listeners) listener();
  }
  private reset(phase: Phase, reason: string | null = null) {
    this.lane.cancel(); this.detailLane.cancel(); this.baseline = null; this.capabilityBaselines.clear();
    this.publish({ phase, reason, record: null, detail: emptyDetail() });
  }
  clear() {
    if (this.disposed) return;
    this.selection = null; this.bookmark = null; this.reset(this.visible ? 'idle' : 'hidden');
  }
  invalidate() { if (!this.disposed) this.reset(this.visible ? 'stale' : 'hidden'); }
  dispose() {
    if (this.disposed) return;
    this.lane.cancel(); this.detailLane.cancel(); this.selection = null; this.baseline = null; this.bookmark = null;
    this.capabilityBaselines.clear();
    this.disposed = true; this.state = Object.freeze({ phase: 'idle', record: null, reason: null, detail: emptyDetail() });
    this.listeners.clear();
  }
  async setVisible(visible: boolean) {
    if (this.disposed || this.visible === visible) return;
    this.visible = visible;
    if (!visible) this.reset('hidden');
    else await this.refresh();
  }
  async select(selection: CurationSelection | null) {
    if (this.disposed) return;
    if (selection === null) { this.clear(); return; }
    try { validSelection(selection); }
    catch { this.selection = null; this.bookmark = null; this.reset('failed', 'invalid_request'); return; }
    if (!sameValue(selection, this.selection)) { this.baseline = null; this.bookmark = null; this.capabilityBaselines.clear(); }
    this.selection = immutable(selection);
    if (!this.visible) { this.reset('hidden'); return; }
    await this.refresh();
  }
  async refresh() {
    if (this.disposed || !this.visible) return;
    if (!this.selection) { this.reset('idle'); return; }
    const selection = this.selection, prior = this.baseline, bookmark = this.bookmark;
    const request = this.lane.begin(); this.detailLane.cancel();
    this.publish({ phase: 'loading', record: null, reason: null, detail: emptyDetail() });
    if (!request.current()) return;
    try {
      const value = await this.source.curation(selection, request.signal);
      if (!request.current()) return;
      if (value === null) { this.baseline = null; this.bookmark = null; this.capabilityBaselines.clear(); this.publish({ phase: 'missing', record: null, reason: null, detail: emptyDetail() }); return; }
      const record = new RecordedCuration(value, selection);
      prior?.reconcile(record); this.baseline = record;
      this.publish({ phase: 'ready', record, reason: null, detail: emptyDetail() });
      if (request.current() && this.state.detail.phase === 'idle' && bookmark !== null &&
        this.bookmark === bookmark && bookmark < record.requests.length)
        await this.inspect(bookmark);
    } catch (error) {
      if (!request.current()) return;
      const reason = failure(error); this.bookmark = null;
      this.reset(reason === 'denied' ? 'denied' : reason === 'aborted' ? 'stale' : 'failed', reason);
    }
  }
  async inspect(index: number) {
    if (this.disposed || !this.visible || this.state.phase !== 'ready' || !this.state.record) return;
    const original = this.state.record;
    let selection;
    try { selection = original.capability(index); } catch { return; }
    const request = this.detailLane.begin(); this.bookmark = index;
    this.publish({ ...this.state, detail: { phase: 'loading', index, record: null, reason: null } });
    if (!request.current()) return;
    try {
      const value = await this.source.capability(selection, request.signal);
      if (!request.current() || this.state.record !== original) return;
      const record = value === null ? null : new RecordedCapability(value, selection);
      if (record) {
        this.capabilityBaselines.get(selection.reference.request_id)?.reconcile(record);
        this.capabilityBaselines.set(selection.reference.request_id, record);
      }
      this.publish({ ...this.state, detail: { phase: record ? 'ready' : 'missing', index, record, reason: null } });
    } catch (error) {
      if (!request.current() || this.state.record !== original) return;
      const reason = failure(error);
      if (reason === 'denied') { this.bookmark = null; this.reset('denied', reason); }
      else this.publish({ ...this.state, detail: { phase: reason === 'aborted' ? 'stale' : 'failed', index, record: null, reason } });
    }
  }
}
function failure(error: unknown) { return error instanceof ScientificReadFailure ? error.kind : 'invalid_response'; }
