import { useCallback, useEffect, useSyncExternalStore } from "react";
import type { CampaignLaunch } from "../../page_models/launch/model.js";
import type { LaunchPreparation } from "../../page_models/launch/preparation.js";
import "./launch.css";

const phases = {
  preparing: "Checking the saved plan, inputs and installed tools",
  admission_unresolved: "Waiting for Runtime to confirm this campaign",
  admitted_not_engaged: "Campaign admitted; preparing its workers",
  engaging: "Starting the campaign’s workers",
  engaged: "Workers engaged; follow actual node progress below",
  draining: "Execution ended; safely releasing workers",
  released: "Campaign released; results remain available",
  rejected: "Launch rejected; the saved draft is unchanged",
  recovery_required: "Launch needs recovery; its original campaign is preserved",
} as const;

export function LaunchPanel({ launch, preparation }: { launch: CampaignLaunch; preparation: LaunchPreparation }) {
  const listen = useCallback((notify: () => void) => launch.subscribe(notify), [launch]);
  const listenPreparation = useCallback((notify: () => void) => preparation.subscribe(notify), [preparation]);
  const view = useSyncExternalStore(listen, () => launch.snapshot);
  const ready = useSyncExternalStore(listenPreparation, () => preparation.snapshot);
  useEffect(() => { if (ready.phase === "idle") void preparation.load(); }, [preparation, ready.phase]);
  const busy = ["submitting", "reconciling"].includes(view.phase);
  const message = view.phase === "storage_failed" ? "The browser recovery record is unavailable. Launch is blocked to protect existing work."
    : view.phase === "denied" ? "Launch access denied. Reopen the workspace session."
    : view.phase === "conflict" ? "This request identity conflicts with an existing launch. It has not been replaced."
    : view.phase === "unresolved" ? view.reason === "busy" ? "Another campaign is still active. This request has not replaced it."
    : "Launch confirmation is unavailable. Keep this request and check again."
    : view.receipt ? phases[view.receipt.phase] : busy ? "Submitting this exact saved campaign…" : "Prepare a new autonomous campaign";
  return <section className="campaign-launch" aria-label="Run campaign">
    <div className="campaign-launch-heading"><div><p className="eyebrow">Campaign control</p><h2>{message}</h2></div>
      {view.receipt && <span className="launch-readiness">{view.receipt.workers.ready} / {view.receipt.workers.expected} workers ready</span>}</div>
    <p role="status">{view.receipt?.run_id ? "Campaign " + view.receipt.run_id : "A new launch gets its own run. Human changes apply to the next campaign."}</p>
    {view.phase === "unresolved" && <div className="toolbar"><button onClick={() => void launch.reconcile()}>Check original launch</button><button onClick={() => void launch.retryOriginal()}>Retry same request</button></div>}
    {launch.canRequest && <div className="launch-preparation">
      <label>Saved campaign<select value={ready.selected ?? ""} disabled={ready.phase !== "ready" || ready.validating}
        onChange={event => { if (event.target.value) void preparation.select(event.target.value); }}>
        <option value="">Choose a saved campaign</option>{ready.drafts?.drafts.map(draft => <option key={draft.draft_id} value={draft.draft_id}>{draft.title} · revision {draft.revision}</option>)}
      </select></label>
      <div className="toolbar"><button disabled={!ready.selected || ready.phase !== "ready"} onClick={() => void preparation.validate(crypto.randomUUID())}>{ready.validating ? "Check pending validation" : "Check saved revision"}</button>
      <button className="launch-primary" disabled={!ready.canRun || busy} onClick={() => void preparation.run(crypto.randomUUID(), launch)}>Run campaign</button>
      <button disabled={ready.phase === "loading" || ready.validating} onClick={() => void preparation.load()}>Refresh choices</button></div>
      <p role="status">{ready.message ?? (ready.phase === "loading" ? "Loading installed tools and saved campaigns…" : !ready.drafts?.drafts.length ? "No prepared campaign is available yet." : "Choose and check a saved revision.")}</p>
      {ready.profiles?.profiles[0] && <p className="launch-profile">Installed tool profile: {ready.profiles.profiles[0].title}. Up to {ready.profiles.profiles[0].maximum_invocations} invocations.</p>}
    </div>}
  </section>;
}
