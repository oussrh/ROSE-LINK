"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { useLanguage } from "@/lib/i18n";
import { VERSION, GITHUB_VERSION_URL } from "@/lib/version";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const docSections = [
  {
    key: "getting-started",
    icon: "rocket",
    color: "rose",
    docs: [
      { key: "quickstart", href: "https://github.com/oussrh/ROSE-LINK/blob/main/QUICKSTART.md" },
      { key: "requirements", href: "https://github.com/oussrh/ROSE-LINK/blob/main/README.md#-device-compatibility" },
      { key: "installation", href: "https://github.com/oussrh/ROSE-LINK/blob/main/README.md#-installation" },
    ],
  },
  {
    key: "configuration",
    icon: "settings",
    color: "blue",
    docs: [
      { key: "vpn-setup", href: "https://github.com/oussrh/ROSE-LINK/blob/main/README.md#-vpn" },
      { key: "hotspot", href: "https://github.com/oussrh/ROSE-LINK/blob/main/README.md#-hotspot-configuration" },
      { key: "adguard", href: "https://github.com/oussrh/ROSE-LINK/blob/main/README.md#-adguard-home-integration" },
    ],
  },
  {
    key: "reference",
    icon: "book",
    color: "green",
    docs: [
      { key: "api", href: "https://github.com/oussrh/ROSE-LINK/blob/main/README.md#-api-rest" },
      { key: "features", href: "https://github.com/oussrh/ROSE-LINK/blob/main/PRODUCT_FEATURES.md" },
      { key: "changelog", href: "https://github.com/oussrh/ROSE-LINK/blob/main/CHANGELOG.md" },
    ],
  },
  {
    key: "development",
    icon: "code",
    color: "purple",
    docs: [
      { key: "contributing", href: "https://github.com/oussrh/ROSE-LINK/blob/main/CONTRIBUTING.md" },
      { key: "development", href: "https://github.com/oussrh/ROSE-LINK/blob/main/DEVELOPMENT.md" },
      { key: "security", href: "https://github.com/oussrh/ROSE-LINK/blob/main/SECURITY.md" },
    ],
  },
];

const translations: Record<string, Record<string, Record<string, string>>> = {
  en: {
    page: {
      title: "Documentation",
      subtitle: "Everything you need to get started with ROSE Link and make the most of its features.",
      search: "Search documentation...",
    },
    sections: {
      "getting-started": "Getting Started",
      configuration: "Configuration",
      reference: "Reference",
      development: "Development",
    },
    docs: {
      quickstart: "Quick Start Guide",
      "quickstart-desc": "Get ROSE Link running in under 5 minutes",
      requirements: "Device Compatibility",
      "requirements-desc": "Supported Raspberry Pi models and requirements",
      installation: "Installation Guide",
      "installation-desc": "Detailed installation instructions",
      "vpn-setup": "VPN Setup",
      "vpn-setup-desc": "Configure WireGuard or OpenVPN",
      hotspot: "Hotspot Configuration",
      "hotspot-desc": "WiFi access point settings",
      adguard: "AdGuard Home",
      "adguard-desc": "Network-wide ad blocking setup",
      api: "API Reference",
      "api-desc": "REST API endpoints documentation",
      features: "Product Features",
      "features-desc": "Complete feature list and capabilities",
      changelog: "Changelog",
      "changelog-desc": "Version history and release notes",
      contributing: "Contributing",
      "contributing-desc": "How to contribute to ROSE Link",
      development: "Development Guide",
      "development-desc": "Set up your development environment",
      security: "Security Policy",
      "security-desc": "Security practices and vulnerability reporting",
    },
  },
  fr: {
    page: {
      title: "Documentation",
      subtitle: "Tout ce dont vous avez besoin pour commencer avec ROSE Link et tirer le meilleur parti de ses fonctionnalites.",
      search: "Rechercher dans la documentation...",
    },
    sections: {
      "getting-started": "Demarrage",
      configuration: "Configuration",
      reference: "Reference",
      development: "Developpement",
    },
    docs: {
      quickstart: "Guide de demarrage rapide",
      "quickstart-desc": "Lancez ROSE Link en moins de 5 minutes",
      requirements: "Compatibilite des appareils",
      "requirements-desc": "Modeles Raspberry Pi supportes et prerequis",
      installation: "Guide d'installation",
      "installation-desc": "Instructions d'installation detaillees",
      "vpn-setup": "Configuration VPN",
      "vpn-setup-desc": "Configurer WireGuard ou OpenVPN",
      hotspot: "Configuration du Hotspot",
      "hotspot-desc": "Parametres du point d'acces WiFi",
      adguard: "AdGuard Home",
      "adguard-desc": "Configuration du blocage des pubs",
      api: "Reference API",
      "api-desc": "Documentation des endpoints REST",
      features: "Fonctionnalites",
      "features-desc": "Liste complete des fonctionnalites",
      changelog: "Journal des modifications",
      "changelog-desc": "Historique des versions",
      contributing: "Contribuer",
      "contributing-desc": "Comment contribuer a ROSE Link",
      development: "Guide de developpement",
      "development-desc": "Configurer votre environnement de dev",
      security: "Politique de securite",
      "security-desc": "Pratiques de securite et signalement",
    },
  },
};

