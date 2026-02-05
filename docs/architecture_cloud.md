# ============================================
# ARCHITECTURE FINALE CLOUD - PROJET IoT
# ============================================
# 
# Ce document décrit l'architecture de déploiement
# pour la mise en production du système IoT.
#
# ============================================

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE CLOUD - PRODUCTION                               │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    INTERNET
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
          ▼                            ▼                            ▼
   ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
   │   Capteur   │            │   Capteur   │            │   Capteur   │
   │    ESP32    │            │    ESP32    │            │    ESP32    │
   │   (C001)    │            │   (C002)    │            │   (C003)    │
   └──────┬──────┘            └──────┬──────┘            └──────┬──────┘
          │                          │                          │
          │         MQTT over TLS (Port 8883)                   │
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │
                                     ▼
                    ┌────────────────────────────────┐
                    │      HIVEMQ CLOUD (MQTT)       │
                    │                                │
                    │  • Broker MQTT managé          │
                    │  • TLS/SSL obligatoire         │
                    │  • Authentification            │
                    │  • Scalable automatiquement    │
                    │                                │
                    │  Host: *.s1.eu.hivemq.cloud    │
                    │  Port: 8883                    │
                    └────────────────┬───────────────┘
                                     │
                                     │ MQTT Subscribe
                                     ▼
                    ┌────────────────────────────────┐
                    │   PC LOCAL (Backend Python)    │
                    │                                │
                    │  ┌──────────────────────────┐  │
                    │  │  simulateur_capteurs.py  │  │
                    │  │  • Publish MQTT          │  │
                    │  └──────────────────────────┘  │
                    │                                │
                    │  ┌──────────────────────────┐  │
                    │  │  detection_anomalies.py  │  │
                    │  │  • Subscribe MQTT        │  │
                    │  │  • Isolation Forest      │  │
                    │  │  • Z-score               │  │
                    │  │  • MongoDB storage       │  │
                    │  │  • Gmail SMTP alerts     │  │
                    │  └──────────────────────────┘  │
                    └────────────────┬───────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
   │  MONGODB ATLAS   │   │   GMAIL SMTP     │   │ STREAMLIT CLOUD  │
   │                  │   │                  │   │                  │
   │  • Stockage NoSQL│   │  • Alertes email │   │  • Dashboard web │
   │  • Cluster M0    │   │  • App Password  │   │  • Auto-refresh  │
   │  • Backup auto   │   │  • Gratuit       │   │  • HTTPS gratuit │
   │                  │   │                  │   │                  │
   │  Gratuit: 512 MB │   │  Gratuit: 500/j  │   │  Gratuit: 1 app  │
   └──────────────────┘   └──────────────────┘   └──────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FLUX DE DONNÉES                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

  1. ACQUISITION
     Capteur ESP32 → Mesure température/humidité → Publish MQTT

  2. TRANSPORT
     HiveMQ Cloud → Authentification TLS → Distribution messages

  3. TRAITEMENT
     Backend Python → Subscribe MQTT → Analyse IA → Détection anomalies

  4. STOCKAGE
     MongoDB Atlas → Insert mesures → Insert anomalies → Historisation

  5. ALERTE
     Gmail SMTP → Email automatique → Notification admin

  6. VISUALISATION
     Streamlit Cloud → Lecture MongoDB → Graphiques temps réel


┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SÉCURITÉ                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

  ✅ TLS/SSL : Toutes les connexions sont chiffrées
  ✅ Authentification : Username/password pour MQTT
  ✅ Secrets : Variables d'environnement (pas dans le code)
  ✅ RBAC : Contrôle d'accès MongoDB Atlas
  ✅ HTTPS : Certificat SSL automatique sur Streamlit Cloud


# Guide de déploiement

## 1. Préparer le code

```bash
# Structure du projet
projet_IoT/
├── src/
│   ├── dashboard.py          # App principale Streamlit
│   ├── detection_anomalies.py
│   ├── cloud_integration.py
│   └── config.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
└── README.md
```

## 2. Déployer sur Streamlit Cloud

1. Pusher le code sur GitHub
2. Aller sur https://share.streamlit.io
3. Connecter le repo GitHub
4. Sélectionner `src/dashboard.py` comme fichier principal
5. Ajouter les secrets dans les paramètres :

```toml
[mongodb]
uri = "mongodb+srv://user:password@cluster.mongodb.net/"

[mqtt]
host = "xxx.s1.eu.hivemq.cloud"
port = 8883
username = "username"
password = "password"

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_user = "votre.email@gmail.com"
smtp_password = "xxxx xxxx xxxx xxxx"
email_to = "destinataire@email.com"
```

6. Cliquer sur "Deploy"

## 3. Lancer le simulateur (local)

Le simulateur de capteurs et la détection d'anomalies s'exécutent sur votre PC :

```bash
# Terminal 1 : Simulateur de capteurs
python src/simulateur_capteurs.py

# Terminal 2 : Détection d'anomalies  
python src/detection_anomalies.py
```

Ces scripts locaux publient vers HiveMQ Cloud et stockent dans MongoDB Atlas.
Le dashboard Streamlit Cloud lit les données depuis MongoDB en temps réel.

## 4. Configurer MongoDB Atlas

1. Créer un compte sur https://www.mongodb.com/cloud/atlas
2. Créer un cluster M0 (gratuit)
3. Ajouter un utilisateur database
4. Whitelist les IP (0.0.0.0/0 pour le développement)
5. Récupérer l'URI de connexion

## 5. Configurer Gmail SMTP

1. Activer 2FA sur votre compte Gmail
2. Créer un App Password: Google Account → Security → App passwords
3. Ajouter dans .env: SMTP_USER, SMTP_PASSWORD, EMAIL_TO
4. Tester l'envoi d'un email
