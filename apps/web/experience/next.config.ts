import type { NextConfig } from "next";
const config: NextConfig = {
  poweredByHeader: false,
  devIndicators: false,
  agentRules: false,
  logging: { incomingRequests: { ignore: [/^\/api\/auth\/callback\//] } },
  distDir: "node_modules/.cache/axignal-next",
};
export default config;
