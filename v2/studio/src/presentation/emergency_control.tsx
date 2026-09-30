import { useCallback, useEffect, useSyncExternalStore } from "react";
import type { GraphSnapshotPage } from "../contracts/observations.js";
import type { EmergencyStop } from "../page_models/design/emergency_stop.js";

export function EmergencyControl({ model, observation, denied = false }: {
  model: EmergencyStop; observation: GraphSnapshotPage["snapshot"] | null; denied?: boolean;
}) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const compatible = !observation || model.matches({ scope: observation.cut.scope, run: observation.cut.run_id });
  useEffect(() => { model.observe(compatible ? observation : null, denied); }, [model, observation, denied, compatible]);
  const canStop = compatible && !denied && !!observation && observation.status === "running" &&
    observation.cut.revision === view.revision && view.phase === "idle";
  return <section id="emergency-control" className="emergency-control" aria-label="Emergency control" tabIndex={-1}>
    <h2>Emergency stop</h2>
    <p>Operational control for the observed run. Draft graphs are unchanged.</p>
    <div className="toolbar">
      <button disabled={!canStop} onClick={() => void model.request(crypto.randomUUID())}>Request emergency stop</button>
      {view.phase === "unresolved" && !denied && <button onClick={() => void model.reconcile()}>Check original stop receipt</button>}
    </div>
    <p role="status">{view.phase === "accepted" ? `Stop accepted at run revision ${view.committedRevision}. Refresh observations to inspect committed history. In-flight external effects may remain uncertain.`
      : view.phase === "conflict" ? "Stop command identity conflicted. Its existing receipt cannot confirm this request. Refresh observations; no replacement stop was sent."
      : view.phase === "rejected" ? `Stop rejected (${view.reason}). Refresh observations before deciding on another operational action.`
      : view.phase === "denied" || denied ? "Emergency control access denied. Protected observations cleared."
      : view.phase === "submitting" || view.phase === "reconciling" ? "Checking the original stop command. Cancellation is not yet confirmed."
      : view.phase === "unresolved" ? "Stop outcome unresolved. Check its original receipt; no second stop has been submitted."
      : canStop ? `Observed run revision ${view.revision}. A stop request does not prove every external effect has stopped.`
      : "A current running observation is required to request a stop."}</p>
  </section>;
}
