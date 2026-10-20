import "server-only";
import { firstReadingScript } from "@/lib/landing-first-reading";
import fonts from "@/lib/landing-lab-fonts.json";

const body = fonts.fonts[0];
const css = `@font-face{font-family:"AXIGNAL Reading";src:url(${body.url}) format("woff2");font-weight:${body.weight};font-display:swap;unicode-range:${body.unicodeRange}}:root[data-lab-first-reading] .landing-lab .lab-hand{font-family:"AXIGNAL Reading",Manrope,Arial,sans-serif}`;

/** Server-only: declare the small, official reading face in the initial HTML.
 * Only the declaration enters HTML; the official bytes remain cacheable and are
 * preloaded by the lab. This avoids duplicating base64 font bytes in the Flight payload.
 */
export function LandingLabCriticalType() {
  return (
    <>
      <script dangerouslySetInnerHTML={{ __html: firstReadingScript }} />
      <style href="axignal-manrope-critical" precedence="axignal-critical-type">
        {css}
      </style>
    </>
  );
}
