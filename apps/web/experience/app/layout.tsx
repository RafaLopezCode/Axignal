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
    default: "AXIGNAL — What is changing around your company, and why does it matter?",
    template: "%s · AXIGNAL",
  },
  description:
    "AXIGNAL continuously observes the organizations you choose in public sources, remembers what it finds, and shows you what changes and why it matters — with source and date.",
  icons: { icon: "/brand/favicon.svg", apple: "/brand/apple-touch-icon.png" },
  openGraph: {
    title: "AXIGNAL — What is changing around your company, and why does it matter?",
    description: "Continuous economic observation, with memory and evidence.",
    images: ["/brand/og-image-1200x630.png"],
  },
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
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
