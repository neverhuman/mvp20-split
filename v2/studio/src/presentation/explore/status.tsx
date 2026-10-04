import type { RegionState } from "../../page_models/explore/projection.js";
export function RegionStatus({ region, label }: { region: RegionState<unknown>; label: string }) {
  if (region.phase === "ready" || region.phase === "idle") return null;
  const message = region.phase === "loading" ? `Loading ${label}...` : region.phase === "empty" ? `No ${label} in this selection.` :
    region.phase === "partial" ? `Showing a bounded portion of ${label}. More context remains outside this view.` :
    region.phase === "denied" ? "Access denied. Loaded evidence has been cleared." : region.phase === "stale" ? "This view needs a fresh read." :
    region.error?.message ?? "This selection is unavailable.";
  return <p className="explore-status" role="status">{message}</p>;
}
