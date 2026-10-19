"use client";
import { useRef, type RefObject } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(useGSAP, ScrollTrigger);

/** Bounded stories about existing evidence. Scroll and economic state stay in React. */
export default function NarrativeMotion({
  root,
  revision,
  proofOpen,
  replay,
}: {
  root: RefObject<HTMLDivElement | null>;
  revision: string;
  proofOpen: boolean;
  replay: number;
}) {
  const previous = useRef(revision);
  useGSAP(
    () => {
      const media = gsap.matchMedia();
      media.add(
        {
          desktop: "(min-width: 701px)",
          animate: "(prefers-reduced-motion: no-preference)",
        },
        (context) => {
          if (!context.conditions?.animate || !root.current) return;
          const scope = root.current;
          const distance = context.conditions.desktop ? 28 : 14;
          const scene = scope.querySelector(".lab-world");
          if (scene) {
            const sequence = gsap.timeline({
              scrollTrigger: {
                trigger: scene,
                start: "top 88%",
                toggleActions: "restart none restart none",
              },
              defaults: { ease: "power2.out", duration: 0.85 },
              onStart: () => scope.setAttribute("data-narrative", "playing"),
              onComplete: () =>
                scope.setAttribute("data-narrative", "complete"),
            });
            sequence
              .fromTo(
                ".lab-clue-one",
                { x: -distance, y: 14 },
                { x: 0, y: 0, immediateRender: false },
                0,
              )
              .fromTo(
                ".lab-hero-observer img",
                { x: -distance, rotation: -2, opacity: 0.7 },
                { x: 0, rotation: 0, opacity: 1, immediateRender: false },
                0.15,
              )
              .fromTo(
                ".lab-clue-two",
                { x: distance, y: 18 },
                { x: 0, y: 0, immediateRender: false },
                0.65,
              )
              .fromTo(
                ".lab-world-line",
                { scaleX: 0.05, opacity: 0.15 },
                {
                  scaleX: 1,
                  opacity: 1,
                  transformOrigin: "left center",
                  stagger: 0.22,
                  immediateRender: false,
                },
                0.9,
              )
              .fromTo(
                ".lab-connection",
                { scale: 0.8, y: 12 },
                { scale: 1, y: 0, immediateRender: false },
                1.25,
              )
              .fromTo(
                ".lab-hero-finding",
                { y: distance, scale: 0.97 },
                { y: 0, scale: 1, immediateRender: false },
                1.65,
              )
              .set(
                ".lab-clue-one, .lab-clue-two, .lab-connection, .lab-hero-finding, .lab-hero-observer img, .lab-world-line",
                { clearProps: "transform,opacity" },
              );
            if (replay > 0 && ScrollTrigger.isInViewport(scene))
              sequence.restart();
          }
          scope
            .querySelectorAll(".lab-method-loop li")
            .forEach((step, index) => {
              const art = step.querySelector("[data-observer]");
              if (art)
                gsap.fromTo(
                  art,
                  {
                    x: index % 2 ? distance : -distance,
                    y: 18,
                    rotation: index % 2 ? 2 : -2,
                  },
                  {
                    x: 0,
                    y: 0,
                    rotation: 0,
                    duration: 1.1,
                    ease: "power2.out",
                    immediateRender: false,
                    scrollTrigger: {
                      trigger: step,
                      start: "top 82%",
                      toggleActions: "restart none restart none",
                    },
                  },
                );
            });
          const observer = scope.querySelector("[data-trust-observer]");
          if (observer)
            gsap.fromTo(
              observer,
              { x: -distance, rotation: -3 },
              {
                x: 0,
                rotation: 0,
                duration: 1.1,
                ease: "power2.out",
                immediateRender: false,
                scrollTrigger: {
                  trigger: "#trust",
                  start: "top 78%",
                  toggleActions: "restart none restart none",
                },
              },
            );
          scope
            .querySelectorAll(".lab-memory-argument article")
            .forEach((article) => {
              gsap.fromTo(
                article,
                { y: 22 },
                {
                  y: 0,
                  duration: 0.75,
                  ease: "power2.out",
                  immediateRender: false,
                  scrollTrigger: {
                    trigger: article,
                    start: "top 86%",
                    toggleActions: "play none none none",
                  },
                },
              );
            });
        },
        root,
      );
      return () => {
        media.revert();
        const scope = root.current;
        scope?.removeAttribute("data-narrative");
        // These elements have no authored inline transforms/opacity. Remove only
        // the properties owned by this enhancement after reverting its contexts.
        scope
          ?.querySelectorAll<
            HTMLElement | SVGElement
          >(".lab-world-line, .lab-clue, .lab-connection, .lab-hero-finding, [data-observer], [data-trust-observer]")
          .forEach((element) => {
            element.style.removeProperty("transform");
            element.style.removeProperty("opacity");
          });
      };
    },
    { scope: root, dependencies: [replay], revertOnUpdate: true },
  );
  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      if (previous.current !== revision) {
        gsap.fromTo(
          ".lab-finding-copy",
          { x: 20 },
          {
            x: 0,
            duration: 0.55,
            ease: "power2.out",
            clearProps: "transform",
            immediateRender: false,
          },
        );
        previous.current = revision;
      }
      if (proofOpen)
        gsap.fromTo(
          "[data-proof]",
          { y: 16 },
          {
            y: 0,
            duration: 0.5,
            ease: "power2.out",
            clearProps: "transform",
            immediateRender: false,
          },
        );
    },
    { scope: root, dependencies: [revision, proofOpen], revertOnUpdate: true },
  );
  return null;
}
