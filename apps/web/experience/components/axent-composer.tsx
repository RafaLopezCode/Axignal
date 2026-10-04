"use client";
import { useId } from "react";
import { ArrowUpRight, Square } from "lucide-react";
import { useLocale } from "@/lib/locale";
export function AxentComposer({
  value,
  onChange,
  onSubmit,
  busy,
  onStop,
}: {
  value: string;
  onChange: (s: string) => void;
  onSubmit: () => void;
  busy: boolean;
  onStop: () => void;
}) {
  const { t } = useLocale();
  const id = useId();
  return (
    <div className="axent-compose">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
      >
        <label className="sr-only" htmlFor={id}>
          {t("Pregunta sobre este contexto", "Ask about this context")}
        </label>
        <textarea
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          maxLength={1000}
          placeholder={t(
            "Pregunta sobre este contexto…",
            "Ask about this context…",
          )}
          rows={2}
          onKeyDown={(e) => {
            if (
              e.key === "Enter" &&
              !e.shiftKey &&
              !e.nativeEvent.isComposing
            ) {
              e.preventDefault();
              onSubmit();
            }
          }}
        />
        {busy ? (
          <button
            type="button"
            className="send-button"
            onClick={onStop}
            aria-label={t("Detener respuesta", "Stop response")}
          >
            <Square size={13} />
          </button>
        ) : (
          <button
            className="send-button"
            type="submit"
            disabled={!value.trim()}
            aria-label={t("Enviar pregunta", "Send question")}
          >
            <ArrowUpRight size={18} />
          </button>
        )}
      </form>
      <p>
        {t(
          "Explica la evidencia. No decide la verdad.",
          "Explains evidence. Does not decide truth.",
        )}
      </p>
    </div>
  );
}
