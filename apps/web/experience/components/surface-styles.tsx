"use client";
import { usePathname } from "next/navigation";
import styles from "@/lib/surface-styles.json";
import { isLandingLabPath } from "@/lib/surface-style-path";

export function SurfaceStyles() {
  const lab = isLandingLabPath(usePathname());
  return (
    <>
      <link
        rel="stylesheet"
        href={styles.base.url}
        precedence="axignal-base"
        data-axignal-style="base"
      />
      {/* Reserve the legacy group before page CSS even when entering via the lab.
          Otherwise its first client navigation would append the global skin after
          route overrides, making appearance depend on navigation history. */}
      <style href="axignal-legacy-order" precedence="axignal-legacy">
        {":root{}"}
      </style>
      {!lab && (
        <link
          rel="stylesheet"
          href={styles.legacy.url}
          precedence="axignal-legacy"
          data-axignal-style="legacy"
        />
      )}
    </>
  );
}
