"use client";
import { useState } from "react";
import { ArrowRight, Mail } from "lucide-react";
import { useLocale } from "@/lib/locale";
import { Observer } from "./ui";
import { PublicShell } from "./public-shell";
import { PublicRequestChannel } from "./public-request-channel";
import { WeeklyBriefChannel } from "./weekly-brief-channel";
export function Contact() {
  const { t } = useLocale();
  const options = [
    t("Conocer AXIGNAL", "Get to know AXIGNAL"),
    t("Una pregunta de producto", "A product question"),
    t("Privacidad y datos", "Privacy and data"),
  ];
  const [topic, setTopic] = useState(0);
  return (
    <PublicShell className="contact-page">
      <div className="contact-spread">
        <section className="contact-perspective">
          <span className="eyebrow">
            {t(
              "Contacto / Una conversación abierta",
              "Contact / An open conversation",
            )}
          </span>
          <h1>
            {t("Las buenas preguntas", "Good questions")}
            <br />
            <em>{t("nos acercan.", "bring us closer.")}</em>
          </h1>
          <p>
            {t(
              "Cuéntanos qué intentas comprender. El mejor punto de partida es una pregunta con contexto.",
              "Tell us what you are trying to understand. A question with context is the best place to start.",
            )}
          </p>
          <div
            className="contact-topics"
            role="group"
            aria-label={t("Tema del mensaje", "Message topic")}
          >
            {options.map((option, i) => (
              <button
                key={i}
                aria-pressed={topic === i}
                onClick={() => setTopic(i)}
              >
                {option}
                <ArrowRight size={16} />
              </button>
            ))}
          </div>
          <div className="contact-illustration">
            <div className="letter-paper">
              <Mail size={23} />
              <span>
                {t("Una pregunta.", "A question.")}
                <br />
                {t("Más perspectiva.", "More perspective.")}
              </span>
              <i />
              <i />
              <img src="/brand/isotope.svg" alt="" width={32} height={35} />
            </div>
            <Observer scene="contact" />
            <span className="hand-note">
              {t("te leemos con atención", "we read with care")}
            </span>
          </div>
          <p className="contact-publication">
            {t(
              "Responsable: AXIGNAL · España. El correo público sólo se muestra cuando el canal lo publica.",
              "Controller: AXIGNAL · Spain. A public email appears only when published by the channel.",
            )}
          </p>
        </section>
        <PublicRequestChannel key={topic} subject={options[topic]} />
      </div>
      <WeeklyBriefChannel />
    </PublicShell>
  );
}
