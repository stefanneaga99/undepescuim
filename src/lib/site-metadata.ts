import type { Metadata } from "next";
import { siteUrl, SITE_URL } from "@/lib/site-url";

export const siteMetadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "UndePescuim.ro",
  description: "Harta apelor de pescuit contractate din România — contracted fishing waters in Romania",
  alternates: { canonical: "/" },
  openGraph: {
    title: "UndePescuim.ro",
    description: "Harta apelor de pescuit contractate din România",
    url: siteUrl("/"),
    siteName: "UndePescuim.ro",
    locale: "ro_RO",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "UndePescuim.ro",
    description: "Harta apelor de pescuit contractate din România",
  },
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "UndePescuim",
  },
  icons: {
    apple: [
      {
        url: "/icons/apple-touch-icon-180x180.png",
        sizes: "180x180",
        type: "image/png",
      },
    ],
  },
};
