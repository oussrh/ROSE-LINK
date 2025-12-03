"use client";

import Link from "next/link";
import Image from "next/image";
import { useLanguage } from "@/lib/i18n";
import VersionBadge from "./VersionBadge";

const footerLinks = {
  product: [
    { key: "nav.features", href: "#features" },
    { key: "nav.roadmap", href: "#roadmap" },
    { key: "nav.installation", href: "#installation" },
    { key: "nav.docs", href: "#docs" },
  ],
  resources: [
    { key: "docs.quickstart", href: "https://github.com/oussrh/ROSE-LINK/blob/main/QUICKSTART.md", external: true },
    { key: "docs.features", href: "https://github.com/oussrh/ROSE-LINK/blob/main/PRODUCT_FEATURES.md", external: true },
    { key: "docs.changelog", href: "https://github.com/oussrh/ROSE-LINK/blob/main/CHANGELOG.md", external: true },
    { key: "footer.contributing", href: "https://github.com/oussrh/ROSE-LINK/blob/main/CONTRIBUTING.md", external: true },
  ],
  community: [
    { key: "nav.github", href: "https://github.com/oussrh/ROSE-LINK", external: true },
    { key: "footer.issues", href: "https://github.com/oussrh/ROSE-LINK/issues", external: true },
    { key: "footer.discussions", href: "https://github.com/oussrh/ROSE-LINK/discussions", external: true },
    { key: "footer.coc", href: "https://github.com/oussrh/ROSE-LINK/blob/main/CODE_OF_CONDUCT.md", external: true },
  ],
};

export default function Footer() {
  const currentYear = new Date().getFullYear();
  const { t } = useLanguage();

  return (
    <footer role="contentinfo" className="relative bg-dark-950 border-t border-dark-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12">
          {/* Brand */}
          <div className="lg:col-span-2">
            <Link
              href="/"
              className="flex items-center space-x-3 mb-4 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-950 rounded-lg w-fit"
              aria-label="ROSE Link - Home"
            >
              <Image
                src="/Logo-250X178.webp"
                alt=""
                width={250}
                height={178}
                className="w-11 h-auto rounded-xl shadow-lg"
                loading="lazy"
              />
              <span className="text-xl font-bold">
                <span className="text-white">ROSE</span>
                <span className="text-rose-500"> Link</span>
              </span>
            </Link>
            <p className="text-dark-400 mb-6 max-w-sm">
              {t("footer.description")}
            </p>
            <div className="flex items-center space-x-3">
              <a
                href="https://github.com/oussrh/ROSE-LINK"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg bg-dark-800 hover:bg-dark-700 text-dark-400 hover:text-white transition-all focus:outline-none focus:ring-2 focus:ring-rose-500"
                aria-label="Visit ROSE Link on GitHub (opens in new tab)"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z"/>
                </svg>
              </a>
              <a
                href="https://www.paypal.com/donate/?business=SZ5DMA65UBCP2&no_recurring=0&currency_code=EUR"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-lg text-sm font-medium transition-all shadow-lg shadow-rose-500/25 hover:shadow-rose-500/40 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-950"
                aria-label={t("nav.support.aria")}
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
                <span>{t("nav.support")}</span>
              </a>
            </div>
          </div>

          {/* Product */}
          <nav aria-labelledby="footer-product-heading">
            <h2 id="footer-product-heading" className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
              {t("footer.product")}
            </h2>
            <ul className="space-y-3" role="list">
              {footerLinks.product.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-dark-400 hover:text-white transition-colors focus:outline-none focus:text-white focus:underline"
                  >
                    {t(link.key)}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* Resources */}
          <nav aria-labelledby="footer-resources-heading">
            <h2 id="footer-resources-heading" className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
              {t("footer.resources")}
            </h2>
            <ul className="space-y-3" role="list">
              {footerLinks.resources.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-dark-400 hover:text-white transition-colors inline-flex items-center gap-1 focus:outline-none focus:text-white focus:underline"
                  >
                    {t(link.key)}
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    <span className="sr-only">(opens in new tab)</span>
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          {/* Community */}
          <nav aria-labelledby="footer-community-heading">
            <h2 id="footer-community-heading" className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
              {t("footer.community")}
            </h2>
            <ul className="space-y-3" role="list">
              {footerLinks.community.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-dark-400 hover:text-white transition-colors inline-flex items-center gap-1 focus:outline-none focus:text-white focus:underline"
                  >
                    {t(link.key)}
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    <span className="sr-only">(opens in new tab)</span>
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-dark-800">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-dark-300 text-sm">
              <span aria-label={`Copyright ${currentYear}`}>&copy;</span> {currentYear} {t("footer.copyright")}{" "}
              <a
                href="https://opensource.org/licenses/MIT"
                target="_blank"
                rel="noopener noreferrer"
                className="text-dark-300 hover:text-white focus:text-white focus:underline"
              >
                {t("footer.license")}
                <span className="sr-only">(opens in new tab)</span>
              </a>
              .
            </p>
            <div className="flex items-center gap-6 text-sm text-dark-300">
              <span className="flex items-center gap-2">
                {t("footer.madeWith")}
                <svg
                  className="w-4 h-4 text-rose-500"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-label="love"
                  role="img"
                >
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
                {t("footer.forPrivacy")}
              </span>
              <span className="hidden sm:inline" aria-hidden="true">|</span>
              <span>Raspberry Pi</span>
              <span className="hidden sm:inline" aria-hidden="true">|</span>
              <VersionBadge />
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
