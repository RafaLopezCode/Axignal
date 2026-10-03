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
export function Observer({
  className = "",
  pose = "standing",
}: {
  className?: string;
  pose?:
    | "standing"
    | "thinking"
    | "analyzing"
    | "connecting"
    | "guiding"
    | "pointing"
    | "walking"
    | "accompanying";
}) {
  const clipId = useId().replaceAll(":", "");
  const views = {
    analyzing: "352 646 175 237",
    connecting: "599 648 194 235",
    guiding: "862 654 225 231",
    pointing: "597 1064 235 194",
    walking: "873 1057 216 201",
    accompanying: "309 1064 238 194",
  };
  const poseMasks = {
    analyzing:
      "451,686 480,688 499,706 505,749 497,767 505,817 495,844 484,856 494,870 524,874 524,882 352,882 352,874 395,870 405,851 390,838 384,817 392,789 410,767 394,756 375,744 374,728 387,710 420,694",
    connecting: "599,648 793,648 793,883 599,883",
    guiding:
      "901,664 941,663 970,674 983,692 983,738 972,751 1000,746 1072,732 1083,743 1074,762 1054,781 993,798 982,811 984,852 1003,873 1087,878 1087,883 862,883 862,876 894,870 894,856 878,843 871,820 878,793 899,766 904,755 880,748 861,730 860,713 876,686",
    pointing:
      "645,1066 688,1067 713,1080 723,1101 831,1098 831,1211 714,1211 712,1225 734,1248 832,1252 832,1258 597,1258 597,1250 630,1245 644,1225 624,1211 610,1196 608,1180 617,1156 636,1138 621,1129 600,1117 597,1101 610,1081",
    walking:
      "927,1057 969,1057 998,1076 1010,1101 1015,1127 1010,1151 1028,1172 1024,1211 1052,1214 1056,1236 1031,1253 1089,1254 1089,1258 873,1258 873,1253 898,1249 902,1221 912,1195 912,1177 922,1156 903,1149 889,1136 882,1121 887,1102 903,1078",
    accompanying:
      "349,1069 397,1068 423,1084 431,1106 432,1137 448,1149 464,1149 467,1131 477,1109 500,1103 524,1111 535,1129 535,1153 550,1178 550,1258 309,1258 309,1077",
  };
  const actionPose = pose !== "standing" && pose !== "thinking";
  return (
    <svg
      className={"observer " + className}
      viewBox={
        actionPose
          ? views[pose as keyof typeof views]
          : pose === "standing"
            ? "582 112 293 421"
            : "522 860 263 262"
      }
      role="img"
      aria-label="El Observador AXIGNAL"
    >
      <defs>
        <clipPath id={clipId}>
          <polygon
            points={
              actionPose
                ? poseMasks[pose as keyof typeof poseMasks]
                : "740,110 792,111 836,129 850,145 858,173 844,194 850,222 859,241 860,260 849,277 838,290 852,311 862,344 861,390 853,413 835,434 817,437 804,437 813,496 828,522 879,527 879,534 582,534 582,527 635,524 655,510 670,477 645,470 635,449 634,411 645,378 659,349 687,326 657,314 639,297 624,278 617,267 597,263 589,245 589,222 600,195 621,164 660,138 702,120"
            }
          />
        </clipPath>
      </defs>
      <image
        href={actionPose ? "/observer/actions.png" : "/observer/reference.png"}
        width="1122"
        height="1402"
        clipPath={pose !== "thinking" ? "url(#" + clipId + ")" : undefined}
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
