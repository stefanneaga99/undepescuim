import type { Metadata, Viewport } from "next";
import { ThemeProvider } from "next-themes";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ServiceWorkerRegister } from "@/components/pwa/ServiceWorkerRegister";
import { I18nProvider } from "@/i18n/provider";
import { siteUrl } from "@/lib/site-url";
import { siteMetadata } from "@/lib/site-metadata";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = siteMetadata;

// Android/Chromium status-bar color (matches the manifest theme_color).
export const viewport: Viewport = {
  themeColor: "#171717",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  colorScheme: "light dark",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="ro"
      // suppressHydrationWarning is REQUIRED with next-themes: it mutates
      // <html class> on the client before hydration (attribute="class"),
      // so the server-rendered class can legitimately differ.
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col overscroll-none">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "WebSite",
              name: "UndePescuim.ro",
              description: "Harta apelor de pescuit contractate din România",
              url: siteUrl("/"),
            }),
          }}
        />
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {/* t_920a7b7b: i18n context — per-locale strings + the header
              switcher. RO is the SSR default; persisted/browser locale is
              applied client-side (no hydration mismatch). */}
          <I18nProvider>{children}</I18nProvider>
        </ThemeProvider>
        {/* F6 PWA light: register the Serwist SW (prod builds only — dev has
            no cache tier and a stray SW would confuse HMR). */}
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
