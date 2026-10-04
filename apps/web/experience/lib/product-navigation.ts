// UI focus history only. It cannot change an economic projection or its time.
export type ProductFocus = {
  view: "panorama" | "today" | "timeline" | "dimension";
  signalId: string | null;
  dimension: "signals" | "capabilities" | "markets" | "activity";
};
export const productHome: ProductFocus = {
  view: "panorama",
  signalId: null,
  dimension: "signals",
};
export type FocusHistory = { trail: ProductFocus[]; cursor: number };
export function focusHistory(
  history: FocusHistory,
  action:
    | { type: "go"; focus: ProductFocus }
    | { type: "back" }
    | { type: "forward" }
    | { type: "home" },
): FocusHistory {
  if (action.type === "back")
    return { ...history, cursor: Math.max(0, history.cursor - 1) };
  if (action.type === "forward")
    return {
      ...history,
      cursor: Math.min(history.trail.length - 1, history.cursor + 1),
    };
  const focus = action.type === "home" ? productHome : action.focus;
  if (JSON.stringify(history.trail[history.cursor]) === JSON.stringify(focus))
    return history;
  return {
    trail: [...history.trail.slice(0, history.cursor + 1), focus],
    cursor: history.cursor + 1,
  };
}
