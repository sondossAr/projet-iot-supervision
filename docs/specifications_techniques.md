# 📋 Cahier des Spécifications Techniques
## Supervision Intelligente de Capteurs IoT avec Détection d'Anomalies

---

## 1. Vue d'ensemble du système

### 1.1 Description générale
Ce projet implémente un système de supervision IoT complet comprenant :
- **Capteurs simulés** : Génération de données de température et humidité
- **Broker MQTT Cloud** : Centralisation des communications (HiveMQ Cloud)
- **Backend IA** : Détection d'anomalies en temps réel
- **Dashboard Web** : Visualisation avec Streamlit

### 1.2 Schéma d'architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURE DU SYSTÈME IoT                          │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │  Capteur C001│     │  Capteur C002│     │  Capteur C003│
    │  (Simulé)    │     │  (Simulé)    │     │  (Simulé)    │
    │  Python      │     │  Python      │     │  Python      │
    └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
           │                    │                    │
           │    MQTT Publish    │    MQTT Publish    │
           │    (TLS/SSL)       │    (TLS/SSL)       │
           └────────────────────┼────────────────────┘
                                │
                                ▼
           ┌────────────────────────────────────────┐
           │         BROKER MQTT CLOUD              │
           │         (HiveMQ Cloud)                 │
           │                                        │
           │  • Host: xxxxxxxx.hivemq.cloud         │
           │  • Port: 8883 (TLS)                    │
           │  • Authentification: username/password │
           └────────────────────┬───────────────────┘
                                │
                                │ MQTT Subscribe
                                ▼
           ┌────────────────────────────────────────┐
           │         BACKEND PYTHON                 │
           │                                        │
           │  ┌──────────────────────────────────┐  │
           │  │     Module de Réception MQTT     │  │
           │  │     (paho-mqtt)                  │  │
           │  └──────────────┬───────────────────┘  │
           │                 │                      │
           │                 ▼                      │
           │  ┌──────────────────────────────────┐  │
           │  │     Module IA                    │  │
           │  │     • Isolation Forest           │  │
           │  │     • Analyse statistique        │  │
           │  │     • Détection d'anomalies      │  │
           │  └──────────────┬───────────────────┘  │
           │                 │                      │
           │                 ▼                      │
           │  ┌──────────────────────────────────┐  │
           │  │     Stockage des données         │  │
           │  │     • CSV local                  │  │
           │  │     • MongoDB Atlas (optionnel)  │  │
           │  └──────────────────────────────────┘  │
           └────────────────────┬───────────────────┘
                                │
                                │ Données traitées
                                ▼
           ┌────────────────────────────────────────┐
           │         DASHBOARD STREAMLIT            │
           │                                        │
           │  • Graphiques temps réel               │
           │  • Tableau des mesures                 │
           │  • Alertes d'anomalies                 │
           │  • Export CSV                          │
           │                                        │
           │  URL: http://localhost:8501            │
           └────────────────────────────────────────┘