const colorClasses: Record<string, { bg: string; text: string; border: string }> = {
  rose: { bg: "bg-rose-500/10", text: "text-rose-500", border: "border-rose-500/30" },
  blue: { bg: "bg-blue-500/10", text: "text-blue-500", border: "border-blue-500/30" },
  green: { bg: "bg-green-500/10", text: "text-green-500", border: "border-green-500/30" },
  purple: { bg: "bg-purple-500/10", text: "text-purple-500", border: "border-purple-500/30" },
};

const icons: Record<string, ReactNode> = {
  rocket: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  settings: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  book: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
    </svg>
  ),
  code: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
    </svg>
  ),
};

export default function DocsPage() {
  const [version, setVersion] = useState<string>(VERSION);
  const { language } = useLanguage();
  const t = translations[language] || translations.en;

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await fetch(GITHUB_VERSION_URL);
        if (response.ok) {
          const text = await response.text();
          setVersion(text.trim());
        }
      } catch {
        // Use fallback
      }
    };
    fetchVersion();
  }, []);

  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-dark-950 pt-24 pb-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-16">
            <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-rose-500/10 text-rose-500 border border-rose-500/20 mb-4">
              v{version}
            </span>
            <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
              {t.page.title}
            </h1>
            <p className="text-lg text-dark-400 max-w-2xl mx-auto">
              {t.page.subtitle}
            </p>
          </div>

          {/* Documentation Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {docSections.map((section) => {
              const colors = colorClasses[section.color];
              return (
                <div key={section.key} className="glass rounded-2xl p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <div className={`p-2 rounded-lg ${colors.bg} ${colors.text}`}>
                      {icons[section.icon]}
                    </div>
                    <h2 className="text-xl font-semibold text-white">
                      {t.sections[section.key]}
                    </h2>
                  </div>
                  <div className="space-y-4">
                    {section.docs.map((doc) => (
                      <a
                        key={doc.key}
                        href={doc.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`block p-4 rounded-xl border ${colors.border} hover:bg-dark-800/50 transition-all group`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium text-white group-hover:text-rose-400 transition-colors">
                              {t.docs[doc.key]}
                            </h3>
                            <p className="text-sm text-dark-400 mt-1">
                              {t.docs[`${doc.key}-desc`]}
                            </p>
                          </div>
                          <svg className="w-5 h-5 text-dark-500 group-hover:text-rose-400 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Help Section */}
          <div className="mt-16 text-center">
            <div className="glass rounded-2xl p-8 inline-block">
              <h3 className="text-xl font-bold text-white mb-2">
                {language === "fr" ? "Besoin d'aide ?" : "Need Help?"}
              </h3>
              <p className="text-dark-400 mb-4">
                {language === "fr"
                  ? "Consultez notre FAQ ou ouvrez une issue sur GitHub."
                  : "Check our FAQ or open an issue on GitHub."}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/faq"
                  className="px-6 py-3 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-lg font-medium transition-all"
                >
                  {language === "fr" ? "Voir la FAQ" : "View FAQ"}
                </Link>
                <a
                  href="https://github.com/oussrh/ROSE-LINK/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-3 border border-dark-700 hover:border-rose-500/50 text-white rounded-lg font-medium transition-all"
                >
                  {language === "fr" ? "Ouvrir une Issue" : "Open Issue"}
                </a>
              </div>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
