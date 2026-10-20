import type { Metadata } from "next";
import { LocaleProvider } from "@/lib/locale";
import { SurfaceStyles } from "@/components/surface-styles";
import { PrivacyNotice } from "@/components/privacy-notice";
import { siteIcons } from "@/lib/site-icons";

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "https://axignal.com",
  ),
  title: {
    default: "AXIGNAL — What changes around your company, and why it matters",
    template: "%s · AXIGNAL",
  },
  description:
    "Business and economic intelligence from public evidence: AXIGNAL observes the organizations you choose and shows what changes, with source and date.",
  icons: siteIcons,
  openGraph: {
    title: "AXIGNAL — What changes around your company, and why it matters",
    description: "Continuous economic observation, with memory and evidence.",
    images: ["/brand/og-image-1200x630.png"],
  },
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <head>
        <SurfaceStyles />
      </head>
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
