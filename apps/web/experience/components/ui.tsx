"use client";
import Link from "next/link";
import { useEffect, useRef, useId } from "react";
import {
  ArrowRight,
  X,
  RotateCcw,
  CircleHelp,
  AlertCircle,
  LoaderCircle,
  BookOpen,
  LockKeyhole,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import type { Epistemic } from "@/lib/projection";
export function Brand({
  dark = false,
  compact = false,
}: {
  dark?: boolean;
  compact?: boolean;
}) {
  const { t } = useLocale();
  return (
    <Link
      href="/"
      aria-label={t("AXIGNAL · Inicio", "AXIGNAL · Home")}
      className={compact ? "brand compact" : "brand"}
    >
      <img
        src={
          compact
            ? "/brand/isotope.svg"
            : dark
              ? "/brand/logo-dark.svg"
              : "/brand/logo-light.svg"
        }
        alt="AXIGNAL"
        width={compact ? 32 : 147}
        height={compact ? 35 : 43}
      />
    </Link>
  );
}
export function LocaleToggle() {
  const { locale, setLocale, t } = useLocale();
  return (
    <button
      className="locale-toggle"
      onClick={() => setLocale(locale === "es" ? "en" : "es")}
      aria-label={t("Cambiar a inglés", "Switch to Spanish")}
    >
      <span className={locale === "es" ? "active" : ""}>ES</span>
      <span aria-hidden="true">/</span>
      <span className={locale === "en" ? "active" : ""}>EN</span>
    </button>
  );
}
export function Observer({
  className = "",
  pose = "standing",
}: {
  className?: string;
  pose?: "standing" | "thinking";
}) {
  const clipId = useId().replaceAll(":", "");
  return (
    <svg
      className={"observer " + className}
      viewBox={pose === "standing" ? "582 112 293 421" : "522 860 263 262"}
      role="img"
      aria-label="El Observador AXIGNAL"
    >
      <defs>
        <clipPath id={clipId}>
          <polygon points="740,110 792,111 836,129 850,145 858,173 844,194 850,222 859,241 860,260 849,277 838,290 852,311 862,344 861,390 853,413 835,434 817,437 804,437 813,496 828,522 879,527 879,534 582,534 582,527 635,524 655,510 670,477 645,470 635,449 634,411 645,378 659,349 687,326 657,314 639,297 624,278 617,267 597,263 589,245 589,222 600,195 621,164 660,138 702,120" />
        </clipPath>
      </defs>
      <image
        href="/observer/reference.png"
        width="1122"
        height="1402"
        clipPath={pose === "standing" ? "url(#" + clipId + ")" : undefined}
      />
    </svg>
  );
}
export function Badge({ state }: { state: Epistemic }) {
  const { t } = useLocale();
  return (
    <span className={"badge badge-" + state.toLowerCase()}>
      <span className="badge-mark" aria-hidden="true" />
      {state === "OBSERVED"
        ? t("Observado", "Observed")
        : state === "POTENTIAL"
          ? t("Potencial", "Potential")
          : t("Desconocido", "Unknown")}
    </span>
  );
}
export function DemoLabel({ privateMode = false }: { privateMode?: boolean }) {
  const { t } = useLocale();
  return (
    <span className="demo-label">
      {privateMode ? <LockKeyhole size={12} /> : <BookOpen size={12} />}{" "}
      {privateMode
        ? t(
            "Vista privada · datos ilustrativos",
            "Private view · illustrative data",
          )
        : t("Demo · datos ilustrativos", "Demo · illustrative data")}
    </span>
  );
}
export function IconButton({
  label,
  children,
  onClick,
  disabled = false,
  className = "",
}: {
  label: string;
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button
      className={"icon-button " + className}
      title={label}
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
export function Dialog({
  title,
  onClose,
  children,
  className = "",
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const { t } = useLocale();
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
      previous?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={"dialog " + className}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      aria-labelledby="dialog-title"
    >
      <div className="dialog-body">
        <header className="dialog-header">
          <h2 id="dialog-title">{title}</h2>
          <IconButton label={t("Cerrar", "Close")} onClick={onClose}>
            <X size={20} />
          </IconButton>
        </header>
        {children}
      </div>
    </dialog>
  );
}
export type ViewState =
  | "empty"
  | "unknown"
  | "loading"
  | "error"
  | "unavailable";
export function StatePanel({
  state,
  onRetry,
}: {
  state: ViewState;
  onRetry?: () => void;
}) {
  const { t } = useLocale();
  const content = {
    empty: [
      t("Todo comienza con una mirada.", "Everything begins with a look."),
      t(
        "Selecciona una organización para orientar un foco de observación persistente.",
        "Select an organization to direct a persistent observation focus.",
      ),
    ],
    unknown: [
      t(
        "Aún no hay base para concluir.",
        "There is not yet a basis to conclude.",
      ),
      t(
        "Lo que no sabemos sigue abierto. Una ausencia de evidencia no es una respuesta negativa.",
        "What we do not know remains open. Absence of evidence is not a negative answer.",
      ),
    ],
    loading: [
      t("Preparando esta vista…", "Preparing this view…"),
      t(
        "Estamos leyendo la proyección. Este estado no representa progreso de investigación.",
        "Reading the projection. This state does not represent research progress.",
      ),
    ],
    error: [
      t("Esta vista no pudo cargarse.", "This view could not be loaded."),
      t(
        "Tu contexto se conserva. Puedes volver a intentarlo.",
        "Your context is preserved. You can try again.",
      ),
    ],
    unavailable: [
      t(
        "Esta información no está disponible.",
        "This information is unavailable.",
      ),
      t(
        "No existe una proyección autorizada para este contexto. No completamos los huecos con suposiciones.",
        "There is no authorized projection for this context. We do not fill gaps with assumptions.",
      ),
    ],
  }[state];
  const Icon =
    state === "loading"
      ? LoaderCircle
      : state === "error"
        ? AlertCircle
        : CircleHelp;
  return (
    <section
      className={"state-panel state-" + state}
      aria-busy={state === "loading"}
      aria-live="polite"
    >
      <Observer className="state-observer" />
      <div>
        <Icon
          className={state === "loading" ? "spin" : ""}
          size={24}
          strokeWidth={1.5}
        />
        <h2>{content[0]}</h2>
        <p>{content[1]}</p>
        {onRetry && state !== "loading" && (
          <button className="button secondary" onClick={onRetry}>
            <RotateCcw size={16} />
            {state === "empty"
              ? t("Elegir organización", "Choose organization")
              : t("Volver a la vista", "Return to view")}
            <ArrowRight size={16} />
          </button>
        )}
      </div>
    </section>
  );
}
export function MiniFooter() {
  const { t } = useLocale();
  return (
    <footer className="mini-footer">
      <Brand />
      <span>
        {t("Una mirada que conecta.", "A perspective that connects.")}
      </span>
      <Link href="/design">{t("Sistema visual", "Visual system")}</Link>
      <Link href="/admin">Admin</Link>
    </footer>
  );
}

export function useFocusTrap(
  active: boolean,
  ref: React.RefObject<HTMLElement | null>,
  onClose: () => void,
) {
  useEffect(() => {
    if (!active) return;
    const previous = document.activeElement as HTMLElement | null,
      node = ref.current;
    if (!node) return;
    const getItems = () =>
      Array.from(
        node.querySelectorAll<HTMLElement>(
          'a[href],button:not([disabled]),input,select,textarea,[tabindex="0"]',
        ),
      );
    getItems()[0]?.focus();
    function handle(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
      if (event.key === "Tab") {
        const items = getItems(),
          first = items[0],
          last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    }
    node.addEventListener("keydown", handle);
    return () => {
      node.removeEventListener("keydown", handle);
      previous?.focus();
    };
  }, [active, ref]);
}
