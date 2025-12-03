"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import { useLanguage } from "@/lib/i18n";

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { language, setLanguage, t } = useLanguage();

  const navLinks = [
    { href: "/#features", label: t("nav.features") },
    { href: "/#roadmap", label: t("nav.roadmap") },
    { href: "/#installation", label: t("nav.installation") },
    { href: "/docs", label: t("nav.docs") },
    { href: "/faq", label: "FAQ" },
  ];

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close menu on Escape key
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape" && isMobileMenuOpen) {
      setIsMobileMenuOpen(false);
    }
  }, [isMobileMenuOpen]);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  const toggleLanguage = () => {
    setLanguage(language === "en" ? "fr" : "en");
  };

  return (
    <header
      role="banner"
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 w-full ${
        isScrolled || isMobileMenuOpen
          ? "bg-dark-900/95 backdrop-blur-lg shadow-lg shadow-rose-500/5"
          : "bg-transparent"
      }`}
    >
      <nav aria-label="Main navigation" className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center space-x-2 sm:space-x-3 group focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg flex-shrink-0"
            aria-label="ROSE Link - Home"
          >
            <Image
              src="/Logo-250X178.webp"
              alt=""
              width={250}
              height={178}
              className="w-12 h-auto sm:w-14 rounded-xl shadow-lg group-hover:shadow-rose-500/30 transition-shadow flex-shrink-0"
              priority
              fetchPriority="high"
            />
            <span className="text-xl sm:text-2xl font-bold relative">
              <span className="text-white">ROSE</span>
              <span className="text-rose-500"> Link</span>
              <span
                className="absolute -top-0.5 -right-3 w-2 h-2 sm:w-2.5 sm:h-2.5 bg-green-500 rounded-full"
                aria-hidden="true"
              />
            </span>
          </Link>

          {/* Desktop Navigation */}
          <ul className="hidden md:flex items-center space-x-8" role="list">
            {navLinks.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className="text-dark-300 hover:text-white transition-colors relative group focus:outline-none focus:text-white focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded px-2 py-1"
                >
                  {link.label}
                  <span
                    className="absolute -bottom-1 left-0 w-0 h-0.5 bg-rose-500 group-hover:w-full group-focus:w-full transition-all duration-300"
                    aria-hidden="true"
                  />
                </Link>
              </li>
            ))}
          </ul>

          {/* CTA Buttons */}
          <div className="hidden md:flex items-center space-x-4">
            {/* Language Switcher */}
            <button
              onClick={toggleLanguage}
              className="flex items-center space-x-1 px-3 py-1.5 text-dark-300 hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg border border-dark-700 hover:border-dark-600"
              aria-label={language === "en" ? "Switch to French" : "Passer en anglais"}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
              <span className="text-sm font-medium">{language === "en" ? "FR" : "EN"}</span>
            </button>
            <Link
              href="https://github.com/oussrh/ROSE-LINK"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 text-dark-300 hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg px-2 py-1"
              aria-label="View ROSE Link on GitHub (opens in new tab)"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path
                  fillRule="evenodd"
                  clipRule="evenodd"
                  d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.87 8.17 6.84 9.5.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.87 1.52 2.34 1.07 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.92 0-1.11.38-2 1.03-2.71-.1-.25-.45-1.29.1-2.64 0 0 .84-.27 2.75 1.02.79-.22 1.65-.33 2.5-.33.85 0 1.71.11 2.5.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.35.2 2.39.1 2.64.65.71 1.03 1.6 1.03 2.71 0 3.82-2.34 4.66-4.57 4.91.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0012 2z"
                />
              </svg>
              <span>{t("nav.github")}</span>
            </Link>
            <a
              href="https://www.paypal.com/donate/?business=SZ5DMA65UBCP2&no_recurring=0&currency_code=EUR"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-lg font-medium transition-all shadow-lg shadow-rose-500/25 hover:shadow-rose-500/40 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-900"
              aria-label="Support ROSE Link via PayPal (opens in new tab)"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
              <span>{t("nav.support")}</span>
            </a>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 text-dark-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:ring-offset-dark-900 rounded-lg"
            aria-expanded={isMobileMenuOpen}
            aria-controls="mobile-menu"
            aria-label={isMobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              {isMobileMenuOpen ? (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              ) : (
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div
            id="mobile-menu"
            className="md:hidden py-4 border-t border-dark-800 bg-dark-900"
            role="menu"
            aria-label="Mobile navigation"
          >
            <ul className="flex flex-col space-y-4" role="list">
              {navLinks.map((link) => (
                <li key={link.href} role="none">
                  <Link
                    href={link.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="text-dark-300 hover:text-white transition-colors px-4 py-2 block focus:outline-none focus:bg-dark-800 focus:text-white rounded-lg"
                    role="menuitem"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
            <div className="flex flex-col space-y-2 px-4 pt-4 border-t border-dark-800 mt-4">
              {/* Mobile Language Switcher */}
              <button
                onClick={toggleLanguage}
                className="flex items-center justify-center space-x-2 py-2.5 border border-dark-700 rounded-lg text-dark-300 hover:text-white hover:border-dark-600 transition-all focus:outline-none focus:ring-2 focus:ring-rose-500"
                aria-label={language === "en" ? "Switch to French" : "Passer en anglais"}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                </svg>
                <span className="font-medium">{language === "en" ? "Français" : "English"}</span>
              </button>
              <Link
                href="https://github.com/oussrh/ROSE-LINK"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center space-x-2 py-2.5 border border-dark-700 rounded-lg text-dark-300 hover:text-white hover:border-dark-600 transition-all focus:outline-none focus:ring-2 focus:ring-rose-500"
                aria-label={t("nav.github.aria")}
              >
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
                <span>{t("nav.github")}</span>
              </Link>
              <a
                href="https://www.paypal.com/donate/?business=SZ5DMA65UBCP2&no_recurring=0&currency_code=EUR"
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => setIsMobileMenuOpen(false)}
                className="flex items-center justify-center space-x-2 py-2.5 bg-gradient-to-r from-rose-500 to-rose-600 text-white rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2"
                aria-label={t("nav.support.aria")}
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
                <span>{t("nav.support")}</span>
              </a>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
