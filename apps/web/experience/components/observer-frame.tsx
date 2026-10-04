"use client";
import { useEffect, useRef, useState } from "react";
import atlas from "@/lib/observer-atlas.json";

export type NarratorScene = keyof typeof atlas;

// Independent artwork. Bounds trim empty alpha, never the character silhouette.
export function FramedObserver({ scene, className = "", label }: {
  scene: NarratorScene; className?: string; label?: string;
}) {
  const frame = atlas[scene];
  const ref = useRef<SVGSVGElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setVisible(true); observer.disconnect(); }
    }, { rootMargin: "240px" });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return (
    <svg ref={ref} className={"observer narrator " + className} viewBox="0 0 290 260"
      data-narrative={scene} role={label ? "img" : undefined} aria-label={label}
      aria-hidden={label ? undefined : true} focusable="false">
      <svg x="12" y="12" width="266" height="236" viewBox={frame.viewBox}
        preserveAspectRatio="xMidYMax meet">
        {visible && <image href={frame.src} width={frame.width} height={frame.height} />}
      </svg>
    </svg>
  );
}
