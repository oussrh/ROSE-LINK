"use client";

import { useEffect, useRef, useState } from "react";

const steps = [
  {
    number: "01",
    title: "Flash Raspberry Pi OS",
    description: "Download Raspberry Pi Imager and flash Raspberry Pi OS Lite (64-bit) to your SD card.",
    code: null,
  },
  {
    number: "02",
    title: "Run the Installer",
    description: "SSH into your Pi and run our one-line installer. It handles everything automatically.",
    code: "curl -sSL https://get.rose-link.io | sudo bash",
  },
  {
    number: "03",
    title: "Open the Web UI",
    description: "Navigate to https://raspberrypi.local in your browser to access the setup wizard.",
    code: null,
  },
  {
    number: "04",
    title: "Configure & Connect",
    description: "Follow the wizard to set up your WAN, VPN, and hotspot. You're protected in minutes!",
    code: null,
  },
];

const requirements = [
  { name: "Raspberry Pi 3/4/5 or Zero 2W", icon: "🍓" },
  { name: "MicroSD Card (8GB+)", icon: "💾" },
  { name: "USB WiFi Adapter (for dual-band)", icon: "📡" },
  { name: "Ethernet cable (recommended)", icon: "🔌" },
  { name: "VPN subscription or config file", icon: "🔐" },
];

export default function Installation() {
  const [visible, setVisible] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
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

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <section id="installation" ref={sectionRef} className="py-24 relative">
      <div className="absolute inset-0 bg-gradient-to-b from-dark-900 via-dark-950 to-dark-900" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className={`text-center mb-16 transition-all duration-700 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
          <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-green-500/10 text-green-500 border border-green-500/20 mb-4">
            Quick Start
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="text-white">Up and Running in</span>{" "}
            <span className="gradient-text">Under 5 Minutes</span>
          </h2>
          <p className="text-lg text-dark-400 max-w-2xl mx-auto">
            Our automated installer handles all the complex setup. Just run one command and follow the wizard.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Installation Steps */}
          <div className="space-y-6">
            {steps.map((step, index) => (
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
                  <h3 className="text-lg font-semibold text-white mb-1">{step.title}</h3>
                  <p className="text-dark-400 text-sm mb-3">{step.description}</p>
                  {step.code && (
                    <div className="relative group">
                      <pre className="bg-dark-800 border border-dark-700 rounded-lg p-4 text-sm overflow-x-auto">
                        <code className="text-green-400">{step.code}</code>
                      </pre>
                      <button
                        onClick={() => copyToClipboard(step.code!, index)}
                        className="absolute top-2 right-2 p-2 rounded-md bg-dark-700 hover:bg-dark-600 text-dark-300 hover:text-white transition-all opacity-0 group-hover:opacity-100"
                        aria-label="Copy to clipboard"
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
            <div className="glass rounded-2xl p-8 sticky top-24">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <svg className="w-6 h-6 text-rose-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                Requirements
              </h3>
              <ul className="space-y-4">
                {requirements.map((req, index) => (
                  <li key={index} className="flex items-center gap-3 text-dark-300">
                    <span className="text-xl">{req.icon}</span>
                    <span>{req.name}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-8 pt-6 border-t border-dark-700">
                <h4 className="text-sm font-medium text-dark-400 mb-3">Supported OS</h4>
                <div className="flex flex-wrap gap-2">
                  {["Raspberry Pi OS", "Debian 11", "Debian 12"].map((os) => (
                    <span key={os} className="px-3 py-1 bg-dark-800 rounded-full text-sm text-dark-300">
                      {os}
                    </span>
                  ))}
                </div>
              </div>

              <a
                href="https://github.com/ROSE-Link/ROSE-LINK#quick-start"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-6 w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-lg font-medium transition-all shadow-lg shadow-rose-500/25"
              >
                Full Installation Guide
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
            Alternative Installation Methods
          </h3>
          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { method: "APT Repository", command: "apt install rose-link", icon: "📦" },
              { method: "Debian Package", command: "dpkg -i rose-link.deb", icon: "🗃️" },
              { method: "From Source", command: "make install", icon: "🔧" },
            ].map((item, index) => (
              <div key={index} className="glass rounded-xl p-4 text-center card-hover">
                <span className="text-2xl mb-2 block">{item.icon}</span>
                <h4 className="font-semibold text-white mb-1">{item.method}</h4>
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
