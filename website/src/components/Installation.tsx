"use client";

import { useEffect, useRef, useState } from "react";
import { useLanguage } from "@/lib/i18n";

const stepKeys = [
  { number: "01", key: "step1", code: null },
  { number: "02", key: "step2", code: "curl -sSL https://oussrh.github.io/ROSE-LINK/install.sh | sudo bash\nsudo apt install rose-link" },
  { number: "03", key: "step3", code: null },
  { number: "04", key: "step4", code: null },
];

const requirementIcons = ["🍓", "💾", "📡", "🔌", "🔐"];

export default function Installation() {
  const [visible, setVisible] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
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
    return () => observer.disconnect();
  }, []);

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <section id="installation" ref={sectionRef} className="py-24 relative overflow-hidden" aria-labelledby="installation-heading">
      <div className="absolute inset-0 bg-gradient-to-b from-dark-900 via-dark-950 to-dark-900" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className={`text-center mb-16 transition-all duration-700 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
          <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-green-500/10 text-green-500 border border-green-500/20 mb-4">
            {t("install.badge")}
          </span>
          <h2 id="installation-heading" className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="text-white">{t("install.title1")}</span>{" "}
            <span className="gradient-text">{t("install.title2")}</span>
          </h2>
          <p className="text-lg text-dark-400 max-w-2xl mx-auto">
            {t("install.subtitle")}
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-start">
          {/* Installation Steps */}
          <div className="space-y-6 order-2 lg:order-1">
            {stepKeys.map((step, index) => (
              <div
                key={index}
                className={`flex gap-4 transition-all duration-500 ${
                  visible ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-8"
                }`}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-rose-500 to-rose-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-rose-500/25">
                    {step.number}
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-white mb-1">{t(`install.${step.key}.title`)}</h3>
                  <p className="text-dark-400 text-sm mb-3">{t(`install.${step.key}.desc`)}</p>
                  {step.code && (
                    <div className="relative group">
                      <pre className="bg-dark-800 border border-dark-700 rounded-lg p-3 sm:p-4 text-xs sm:text-sm overflow-x-auto">
                        <code className="text-green-400 whitespace-pre-wrap break-words">{step.code}</code>
                      </pre>
                      <button
                        onClick={() => copyToClipboard(step.code!, index)}
                        className="absolute top-2 right-2 p-2 rounded-md bg-dark-700 hover:bg-dark-600 text-dark-300 hover:text-white transition-all opacity-0 group-hover:opacity-100 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-rose-500"
                        aria-label={copiedIndex === index ? "Copied to clipboard" : "Copy command to clipboard"}
                      >
                        {copiedIndex === index ? (
                          <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Requirements Card */}
          <div className={`transition-all duration-700 delay-300 ${visible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-8"}`}>
            <div className="glass rounded-2xl p-6 sm:p-8 lg:sticky lg:top-24">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <svg className="w-6 h-6 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                {t("install.requirements")}
              </h3>
              <ul className="space-y-4">
                {requirementIcons.map((icon, index) => (
                  <li key={index} className="flex items-center gap-3 text-dark-300">
                    <span className="text-xl">{icon}</span>
                    <span>{t(`install.req${index + 1}`)}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-8 pt-6 border-t border-dark-700">
                <h4 className="text-sm font-medium text-dark-400 mb-3">{t("install.supportedOs")}</h4>
                <div className="flex flex-wrap gap-2">
                  {["Raspberry Pi OS", "Debian 11", "Debian 12", "Debian 13"].map((os) => (
                    <span key={os} className="px-3 py-1 bg-dark-800 rounded-full text-sm text-dark-300">
                      {os}
                    </span>
                  ))}
                </div>
              </div>

              <a
                href="https://github.com/oussrh/ROSE-LINK#quick-start"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-6 w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-lg font-medium transition-all shadow-lg shadow-rose-500/25 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-950"
                aria-label="View full installation guide on GitHub (opens in new tab)"
              >
                {t("install.fullGuide")}
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            </div>
          </div>
        </div>

        {/* Alternative Install Methods */}
        <div className={`mt-16 transition-all duration-700 delay-500 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
          <h3 className="text-xl font-semibold text-white mb-6 text-center">
            {t("install.alternative")}
          </h3>
          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { key: "apt", command: "apt install rose-link", icon: "📦" },
              { key: "deb", command: "dpkg -i rose-link.deb", icon: "🗃️" },
              { key: "source", command: "make install", icon: "🔧" },
            ].map((item, index) => (
              <div key={index} className="glass rounded-xl p-4 text-center card-hover">
                <span className="text-2xl mb-2 block">{item.icon}</span>
                <h4 className="font-semibold text-white mb-1">{t(`install.${item.key}`)}</h4>
                <code className="text-xs text-rose-400 bg-dark-800 px-2 py-1 rounded">
                  {item.command}
                </code>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
