import type { Metadata } from "next";
import { LocaleProvider } from "@/lib/locale";
import { SurfaceStyles } from "@/components/surface-styles";
import { PrivacyNotice } from "@/components/privacy-notice";
import { siteIcons } from "@/lib/site-icons";
import { HOME_METADATA } from "@/lib/public-home-metadata";
import { publicSocialMetadata } from "@/lib/site-seo";

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "https://axignal.com",
  ),
  title: {
    default: HOME_METADATA.en.title,
    template: "%s · AXIGNAL",
  },
  description: HOME_METADATA.en.description,
  icons: siteIcons,
  ...publicSocialMetadata({ ...HOME_METADATA.en, path: "/", locale: "en" }),
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
