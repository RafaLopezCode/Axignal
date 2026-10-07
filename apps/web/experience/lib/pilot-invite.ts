const key = "axignal_pilot_invite";
const lifetimeMs = 30 * 60 * 1000;
type InviteStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">;
type StorageSource = InviteStorage | (() => InviteStorage);
const resolveStorage = (source: StorageSource): InviteStorage => typeof source === "function" ? source() : source;

// Transient OIDC transport, never entitlement or identity authority.
export function capturePilotInvite(
  location: Pick<Location, "hash" | "pathname" | "search">,
  history: Pick<History, "replaceState">, storage: StorageSource, now = Date.now(),
): boolean {
  const match = /^#pilot=([A-Za-z0-9_-]{20,256})$/.exec(location.hash);
  if (!match) return false;
  history.replaceState(null, "", location.pathname + location.search);
  try { resolveStorage(storage).setItem(key, JSON.stringify({ token: match[1], expiresAt: now + lifetimeMs })); return true; }
  catch { return false; }
}
export function clearPilotInvite(storage: StorageSource): void {
  try { resolveStorage(storage).removeItem(key); } catch { /* Storage failure grants no access. */ }
}
export function pendingPilotInvite(storage: StorageSource, now = Date.now()): string | null {
  try {
    const raw = resolveStorage(storage).getItem(key);
    if (!raw) return null;
    const value: unknown = JSON.parse(raw);
    if (typeof value === "object" && value !== null &&
        "token" in value && typeof value.token === "string" && /^[A-Za-z0-9_-]{20,256}$/.test(value.token) &&
        "expiresAt" in value && typeof value.expiresAt === "number" &&
        value.expiresAt > now && value.expiresAt <= now + lifetimeMs) return value.token;
  } catch { /* Missing or malformed invitation grants no access. */ }
  clearPilotInvite(storage);
  return null;
}
