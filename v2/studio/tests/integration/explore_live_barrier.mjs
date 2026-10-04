/** Test-only bounded hold after actual owner bytes arrive; no response fabrication. */
export class ResponseHold {
  constructor() {
    this.entered = new Promise((resolve, reject) => {
      this.enter = value => { clearTimeout(this.entryTimer); resolve(value); };
      this.entryTimer = setTimeout(() => reject(new Error('response_hold_not_entered')), 10000);
    });
    this.released = new Promise(resolve => { this.finish = resolve; });
    this.completed = new Promise(resolve => { this.delivered = resolve; });
    this.releaseTimer = setTimeout(() => this.release(), 35000);
  }
  release() { clearTimeout(this.entryTimer); clearTimeout(this.releaseTimer); this.finish(); }
}
