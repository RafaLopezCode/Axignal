"use client";
import Link from "next/link";
import { capturePilotInvite } from "@/lib/pilot-invite";
import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  KeyRound,
  ShieldCheck,
  Info,
  LoaderCircle,
  RefreshCw,
} from "lucide-react";
import { useLocale } from "@/lib/locale";
import {
  preparedProviders,
  type AuthStartRequest,
} from "@/lib/public-contracts";
import { Observer } from "./ui";
import { PublicShell } from "./public-shell";

export function Access({ intent }: { intent: AuthStartRequest["intent"] }) {
  const { t } = useLocale();
  const controller = useRef<AbortController | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [available, setAvailable] = useState(false);
  const [chatgptAvailable, setChatgptAvailable] = useState(false);
  const [outcome, setOutcome] = useState<{
    provider: string;
    error: boolean;
  } | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  useEffect(() => {
    capturePilotInvite(window.location, window.history, () => window.sessionStorage);
  }, []);
  useEffect(() => {
    const current = new AbortController();
    void fetch("/api/auth/status", { cache: "no-store", signal: current.signal }).then(response => response.json()).then(data => {
      if (!current.signal.aborted && Array.isArray(data.providers)) {
        setAvailable(data.providers.some((item: { status?: string }) => item.status === "AVAILABLE"));
        setChatgptAvailable(data.providers.some((item: { id?: string; status?: string }) => item.id === "openai" && item.status === "AVAILABLE"));
      }
    }).catch(() => {});
    return () => current.abort();
  }, []);
  async function start(provider: AuthStartRequest["provider"]) {
    if (busy || (provider === "openai" && !chatgptAvailable)) return;
    setOutcome(null);
    setBusy(provider);
    controller.current?.abort();
    const current = new AbortController();
    controller.current = current;
    try {
      const response = await fetch("/api/auth/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, intent }),
        signal: current.signal,
      });
      const data = await response.json();
      if (response.ok && data.status === "REDIRECT" && typeof data.authorizationUrl === "string") {
        const target = new URL(data.authorizationUrl);
        const host = provider === "google" ? "accounts.google.com" : "auth.openai.com";
        if (target.protocol !== "https:" || target.hostname !== host || target.username || target.password || (target.port && target.port !== "443")) throw new Error("PROVIDER_URL_REJECTED");
        window.location.assign(target.href);
        return;
      }
      setOutcome({
        provider,
        error:
          response.status !== 503 ||
          !["AUTHENTICATION_PORT_NOT_CONNECTED", "AUTH_PROVIDER_UNAVAILABLE"].includes(data.code),
      });
    } catch {
      if (!current.signal.aborted) setOutcome({ provider, error: true });
    } finally {
      if (!current.signal.aborted) setBusy(null);
    }
  }
  return (
    <PublicShell className="access-page">
      <div className="access-spread">
        <section className="access-perspective">
          <span className="eyebrow">
            {t(
              "AXIGNAL / Tu próxima mirada",
              "AXIGNAL / Your next perspective",
            )}
          </span>
          <h1>
            {t("El contexto espera.", "Context awaits.")}
            <br />
            <em>{t("Acércate.", "Come closer.")}</em>
          </h1>
          <p>
            {t(
              "Una entrada sencilla a una forma más profunda de observar. Tu identidad abre el acceso; la evidencia sostiene lo que ves.",
              "A simple entrance to a deeper way of observing. Your identity opens access; evidence supports what you see.",
            )}
          </p>
          <div className="access-world" aria-hidden="true">
            <div className="access-ring" />
            <div className="access-ring ring-inner" />
            <div className="access-slip slip-context">
              <span className="mono">{t("Contexto", "Context")}</span>
              <span>{t("Lo que conecta.", "What connects.")}</span>
              <i />
              <i />
            </div>
            <div className="access-slip slip-signal">
              <span className="mono">{t("Señal", "Signal")}</span>
              <span>
                {t(
                  "Lo que merece tu atención.",
                  "What deserves your attention.",
                )}
              </span>
              <i />
            </div>
            <Observer scene="welcome" />
            <span className="hand-note">
              {t("una mirada que continúa", "a perspective that continues")}
            </span>
          </div>
        </section>
        <section className="access-panel" aria-labelledby="access-title">
          <nav
            className="access-intents"
            aria-label={t("Tipo de acceso", "Access type")}
          >
            <Link
              href="/login"
              aria-current={intent === "login" ? "page" : undefined}
            >
              {t("Acceder", "Sign in")}
            </Link>
            <Link
              href="/signup"
              aria-current={intent === "signup" ? "page" : undefined}
            >
              {t("Crear cuenta", "Sign up")}
            </Link>
          </nav>
          <KeyRound size={26} className="access-key" />
          <h2 id="access-title">
            {intent === "login"
              ? t("Vuelve a tu mirada.", "Return to your perspective.")
              : t("Tu primera mirada.", "Your first perspective.")}
          </h2>
          <p className="access-deck">
            {intent === "login"
              ? t(
                  "Elige la identidad con la que quieres continuar.",
                  "Choose the identity you want to continue with.",
                )
              : t(
                  "Elige cómo te gustaría entrar en AXIGNAL.",
                  "Choose how you would like to enter AXIGNAL.",
                )}
          </p>
          <div className="access-availability">
            <Info size={17} />
            <p>
              {available ? t("Elige una identidad conectada para continuar de forma segura.", "Choose a connected identity to continue securely.") : t(
                "Acceso en preparación. Google y ChatGPT aún no están conectados; esta versión no crea cuentas ni sesiones.",
                "Access is being prepared. Google and ChatGPT are not connected yet; this version creates no accounts or sessions.",
              )}
            </p>
          </div>
          <div className="provider-options" aria-busy={!!busy}>
            {preparedProviders.map((provider) => (
              <button
                className={"provider-button provider-" + provider.id}
                key={provider.id}
                onClick={() => void start(provider.id)}
                disabled={!!busy || (provider.id === "openai" && !chatgptAvailable)}
                aria-label={provider.id === "openai" && !chatgptAvailable ? t("ChatGPT · Próximamente", "ChatGPT · Coming soon") : undefined}
              >
                <img
                  src={
                    provider.id === "google"
                      ? "/providers/google-g.png"
                      : "/providers/chatgpt-black.svg"
                  }
                  alt=""
                  width={20}
                  height={20}
                />
                <span>
                  {provider.id === "google"
                    ? t("Continuar con Google", "Continue with Google")
                    : chatgptAvailable ? t("Continuar con ChatGPT", "Continue with ChatGPT") : t("Próximamente", "Coming soon")}
                </span>
                {busy === provider.id ? (
                  <LoaderCircle className="spin" size={18} />
                ) : (
                  <ArrowRight size={18} />
                )}
              </button>
            ))}
          </div>
          <span className="sr-only" role="status">
            {busy
              ? t("Comprobando disponibilidad…", "Checking availability…")
              : ""}
          </span>
          {outcome && (
            <div
              className={"auth-outcome " + (outcome.error ? "auth-error" : "")}
              role={outcome.error ? "alert" : "status"}
            >
              <strong>
                {outcome.error
                  ? t(
                      "No pudimos comprobar el acceso.",
                      "We could not check access.",
                    )
                  : t(
                      "Esta conexión todavía no está activa.",
                      "This connection is not active yet.",
                    )}
              </strong>
              <p>
                {outcome.error
                  ? t(
                      "La conexión no respondió como esperábamos. Esta versión no ha establecido una sesión. Puedes volver a comprobarlo.",
                      "The connection did not respond as expected. This version has established no session. You can check again.",
                    )
                  : outcome.provider === "openai"
                    ? t(
                        "Continuar con ChatGPT requiere un cliente de OpenAI aprobado para acceso web y el servicio de identidad de AXIGNAL conectado.",
                        "Continue with ChatGPT requires an OpenAI-approved web client and a connected AXIGNAL identity service.",
                      )
                    : t(
                        "Google requiere un cliente OAuth registrado y el servicio de identidad de AXIGNAL conectado.",
                        "Google requires a registered OAuth client and a connected AXIGNAL identity service.",
                      )}
              </p>
              <button className="text-link" onClick={() => setOutcome(null)}>
                <RefreshCw size={14} />
                {t("Volver a las opciones", "Back to options")}
              </button>
            </div>
          )}
          <div className="identity-permissions">
            <ShieldCheck size={20} />
            <div>
              <h3>
                {t("Solo identidad para entrar.", "Identity only, for access.")}
              </h3>
              <p>
                {t(
                  "La integración prevista solicita identificador, nombre y correo. No acceso a Gmail, Drive, conversaciones de ChatGPT ni uso de tu plan de IA.",
                  "The planned integration requests an identifier, name and email. No Gmail, Drive, ChatGPT conversation access or use of your AI plan.",
                )}
              </p>
            </div>
          </div>
          <p className="access-legal">
            {t(
              "Los textos legales están pendientes de publicación.",
              "Legal texts are pending publication.",
            )}{" "}
            <Link href="/policies/terms">
              {t("Uso y límites", "Use and limitations")}
            </Link>{" "}
            · <Link href="/policies/privacy">{t("Privacidad", "Privacy")}</Link>
          </p>
          <div className="demo-access">
            <span>
              {t(
                "Mientras tanto, descubre cómo se siente.",
                "Meanwhile, discover how it feels.",
              )}
            </span>
            <Link className="text-link" href="/panorama">
              {t(
                "Explorar la demo ilustrativa",
                "Explore the illustrative demo",
              )}
              <ArrowUpRight size={17} />
            </Link>
          </div>
        </section>
      </div>
    </PublicShell>
  );
}
