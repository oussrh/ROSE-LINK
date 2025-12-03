"use client";

import { useState } from "react";
import Link from "next/link";
import { useLanguage } from "@/lib/i18n";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

interface FAQItem {
  question: { en: string; fr: string };
  answer: { en: string; fr: string };
  category: string;
}

const faqData: FAQItem[] = [
  // Getting Started
  {
    category: "getting-started",
    question: {
      en: "What Raspberry Pi models are supported?",
      fr: "Quels modeles Raspberry Pi sont supportes ?",
    },
    answer: {
      en: "ROSE Link supports Raspberry Pi 5, Pi 4, Pi 3 Model B/B+, Pi Zero 2 W, Pi 400, and CM4. Pi 5 and Pi 4 offer the best performance with 5GHz WiFi support. Pi 3 and Zero 2W are limited to 2.4GHz WiFi and require Ethernet for WAN.",
      fr: "ROSE Link supporte Raspberry Pi 5, Pi 4, Pi 3 Model B/B+, Pi Zero 2 W, Pi 400 et CM4. Pi 5 et Pi 4 offrent les meilleures performances avec WiFi 5GHz. Pi 3 et Zero 2W sont limites au WiFi 2.4GHz et necessitent Ethernet pour le WAN.",
    },
  },
  {
    category: "getting-started",
    question: {
      en: "Do I need an Ethernet connection?",
      fr: "Ai-je besoin d'une connexion Ethernet ?",
    },
    answer: {
      en: "It depends on your device. Single WiFi devices (Pi 3, Zero 2W) require Ethernet because the WiFi is reserved for the hotspot. Dual-interface setups (Pi 4/5 with USB WiFi adapter) can use WiFi for WAN. Ethernet is always recommended for stability.",
      fr: "Cela depend de votre appareil. Les appareils WiFi unique (Pi 3, Zero 2W) necessitent Ethernet car le WiFi est reserve au hotspot. Les configurations double interface (Pi 4/5 avec adaptateur WiFi USB) peuvent utiliser le WiFi pour le WAN. L'Ethernet est toujours recommande pour la stabilite.",
    },
  },
  {
    category: "getting-started",
    question: {
      en: "How long does installation take?",
      fr: "Combien de temps dure l'installation ?",
    },
    answer: {
      en: "The installation typically takes 3-5 minutes. The installer automatically downloads dependencies, configures services, and sets up the hotspot. After installation, you can access the web interface immediately.",
      fr: "L'installation prend generalement 3-5 minutes. L'installateur telecharge automatiquement les dependances, configure les services et met en place le hotspot. Apres l'installation, vous pouvez acceder a l'interface web immediatement.",
    },
  },
  // VPN
  {
    category: "vpn",
    question: {
      en: "Which VPN providers are supported?",
      fr: "Quels fournisseurs VPN sont supportes ?",
    },
    answer: {
      en: "ROSE Link supports any WireGuard or OpenVPN provider including NordVPN, ExpressVPN, ProtonVPN, Mullvad, PIA, Surfshark, and custom servers like Fritz!Box or pfSense. Simply import your .conf or .ovpn file.",
      fr: "ROSE Link supporte tout fournisseur WireGuard ou OpenVPN incluant NordVPN, ExpressVPN, ProtonVPN, Mullvad, PIA, Surfshark, et les serveurs personnalises comme Fritz!Box ou pfSense. Importez simplement votre fichier .conf ou .ovpn.",
    },
  },
  {
    category: "vpn",
    question: {
      en: "What happens if the VPN disconnects?",
      fr: "Que se passe-t-il si le VPN se deconnecte ?",
    },
    answer: {
      en: "ROSE Link includes an automatic kill-switch that blocks all internet traffic if the VPN disconnects, preventing data leaks. The watchdog service will automatically attempt to reconnect the VPN.",
      fr: "ROSE Link inclut un kill-switch automatique qui bloque tout le trafic Internet si le VPN se deconnecte, empechant les fuites de donnees. Le service watchdog tentera automatiquement de reconnecter le VPN.",
    },
  },
  {
    category: "vpn",
    question: {
      en: "Can I use multiple VPN profiles?",
      fr: "Puis-je utiliser plusieurs profils VPN ?",
    },
    answer: {
      en: "Yes! You can import multiple VPN configuration files and switch between them from the web interface. Only one VPN can be active at a time, but switching is instant.",
      fr: "Oui ! Vous pouvez importer plusieurs fichiers de configuration VPN et basculer entre eux depuis l'interface web. Un seul VPN peut etre actif a la fois, mais le changement est instantane.",
    },
  },
  // Hotspot
  {
    category: "hotspot",
    question: {
      en: "What WiFi bands are supported?",
      fr: "Quelles bandes WiFi sont supportees ?",
    },
    answer: {
      en: "Pi 5 and Pi 4 support both 2.4GHz and 5GHz bands. Pi 3 and Zero 2W only support 2.4GHz. The hotspot uses WPA2/WPA3 encryption for security.",
      fr: "Pi 5 et Pi 4 supportent les bandes 2.4GHz et 5GHz. Pi 3 et Zero 2W ne supportent que 2.4GHz. Le hotspot utilise le chiffrement WPA2/WPA3 pour la securite.",
    },
  },
  {
    category: "hotspot",
    question: {
      en: "How many devices can connect to the hotspot?",
      fr: "Combien d'appareils peuvent se connecter au hotspot ?",
    },
    answer: {
      en: "The practical limit depends on your Raspberry Pi model and usage patterns. Pi 5/4 can handle 15-20+ devices comfortably. Pi 3 is best for 5-10 devices. Pi Zero 2W is recommended for 2-3 devices only.",
      fr: "La limite pratique depend du modele Raspberry Pi et des usages. Pi 5/4 peuvent gerer 15-20+ appareils confortablement. Pi 3 est adapte pour 5-10 appareils. Pi Zero 2W est recommande pour 2-3 appareils seulement.",
    },
  },
  {
    category: "hotspot",
    question: {
      en: "Can I change the hotspot name and password?",
      fr: "Puis-je changer le nom et mot de passe du hotspot ?",
    },
    answer: {
      en: "Yes, you can customize the SSID (network name), password, country code, and WiFi channel through the web interface under the Hotspot tab. Changes take effect after restarting the hotspot.",
      fr: "Oui, vous pouvez personnaliser le SSID (nom du reseau), le mot de passe, le code pays et le canal WiFi via l'interface web sous l'onglet Hotspot. Les modifications prennent effet apres le redemarrage du hotspot.",
    },
  },
  // AdGuard
  {
    category: "adguard",
    question: {
      en: "How does AdGuard Home work with ROSE Link?",
      fr: "Comment fonctionne AdGuard Home avec ROSE Link ?",
    },
    answer: {
      en: "AdGuard Home provides network-wide ad blocking at the DNS level. All devices connected to the ROSE Link hotspot automatically benefit from ad blocking without needing to install any apps.",
      fr: "AdGuard Home fournit un blocage des pubs au niveau DNS sur tout le reseau. Tous les appareils connectes au hotspot ROSE Link beneficient automatiquement du blocage des pubs sans installer d'application.",
    },
  },
  {
    category: "adguard",
    question: {
      en: "Can I disable AdGuard Home?",
      fr: "Puis-je desactiver AdGuard Home ?",
    },
    answer: {
      en: "Yes, AdGuard Home can be enabled, disabled, or restarted from the Ad Blocker tab in the web interface. When disabled, DNS queries are forwarded directly to upstream DNS servers.",
      fr: "Oui, AdGuard Home peut etre active, desactive ou redemarre depuis l'onglet Bloqueur de pubs dans l'interface web. Lorsqu'il est desactive, les requetes DNS sont transmises directement aux serveurs DNS upstream.",
    },
  },
  // Troubleshooting
  {
    category: "troubleshooting",
    question: {
      en: "I can't connect to the hotspot, what should I do?",
      fr: "Je ne peux pas me connecter au hotspot, que dois-je faire ?",
    },
    answer: {
      en: "First, check if the ROSE-Link network appears in your WiFi list. If not, SSH into your Pi and run 'sudo systemctl status hostapd' to check the service. Try 'sudo systemctl restart hostapd' to restart it.",
      fr: "D'abord, verifiez si le reseau ROSE-Link apparait dans votre liste WiFi. Sinon, connectez-vous en SSH a votre Pi et executez 'sudo systemctl status hostapd' pour verifier le service. Essayez 'sudo systemctl restart hostapd' pour le redemarrer.",
    },
  },
  {
    category: "troubleshooting",
    question: {
      en: "The VPN won't connect, how do I fix it?",
      fr: "Le VPN ne se connecte pas, comment le reparer ?",
    },
    answer: {
      en: "Check your VPN configuration file is valid and your subscription is active. Run 'sudo journalctl -u wg-quick@wg0 -n 50' to see VPN logs. Common issues include incorrect keys, expired configs, or DNS resolution problems.",
      fr: "Verifiez que votre fichier de configuration VPN est valide et que votre abonnement est actif. Executez 'sudo journalctl -u wg-quick@wg0 -n 50' pour voir les logs VPN. Les problemes courants incluent des cles incorrectes, des configs expirees ou des problemes de resolution DNS.",
    },
  },
  {
    category: "troubleshooting",
    question: {
      en: "How do I access the web interface?",
      fr: "Comment acceder a l'interface web ?",
    },
    answer: {
      en: "Connect to the ROSE-Link WiFi network, then open https://roselink.local or https://192.168.50.1 in your browser. Accept the self-signed certificate warning to proceed.",
      fr: "Connectez-vous au reseau WiFi ROSE-Link, puis ouvrez https://roselink.local ou https://192.168.50.1 dans votre navigateur. Acceptez l'avertissement de certificat auto-signe pour continuer.",
    },
  },
];

