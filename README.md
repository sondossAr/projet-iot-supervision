# 🌡️ Supervision Intelligente de Capteurs IoT

## Description du projet

Système complet IoT + IA + Dashboard pour la supervision de capteurs avec détection d'anomalies en temps réel.

## Architecture

```
Capteurs simulés → Broker MQTT Cloud → Backend IA → Dashboard Streamlit
```

## Installation

```bash
# Cloner le projet
cd projet_IoT

# Installer les dépendances
pip install -r requirements.txt

# Configurer les credentials MQTT
# Modifier src/config.py avec vos informations HiveMQ Cloud
```

## Configuration HiveMQ Cloud

1. Créer un compte sur [HiveMQ Cloud](https://www.hivemq.com/cloud/)
2. Créer un cluster gratuit
3. Ajouter un utilisateur dans "Access Management"
4. Copier host, username et password dans `src/config.py`

## Lancement

```bash
# 1. Lancer le simulateur de capteurs
python src/simulateur_capteurs.py

# 2. Dans un autre terminal, lancer le dashboard
streamlit run src/dashboard.py
```

## Structure du projet

```
projet_IoT/
├── docs/                       # Documentation
├── src/
│   ├── config.py              # Configuration
│   ├── simulateur_capteurs.py # Simulation IoT
│   ├── detection_anomalies.py # Module IA
│   └── dashboard.py           # Interface Streamlit
├── data/                       # Données CSV
├── requirements.txt
└── README.md
```

## Technologies

- Python 3.10+
- paho-mqtt (communication MQTT)
- scikit-learn (détection d'anomalies)
- Streamlit (dashboard)
- HiveMQ Cloud (broker MQTT)

## Auteur

Projet réalisé dans le cadre de l'examen 5 BIM IA - Janvier 2026
