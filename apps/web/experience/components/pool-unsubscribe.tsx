"use client";
import { useState } from "react";

export function PoolUnsubscribe({ token, copy }: { token: string; copy: { button: string; done: string; failed: string } }) {
  const [state, setState] = useState<"idle" | "busy" | "done" | "failed">("idle");
  async function confirm() {
    setState("busy");
    try {
      const response = await fetch("/api/marketing/unsubscribe/" + encodeURIComponent(token), { method: "POST" });
      setState(response.ok ? "done" : "failed");
    } catch { setState("failed"); }
  }
  if (state === "done") return <p role="status" className="pool-reading-done">{copy.done}</p>;
  return <>
    <button type="button" className="button primary" disabled={state === "busy"} onClick={() => void confirm()}>{copy.button}</button>
    {state === "failed" && <p role="alert">{copy.failed}</p>}
  </>;
}
