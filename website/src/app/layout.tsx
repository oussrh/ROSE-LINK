import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "ROSE Link - Home VPN Router + Ad Blocking on Raspberry Pi",
  description:
    "Transform your Raspberry Pi into a professional WiFi access point with VPN routing and network-wide ad blocking. Open source, easy to install, and fully featured.",
  keywords: [
    "VPN router",
    "Raspberry Pi",
    "WireGuard",
    "OpenVPN",
    "AdGuard",
    "WiFi hotspot",
    "ad blocking",
    "privacy",
    "open source",
  ],
  authors: [{ name: "ROSE Link Team" }],
  openGraph: {
    title: "ROSE Link - Home VPN Router + Ad Blocking on Raspberry Pi",
    description:
      "Transform your Raspberry Pi into a professional WiFi access point with VPN routing and network-wide ad blocking.",
    type: "website",
    locale: "en_US",
    siteName: "ROSE Link",
  },
  twitter: {
    card: "summary_large_image",
    title: "ROSE Link - Home VPN Router on Raspberry Pi",
    description:
      "Transform your Raspberry Pi into a professional WiFi access point with VPN routing and ad blocking.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body
        className={`${inter.variable} font-sans antialiased bg-dark-950 text-white`}
      >
        {children}
      </body>
    </html>
  );
}
