import type { NextConfig } from "next";
import publicDelivery from "./lib/marketing-delivery.json";
// Baseline CSP in report-only mode: collect browser compatibility evidence before
// enforcing a policy on OAuth, payment or the Next.js hydration runtime.
const cspReportOnly = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
  "script-src 'self' 'unsafe-inline' https:",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: https:",
  "font-src 'self' data:",
  "connect-src 'self' https:",
].join("; ");
const config: NextConfig = {
  async headers() {
    return [
      { source: "/:path*", headers: [{ key: "Content-Security-Policy-Report-Only", value: cspReportOnly }] },
      ...[
        ...publicDelivery.fonts.map(({url}) => url),
        ...Object.values(publicDelivery.images).flatMap(({variants}) => variants.map(({url}) => url)),
      ].map(source => ({source, headers: [{key: "Cache-Control", value: "public, max-age=31536000, immutable"}]})),
    ];
  },
  poweredByHeader: false,
  devIndicators: false,
  agentRules: false,
  async redirects() {
    return [
      // Permanent aliases preserve query parameters (including demo deep links).
      { source: "/panorama", destination: "/demo", permanent: true },
      { source: "/admin/customer-zero", destination: "/admin", permanent: true },
    ];
  },
  logging: { incomingRequests: { ignore: [/^\/api\/auth\/callback\//] } },
  distDir: "node_modules/.cache/axignal-next",
};
export default config;
