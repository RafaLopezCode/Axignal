/** Read only the owning channel's explicit availability. Failure is unknown, not paused. */
export async function readWeeklyBriefAvailability(
  signal: AbortSignal,
): Promise<boolean | null> {
  try {
    const response = await fetch("/api/weekly-brief/status", {
      cache: "no-store",
      signal,
    });
    if (!response.ok) return null;
    const data: unknown = await response.json();
    return typeof data === "object" &&
      data !== null &&
      "enabled" in data &&
      typeof data.enabled === "boolean"
      ? data.enabled
      : null;
  } catch {
    return null;
  }
}
