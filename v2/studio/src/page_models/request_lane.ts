/** One request owner per region; cancellation plus generation checks handle uncancellable peers. */
export class RequestLane {
  private generation = 0;
  private controller: AbortController | undefined;

  begin() {
    this.cancel();
    const controller = this.controller = new AbortController();
    const generation = this.generation;
    return { signal: controller.signal, current: () => this.generation === generation && !controller.signal.aborted };
  }
  cancel() { this.controller?.abort(); this.controller = undefined; this.generation++; }
}
