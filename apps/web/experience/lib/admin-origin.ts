/** Admin writes also run through the documented authenticated loopback SSH tunnel. */
export function adminOriginAllowed(request: Request, configured?: string): boolean {
  const origin = request.headers.get("origin");
  const allowed = [
    ...(configured ? [configured] : ["http://127.0.0.1:3810", "http://localhost:3810"]),
    "http://127.0.0.1:18182", "http://localhost:18182",
  ];
  try {
    return !!origin && allowed.includes(origin) && new URL(origin).host === request.headers.get("host");
  } catch { return false; }
}
