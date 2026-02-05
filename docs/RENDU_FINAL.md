# 📋 DOCUMENT DE RENDU FINAL
## Projet : Supervision Intelligente de Capteurs IoT avec Détection d'Anomalies


## 📌 Résumé du Projet

Ce projet implémente un système complet de supervision IoT incluant :
- Simulation de capteurs de température/humidité
- Communication via broker MQTT Cloud (HiveMQ)
- Détection d'anomalies par Intelligence Artificielle
- Dashboard web temps réel avec Streamlit
- Architecture Cloud sécurisée et extensible

---

## ✅ Objectifs Atteints

| Objectif | Statut | Description |
|----------|--------|-------------|
| Réseau IoT simulé | ✅ | 3 capteurs virtuels publiant vers HiveMQ Cloud |
| IA embarquée | ✅ | Détection par Isolation Forest et Z-score |
| Dashboard web | ✅ | Interface Streamlit temps réel |
| Architecture Cloud | ✅ | TLS, MongoDB Atlas, Gmail SMTP |

---

## 🏗️ Architecture Technique

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Capteur    │     │  Capteur    │     │  Capteur    │
│   C001      │     │   C002      │     │   C003      │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │ MQTT (TLS)
                           ▼
              ┌────────────────────────┐
              │   HiveMQ Cloud         │
              │   (Broker MQTT)        │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │   Backend Python       │
              │   • Réception MQTT     │
              │   • Isolation Forest   │
              │   • Z-score            │
              └───────────┬────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
  ┌────────────┐   ┌────────────┐   ┌────────────┐
  │  MongoDB   │   │ Gmail SMTP │   │ Streamlit  │
  │  Atlas     │   │  (Alertes) │   │ Dashboard  │
  └────────────┘   └────────────┘   └────────────┘
