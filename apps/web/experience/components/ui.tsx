"use client";
import Link from "next/link";
import { useEffect, useRef, useId, useState } from "react";
import {
  ArrowRight,
  X,
  RotateCcw,
  CircleHelp,
  AlertCircle,
  LoaderCircle,
  BookOpen,
  LockKeyhole,
  Languages,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import { locales, type Locale } from "@/lib/languages";
import type { Epistemic } from "@/lib/projection";
import { FramedObserver, type NarratorScene } from "./observer-frame";
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
  const [keyboardFocus, setKeyboardFocus] = useState(false);
  const pointerInteraction = useRef(false);
  const { locale, setLocale, t } = useLocale();
  return (
    <label className={"locale-selector" + (keyboardFocus ? " keyboard-focus" : "")}>
      <Languages size={16} aria-hidden="true" />
      <span className="sr-only">{t("Idioma", "Language")}</span>
      <select
        value={locale}
        onPointerDown={() => { pointerInteraction.current = true; setKeyboardFocus(false); }}
        onKeyDown={() => { pointerInteraction.current = false; setKeyboardFocus(true); }}
        onFocus={(e) => setKeyboardFocus(!pointerInteraction.current && e.target.matches(":focus-visible"))}
        onBlur={() => { pointerInteraction.current = false; setKeyboardFocus(false); }}
        onChange={(e) => setLocale(e.target.value as Locale)}
      >
        {locales.map((l) => (
          <option value={l.id} key={l.id} lang={l.id}>
            {l.name}
          </option>
        ))}
      </select>
    </label>
  );
}
export function Observer({ scene, className = "", label }: {
  scene: NarratorScene; className?: string; label?: string;
}) {
  return <FramedObserver scene={scene} className={className} label={label} />;
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
  const titleId = useId();
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
        e.stopPropagation();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      aria-labelledby={titleId}
    >
      <div className="dialog-body">
        <header className="dialog-header">
          <h2 id={titleId}>{title}</h2>
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
      {state === "empty" && <Observer scene="unknown" className="state-observer" />}
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
export function AxentIdentity() {
  return (
    <div className="axent-identity">
      <img src="/brand/isotope.svg" alt="" width={25} height={27} />
      <span className="axent-wordmark">Axent</span>
    </div>
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
      <nav aria-label={t("Más sobre AXIGNAL", "More about AXIGNAL")}>
        <Link href="/knowledge">Knowledge</Link>
        <a
          href="https://www.linkedin.com/company/axignal/"
          target="_blank"
          rel="noopener noreferrer"
        >
          LinkedIn
        </a>
        <Link href="/contact">{t("Contacto", "Contact")}</Link>
        <Link href="/policies">{t("Políticas", "Policies")}</Link>
        <Link href="/gdpr">GDPR</Link>
        <Link href="/login">{t("Acceder", "Sign in")}</Link>
        <Link href="/signup">{t("Crear cuenta", "Sign up")}</Link>
        <Link href="/design">{t("Sistema visual", "Visual system")}</Link>
      </nav>
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
