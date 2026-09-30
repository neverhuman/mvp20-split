import { useCommandFocus } from "./command_focus.js";
import { useCallback, useState, useSyncExternalStore } from "react";
import type { DraftActivation } from "../page_models/design/draft_activation.js";
import type { ActivationParameters } from "../page_models/design/draft_session.js";
import { numericInput, parseDraftJSON } from "../page_models/design/scalar_input.js";

export function DraftActivationControl({ model }: { model: DraftActivation }) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const commandStatus = useCommandFocus(view.phase);
  const [inputs, setInputs] = useState("[]"), [budget, setBudget] = useState("100"), [maximum, setMaximum] = useState("1000"), [deadline, setDeadline] = useState("3600");
  const [error, setError] = useState<string | null>(null);
  const request = () => {
    try {
      const parameters: ActivationParameters = { inputs: parseDraftJSON(inputs) as ActivationParameters["inputs"],
        budget: { limit: numericInput(budget, "integer") },
        limits: { max_activations: numericInput(maximum, "integer"), deadline_seconds: numericInput(deadline, "integer") } };
      void model.request(crypto.randomUUID(), parameters); setError(null);
    } catch { setError("A saved, currently validated draft and valid bounded campaign inputs and limits are required."); }
  };
  return <section aria-label="Next campaign activation" className="emergency-control">
    <h2>Start the next campaign</h2>
    <p>Runtime checks the exact saved revision, current tool eligibility, budget, and whether another campaign is running. Validation alone does not authorize execution or establish scientific applicability.</p>
    <details><summary>Campaign inputs and limits</summary>
      <div className="toolbar">
        <label>Attempt budget<input aria-label="Attempt budget" value={budget} maxLength={32} onChange={event => setBudget(event.target.value)} /></label>
        <label>Maximum activations<input aria-label="Maximum activations" value={maximum} maxLength={32} onChange={event => setMaximum(event.target.value)} /></label>
        <label>Campaign deadline (seconds)<input aria-label="Campaign deadline (seconds)" value={deadline} maxLength={32} onChange={event => setDeadline(event.target.value)} /></label>
      </div>
      <label>Campaign input bindings<textarea aria-label="Campaign input bindings" value={inputs} maxLength={262144} rows={6} onChange={event => setInputs(event.target.value)} /></label>
      <p>Bindings must match the graph's declared inputs. Artifact bindings reference existing scoped artifacts.</p>
    </details>
    <div className="toolbar"><button disabled={!model.canRequest} onClick={request}>Request next campaign</button>
      {model.canResume && <button onClick={() => void model.resume()}>Resume original activation command</button>}
      {view.phase === "unresolved" && !model.session.snapshot.denied && <button onClick={() => void model.reconcile()}>Check original activation receipt</button>}
    </div>
    {error && <p role="alert">{error}</p>}
    <p ref={commandStatus} tabIndex={-1} role="status">{view.phase === "accepted" ? `Campaign admitted: ${view.runId}, from draft revision ${view.draftRevision}. Inspect its execution in Monitor.`
      : view.phase === "rejected" ? `Campaign was not admitted (${view.reason}). Local work is unchanged; no automatic retry was sent.`
      : view.phase === "conflict" ? "Activation command identity conflicted. Its existing receipt cannot confirm this request; no replacement command was sent."
      : view.phase === "denied" ? "Activation access denied. Local work retained; protected projections cleared."
      : view.phase === "unresolved" ? "Activation outcome unresolved. Check the original receipt before making another request."
      : view.phase === "submitting" || view.phase === "reconciling" ? "Checking the original activation command. No admission is confirmed."
      : "Save and validate your draft before requesting activation."}</p>
  </section>;
}
