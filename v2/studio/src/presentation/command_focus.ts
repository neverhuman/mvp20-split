import { useEffect, useRef } from "react";

/** Announce command settlement without taking focus from edits made while it was pending. */
export function useCommandFocus(phase: string) {
  const status = useRef<HTMLParagraphElement>(null), previous = useRef(phase), trigger = useRef<Element | null>(null);
  useEffect(() => {
    const busy = (value: string) => value === "submitting" || value === "reconciling";
    if (busy(phase) && !busy(previous.current)) trigger.current = document.activeElement;
    if ((!busy(phase) && busy(previous.current)) || (phase === "denied" && previous.current !== "denied")) {
      const active = document.activeElement;
      if (active === document.body || active === trigger.current || active instanceof HTMLButtonElement && active.disabled)
        status.current?.focus({ preventScroll: true });
    }
    previous.current = phase;
  }, [phase]);
  return status;
}
