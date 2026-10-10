"use client";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useLocale } from "@/lib/locale";
import "./example-observatory.css";

/** The one thing the demo adds to the Observatory: a plain statement that the data is fictional. */
export function DemoNotice() {
  const { t } = useLocale();
  return <div className="obs-example" data-example="fictional">
    <div className="obs-example-notice" role="note">
      <strong>{t("Ejemplo guiado · datos ficticios", "Guided example · fictional data")}</strong>
      <span>{t("Así se lee el Observatorio real. Esta organización y sus hallazgos son ilustrativos; no se está realizando ninguna investigación.", "This is how the real Observatory is read. This organization and its findings are illustrative; no investigation is taking place.")}</span>
      <Link href="/signup">{t("Empezar con datos reales", "Start with real data")}<ArrowRight size={14} aria-hidden="true"/></Link>
    </div>
  </div>;
}
