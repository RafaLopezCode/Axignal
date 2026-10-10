import type { NextConfig } from "next";
const config: NextConfig = {
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
