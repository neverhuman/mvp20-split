import { useState } from "react";
import type { QualityModel } from "../../page_models/quality/model.js";
import type { QualityPoint } from "../../page_models/quality/projection.js";
import type { FocusIntent } from "../../page_models/quality/focus.js";

export function FocusEditor({ model, point, saved, full }: {
  model: QualityModel; point: QualityPoint; saved: FocusIntent | undefined; full: boolean;
}) {
  const [improvement, setImprovement] = useState(saved?.improvement ?? "");
  const [learning, setLearning] = useState(saved?.expectedLearning ?? "");
  const [message, setMessage] = useState("");
  return <form className="quality-focus" aria-label="Next campaign focus" onSubmit={event => {
    event.preventDefault(); model.focusPoint(point.key, improvement, learning); setMessage("Saved in this local draft.");
  }}>
    <h4>Focus for the next campaign</h4>
    <p className="muted">Local draft only. Export it before leaving this view. Saving does not schedule work or change the running campaign.</p>
    <label>Intended improvement<textarea required maxLength={2048} rows={3} value={improvement}
      onChange={event => { setImprovement(event.target.value); setMessage(""); }} /></label>
    <label>What do you expect to learn?<textarea required maxLength={2048} rows={3} value={learning}
      onChange={event => { setLearning(event.target.value); setMessage(""); }} /></label>
    <p className="muted">Describe the expected learning in words; this is not a measured information gain.</p>
    <button type="submit" disabled={!improvement.trim() || !learning.trim() || (full && !saved)}>{saved ? "Update focus" : "Save focus"}</button>
    {saved && <button type="button" onClick={() => { model.unfocus(point.key); setMessage("Removed from the local focus draft."); }}>Remove focus</button>}
    {full && !saved && <p role="status">The local draft holds up to 32 points. Remove a point to add another.</p>}
    <p role="status">{message}</p>
  </form>;
}

export function downloadFocus(model: QualityModel) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(model.exportFocus(), null, 2) + "\n"], { type: "application/json" }));
  const link = document.createElement("a"); link.href = url; link.download = "amphora-next-campaign-focus.json";
  document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
