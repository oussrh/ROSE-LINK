import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { Providers } from "@/components/Providers";
import { VERSION } from "@/lib/version";

const GA_MEASUREMENT_ID = "G-KTCQJT57YS";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
  preload: true,
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f43f5e" },
    { media: "(prefers-color-scheme: dark)", color: "#f43f5e" },
  ],
  colorScheme: "dark",
};

export const metadata: Metadata = {
  metadataBase: new URL("https://rose-link.dev"),
  title: {
    default: "ROSE Link - Home VPN Router + Ad Blocking on Raspberry Pi",
    template: "%s | ROSE Link",
  },
  description:
    "Transform your Raspberry Pi into a professional WiFi access point with VPN routing and network-wide ad blocking. Open source, easy to install, WireGuard & OpenVPN support.",
  keywords: [
    "VPN router",
    "Raspberry Pi",
    "WireGuard",
    "OpenVPN",
    "AdGuard Home",
    "WiFi hotspot",
    "ad blocking",
    "privacy",
    "open source",
    "network security",
    "home router",
    "Pi VPN",
    "DNS filtering",
    "kill switch",
  ],
  authors: [{ name: "ROSE Link Team", url: "https://github.com/oussrh" }],
  creator: "ROSE Link Team",
  publisher: "ROSE Link",
  category: "Technology",
  icons: {
    icon: [
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/icon.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
    other: [
      { rel: "icon", url: "/android-chrome-192x192.png", sizes: "192x192" },
      { rel: "icon", url: "/android-chrome-512x512.png", sizes: "512x512" },
    ],
  },
  manifest: "/manifest.json",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://rose-link.dev",
    siteName: "ROSE Link",
    title: "ROSE Link - Home VPN Router + Ad Blocking on Raspberry Pi",
    description:
      "Transform your Raspberry Pi into a professional WiFi access point with VPN routing and network-wide ad blocking. Open source and easy to install.",
    images: [
      {
        url: "/icon.png",
        width: 512,
        height: 512,
        alt: "ROSE Link - VPN Router for Raspberry Pi",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "ROSE Link - Home VPN Router on Raspberry Pi",
    description:
      "Transform your Raspberry Pi into a professional WiFi access point with VPN routing and ad blocking. Open source.",
    images: ["/icon.png"],
    creator: "@roselink",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  alternates: {
    canonical: "https://rose-link.dev",
  },
  other: {
    "apple-mobile-web-app-capable": "yes",
    "apple-mobile-web-app-status-bar-style": "black-translucent",
    "format-detection": "telephone=no",
    "mobile-web-app-capable": "yes",
    "msapplication-TileColor": "#f43f5e",
    "msapplication-tap-highlight": "no",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "ROSE Link",
    applicationCategory: "NetworkApplication",
    operatingSystem: "Raspberry Pi OS, Debian",
    description:
      "Transform your Raspberry Pi into a professional WiFi access point with VPN routing and network-wide ad blocking.",
    url: "https://rose-link.dev",
    downloadUrl: "https://github.com/oussrh/ROSE-LINK",
    softwareVersion: VERSION,
    author: {
      "@type": "Organization",
      name: "ROSE Link Team",
      url: "https://github.com/oussrh",
    },
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
    featureList: [
      "WireGuard VPN support",
      "OpenVPN support",
      "AdGuard Home integration",
      "WiFi hotspot creation",
      "VPN kill switch",
      "Real-time monitoring",
      "Client management",
    ],
    screenshot: "https://rose-link.dev/icon.png",
    license: "https://opensource.org/licenses/MIT",
  };

  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="preconnect" href="https://github.com" />
        <link rel="dns-prefetch" href="https://github.com" />
        <link rel="dns-prefetch" href="https://www.paypal.com" />
        <link rel="dns-prefetch" href="https://www.googletagmanager.com" />
        <meta name="application-name" content="ROSE Link" />
        <meta name="apple-mobile-web-app-title" content="ROSE Link" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body
        className={`${inter.variable} font-sans antialiased bg-dark-950 text-white`}
      >
        <Script
          strategy="afterInteractive"
          src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
        />
        <Script
          id="google-analytics"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', '${GA_MEASUREMENT_ID}');
            `,
          }}
        />
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-rose-500 focus:text-white focus:rounded-lg focus:outline-none"
        >
          Skip to main content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