const categories = [
  { key: "all", icon: "all" },
  { key: "getting-started", icon: "rocket" },
  { key: "vpn", icon: "shield" },
  { key: "hotspot", icon: "wifi" },
  { key: "adguard", icon: "block" },
  { key: "troubleshooting", icon: "tool" },
];

const categoryNames: Record<string, Record<string, string>> = {
  en: {
    all: "All Questions",
    "getting-started": "Getting Started",
    vpn: "VPN",
    hotspot: "Hotspot",
    adguard: "Ad Blocking",
    troubleshooting: "Troubleshooting",
  },
  fr: {
    all: "Toutes les questions",
    "getting-started": "Demarrage",
    vpn: "VPN",
    hotspot: "Hotspot",
    adguard: "Blocage des pubs",
    troubleshooting: "Depannage",
  },
};

export default function FAQPage() {
  const [activeCategory, setActiveCategory] = useState("all");
  const [openItems, setOpenItems] = useState<number[]>([]);
  const { language: lang } = useLanguage();

  const toggleItem = (index: number) => {
    setOpenItems((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  const filteredFAQ =
    activeCategory === "all"
      ? faqData
      : faqData.filter((item) => item.category === activeCategory);

  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-dark-950 pt-24 pb-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="text-center mb-12">
            <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-blue-500/10 text-blue-500 border border-blue-500/20 mb-4">
              FAQ
            </span>
            <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
              {lang === "fr" ? "Questions Frequentes" : "Frequently Asked Questions"}
            </h1>
            <p className="text-lg text-dark-400">
              {lang === "fr"
                ? "Trouvez des reponses aux questions les plus courantes sur ROSE Link."
                : "Find answers to the most common questions about ROSE Link."}
            </p>
          </div>

          {/* Category Filter */}
          <div className="flex flex-wrap justify-center gap-2 mb-12">
            {categories.map((cat) => (
              <button
                key={cat.key}
                onClick={() => setActiveCategory(cat.key)}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeCategory === cat.key
                    ? "bg-rose-500 text-white"
                    : "bg-dark-800 text-dark-400 hover:text-white hover:bg-dark-700"
                }`}
              >
                {categoryNames[lang]?.[cat.key] || categoryNames.en[cat.key]}
              </button>
            ))}
          </div>

          {/* FAQ Items */}
          <div className="space-y-4">
            {filteredFAQ.map((item, index) => (
              <div
                key={index}
                className="glass rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => toggleItem(index)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left"
                >
                  <span className="font-medium text-white pr-4">
                    {item.question[lang] || item.question.en}
                  </span>
                  <svg
                    className={`w-5 h-5 text-dark-400 transition-transform flex-shrink-0 ${
                      openItems.includes(index) ? "rotate-180" : ""
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                {openItems.includes(index) && (
                  <div className="px-6 pb-4 text-dark-300 border-t border-dark-700 pt-4">
                    {item.answer[lang] || item.answer.en}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Still Need Help */}
          <div className="mt-16 text-center">
            <div className="glass rounded-2xl p-8">
              <h3 className="text-xl font-bold text-white mb-2">
                {lang === "fr" ? "Toujours besoin d'aide ?" : "Still need help?"}
              </h3>
              <p className="text-dark-400 mb-4">
                {lang === "fr"
                  ? "Consultez notre documentation complete ou ouvrez une issue."
                  : "Check our complete documentation or open an issue."}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/docs"
                  className="px-6 py-3 bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700 text-white rounded-lg font-medium transition-all"
                >
                  {lang === "fr" ? "Documentation" : "Documentation"}
                </Link>
                <a
                  href="https://github.com/oussrh/ROSE-LINK/issues/new"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-3 border border-dark-700 hover:border-rose-500/50 text-white rounded-lg font-medium transition-all"
                >
                  {lang === "fr" ? "Signaler un probleme" : "Report Issue"}
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
