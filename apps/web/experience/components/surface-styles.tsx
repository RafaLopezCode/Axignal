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
