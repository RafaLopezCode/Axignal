import type { Metadata } from "next";
import "./globals.css";
import "./public.css";
import "./typography.css";
import "./acquisition.css";
import "./funnel.css";
import "../components/cognition/cognition.css";
import { LocaleProvider } from "@/lib/locale";
import { PrivacyNotice } from "@/components/privacy-notice";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://axignal.com"),
  title: {
    default: "AXIGNAL — Qué cambia alrededor de tu empresa, y por qué importa",
    template: "%s · AXIGNAL",
  },
  description:
    "AXIGNAL observa de forma continua las organizaciones que eliges en fuentes públicas, recuerda lo que encuentra y te muestra qué cambia y por qué importa, con su fuente y su fecha.",
  icons: { icon: "/brand/favicon.svg", apple: "/brand/apple-touch-icon.png" },
  openGraph: {
    title: "AXIGNAL — Qué cambia alrededor de tu empresa, y por qué importa",
    description: "Observación económica continua, con memoria y evidencia.",
    images: ["/brand/og-image-1200x630.png"],
  },
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es" data-scroll-behavior="smooth">
      <body>
        <LocaleProvider>
          <a className="skip-link" href="#main">
            Ir al contenido / Skip to content
          </a>
          {children}
          <PrivacyNotice />
        </LocaleProvider>
      </body>
    </html>
  );
}
