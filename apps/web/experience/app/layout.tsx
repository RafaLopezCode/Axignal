import type { Metadata } from "next";
import "./globals.css";
import { LocaleProvider } from "@/lib/locale";

export const metadata: Metadata = {
  metadataBase: new URL("http://127.0.0.1:3810"),
  title: {
    default: "AXIGNAL — Una mirada que conecta",
    template: "%s · AXIGNAL",
  },
  description:
    "Observa el mundo económico. Entiende qué cambia, por qué importa y qué lo sostiene.",
  icons: { icon: "/brand/favicon.svg", apple: "/brand/apple-touch-icon.png" },
  openGraph: {
    title: "AXIGNAL — Una mirada que conecta",
    description: "El contexto se acumula. La comprensión también.",
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
        </LocaleProvider>
      </body>
    </html>
  );
}
