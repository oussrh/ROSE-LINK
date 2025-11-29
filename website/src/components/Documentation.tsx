"use client";

import { useEffect, useRef, useState } from "react";

const docs = [
  {
    title: "Quick Start Guide",
    description: "Get ROSE Link running on your Raspberry Pi in under 5 minutes.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    href: "https://github.com/ROSE-Link/ROSE-LINK/blob/main/QUICKSTART.md",
    color: "green",
  },
  {
    title: "API Documentation",
    description: "Complete REST API reference with Swagger UI and examples.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
      </svg>
    ),
    href: "https://github.com/ROSE-Link/ROSE-LINK/blob/main/backend/README.md",
    color: "blue",
  },
  {
    title: "Development Guide",
    description: "Set up your development environment and contribute to ROSE Link.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
    href: "https://github.com/ROSE-Link/ROSE-LINK/blob/main/DEVELOPMENT.md",
    color: "purple",
  },
  {
    title: "Security Policy",
    description: "Learn about our security practices and how to report vulnerabilities.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    href: "https://github.com/ROSE-Link/ROSE-LINK/blob/main/SECURITY.md",
    color: "rose",
  },
  {
    title: "Changelog",
    description: "See what's new in each version of ROSE Link.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
    href: "https://github.com/ROSE-Link/ROSE-LINK/blob/main/CHANGELOG.md",
    color: "amber",
  },
  {
    title: "Accessibility",
    description: "WCAG 2.1 AA compliance and accessibility features.",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </svg>
    ),
    href: "https://github.com/ROSE-Link/ROSE-LINK/blob/main/ACCESSIBILITY.md",
    color: "teal",
  },
];

const colorClasses: Record<string, { bg: string; text: string; hover: string }> = {
  green: { bg: "bg-green-500/10", text: "text-green-500", hover: "hover:border-green-500/50" },
  blue: { bg: "bg-blue-500/10", text: "text-blue-500", hover: "hover:border-blue-500/50" },
  purple: { bg: "bg-purple-500/10", text: "text-purple-500", hover: "hover:border-purple-500/50" },
  rose: { bg: "bg-rose-500/10", text: "text-rose-500", hover: "hover:border-rose-500/50" },
  amber: { bg: "bg-amber-500/10", text: "text-amber-500", hover: "hover:border-amber-500/50" },
  teal: { bg: "bg-teal-500/10", text: "text-teal-500", hover: "hover:border-teal-500/50" },
};

export default function Documentation() {
  const [visible, setVisible] = useState(false);
  const sectionRef = useRef<HTMLElement>(null);

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

  return (
    <section id="docs" ref={sectionRef} className="py-24 relative">
      <div className="absolute inset-0 bg-gradient-to-b from-dark-900 via-dark-950 to-dark-900" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className={`text-center mb-16 transition-all duration-700 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
          <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-blue-500/10 text-blue-500 border border-blue-500/20 mb-4">
            Documentation
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="text-white">Everything</span>{" "}
            <span className="gradient-text">Documented</span>
          </h2>
          <p className="text-lg text-dark-400 max-w-2xl mx-auto">
            Comprehensive guides, API references, and tutorials to help you get the most out of ROSE Link.
          </p>
        </div>

        {/* Docs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {docs.map((doc, index) => {
            const colors = colorClasses[doc.color];
            return (
              <a
                key={index}
                href={doc.href}
                target="_blank"
                rel="noopener noreferrer"
                className={`glass rounded-2xl p-6 border border-transparent ${colors.hover} transition-all duration-300 group card-hover ${
                  visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
                }`}
                style={{ transitionDelay: `${index * 75}ms` }}
              >
                <div className={`w-12 h-12 rounded-xl ${colors.bg} ${colors.text} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  {doc.icon}
                </div>
                <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-rose-400 transition-colors">
                  {doc.title}
                </h3>
                <p className="text-dark-400 text-sm mb-4">{doc.description}</p>
                <div className="flex items-center text-sm text-rose-500 group-hover:translate-x-2 transition-transform">
                  <span>Read more</span>
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </a>
            );
          })}
        </div>

        {/* Missing Docs Note */}
        <div className={`mt-12 text-center transition-all duration-700 delay-500 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
          <div className="glass rounded-xl p-6 inline-block">
            <h3 className="text-lg font-semibold text-white mb-2">
              Coming Soon
            </h3>
            <p className="text-dark-400 text-sm mb-4">
              We&apos;re working on more documentation including troubleshooting guides,
              architecture diagrams, and enterprise VPN integration tutorials.
            </p>
            <a
              href="https://github.com/ROSE-Link/ROSE-LINK/issues/new?labels=documentation"
              target="_blank"
              rel="noopener noreferrer"
              className="text-rose-500 hover:text-rose-400 text-sm font-medium inline-flex items-center gap-1"
            >
              Request Documentation
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
