<div align="center">

<img src="web/Logo.webp" alt="ROSE Link Logo" width="200">

# ROSE Link

**Routeur VPN domestique sur Raspberry Pi**

<img src="web/icon.webp" alt="ROSE Link Icon" width="64">

Transformez votre Raspberry Pi en routeur/point d'accès Wi-Fi professionnel qui établit un tunnel VPN sécurisé vers votre réseau distant, vous permettant d'accéder à vos ressources locales et d'obtenir l'IP publique de votre serveur VPN depuis n'importe où dans le monde.

![Version](https://img.shields.io/badge/version-1.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%203%2F4%2F5%2FZero%202W-red)

**[English Version](README.md)**

</div>

---

## 🎯 Objectif

ROSE Link crée une solution VPN complète qui :

- 📡 **Se connecte à Internet** via Ethernet RJ45 (priorité) ou WiFi client (fallback automatique)
- 🔐 **Établit un tunnel WireGuard** vers votre serveur VPN (Fritz!Box, pfSense, OpenWrt, VPS...)
- 📶 **Crée un hotspot Wi-Fi local** pour vos appareils (PC, smartphone, tablette)
- 🌍 **Route tout le trafic** via le VPN pour accès réseau distant + IP publique du serveur
- 🎨 **Interface Web moderne** pour configurer WAN, VPN et Hotspot facilement
- ⚙️ **Configuration flexible** via l'interface web (pays, canaux WiFi, paramètres VPN)

```
[PC/Smartphone] ~~~Wi-Fi~~~> Raspberry Pi (ROSE Link Hotspot)
                                    │
                              WireGuard (wg0)
                                    │
                              Serveur VPN distant
                              (Fritz!Box, VPS, etc.)
                                    │
                          Réseau distant + Internet
```

---

## ✨ Fonctionnalités Pro

### 🌐 Connectivité WAN Intelligente
- ✅ **Auto-basculement** : Ethernet RJ45 prioritaire → WiFi client en fallback
- ✅ **Configuration facile** : Scanner et connexion WiFi depuis l'interface Web
- ✅ **Surveillance** : Statut en temps réel de la connexion WAN

### 🔒 VPN WireGuard Avancé
- ✅ **Multi-profils** : Importez et gérez plusieurs configurations VPN
- ✅ **Import .conf** : Upload direct de fichiers WireGuard depuis Fritz!Box
- ✅ **Kill-switch** : Bloque tout trafic si le VPN tombe (pas de fuite)
- ✅ **Watchdog** : Surveillance et reconnexion automatique du tunnel
- ✅ **Statut détaillé** : Handshake, endpoint, transfert de données

### 📶 Hotspot WiFi Configurable
- ✅ **SSID personnalisable** : Choisissez votre nom de réseau
- ✅ **Sécurité WPA2/WPA3** : WPA3 si matériel compatible
- ✅ **Configuration pays** : Canaux et puissance conformes à la réglementation
- ✅ **Sélection canal** : Optimisez les performances
- ✅ **Clients connectés** : Compteur en temps réel

### 🎨 Interface Utilisateur Moderne
- ✅ **Dark mode** : Interface élégante et agréable pour les yeux
- ✅ **Responsive** : Fonctionne sur desktop, tablette et mobile
- ✅ **Temps réel** : Rafraîchissement automatique des statuts
- ✅ **HTTPS** : Connexion sécurisée (certificat auto-signé)

### 🛡️ Sécurité Renforcée
- ✅ **Isolation backend** : API accessible uniquement via Nginx reverse proxy
- ✅ **Sudoers restreint** : Accès minimal aux commandes système avec validation
- ✅ **Fichiers protégés** : Configurations VPN en mode 600, répertoire WireGuard mode 700
- ✅ **Kill-switch iptables** : Protection contre les fuites, bloque tout trafic si VPN déconnecté
- ✅ **SSL/TLS** : Certificats RSA 4096 bits avec Subject Alternative Names
- ✅ **Mots de passe sécurisés** : Génération aléatoire de 12 caractères pour le WiFi
- ✅ **Durcissement systemd** : `ProtectSystem=strict`, `PrivateTmp=true`, `NoNewPrivileges=true`
- ✅ **Limites ressources** : Limites mémoire et CPU sur le service backend

---

## 📦 Installation

### Prérequis

- **Matériel** : Raspberry Pi 3, 4, 5 ou Zero 2W
- **OS** : Raspberry Pi OS (Bullseye/Bookworm) ou Debian 11/12
- **Mémoire** : 512 Mo RAM minimum, 1 Go+ recommandé
- **Stockage** : 300 Mo d'espace disque minimum

### Méthode 1 : Installation en une ligne (Rapide)

```bash
curl -fsSL https://raw.githubusercontent.com/oussrh/ROSE-LINK/main/install.sh | sudo bash
```

### Méthode 2 : Télécharger et Installer (Recommandé)

```bash
# Télécharger l'archive
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link-pro.tar.gz

# Extraire
tar -xzf rose-link-pro.tar.gz
cd rose-link

# Installation interactive
sudo bash install.sh

# Ou avec options personnalisées
sudo bash install.sh --ssid "MonVPN" --country FR
```

### Méthode 3 : Paquet Debian (Meilleur pour les mises à jour)

```bash
# Télécharger le paquet
wget https://github.com/oussrh/ROSE-LINK/releases/latest/download/rose-link-pro_0.2.0-1_all.deb

# Installer avec apt (gère les dépendances)
sudo apt install ./rose-link-pro_0.2.0-1_all.deb
```

### Options d'installation

| Option | Description |
|--------|-------------|
| `-h, --help` | Afficher l'aide |
| `-y, --yes` | Mode non-interactif (accepter les défauts) |
| `-f, --force` | Forcer l'installation (ignorer les vérifications) |
| `--ssid NOM` | SSID WiFi personnalisé (défaut: ROSE-Link) |
| `--password MOT` | Mot de passe WiFi personnalisé (min 8 car., auto-généré si non défini) |
| `--country CODE` | Code pays pour la réglementation WiFi (défaut: BE) |

**Exemples :**
```bash
# Installation silencieuse avec défauts
sudo bash install.sh -y

# Configuration hotspot personnalisée
sudo bash install.sh --ssid "MaisonVPN" --password "MonMotDePasse123" --country FR

# Forcer l'installation sur matériel non-Pi (test)
sudo bash install.sh -f
```

### Désinstallation

```bash
# Désinstallation interactive
sudo bash uninstall.sh

# Désinstallation rapide (garder profils VPN)
sudo bash uninstall.sh -y

# Suppression complète
sudo bash uninstall.sh -y -f

# Si installé via paquet Debian
sudo apt remove rose-link-pro    # Garder config
sudo apt purge rose-link-pro     # Tout supprimer
```

---

## 🚀 Configuration Rapide

### 1️⃣ Accès à l'interface Web

Après installation, connectez-vous au hotspot :
- **SSID** : `ROSE-Link` (ou votre nom personnalisé)
- **Mot de passe** : Affiché à la fin de l'installation (généré aléatoirement pour la sécurité)

Puis ouvrez votre navigateur :
- **URL** : `https://roselink.local` ou `https://192.168.50.1`

⚠️ **Note** : Acceptez l'avertissement du certificat auto-signé (le certificat utilise un chiffrement RSA 4096 bits)

### 2️⃣ Configurer le VPN WireGuard

1. Allez dans l'onglet **🔐 VPN**
2. Cliquez sur **"Importer un profil WireGuard (.conf)"**
3. Sélectionnez votre fichier `.conf` depuis la Fritz!Box
4. Le VPN démarre automatiquement !

### 3️⃣ Personnaliser le Hotspot

1. Allez dans l'onglet **📶 Hotspot**
2. Configurez :
   - SSID (nom du réseau)
   - Mot de passe (min. 8 caractères)
   - Pays (BE, MA, FR, etc.)
   - Canal (1, 6 ou 11 recommandés)
   - WPA3 (cochez si supporté)
3. Cliquez sur **"Appliquer"**

### 4️⃣ Configurer la connexion WAN (optionnel)

Si vous voulez utiliser WiFi comme WAN (au lieu d'Ethernet) :

1. Allez dans l'onglet **📡 WiFi WAN**
2. Cliquez sur **"Scanner les réseaux"**
3. Connectez-vous au réseau souhaité
4. Le basculement se fait automatiquement si l'Ethernet est déconnecté

---

## 🧪 Tests et Validation

### Vérifier l'IP publique

```bash
# Depuis un appareil connecté au hotspot ROSE Link
curl ifconfig.me
# Devrait afficher une IP belge
```

### Accéder au réseau local belge

```bash
# Ping la Fritz!Box
ping 192.168.178.1

# Accéder à l'interface Fritz!Box
# Ouvrir http://192.168.178.1 dans le navigateur
```

### Vérifier les services

```bash
# Sur la Raspberry Pi
sudo systemctl status rose-backend
sudo systemctl status rose-watchdog
sudo systemctl status wg-quick@wg0
sudo systemctl status hostapd

# Statut VPN
sudo wg show
```

---

## 🛠️ Administration

### Redémarrer le VPN

```bash
sudo systemctl restart wg-quick@wg0
```

### Voir les logs

```bash
# Backend API
journalctl -u rose-backend -f

# VPN Watchdog
journalctl -u rose-watchdog -f

# Hotspot
journalctl -u hostapd -f
```

### Règles iptables (NAT + Kill-switch)

```bash
# Voir les règles NAT
sudo iptables -t nat -S

# Voir les règles de forwarding
sudo iptables -S FORWARD
```

### Changer le mot de passe du hotspot

Via l'interface Web (onglet Hotspot) ou manuellement :

```bash
# Éditer /etc/hostapd/hostapd.conf
sudo nano /etc/hostapd/hostapd.conf

# Redémarrer hostapd
sudo systemctl restart hostapd
```

---

## 🔌 Matériel Supporté

### Modèles Raspberry Pi Compatibles

| Modèle | Support | WiFi | Notes |
|--------|---------|------|-------|
| **Raspberry Pi 5** | ✅ Complet | 2.4GHz + 5GHz | Performances optimales, WiFi 802.11ac |
| **Raspberry Pi 4** | ✅ Complet | 2.4GHz + 5GHz | Recommandé, bon équilibre prix/performance |
| **Raspberry Pi 3 B+** | ✅ Avec limitations | 2.4GHz uniquement | Performances réduites, suffisant pour usage léger |
| **Raspberry Pi Zero 2 W** | ⚠️ Basique | 2.4GHz uniquement | Ressources limitées, usage personnel uniquement |

### Configuration Recommandée

#### Raspberry Pi 5 / Pi 4 (Recommandé)
- **RAM** : 2 Go minimum, 4 Go recommandé
- **Alimentation** : 5V 3A USB-C (5V 5A pour Pi 5)
- **Carte microSD** : Classe A2, 32-64 Go
- **Boîtier avec ventilateur** (refroidissement actif recommandé)

#### Raspberry Pi 3
- **RAM** : 1 Go (suffisant pour usage léger)
- **Alimentation** : 5V 2.5A micro-USB
- **Limitations** : WiFi 2.4GHz uniquement, performances VPN réduites

#### Raspberry Pi Zero 2 W
- **RAM** : 512 Mo (usage très léger)
- **Alimentation** : 5V 2A micro-USB
- **Limitations** : Usage personnel uniquement, 2-3 clients max

### Connectivité

| Interface | Usage | Pi 5 | Pi 4 | Pi 3 | Zero 2W |
|-----------|-------|------|------|------|---------|
| **Ethernet RJ45** | WAN prioritaire | ✅ Gigabit | ✅ Gigabit | ✅ 100Mbps | ❌ |
| **WiFi intégré** | Hotspot AP | ✅ 5GHz/ac | ✅ 5GHz/ac | ⚠️ 2.4GHz | ⚠️ 2.4GHz |
| **Dongle WiFi USB** | WAN + AP séparés | ✅ | ✅ | ✅ | ✅ |

### Détection Automatique du Matériel

ROSE Link détecte automatiquement :
- 🔍 **Modèle Raspberry Pi** et ses capacités
- 🔍 **Interfaces réseau** (Ethernet, WiFi intégré, WiFi USB)
- 🔍 **Capacités WiFi** (5GHz, 802.11ac/ax, mode AP)
- 🔍 **Ressources système** (RAM, espace disque, température CPU)

### Notes Importantes

- **Pi 5 avec end0** : L'interface Ethernet s'appelle `end0` au lieu de `eth0` - détecté automatiquement
- **Mode 5GHz** : Activé automatiquement si le matériel le supporte
- **WiFi simultané** : Le WiFi intégré peut gérer AP + client, mais un dongle USB améliore les performances
- **Ethernet recommandé** : Pour WAN, préférez Ethernet RJ45 (plus stable que WiFi)

---

## 📁 Architecture Technique

### Structure des fichiers

```
/opt/rose-link/
├── backend/
│   ├── main.py              # API FastAPI
│   ├── requirements.txt
│   └── venv/                # Environnement Python
├── web/
│   ├── index.html           # Interface Web
│   └── favicon.svg
└── system/
    ├── hostapd.conf         # Config hotspot
    ├── dnsmasq.conf         # DHCP/DNS local
    ├── rose-watchdog.sh     # Watchdog VPN
    └── nginx/roselink       # Config Nginx

/etc/
├── wireguard/
│   ├── wg0.conf -> profiles/xxx.conf  # Symlink actif
│   └── profiles/            # Profils VPN
├── systemd/system/
│   ├── rose-backend.service
│   ├── rose-watchdog.service
│   └── wg-quick@wg0.service
└── nginx/
    └── sites-enabled/roselink
```

### Services systemd

- **rose-backend** : API FastAPI (port 8000, local)
- **rose-watchdog** : Surveillance du VPN et reconnexion auto
- **wg-quick@wg0** : Tunnel WireGuard
- **hostapd** : Point d'accès WiFi
- **dnsmasq** : DHCP + DNS local
- **nginx** : Reverse proxy HTTPS

### Réseau

- **eth0** : WAN Ethernet (prioritaire)
- **wlan0** : WAN WiFi (fallback) ou inutilisé
- **wlan1** : Hotspot AP (192.168.50.1/24)
- **wg0** : Interface VPN WireGuard

### Routage

```
Clients (192.168.50.0/24)
    ↓
wlan1 (AP) → iptables NAT → wg0 → Internet via Fritz!Box
                         ↓
                   Kill-switch si wg0 down
```

---

## 🔒 Sécurité

### Mesures implémentées

1. **Isolation du backend** : API accessible uniquement via Nginx (127.0.0.1)
2. **HTTPS obligatoire** : Certificat auto-signé (remplaçable par Let's Encrypt)
3. **Sudoers restreint** : Utilisateur `rose` avec accès minimal aux commandes
4. **Kill-switch iptables** : Pas de trafic si wg0 tombe
5. **Permissions fichiers** : Configurations VPN en mode 600
6. **Pas de root** : Services tournent avec utilisateur dédié `rose`

### Améliorer la sécurité

#### Remplacer le certificat auto-signé (optionnel)

```bash
# Avec Let's Encrypt (nécessite domaine public)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
```

#### Changer le mot de passe par défaut

Via l'interface Web, onglet **Hotspot**, ou :

```bash
sudo nano /etc/hostapd/hostapd.conf
# Modifier wpa_passphrase
sudo systemctl restart hostapd
```

---

## 🌍 Cas d'usage

### 1. Accès réseau domestique à distance

Vous êtes au Maroc, votre réseau principal est en Belgique :
- Accédez à votre Fritz!Box (192.168.178.1)
- Accédez à votre NAS, imprimante, etc.
- Gérez votre réseau comme si vous étiez sur place

### 2. IP publique belge

Pour contourner les restrictions géographiques :
- Services bancaires belges
- Streaming vidéo géo-restreint
- Services web nécessitant IP belge

### 3. Connexion sécurisée en déplacement

- Hôtel, café, coworking : VPN automatique
- Pas besoin de configurer chaque appareil
- Un seul hotspot ROSE Link protège tout

### 4. Partage VPN familial/équipe

- Plusieurs appareils connectés au hotspot
- Tous passent par le VPN automatiquement
- Configuration centralisée

---

## 🐛 Dépannage

### Vérification rapide des services

```bash
# Vérifier tous les services ROSE Link en une fois
for svc in rose-backend rose-watchdog hostapd dnsmasq nginx; do
    status=$(systemctl is-active $svc 2>/dev/null || echo "inactif")
    echo "$svc: $status"
done
```

### Problèmes courants

| Problème | Solution |
|----------|----------|
| Impossible de se connecter au hotspot | `sudo systemctl restart hostapd` |
| VPN ne se connecte pas | `sudo systemctl restart wg-quick@wg0` |
| Interface web ne charge pas | `sudo systemctl restart nginx rose-backend` |
| Pas d'internet sur les clients | Vérifier VPN: `sudo wg show` et IP forwarding: `cat /proc/sys/net/ipv4/ip_forward` |

### Consulter les logs

```bash
# Logs du backend
sudo journalctl -u rose-backend -f

# Logs VPN
sudo journalctl -u wg-quick@wg0 -n 50

# Logs hotspot
sudo journalctl -u hostapd -n 50

# Log d'installation
cat /var/log/rose-link-install.log
```

### Le VPN ne démarre pas

```bash
# Vérifier les logs
journalctl -u wg-quick@wg0 -n 50

# Vérifier la config
sudo wg show

# Tester manuellement
sudo wg-quick up wg0
```

### Le hotspot ne fonctionne pas

```bash
# Vérifier hostapd
systemctl status hostapd
journalctl -u hostapd -n 50

# Vérifier l'interface
ip addr show wlan1

# Tester hostapd manuellement
sudo hostapd -dd /etc/hostapd/hostapd.conf
```

### Pas d'Internet sur les clients

```bash
# Vérifier le forwarding IP
cat /proc/sys/net/ipv4/ip_forward
# Devrait afficher 1

# Vérifier iptables
sudo iptables -t nat -L POSTROUTING -v
sudo iptables -L FORWARD -v

# Vérifier wg0
sudo wg show
ping -I wg0 8.8.8.8
```

### L'interface Web est inaccessible

```bash
# Vérifier Nginx
systemctl status nginx
sudo nginx -t

# Vérifier le backend
systemctl status rose-backend
journalctl -u rose-backend -n 50

# Tester le backend directement
curl http://127.0.0.1:8000/api/health
```

### WiFi WAN ne se connecte pas

```bash
# Lister les réseaux
sudo nmcli device wifi list

# Vérifier NetworkManager
systemctl status NetworkManager

# Se connecter manuellement
sudo nmcli device wifi connect "SSID" password "PASSWORD"
```

---

## 📊 API REST

### Endpoints disponibles

#### Santé et statut
- `GET /api/health` - Health check
- `GET /api/status` - Statut global (WAN, VPN, AP)

#### WiFi WAN
- `POST /api/wifi/scan` - Scanner les réseaux WiFi *(requiert auth)*
- `POST /api/wifi/connect` - Se connecter à un réseau *(requiert auth)*
- `POST /api/wifi/disconnect` - Se déconnecter *(requiert auth)*

#### VPN
- `GET /api/vpn/status` - Statut du VPN
- `GET /api/vpn/profiles` - Liste des profils *(requiert auth)*
- `POST /api/vpn/upload` - Upload un profil (sans activer) *(requiert auth)*
- `POST /api/vpn/import` - Import et activation *(requiert auth)*
- `POST /api/vpn/activate` - Activer un profil existant *(requiert auth)*
- `POST /api/vpn/start` - Démarrer le VPN *(requiert auth)*
- `POST /api/vpn/stop` - Arrêter le VPN *(requiert auth)*
- `POST /api/vpn/restart` - Redémarrer le VPN *(requiert auth)*

#### Hotspot
- `GET /api/hotspot/status` - Statut du hotspot
- `GET /api/hotspot/clients` - Liste des clients connectés *(requiert auth)*
- `POST /api/hotspot/apply` - Appliquer une config *(requiert auth)*
- `POST /api/hotspot/restart` - Redémarrer le hotspot *(requiert auth)*

#### Paramètres
- `GET /api/settings/vpn` - Paramètres watchdog VPN *(requiert auth)*
- `POST /api/settings/vpn` - Mettre à jour paramètres watchdog VPN *(requiert auth)*

#### Système
- `GET /api/system/info` - Informations système (modèle Pi, RAM, CPU, WiFi)
- `GET /api/system/interfaces` - Liste des interfaces réseau détectées
- `GET /api/system/logs?service=xxx` - Logs d'un service *(requiert auth)*
- `POST /api/system/reboot` - Redémarrer le système *(requiert auth)*

#### Métriques
- `GET /api/metrics` - Métriques Prometheus
- `GET /api/metrics/performance` - Métriques de performance (latence, erreurs, requêtes)

### Exemple d'utilisation

```bash
# Health check
curl -k https://roselink.local/api/health

# Statut global
curl -k https://roselink.local/api/status | jq

# Scanner WiFi
curl -k -X POST https://roselink.local/api/wifi/scan | jq

# Statut VPN
curl -k https://roselink.local/api/vpn/status | jq

# Informations système (nouveau)
curl -k https://roselink.local/api/system/info | jq

# Interfaces réseau détectées (nouveau)
curl -k https://roselink.local/api/system/interfaces | jq
```

### Exemple de réponse `/api/system/info`

```json
{
  "model": "Raspberry Pi 4 Model B Rev 1.4",
  "model_short": "Pi 4",
  "architecture": "aarch64",
  "ram_mb": 4096,
  "ram_free_mb": 2048,
  "disk_total_gb": 32,
  "disk_free_gb": 20,
  "cpu_temp_c": 45,
  "cpu_usage_percent": 12.5,
  "uptime_seconds": 86400,
  "interfaces": {
    "ethernet": "eth0",
    "wifi_ap": "wlan0",
    "wifi_wan": "wlan0"
  },
  "wifi_capabilities": {
    "supports_5ghz": true,
    "supports_ac": true,
    "supports_ax": false,
    "ap_mode": true
  },
  "kernel_version": "6.1.0-rpi7-rpi-v8",
  "os_version": "Debian GNU/Linux 12 (bookworm)"
}
```

---

## 🛣️ Roadmap

### Version 0.2.x (Publiée)
- [x] Support i18n complet (anglais & français)
- [x] Design mobile-first responsive pour tous les écrans
- [x] Optimisation du code avec docstrings et type hints complets
- [x] Détection dynamique des interfaces (correction du wlan0 codé en dur)
- [x] Mise à jour vers les dernières versions des packages (FastAPI 0.115+, Pydantic 2.10+, htmx 2.0.3)
- [x] Notifications toast et indicateurs de chargement
- [x] Améliorations d'accessibilité (labels ARIA, HTML sémantique)
- [x] Points d'accès documentation API (/api/docs, /api/redoc)

### Version 0.3.0 (Publiée)
- [x] WebSocket pour mises à jour statut temps réel (remplace le polling)
- [x] Sauvegarde/restauration configuration (profils VPN, config hotspot)
- [x] Option certificat SSL Let's Encrypt (+ génération auto-signé)
- [x] Intégration test de vitesse (speedtest-cli, Ookla)
- [x] Point d'accès métriques Prometheus (/api/metrics)
- [x] Statistiques bande passante (par interface, temps réel)

### Version 0.4.0 (En cours)
- [ ] Notifications email pour pannes VPN
- [ ] QoS simple (priorisation trafic)
- [ ] AdGuard Home intégré (DNS + blocage pubs)
- [ ] Support OpenVPN en plus de WireGuard
- [ ] Dashboard métriques Grafana
- [ ] Gestion des clients connectés

### Version 1.0.0 (Future)
- [ ] Image SD flashable prête à l'emploi
- [ ] Assistant de configuration première installation
- [ ] Support multi-WAN (load balancing)
- [ ] Application mobile iOS/Android
- [ ] Mises à jour automatiques
- [ ] Suite de tests complète

---

## 🤝 Contribution

Les contributions sont les bienvenues !

### Comment contribuer

1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

### Développement local

```bash
# Clone
git clone https://github.com/oussrh/ROSE-LINK.git
cd ROSE-LINK

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Web : ouvrir web/index.html dans un navigateur
```

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 🙏 Remerciements

- **WireGuard** : VPN moderne et performant
- **FastAPI** : Framework Python rapide et élégant
- **Tailwind CSS** : Framework CSS utility-first
- **htmx** : Interactivité HTML moderne
- **Raspberry Pi Foundation** : Matériel extraordinaire

---

## 📞 Support

- **Documentation** : [GitHub Wiki](https://github.com/oussrh/ROSE-LINK/wiki)
- **Issues** : [GitHub Issues](https://github.com/oussrh/ROSE-LINK/issues)
- **Discussions** : [GitHub Discussions](https://github.com/oussrh/ROSE-LINK/discussions)

---

<div align="center">

**🌹 Made with love for secure remote access**

[⭐ Star ce projet](https://github.com/oussrh/ROSE-LINK) | [🐛 Reporter un bug](https://github.com/oussrh/ROSE-LINK/issues) | [💡 Suggérer une feature](https://github.com/oussrh/ROSE-LINK/issues)

</div>
