"use client";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { ArrowUp } from "lucide-react";
import { useLocale } from "@/lib/locale";
import type { Locale } from "@/lib/languages";

const labels: Record<Locale, string> = {
  es: "Volver arriba", en: "Back to top", de: "Nach oben",
  pt: "Voltar ao início", fr: "Retour en haut", it: "Torna in alto",
};

export function BackToTop() {
  const { locale } = useLocale();
  const path = usePathname();
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    let frame = 0;
    const measure = () => {
      frame = 0;
      setVisible(window.scrollY > Math.max(480, window.innerHeight * .75));
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(measure); };
    measure();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [path]);

  if (!visible) return null;
  return <button className="public-back-top" type="button" onClick={() => {
    // Clear a chapter fragment so selecting that chapter again still navigates.
    if (window.location.hash) {
      const url = new URL(window.location.href);
      url.hash = "";
      // Let Next's native-history integration retain its state and update the URL.
      window.history.replaceState(null, "", url.href);
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    }
    document.getElementById("main")?.focus({ preventScroll: true });
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduced ? "instant" : "smooth" });
  }}>
    <ArrowUp size={18} aria-hidden="true" />
    <span>{labels[locale]}</span>
  </button>;
}
