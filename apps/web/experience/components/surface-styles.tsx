"use client";
import { usePathname } from "next/navigation";
import styles from "@/lib/surface-styles.json";
import { isLandingLabPath } from "@/lib/surface-style-path";

export function SurfaceStyles() {
  const lab = isLandingLabPath(usePathname());
  return (
    <>
      {/* Reserve every group in a stable order on both initial and client navigation.
          React retains precedence resources; arrival order must not change the skin. */}
      <style href="axignal-base-order" precedence="axignal-base">
        {":root{}"}
      </style>
      {!lab && (
        <link
          rel="stylesheet"
          href={styles.base.url}
          precedence="axignal-base"
          data-axignal-style="base"
        />
      )}
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
      <style href="axignal-lab-order" precedence="axignal-lab">
        {":root{}"}
      </style>
      {lab && (
        <link
          rel="stylesheet"
          href={styles.lab.url}
          precedence="axignal-lab"
          data-axignal-style="lab"
        />
      )}
    </>
  );
}
