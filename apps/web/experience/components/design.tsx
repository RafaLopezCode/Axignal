"use client";
import Link from "next/link";
import { useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  ScanEye,
  Network,
  Clock3,
  ShieldCheck,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import {
  Brand,
  LocaleToggle,
  Badge,
  DemoLabel,
  Observer,
  StatePanel,
  MiniFooter,
  type ViewState,
} from "./ui";
export function Design() {
  const { t } = useLocale();
  const [state, setState] = useState<ViewState>("unknown");
  return (
    <div className="design-page">
      <header className="landing-header">
        <Brand />
        <nav>
          <Link href="/">{t("Landing", "Landing")}</Link>
          <Link href="/panorama">{t("Producto", "Product")}</Link>
          <Link href="/admin">Admin</Link>
        </nav>
        <LocaleToggle />
      </header>
      <main id="main">
        <section className="design-hero">
          <span className="eyebrow">
            {t(
              "AXIGNAL / SISTEMA DE EXPERIENCIA",
              "AXIGNAL / EXPERIENCE SYSTEM",
            )}
          </span>
          <h1>
            {t("Una mirada.", "One perspective.")}
            <br />
            <em>{t("Un lenguaje coherente.", "A coherent language.")}</em>
          </h1>
          <p>
            {t(
              "La belleza orienta atención. La estructura conserva el significado. La evidencia limita lo que podemos afirmar.",
              "Beauty directs attention. Structure preserves meaning. Evidence limits what we can assert.",
            )}
          </p>
          <span className="design-mode">
            EXPLORE ·{" "}
            {t(
              "Revisión visual humana pendiente",
              "Human visual review pending",
            )}
          </span>
        </section>
        <section className="design-section">
          <div className="design-section-title">
            <span className="mono">01</span>
            <h2>
              {t(
                "Identidad exacta, voz propia.",
                "Exact identity, distinctive voice.",
              )}
            </h2>
          </div>
          <div className="brand-samples">
            <div>
              <img
                src="/brand/logo-light.svg"
                alt="AXIGNAL · logo claro"
                width={235}
                height={68}
              />
              <span className="mono">Logo_Claro.svg · #354F98</span>
            </div>
            <div className="dark-sample">
              <img
                src="/brand/logo-dark.svg"
                alt="AXIGNAL · logo oscuro"
                width={235}
                height={68}
              />
              <span className="mono">Logo_Oscuro.svg</span>
            </div>
            <div>
              <Observer scene="discover" className="design-observer" />
              <span>
                {t(
                  "El Observador · ilustración narrativa",
                  "The Observer · narrative illustration",
                )}
              </span>
            </div>
          </div>
        </section>
        <section className="design-section">
          <div className="design-section-title">
            <span className="mono">02</span>
            <h2>
              {t("La jerarquía tiene una voz.", "Hierarchy has a voice.")}
            </h2>
          </div>
          <div className="type-specimen">
            <div className="type-display">
              <span className="mono">
                FRAUNCES / {t("PERSPECTIVA", "PERSPECTIVE")}
              </span>
              <h3>
                {t(
                  "El contexto transforma la mirada.",
                  "Context transforms perspective.",
                )}
              </h3>
            </div>
            <div className="type-body">
              <span className="mono">MANROPE / {t("LECTURA", "READING")}</span>
              <p>
                {t(
                  "Una capacidad puede encontrar un nuevo contexto de demanda. Entender la coincidencia es el comienzo de una investigación; no una promesa comercial.",
                  "A capability can meet a new demand context. Understanding the overlap begins an investigation; it is not a commercial promise.",
                )}
              </p>
              <span className="mono">IBM PLEX MONO / 03 OCT 2026</span>
              <span className="hand-note">
                {t("mira un poco más cerca", "look a little closer")}
              </span>
            </div>
          </div>
        </section>
        <section className="design-section">
          <div className="design-section-title">
            <span className="mono">03</span>
            <h2>
              {t(
                "El color orienta. Las palabras precisan.",
                "Color guides. Words clarify.",
              )}
            </h2>
          </div>
          <div className="color-specimen">
            {[
              ["#354F98", "AXIGNAL"],
              ["#3c3c3c", t("Carbón", "Charcoal")],
              ["#e7edf8", t("Azul suave", "Soft blue")],
              ["#dfe8df", t("Salvia", "Sage")],
              ["#e5e0ee", t("Lavanda", "Lavender")],
              ["#eee8dc", t("Arena", "Sand")],
            ].map(([color, name]) => (
              <div key={color}>
                <span className="color-swatch" style={{ background: color }} />
                <strong>{name}</strong>
                <span className="mono">{color}</span>
              </div>
            ))}
          </div>
          <div className="epistemic-specimen">
            <Badge state="OBSERVED" />
            <Badge state="POTENTIAL" />
            <Badge state="UNKNOWN" />
            <p>
              {t(
                "El estado epistémico no depende solo del color. Una posibilidad derivada conserva su diferencia con lo observado.",
                "Epistemic state never depends on color alone. A derived possibility retains its distinction from what is observed.",
              )}
            </p>
          </div>
        </section>
        <section className="design-section">
          <div className="design-section-title">
            <span className="mono">04</span>
            <h2>
              {t(
                "La incertidumbre también se diseña.",
                "Uncertainty is designed too.",
              )}
            </h2>
          </div>
          <div
            className="state-switcher"
            role="group"
            aria-label={t("Estados de recuperación", "Recovery states")}
          >
            {(
              [
                "empty",
                "unknown",
                "loading",
                "error",
                "unavailable",
              ] as ViewState[]
            ).map((s) => (
              <button
                key={s}
                aria-pressed={state === s}
                onClick={() => setState(s)}
              >
                {
                  {
                    empty: t("Vacío", "Empty"),
                    unknown: t("Desconocido", "Unknown"),
                    loading: t("Carga", "Loading"),
                    error: t("Error", "Error"),
                    unavailable: t("No disponible", "Unavailable"),
                  }[s]
                }
              </button>
            ))}
          </div>
          <StatePanel state={state} onRetry={() => setState("unknown")} />
          <Link className="text-link" href={"/panorama?state=" + state}>
            {t(
              "Probar este estado en el producto",
              "Test this state in the product",
            )}
            <ArrowUpRight size={16} />
          </Link>
        </section>
        <section className="design-section">
          <div className="design-section-title">
            <span className="mono">05</span>
            <h2>
              {t(
                "Creatividad con una frontera clara.",
                "Creativity with a clear boundary.",
              )}
            </h2>
          </div>
          <div className="governance-specimen">
            {[
              [
                ScanEye,
                t(
                  "La persona dirige atención.",
                  "The person directs attention.",
                ),
                t(
                  "Una organización no equivale a su foco. Panorama no equivale a AXIGLAND.",
                  "An organization is not its focus. Panorama is not AXIGLAND.",
                ),
              ],
              [
                BookOpen,
                t(
                  "La lectura conserva su base.",
                  "The reading retains its basis.",
                ),
                t(
                  "Estado, evidencia, derivación y temporalidad permanecen inspeccionables.",
                  "State, evidence, derivation and time remain inspectable.",
                ),
              ],
              [
                Network,
                t("La composición es gobernada.", "Composition is governed."),
                t(
                  "AI SDK 7 UI + registro de componentes. El plan selecciona referencias; no inventa contenido ni autoridad.",
                  "AI SDK 7 UI + component registry. A plan selects references; it does not invent content or authority.",
                ),
              ],
              [
                ShieldCheck,
                t(
                  "El privilegio vive en el servicio.",
                  "Privilege lives in the service.",
                ),
                t(
                  "Admin usa un plano privado y deniega comandos sin autorización del servicio propietario.",
                  "Admin uses a private plane and denies commands without owning-service authorization.",
                ),
              ],
            ].map(([Icon, title, body], i) => {
              const I = Icon as typeof ScanEye;
              return (
                <div key={i}>
                  <I size={23} strokeWidth={1.5} />
                  <h3>{title as string}</h3>
                  <p>{body as string}</p>
                </div>
              );
            })}
          </div>
        </section>
        <section className="design-section accessibility-specimen">
          <span className="eyebrow">
            {t("DISEÑADO PARA COMPRENDER", "DESIGNED TO UNDERSTAND")}
          </span>
          <h2>
            {t(
              "También con teclado. También sin movimiento.",
              "With a keyboard too. Without motion too.",
            )}
          </h2>
          <p>
            {t(
              "Lectura lineal alternativa a la composición espacial. Foco visible, controles con nombre, diálogos con retorno de foco y estados expresados con palabras. En móvil, el contenido respira en una secuencia legible.",
              "Linear reading as an alternative to spatial composition. Visible focus, named controls, dialogs that return focus and states expressed in words. On mobile, content breathes in a readable sequence.",
            )}
          </p>
          <div className="design-links">
            <Link href="/panorama" className="button primary">
              {t("Explorar la experiencia", "Explore the experience")}
              <ArrowRight size={17} />
            </Link>
            <Link href="/admin" className="button secondary">
              {t("Inspeccionar Admin", "Inspect Admin")}
              <ArrowUpRight size={17} />
            </Link>
          </div>
          <DemoLabel />
        </section>
      </main>
      <MiniFooter />
    </div>
  );
}
