"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/lib/i18n";
import { VERSION, GITHUB_VERSION_URL } from "@/lib/version";

export default function Hero() {
  const [mounted, setMounted] = useState(false);
  const [version, setVersion] = useState<string>(VERSION);
  const { t, language: lang } = useLanguage();

  useEffect(() => {
    // Use requestIdleCallback for non-critical animations
    if ("requestIdleCallback" in window) {
      requestIdleCallback(() => setMounted(true));
    } else {
      setTimeout(() => setMounted(true), 1);
    }

    // Fetch latest version from GitHub
    const fetchVersion = async () => {
      try {
        const response = await fetch(GITHUB_VERSION_URL);
        if (response.ok) {
          const text = await response.text();
          setVersion(text.trim());
        }
      } catch {
        // Use fallback VERSION
      }
    };
    fetchVersion();
  }, []);

  return (
    <section
      aria-labelledby="hero-heading"
      className="relative min-h-screen flex items-center justify-center overflow-hidden bg-grid"
    >
      {/* Background Effects - simplified for performance */}
      <div className="absolute inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute top-1/4 left-1/4 w-64 sm:w-96 h-64 sm:h-96 bg-rose-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-64 sm:w-96 h-64 sm:h-96 bg-rose-700/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] sm:w-[800px] h-[400px] sm:h-[800px] bg-gradient-radial from-rose-500/5 to-transparent" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-32">
        <div className="text-center">
          {/* Badge */}
          <div
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full glass mb-8 transition-all duration-700 ${
              mounted
                ? "opacity-100 translate-y-0"
                : "opacity-0 -translate-y-4"
            }`}
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
            </span>
            <span className="text-sm text-dark-300">
              {lang === "fr"
                ? `Version ${version} - Support appareil WiFi unique`
                : `Version ${version} - Single WiFi Device Support`}
            </span>
          </div>

          {/* Main Heading */}
          <h1
            id="hero-heading"
            className={`text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6 transition-all duration-700 delay-100 ${
              mounted
                ? "opacity-100 translate-y-0"
                : "opacity-0 translate-y-4"
            }`}
          >
            <span className="text-white">{t("hero.title1")}</span>
            <br />
            <span className="gradient-text">{t("hero.title2")}</span>
            <br />
            <span className="text-white">{t("hero.title3")}</span>{" "}
            <span className="text-rose-500">Raspberry Pi</span>
          </h1>

          {/* Subtitle */}
          <p
            className={`text-lg sm:text-xl text-dark-300 max-w-3xl mx-auto mb-10 transition-all duration-700 delay-200 ${
              mounted
                ? "opacity-100 translate-y-0"
                : "opacity-0 translate-y-4"
            }`}
          >
            {t("hero.subtitle")}
          </p>

          {/* CTA Buttons */}
          <div
            className={`flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 transition-all duration-700 delay-300 ${
              mounted
                ? "opacity-100 translate-y-0"
                : "opacity-0 translate-y-4"
            }`}
          >
            <Link
              href="#installation"
              className="group relative px-8 py-4 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-xl font-semibold text-lg transition-all shadow-xl shadow-rose-500/25 hover:shadow-rose-500/40 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-950"
              aria-label={t("hero.quickInstall")}
            >
              <span className="flex items-center space-x-2">
                <span>{t("hero.quickInstall")}</span>
                <svg
                  className="w-5 h-5 group-hover:translate-x-1 transition-transform"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </svg>
              </span>
            </Link>
            <Link
              href="https://github.com/oussrh/ROSE-LINK"
              target="_blank"
              rel="noopener noreferrer"
              className="group px-8 py-4 border border-dark-700 hover:border-rose-500/50 text-white rounded-xl font-semibold text-lg transition-all hover:bg-dark-800/50 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-950"
              aria-label={t("nav.github.aria")}
            >
              <span className="flex items-center space-x-2">
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z"
                  />
                </svg>
                <span>{t("hero.viewGithub")}</span>
              </span>
            </Link>
          </div>

          {/* Stats */}
          <div
            className={`grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto transition-all duration-700 delay-400 ${
              mounted
                ? "opacity-100 translate-y-0"
                : "opacity-0 translate-y-4"
            }`}
          >
            {[
              { value: "100%", label: t("hero.stat1") },
              { value: "2 VPNs", label: t("hero.stat2") },
              { value: "< 5min", label: t("hero.stat3") },
              { value: "8+ Pi", label: t("hero.stat4") },
            ].map((stat, index) => (
              <div
                key={index}
                className="glass rounded-xl p-4 card-hover"
              >
                <div className="text-2xl sm:text-3xl font-bold text-rose-500">
                  {stat.value}
                </div>
                <div className="text-sm text-dark-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Scroll Indicator */}
        <div
          className={`absolute bottom-8 left-1/2 -translate-x-1/2 transition-all duration-700 delay-500 ${
            mounted ? "opacity-100" : "opacity-0"
          }`}
        >
          <div className="flex flex-col items-center text-dark-400">
            <span className="text-sm mb-2">{t("hero.scroll")}</span>
            <div className="w-6 h-10 border-2 border-dark-600 rounded-full flex justify-center">
              <div className="w-1.5 h-3 bg-rose-500 rounded-full mt-2 animate-bounce" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
