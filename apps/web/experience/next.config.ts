import type { NextConfig } from "next";
const config: NextConfig = {
  poweredByHeader: false,
  devIndicators: false,
  agentRules: false,
  distDir: "node_modules/.cache/axignal-next",
};
export default config;