```

---

## 📁 Structure du Projet

```
projet_IoT/
├── docs/
│   ├── specifications_techniques.md   # Cahier des spécifications
│   └── architecture_cloud.md          # Architecture de déploiement
├── src/
│   ├── config.py                      # Configuration MQTT et paramètres
│   ├── simulateur_capteurs.py         # Simulation des capteurs IoT
│   ├── detection_anomalies.py         # Module IA de détection
│   ├── dashboard.py                   # Interface web Streamlit
│   ├── cloud_integration.py           # Intégration MongoDB
│   ├── email_service.py               # Service d'alertes Gmail SMTP
│   └── deploy.py                      # Script de déploiement
├── data/
│   ├── historique.csv                 # Données historiques
│   ├── anomalies.csv                  # Anomalies détectées
│   └── graphique_anomalies.png        # Graphique généré
├── .streamlit/
│   ├── config.toml                    # Configuration Streamlit
│   └── secrets.toml.example           # Template des secrets
├── requirements.txt                   # Dépendances Python
├── .gitignore
├── .env.example
└── README.md
```

---

## 🔧 Technologies Utilisées

| Catégorie | Technologie | Version |
|-----------|-------------|---------|
| Langage | Python | 3.10+ |
| MQTT Client | paho-mqtt | 2.1.0 |
| Machine Learning | scikit-learn | 1.3+ |
| Data Processing | pandas, numpy | 2.0+, 1.24+ |
| Visualisation | matplotlib, plotly | 3.7+, 5.15+ |
| Dashboard | Streamlit | 1.28+ |
| Broker MQTT | HiveMQ Cloud | - |
| Base de données | MongoDB Atlas | - |
| Email | Gmail SMTP | - |

---

## 📊 Fonctionnalités Implémentées

### 1. Simulateur de Capteurs (simulateur_capteurs.py)
- ✅ Simulation de 3 capteurs (C001, C002, C003)
- ✅ Envoi MQTT toutes les 3 secondes
- ✅ Connexion TLS sécurisée (port 8883)
- ✅ Injection d'anomalies (5% de probabilité)
  - 🔥 Surchauffe (+12°C)
  - ❄️ Sous-température (-10°C)
  - ⚠️ Valeur nulle (0°C)

### 2. Détection d'Anomalies (detection_anomalies.py)
- ✅ Réception temps réel via MQTT Subscribe
- ✅ Analyse statistique (moyenne, écart-type)
- ✅ Algorithme Isolation Forest (sklearn)
- ✅ Détection par Z-score (seuil = 3σ)
- ✅ Sauvegarde CSV automatique
- ✅ Génération de graphiques matplotlib

### 3. Dashboard Streamlit (dashboard.py)
- ✅ Métriques en temps réel
- ✅ Graphiques interactifs Plotly
- ✅ Tableau des dernières mesures
- ✅ Zone d'alertes pour anomalies
- ✅ Rafraîchissement automatique (5s)
- ✅ Export CSV via boutons

### 4. Intégration Cloud (cloud_integration.py)
- ✅ Stockage MongoDB Atlas
- ✅ Service d'alertes email Gmail SMTP
- ✅ Fichiers de déploiement générés
- ✅ Documentation d'architecture Cloud

---

## 📈 Résultats et Captures

### Données collectées
- **Nombre de mesures** : 30+ (lors des tests)
- **Capteurs actifs** : 3 (C001, C002, C003)
- **Anomalies générées** : ~5% du total

### Format des données CSV

| Colonne | Type | Description |
|---------|------|-------------|
| sensor_id | string | Identifiant du capteur |
| timestamp | datetime | Horodatage ISO 8601 |
| temperature | float | Température en °C |
| humidity | float | Humidité en % |
| is_anomaly | bool | Indicateur d'anomalie |
| status | string | NORMAL / ANOMALIE |

---

## 🚀 Guide de Lancement

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Configuration MQTT
Modifier `src/config.py` avec vos credentials HiveMQ :
- Host : `xxx.s1.eu.hivemq.cloud`
- Port : `8883`
- Username / Password

### 3. Lancement du simulateur
```bash
python src/simulateur_capteurs.py
```

### 4. Lancement du module IA
```bash
python src/detection_anomalies.py
```

### 5. Lancement du dashboard
```bash
streamlit run src/dashboard.py
```

### 6. Accès au dashboard
- URL : http://localhost:8501

---

## ☁️ Déploiement Cloud

### Services utilisés (offres gratuites)

| Service | Utilisation | Limite gratuite |
|---------|-------------|-----------------|
| HiveMQ Cloud | Broker MQTT | 10 GB/mois |
| MongoDB Atlas | Stockage données | 512 MB |
| Gmail SMTP | Alertes email | 500/jour |
| Streamlit Cloud | Dashboard web | 1 app |

### Étapes de déploiement
1. Pusher le code sur GitHub
2. Connecter Streamlit Cloud au repo
3. Configurer les secrets
4. Déployer automatiquement

---

## 📝 Grille d'Auto-Évaluation

| Critère | Points | Réalisé |
|---------|--------|---------|
| Conception du système IoT Cloud | 6 | ✅ Schéma + Spécifications |
| Simulation des capteurs | 4 | ✅ Code fonctionnel |
| Module IA | 6 | ✅ Isolation Forest + Z-score |
| Dashboard Streamlit | 4 | ✅ Interface complète |
| Qualité du rendu | 20 | ✅ Documentation complète |
| **TOTAL** | **40** | ✅ |

---

## 📎 Livrables Fournis

1. ✅ **Schéma d'architecture** : `docs/specifications_techniques.md`
2. ✅ **Scripts Python** :
   - `src/simulateur_capteurs.py`
   - `src/detection_anomalies.py`
   - `src/dashboard.py`
   - `src/cloud_integration.py`
3. ✅ **Fichiers CSV** : `data/historique.csv`, `data/anomalies.csv`
4. ✅ **Graphique** : `data/graphique_anomalies.png`
5. ✅ **Documentation** : `README.md`, `docs/`

---

## 🔐 Sécurité

- ✅ Connexions MQTT chiffrées TLS/SSL
- ✅ Authentification par username/password
- ✅ Secrets stockés dans fichiers non versionnés
- ✅ `.gitignore` configuré correctement

---

