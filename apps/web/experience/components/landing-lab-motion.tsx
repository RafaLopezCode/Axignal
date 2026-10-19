"use client";
import { useRef, type RefObject } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(useGSAP, ScrollTrigger);

/** Optional enhancement only. No economic state, scroll interception or global kill. */
export default function NarrativeMotion({
  root,
  revision,
  proofOpen,
}: {
  root: RefObject<HTMLDivElement | null>;
  revision: string;
  proofOpen: boolean;
}) {
  const previous = useRef(revision);
  useGSAP(
    () => {
      const media = gsap.matchMedia();
      media.add(
        {
          desktop: "(min-width: 701px)",
          mobile: "(max-width: 700px)",
          animate: "(prefers-reduced-motion: no-preference)",
        },
        (context) => {
          if (!context.conditions?.animate || !root.current) return;
          const scene = root.current.querySelector(".lab-world");
          if (scene) {
            const sequence = gsap.timeline({
              scrollTrigger: { trigger: scene, start: "top 88%", once: true },
              defaults: { ease: "power2.out", duration: 0.6 },
            });
            sequence
              .from(".lab-world-line", {
                scaleX: 0.1,
                opacity: 0.3,
                transformOrigin: "center center",
                stagger: 0.12,
                immediateRender: false,
              })
              .from(
                "[data-world-node]",
                {
                  y: context.conditions.desktop ? 9 : 5,
                  opacity: 0.65,
                  stagger: 0.1,
                  immediateRender: false,
                },
                0.12,
              )
              .from(
                ".lab-hero-observer img",
                {
                  x: 8,
                  rotation: 1.5,
                  transformOrigin: "bottom center",
                  immediateRender: false,
                },
                0.3,
              );
          }
          root.current
            .querySelectorAll(".lab-method-loop li")
            .forEach((step) => {
              const art = step.querySelector("[data-observer]");
              if (art)
                gsap.from(art, {
                  y: 12,
                  opacity: 0.65,
                  duration: 0.6,
                  ease: "power2.out",
                  immediateRender: false,
                  scrollTrigger: {
                    trigger: step,
                    start: "top 85%",
                    once: true,
                  },
                });
            });
        },
        root,
      );
      return () => media.revert();
    },
    { scope: root },
  );
  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      if (previous.current !== revision) {
        gsap.from(".lab-finding-copy", {
          opacity: 0.72,
          y: 6,
          duration: 0.28,
          ease: "power2.out",
          clearProps: "transform,opacity",
        });
        previous.current = revision;
      }
      if (proofOpen)
        gsap.from("[data-proof]", {
          opacity: 0.72,
          y: 4,
          duration: 0.24,
          ease: "power2.out",
          clearProps: "transform,opacity",
        });
    },
    { scope: root, dependencies: [revision, proofOpen], revertOnUpdate: true },
  );
  return null;
}
