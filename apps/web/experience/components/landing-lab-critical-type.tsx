import "server-only";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import fonts from "@/lib/landing-lab-fonts.json";

const body = fonts.fonts[0];
const bytes = readFileSync(join(process.cwd(), "public", body.url.slice(1)));
const css = `@font-face{font-family:"AXIGNAL Reading";src:url(data:font/woff2;base64,${bytes.toString("base64")}) format("woff2");font-weight:${body.weight};font-display:swap;unicode-range:${body.unicodeRange}}`;

/** Server-only: deliver the small, official reading face with the initial HTML.
 * It cannot enter the client bundle or wait behind navigation code. The remaining
 * faces stay external/cacheable. The existing font CSP already permits data URLs.
 */
export function LandingLabCriticalType() {
  return (
    <style href="axignal-manrope-critical" precedence="axignal-critical-type">
      {css}
    </style>
  );
}
