"use client";
import Link from "next/link";
import { ArrowUpRight, BookOpen, Clock3, Info } from "lucide-react";
import {
  evidence,
  dateLabel,
  type Signal,
  type Evidence as EvidenceType,
} from "@/lib/projection";
import { useLocale } from "@/lib/locale";
import { Dialog, Badge, DemoLabel } from "./ui";
export function EvidenceDialog({
  item,
  onClose,
}: {
  item: EvidenceType;
  onClose: () => void;
}) {
  const { t, copy, locale } = useLocale();
  return (
    <Dialog
      title={t("Volver a la evidencia", "Return to evidence")}
      onClose={onClose}
      className="evidence-dialog"
    >
      <DemoLabel />
      <span className="eyebrow evidence-kicker">
        {t("Fuente conservada · ejemplo", "Preserved source · example")}
      </span>
      <h3 className="evidence-title">{copy(item.title)}</h3>
      <p className="evidence-source">{copy(item.source)}</p>
      <div className="source-dates">
        <div>
          <span>{t("Publicado", "Published")}</span>
          <strong>{dateLabel(item.publishedAt, locale)}</strong>
        </div>
        <div>
          <span>{t("Observado por AXIGNAL", "Observed by AXIGNAL")}</span>
          <strong>{dateLabel(item.observedAt, locale)}</strong>
        </div>
      </div>
      <div className="evidence-block">
        <BookOpen size={18} />
        <div>
          <h4>{t("Qué contiene la fuente", "What the source contains")}</h4>
          <p>{copy(item.body)}</p>
        </div>
      </div>
      <div className="evidence-block">
        <Clock3 size={18} />
        <div>
          <h4>
            {t("Qué sostiene esta lectura", "What supports this reading")}
          </h4>
          <p>{copy(item.basis)}</p>
        </div>
      </div>
      {item.instrument && (
        <div className="source-instrument">
          <span className="mono">
            {t("CONDICIONES DE OBSERVACIÓN", "OBSERVATION CONDITIONS")}
          </span>
          <p>{copy(item.instrument)}</p>
        </div>
      )}
      <div className="limit-note">
        <Info size={17} />
        <div>
          <strong>{t("Su alcance termina aquí", "Its scope ends here")}</strong>
          <p>{copy(item.limitation)}</p>
        </div>
      </div>
      <Link
        className="button secondary"
        target="_blank"
        href={"/sources/" + item.id}
      >
        {t("Abrir documento ilustrativo", "Open illustrative document")}
        <ArrowUpRight size={17} />
      </Link>
    </Dialog>
  );
}
export function EvidenceList({
  signal,
  onOpen,
}: {
  signal: Signal;
  onOpen: (id: string) => void;
}) {
  const { t, copy, locale } = useLocale();
  return (
    <div className="evidence-list">
      {signal.evidenceIds.length === 0 ? (
        <div className="limit-note">
          <Info size={18} />
          <p>
            {t(
              "Sin base suficiente. No mostramos fuentes que no sostienen esta conclusión.",
              "Insufficient basis. We do not show sources that do not support this conclusion.",
            )}
          </p>
        </div>
      ) : (
        signal.evidenceIds.map((id, i) => {
          const e = evidence.find((item) => item.id === id)!;
          return (
            <button
              key={id}
              className="evidence-row"
              onClick={() => onOpen(id)}
            >
              <span className="evidence-number">0{i + 1}</span>
              <div>
                <strong>{copy(e.title)}</strong>
                <span>{copy(e.source)}</span>
                <small>
                  {t("Observado", "Observed")} {dateLabel(e.observedAt, locale)}
                </small>
              </div>
              <ArrowUpRight size={17} />
            </button>
          );
        })
      )}
      <div className="evidence-summary">
        <Badge state={signal.epistemic} />
        <span>
          {t(
            "El estado pertenece a la señal; la fuente conserva su propio alcance.",
            "The state belongs to the signal; the source retains its own scope.",
          )}
        </span>
      </div>
    </div>
  );
}
