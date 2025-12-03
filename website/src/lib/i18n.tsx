"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

export type Language = "en" | "fr";

type Translations = {
  [key: string]: {
    en: string;
    fr: string;
  };
};

export const translations: Translations = {
  // Navbar
  "nav.features": { en: "Features", fr: "Fonctionnalités" },
  "nav.roadmap": { en: "Roadmap", fr: "Feuille de route" },
  "nav.installation": { en: "Installation", fr: "Installation" },
  "nav.docs": { en: "Documentation", fr: "Documentation" },
  "nav.github": { en: "GitHub", fr: "GitHub" },
  "nav.github.aria": { en: "View ROSE Link on GitHub (opens in new tab)", fr: "Voir ROSE Link sur GitHub (ouvre un nouvel onglet)" },
  "nav.support": { en: "Support Us", fr: "Nous soutenir" },
  "nav.support.aria": { en: "Support ROSE Link via PayPal (opens in new tab)", fr: "Soutenir ROSE Link via PayPal (ouvre un nouvel onglet)" },
  "nav.viewGithub": { en: "View on GitHub", fr: "Voir sur GitHub" },

  // Hero
  "hero.badge": { en: "Version 1.6.4 - Single WiFi Device Support", fr: "Version 1.6.4 - Support appareil WiFi unique" },
  "hero.title1": { en: "Home VPN Router", fr: "Routeur VPN Maison" },
  "hero.title2": { en: "+ Ad Blocking", fr: "+ Blocage Pubs" },
  "hero.title3": { en: "on", fr: "sur" },
  "hero.subtitle": { en: "Transform your Raspberry Pi into a professional WiFi access point that routes all traffic through a VPN tunnel. Protect your entire network with one device.", fr: "Transformez votre Raspberry Pi en point d'accès WiFi professionnel qui route tout le trafic via un tunnel VPN. Protégez tout votre réseau avec un seul appareil." },
  "hero.quickInstall": { en: "Quick Install", fr: "Installation rapide" },
  "hero.viewGithub": { en: "View on GitHub", fr: "Voir sur GitHub" },
  "hero.stat1": { en: "Open Source", fr: "Open Source" },
  "hero.stat2": { en: "WireGuard + OpenVPN", fr: "WireGuard + OpenVPN" },
  "hero.stat3": { en: "Installation", fr: "Installation" },
  "hero.stat4": { en: "Models Supported", fr: "Modèles supportés" },
  "hero.scroll": { en: "Scroll to explore", fr: "Défiler pour explorer" },

  // Features
  "features.title1": { en: "Everything You Need for", fr: "Tout ce qu'il faut pour la" },
  "features.title2": { en: "Network Privacy", fr: "Confidentialité Réseau" },
  "features.subtitle": { en: "A complete VPN router solution with enterprise-grade features, designed for home users and small businesses.", fr: "Une solution de routeur VPN complète avec des fonctionnalités professionnelles, conçue pour les particuliers et les petites entreprises." },
  "features.killswitch.title": { en: "VPN Kill-Switch", fr: "Kill-Switch VPN" },
  "features.killswitch.desc": { en: "Automatic traffic blocking when VPN disconnects. Your real IP never leaks.", fr: "Blocage automatique du trafic en cas de déconnexion VPN. Votre IP réelle ne fuit jamais." },
  "features.hotspot.title": { en: "WiFi Hotspot", fr: "Hotspot WiFi" },
  "features.hotspot.desc": { en: "Create a secure hotspot with WPA2/WPA3. Connect any device to your VPN network.", fr: "Créez un hotspot sécurisé avec WPA2/WPA3. Connectez n'importe quel appareil à votre réseau VPN." },
  "features.adblock.title": { en: "Ad Blocking", fr: "Blocage des pubs" },
  "features.adblock.desc": { en: "Network-wide ad blocking with AdGuard Home. No apps needed on devices.", fr: "Blocage des pubs sur tout le réseau avec AdGuard Home. Aucune app requise sur les appareils." },
  "features.monitoring.title": { en: "Real-time Monitoring", fr: "Monitoring temps réel" },
  "features.monitoring.desc": { en: "Prometheus metrics + Grafana dashboards. Track bandwidth, clients, and system health.", fr: "Métriques Prometheus + tableaux Grafana. Suivez la bande passante, les clients et l'état du système." },
  "features.clients.title": { en: "Client Management", fr: "Gestion des clients" },
  "features.clients.desc": { en: "See connected devices in real-time. Block, kick, or rename clients with one click.", fr: "Voyez les appareils connectés en temps réel. Bloquez, éjectez ou renommez les clients en un clic." },
  "features.profiles.title": { en: "Multi-Profile VPN", fr: "VPN Multi-Profil" },
  "features.profiles.desc": { en: "Manage multiple WireGuard and OpenVPN profiles. Switch with one click.", fr: "Gérez plusieurs profils WireGuard et OpenVPN. Changez en un clic." },
  "features.wizard.title": { en: "Setup Wizard", fr: "Assistant de config" },
  "features.wizard.desc": { en: "Guided configuration in under 5 minutes. No terminal knowledge required.", fr: "Configuration guidée en moins de 5 minutes. Aucune connaissance terminal requise." },
  "features.bilingual.title": { en: "Bilingual UI", fr: "Interface bilingue" },
  "features.bilingual.desc": { en: "Full English and French support. Easily add more languages.", fr: "Support complet anglais et français. Ajoutez facilement d'autres langues." },
  "features.compatible": { en: "Compatible with Major VPN Providers", fr: "Compatible avec les principaux fournisseurs VPN" },

  // Roadmap
  "roadmap.badge": { en: "v1.6.4", fr: "v1.6.4" },
  "roadmap.title1": { en: "What's New &", fr: "Nouveautés &" },
  "roadmap.title2": { en: "What's Next", fr: "À venir" },
  "roadmap.subtitle": { en: "See what we've recently shipped and what's coming next. Contributions welcome!", fr: "Découvrez nos dernières livraisons et ce qui arrive. Contributions bienvenues !" },
  "roadmap.e2e.title": { en: "Recently Completed", fr: "Récemment complété" },
  "roadmap.e2e.item1": { en: "Single WiFi device detection (v1.6.0)", fr: "Détection appareil WiFi unique (v1.6.0)" },
  "roadmap.e2e.item2": { en: "Extended VPN file support (.conf, .wg, .vpn)", fr: "Support fichiers VPN étendu (.conf, .wg, .vpn)" },
  "roadmap.e2e.item3": { en: "40+ countries WiFi regulations", fr: "Réglementations WiFi 40+ pays" },
  "roadmap.observability.title": { en: "DNS & Networking", fr: "DNS & Réseau" },
  "roadmap.observability.item1": { en: "AdGuard Home v0.107+ support", fr: "Support AdGuard Home v0.107+" },
  "roadmap.observability.item2": { en: "DNS resolution for VPN hostnames", fr: "Résolution DNS pour noms d'hôte VPN" },
  "roadmap.observability.item3": { en: "dnsmasq/AdGuard port conflict fix", fr: "Correction conflit port dnsmasq/AdGuard" },
  "roadmap.observability.item4": { en: "Upstream DNS configuration", fr: "Configuration DNS upstream" },
  "roadmap.performance.title": { en: "Monitoring", fr: "Monitoring" },
  "roadmap.performance.item1": { en: "Grafana + Prometheus stack (optional)", fr: "Stack Grafana + Prometheus (optionnel)" },
  "roadmap.performance.item2": { en: "Pre-configured alert rules", fr: "Règles d'alertes pré-configurées" },
  "roadmap.performance.item3": { en: "Resource-optimized for Raspberry Pi", fr: "Optimisé ressources pour Raspberry Pi" },
  "roadmap.security.title": { en: "Security", fr: "Sécurité" },
  "roadmap.security.item1": { en: "Kill-switch iptables protection", fr: "Protection kill-switch iptables" },
  "roadmap.security.item2": { en: "Rate limiting per IP", fr: "Rate limiting par IP" },
  "roadmap.security.item3": { en: "HTTPS with RSA 4096-bit certificates", fr: "HTTPS avec certificats RSA 4096-bit" },
  "roadmap.upcoming": { en: "Upcoming Features", fr: "Fonctionnalités à venir" },
  "roadmap.priority.high": { en: "High", fr: "Haute" },
  "roadmap.priority.medium": { en: "Medium", fr: "Moyenne" },
  "roadmap.priority.low": { en: "Low", fr: "Basse" },
  "roadmap.feature.email": { en: "Email notifications", fr: "Notifications email" },
  "roadmap.feature.email.desc": { en: "Alert on VPN failure", fr: "Alerter en cas de panne VPN" },
  "roadmap.feature.updates": { en: "Automatic updates", fr: "Mises à jour automatiques" },
  "roadmap.feature.updates.desc": { en: "Via APT with rollback", fr: "Via APT avec rollback" },
  "roadmap.feature.qos": { en: "QoS Profiles", fr: "Profils QoS" },
  "roadmap.feature.qos.desc": { en: "Gaming/Streaming/Work", fr: "Gaming/Streaming/Travail" },
  "roadmap.feature.syslog": { en: "Syslog Export", fr: "Export Syslog" },
  "roadmap.feature.syslog.desc": { en: "Centralized logs", fr: "Logs centralisés" },
  "roadmap.feature.charts": { en: "Historical charts", fr: "Graphiques historiques" },
  "roadmap.feature.charts.desc": { en: "30-day trends", fr: "Tendances 30 jours" },
  "roadmap.feature.doh": { en: "DNS over HTTPS", fr: "DNS over HTTPS" },
  "roadmap.feature.doh.desc": { en: "Encrypted DNS queries", fr: "Requêtes DNS chiffrées" },
  "roadmap.feature.wired": { en: "Wired Client Mode", fr: "Mode Client Filaire" },
  "roadmap.feature.wired.desc": { en: "WiFi for WAN, Ethernet for clients", fr: "WiFi pour WAN, Ethernet pour clients" },
  "roadmap.ui": { en: "UI/UX Improvements", fr: "Améliorations UI/UX" },
  "roadmap.ui.wizard": { en: "Wizard ✓", fr: "Assistant ✓" },
  "roadmap.ui.wizard.desc": { en: "Skip button & overflow fixed", fr: "Bouton passer & débordement corrigé" },
  "roadmap.ui.errors": { en: "Buttons ✓", fr: "Boutons ✓" },
  "roadmap.ui.errors.desc": { en: "Confirmation before reboot/restart", fr: "Confirmation avant redémarrage" },
  "roadmap.ui.mobile": { en: "Mobile", fr: "Mobile" },
  "roadmap.ui.mobile.desc": { en: "Swipe navigation planned", fr: "Navigation swipe prévue" },
  "roadmap.ui.settings": { en: "Dark Mode ✓", fr: "Mode sombre ✓" },
  "roadmap.ui.settings.desc": { en: "Elegant eye-friendly interface", fr: "Interface élégante et agréable" },
  "roadmap.contribute.title": { en: "Contribute to the Project", fr: "Contribuez au Projet" },
  "roadmap.contribute.desc": { en: "ROSE Link is open source. Join the community!", fr: "ROSE Link est open source. Rejoignez la communauté !" },
  "roadmap.contribute.button": { en: "View Issues", fr: "Voir les Issues" },

  // Installation
  "install.badge": { en: "Quick Start", fr: "Démarrage rapide" },
  "install.title1": { en: "Up and Running in", fr: "Opérationnel en" },
  "install.title2": { en: "Under 5 Minutes", fr: "moins de 5 minutes" },
  "install.subtitle": { en: "Our automated installer handles all the complex setup. Just run one command and follow the wizard.", fr: "Notre installateur automatisé gère toute la configuration complexe. Lancez une commande et suivez l'assistant." },
  "install.step1.title": { en: "Flash Raspberry Pi OS", fr: "Flasher Raspberry Pi OS" },
  "install.step1.desc": { en: "Download Raspberry Pi Imager and flash Raspberry Pi OS Lite (64-bit) to your SD card.", fr: "Téléchargez Raspberry Pi Imager et flashez Raspberry Pi OS Lite (64-bit) sur votre carte SD." },
  "install.step2.title": { en: "Run the Installer", fr: "Lancer l'installateur" },
  "install.step2.desc": { en: "SSH into your Pi and run our one-line installer. It handles everything automatically.", fr: "Connectez-vous en SSH à votre Pi et lancez notre installateur en une ligne. Il gère tout automatiquement." },
  "install.step3.title": { en: "Open the Web UI", fr: "Ouvrir l'interface web" },
  "install.step3.desc": { en: "Navigate to https://roselink.local or https://192.168.50.1 in your browser to access the setup wizard.", fr: "Accédez à https://roselink.local ou https://192.168.50.1 dans votre navigateur pour lancer l'assistant de configuration." },
  "install.step4.title": { en: "Configure & Connect", fr: "Configurer et connecter" },
  "install.step4.desc": { en: "Follow the wizard to set up your WAN, VPN, and hotspot. You're protected in minutes!", fr: "Suivez l'assistant pour configurer votre WAN, VPN et hotspot. Vous êtes protégé en quelques minutes !" },
  "install.requirements": { en: "Requirements", fr: "Prérequis" },
  "install.req1": { en: "Raspberry Pi 3/4/5 or Zero 2W", fr: "Raspberry Pi 3/4/5 ou Zero 2W" },
  "install.req2": { en: "MicroSD Card (8GB+)", fr: "Carte MicroSD (8Go+)" },
  "install.req3": { en: "USB WiFi Adapter (optional, for WiFi WAN)", fr: "Adaptateur WiFi USB (optionnel, pour WiFi WAN)" },
  "install.req4": { en: "Ethernet cable (required for Pi 3/Zero 2W)", fr: "Câble Ethernet (requis pour Pi 3/Zero 2W)" },
  "install.req5": { en: "VPN subscription or config file", fr: "Abonnement VPN ou fichier de config" },
  "install.supportedOs": { en: "Supported OS", fr: "OS supportés" },
  "install.fullGuide": { en: "Full Installation Guide", fr: "Guide d'installation complet" },
  "install.alternative": { en: "Alternative Installation Methods", fr: "Méthodes d'installation alternatives" },
  "install.apt": { en: "APT Repository", fr: "Dépôt APT" },
  "install.deb": { en: "Debian Package", fr: "Paquet Debian" },
  "install.source": { en: "From Source", fr: "Depuis les sources" },

  // Documentation
  "docs.badge": { en: "Documentation", fr: "Documentation" },
  "docs.title1": { en: "Everything", fr: "Tout est" },
  "docs.title2": { en: "Documented", fr: "Documenté" },
  "docs.subtitle": { en: "Comprehensive guides, API references, and tutorials to help you get the most out of ROSE Link.", fr: "Guides complets, références API et tutoriels pour tirer le meilleur parti de ROSE Link." },
  "docs.quickstart": { en: "Quick Start Guide", fr: "Guide de démarrage rapide" },
  "docs.quickstart.desc": { en: "Get ROSE Link running on your Raspberry Pi in under 5 minutes.", fr: "Lancez ROSE Link sur votre Raspberry Pi en moins de 5 minutes." },
  "docs.features": { en: "Product Features", fr: "Fonctionnalités produit" },
  "docs.features.desc": { en: "Complete list of features and capabilities of ROSE Link.", fr: "Liste complète des fonctionnalités et capacités de ROSE Link." },
  "docs.dev": { en: "Development Guide", fr: "Guide de développement" },
  "docs.dev.desc": { en: "Set up your development environment and contribute to ROSE Link.", fr: "Configurez votre environnement de dev et contribuez à ROSE Link." },
  "docs.security": { en: "Security Policy", fr: "Politique de sécurité" },
  "docs.security.desc": { en: "Learn about our security practices and how to report vulnerabilities.", fr: "Découvrez nos pratiques de sécurité et comment signaler les vulnérabilités." },
  "docs.changelog": { en: "Changelog", fr: "Journal des modifications" },
  "docs.changelog.desc": { en: "See what's new in each version of ROSE Link.", fr: "Découvrez les nouveautés de chaque version de ROSE Link." },
  "docs.roadmapLink": { en: "Roadmap", fr: "Feuille de route" },
  "docs.roadmapLink.desc": { en: "See planned features and the future direction of ROSE Link.", fr: "Découvrez les fonctionnalités prévues et l'avenir de ROSE Link." },
  "docs.readMore": { en: "Read more", fr: "En savoir plus" },
  "docs.comingSoon": { en: "Coming Soon", fr: "Bientôt disponible" },
  "docs.comingSoon.desc": { en: "We're working on more documentation including troubleshooting guides, architecture diagrams, and enterprise VPN integration tutorials.", fr: "Nous préparons plus de documentation : guides de dépannage, diagrammes d'architecture et tutoriels d'intégration VPN entreprise." },
  "docs.request": { en: "Request Documentation", fr: "Demander de la documentation" },

  // Open Source
  "opensource.badge": { en: "Open Source", fr: "Open Source" },
  "opensource.title1": { en: "Free as in", fr: "Libre comme dans" },
  "opensource.title2": { en: "Freedom", fr: "Liberté" },
  "opensource.subtitle": { en: "ROSE Link is released under the MIT license. Use it, modify it, share it. Your privacy is not a product.", fr: "ROSE Link est publié sous licence MIT. Utilisez-le, modifiez-le, partagez-le. Votre vie privée n'est pas un produit." },
  "opensource.auditable": { en: "Fully Auditable", fr: "Entièrement auditable" },
  "opensource.auditable.desc": { en: "Every line of code is public. No hidden telemetry, no backdoors, no surprises.", fr: "Chaque ligne de code est publique. Pas de télémétrie cachée, pas de portes dérobées, pas de surprises." },
  "opensource.free": { en: "Forever Free", fr: "Gratuit pour toujours" },
  "opensource.free.desc": { en: "No subscriptions, no premium features. Everything is included at no cost.", fr: "Pas d'abonnement, pas de fonctionnalités premium. Tout est inclus gratuitement." },
  "opensource.community": { en: "Community Driven", fr: "Piloté par la communauté" },
  "opensource.community.desc": { en: "Built by developers, for developers. Contributions and feedback welcome.", fr: "Construit par des développeurs, pour des développeurs. Contributions et retours bienvenus." },
  "opensource.selfhosted": { en: "Self-Hosted", fr: "Auto-hébergé" },
  "opensource.selfhosted.desc": { en: "Your data stays on your network. No cloud dependencies or external services.", fr: "Vos données restent sur votre réseau. Aucune dépendance cloud ou services externes." },
  "opensource.license": { en: "License", fr: "Licence" },
  "opensource.loc": { en: "Lines of Code", fr: "Lignes de code" },
  "opensource.coverage": { en: "Test Coverage", fr: "Couverture de tests" },
  "opensource.piModels": { en: "Pi Models Supported", fr: "Modèles Pi supportés" },
  "opensource.star": { en: "Star on GitHub", fr: "Étoile sur GitHub" },
  "opensource.fork": { en: "Fork & Contribute", fr: "Fork et contribuer" },

  // Footer
  "footer.product": { en: "Product", fr: "Produit" },
  "footer.resources": { en: "Resources", fr: "Ressources" },
  "footer.community": { en: "Community", fr: "Communauté" },
  "footer.description": { en: "Transform your Raspberry Pi into a professional VPN router with network-wide ad blocking. Open source, privacy-focused, and easy to use.", fr: "Transformez votre Raspberry Pi en routeur VPN professionnel avec blocage des pubs sur tout le réseau. Open source, axé sur la confidentialité et facile à utiliser." },
  "footer.copyright": { en: "ROSE Link. Released under", fr: "ROSE Link. Publié sous" },
  "footer.license": { en: "MIT License", fr: "Licence MIT" },
  "footer.madeWith": { en: "Made with", fr: "Fait avec" },
  "footer.forPrivacy": { en: "for privacy", fr: "pour la confidentialité" },
  "footer.contributing": { en: "Contributing", fr: "Contribuer" },
  "footer.issues": { en: "Issues", fr: "Issues" },
  "footer.discussions": { en: "Discussions", fr: "Discussions" },
  "footer.coc": { en: "Code of Conduct", fr: "Code de conduite" },

  // 404
  "404.title": { en: "Page Not Found", fr: "Page non trouvée" },
  "404.desc": { en: "The page you're looking for doesn't exist or has been moved.", fr: "La page que vous recherchez n'existe pas ou a été déplacée." },
  "404.back": { en: "Back to Home", fr: "Retour à l'accueil" },
};

type LanguageContextType = {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>("en");

  useEffect(() => {
    // Check localStorage or browser language
    const saved = localStorage.getItem("language") as Language;
    if (saved && (saved === "en" || saved === "fr")) {
      setLanguage(saved);
    } else {
      // Detect browser language
      const browserLang = navigator.language.toLowerCase();
      if (browserLang.startsWith("fr")) {
        setLanguage("fr");
      }
    }
  }, []);

  const handleSetLanguage = (lang: Language) => {
    setLanguage(lang);
    localStorage.setItem("language", lang);
  };

  const t = (key: string): string => {
    const translation = translations[key];
    if (!translation) {
      console.warn(`Missing translation: ${key}`);
      return key;
    }
    return translation[language];
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage: handleSetLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}