```

---

## 2. Spécifications MQTT

### 2.1 Broker Cloud
| Paramètre | Valeur |
|-----------|--------|
| Fournisseur | HiveMQ Cloud |
| Host | À configurer (xxx.hivemq.cloud) |
| Port | 8883 (connexion sécurisée TLS) |
| Protocole | MQTT v3.1.1 / v5.0 |
| Sécurité | TLS/SSL + Authentification |

### 2.2 Topics MQTT

| Topic | Direction | Description |
|-------|-----------|-------------|
| `iotsystem/capteurs/temperature` | Publish | Données des capteurs |
| `iotsystem/alertes` | Publish | Alertes d'anomalies |

### 2.3 Format des messages (Payload JSON)

#### Message de données capteur
```json
{
    "sensor_id": "C001",
    "timestamp": "2026-01-27T14:30:00Z",
    "temperature": 23.7,
    "humidity": 45.2
}
```

#### Message d'alerte (anomalie détectée)
```json
{
    "sensor_id": "C001",
    "timestamp": "2026-01-27T14:30:00Z",
    "type": "ANOMALIE",
    "temperature": 38.5,
    "message": "Température anormalement élevée détectée"
}
```

---

## 3. Spécifications des capteurs simulés

### 3.1 Caractéristiques
| Paramètre | Valeur |
|-----------|--------|
| Nombre de capteurs | 3 (C001, C002, C003) |
| Intervalle d'envoi | 3-5 secondes |
| Probabilité d'anomalie | 5% |

### 3.2 Plages de valeurs normales
| Mesure | Valeur centrale | Écart-type |
|--------|-----------------|------------|
| Température | 25°C | ±0.8°C |
| Humidité | 40% | ±2% |

### 3.3 Types d'anomalies simulées
- **Surchauffe** : Température +12°C au-dessus de la normale
- **Sous-température** : Température -10°C en dessous de la normale
- **Valeurs nulles** : Température ou humidité à 0

---

## 4. Spécifications du module IA

### 4.1 Algorithme de détection
- **Méthode principale** : Isolation Forest (sklearn)
- **Méthode secondaire** : Z-score (analyse statistique)
- **Taux de contamination** : 5% (paramètre du modèle)

### 4.2 Critères de détection
| Critère | Seuil |
|---------|-------|
| Z-score température | > 3 ou < -3 |
| Z-score humidité | > 3 ou < -3 |
| Isolation Forest | score = -1 |

---

## 5. Spécifications du Dashboard

### 5.1 Fonctionnalités
- Affichage graphique temps réel (température + humidité)
- Tableau des dernières mesures
- Encadré d'alertes pour les anomalies
- Rafraîchissement automatique toutes les 5 secondes
- Export CSV des données

### 5.2 Interface utilisateur
| Composant | Description |
|-----------|-------------|
| Header | Titre + indicateur de connexion |
| Graphique principal | Courbe température/humidité |
| Tableau de données | 10 dernières mesures |
| Zone d'alertes | Anomalies détectées en rouge |
| Boutons | Export CSV, Reset |

---

## 6. Sécurité

### 6.1 Connexion MQTT
- Chiffrement TLS/SSL obligatoire
- Authentification par username/password
- Certificats validés

### 6.2 Stockage des credentials
- Fichier `.env` pour les variables d'environnement
- Fichier `config.py` avec chargement sécurisé
- `.gitignore` configuré pour exclure les secrets

---

## 7. Technologies utilisées

| Composant | Technologie |
|-----------|-------------|
| Langage | Python 3.10+ |
| MQTT Client | paho-mqtt |
| Machine Learning | scikit-learn |
| Data Processing | pandas, numpy |
| Visualisation | matplotlib, plotly |
| Dashboard | Streamlit |
| Base de données | CSV / MongoDB Atlas |

---

## 8. Structure du projet

```
projet_IoT/
├── docs/
│   ├── specifications_techniques.md
│   └── architecture.png
├── src/
│   ├── config.py              # Configuration MQTT
│   ├── simulateur_capteurs.py # Étape 2
│   ├── detection_anomalies.py # Étape 3
│   └── dashboard.py           # Étape 4
├── data/
│   ├── historique.csv         # Données historiques
│   └── anomalies.csv          # Anomalies détectées
├── requirements.txt
├── .env                        # Variables d'environnement (non versionné)
├── .gitignore
└── README.md
```

---

## 9. Instructions de déploiement

### 9.1 Installation locale
```bash
pip install -r requirements.txt
```

### 9.2 Configuration
1. Créer un compte HiveMQ Cloud
2. Copier les credentials dans `.env`
3. Lancer le simulateur
4. Lancer le dashboard

### 9.3 Déploiement Cloud (optionnel)
- Streamlit Cloud pour le dashboard
- Railway.app ou Heroku pour le backend

---

*Document généré le 27/01/2026*
