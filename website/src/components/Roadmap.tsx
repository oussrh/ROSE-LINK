"use client";

import { useEffect, useRef, useState, ReactNode } from "react";
import { useLanguage } from "@/lib/i18n";
import { VERSION, GITHUB_VERSION_URL } from "@/lib/version";

const sectionKeys = [
  { key: "e2e", color: "rose", itemCount: 3, icon: "clipboard" },
  { key: "observability", color: "blue", itemCount: 4, icon: "bolt" },
  { key: "performance", color: "green", itemCount: 3, icon: "chart" },
  { key: "security", color: "purple", itemCount: 3, icon: "shield" },
];

const featureKeys = [
  { key: "wired", priority: "high", icon: "cable" },
  { key: "email", priority: "high", icon: "mail" },
  { key: "updates", priority: "high", icon: "refresh" },
  { key: "qos", priority: "medium", icon: "game" },
  { key: "syslog", priority: "medium", icon: "log" },
  { key: "charts", priority: "low", icon: "chart" },
  { key: "doh", priority: "low", icon: "lock" },
];

const uiKeys = ["wizard", "errors", "mobile", "settings"];

const icons: Record<string, ReactNode> = {
  clipboard: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
    </svg>
  ),
  chart: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  bolt: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  shield: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
};

const featureIcons: Record<string, string> = {
  cable: "🔌",
  mail: "📧",
  refresh: "🔄",
  game: "🎮",
  log: "📋",
  chart: "📊",
  lock: "🔐",
};

const colorMap: Record<string, { bg: string; text: string; border: string }> = {
  rose: { bg: "bg-rose-500/10", text: "text-rose-500", border: "border-rose-500/30" },
  blue: { bg: "bg-blue-500/10", text: "text-blue-500", border: "border-blue-500/30" },
  green: { bg: "bg-green-500/10", text: "text-green-500", border: "border-green-500/30" },
  purple: { bg: "bg-purple-500/10", text: "text-purple-500", border: "border-purple-500/30" },
};

export default function Roadmap() {
  const [visible, setVisible] = useState(false);
  const [version, setVersion] = useState<string>(VERSION);
  const sectionRef = useRef<HTMLElement>(null);
  const { t } = useLanguage();

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setVisible(true);
      },
      { threshold: 0.1 }
    );

    if (sectionRef.current) observer.observe(sectionRef.current);

    // Fetch latest version
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

    return () => observer.disconnect();
  }, []);

  return (
    <section id="roadmap" ref={sectionRef} className="py-24 relative bg-dark-900" aria-labelledby="roadmap-heading">
      <div className="absolute inset-0 bg-grid opacity-50" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className={`text-center mb-16 transition-all duration-700 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
          <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-rose-500/10 text-rose-500 border border-rose-500/20 mb-4">
            v{version}
          </span>
          <h2 id="roadmap-heading" className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="text-white">{t("roadmap.title1")}</span>{" "}
            <span className="gradient-text">{t("roadmap.title2")}</span>
          </h2>
          <p className="text-lg text-dark-400 max-w-2xl mx-auto">
            {t("roadmap.subtitle")}
          </p>
        </div>

        {/* Priority Improvements Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
          {sectionKeys.map((section, index) => {
            const colors = colorMap[section.color];
            return (
              <div
                key={index}
                className={`glass rounded-2xl p-6 transition-all duration-500 ${
                  visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
                }`}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className={`p-2 rounded-lg ${colors.bg} ${colors.text}`}>
                    {icons[section.icon]}
                  </div>
                  <h3 className="text-xl font-semibold text-white">{t(`roadmap.${section.key}.title`)}</h3>
                </div>
                <ul className="space-y-2">
                  {Array.from({ length: section.itemCount }, (_, itemIndex) => (
                    <li key={itemIndex} className="flex items-start gap-2 text-dark-300">
                      <svg className={`w-5 h-5 mt-0.5 flex-shrink-0 ${colors.text}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
                      </svg>
                      <span>{t(`roadmap.${section.key}.item${itemIndex + 1}`)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>

        {/* Upcoming Features */}
        <div className={`mb-16 transition-all duration-700 delay-300 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
          <h3 className="text-2xl font-bold text-white mb-6 text-center">
            {t("roadmap.upcoming")}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {featureKeys.map((item, index) => (
              <div
                key={index}
                className="glass rounded-xl p-4 flex items-start gap-4 card-hover"
              >
                <span className="text-2xl">{featureIcons[item.icon]}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold text-white">{t(`roadmap.feature.${item.key}`)}</h4>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        item.priority === "high"
                          ? "bg-rose-500/20 text-rose-400"
                          : item.priority === "medium"
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-blue-500/20 text-blue-400"
                      }`}
                    >
                      {t(`roadmap.priority.${item.priority}`)}
                    </span>
                  </div>
                  <p className="text-sm text-dark-400">{t(`roadmap.feature.${item.key}.desc`)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* UI/UX Improvements */}
        <div className={`transition-all duration-700 delay-500 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
          <h3 className="text-2xl font-bold text-white mb-6 text-center">
            {t("roadmap.ui")}
          </h3>
          <div className="flex flex-wrap justify-center gap-4">
            {uiKeys.map((key, index) => (
              <div
                key={index}
                className="glass rounded-xl px-6 py-4 text-center card-hover"
              >
                <h4 className="font-semibold text-rose-500 mb-1">{t(`roadmap.ui.${key}`)}</h4>
                <p className="text-sm text-dark-400">{t(`roadmap.ui.${key}.desc`)}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Contribute CTA */}
        <div className={`mt-16 text-center transition-all duration-700 delay-700 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
          <div className="glass rounded-2xl p-8 inline-block">
            <h3 className="text-xl font-bold text-white mb-2">
              {t("roadmap.contribute.title")}
            </h3>
            <p className="text-dark-400 mb-4">
              {t("roadmap.contribute.desc")}
            </p>
            <a
              href="https://github.com/oussrh/ROSE-LINK/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-lg font-medium transition-all shadow-lg shadow-rose-500/25 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-900"
              aria-label="View open issues on GitHub (opens in new tab)"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z"/>
              </svg>
              {t("roadmap.contribute.button")}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
