# Configuration du projet IoT
# ============================
# Ce fichier contient la configuration MQTT et les paramètres du système
# 
# Les credentials sont stockés dans le fichier .env pour la sécurité

import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# ============================================================================
# CONFIGURATION MQTT - HIVEMQ CLOUD
# ============================================================================
# 
# Instructions pour configurer HiveMQ Cloud :
# 1. Aller sur https://www.hivemq.com/cloud/
# 2. Créer un compte gratuit
# 3. Créer un cluster MQTT
# 4. Ajouter les credentials (Access Management)
# 5. Copier les informations ci-dessous
# ============================================================================

@dataclass
class MQTTConfig:
    """Configuration du broker MQTT"""
    
    # Paramètres de connexion HiveMQ Cloud (chargés depuis .env)
    host: str = os.getenv("MQTT_HOST", "")
    port: int = int(os.getenv("MQTT_PORT", "8883"))
    username: str = os.getenv("MQTT_USERNAME", "")
    password: str = os.getenv("MQTT_PASSWORD", "")
    
    # Topics MQTT
    topic_temperature: str = "iotsystem/capteurs/temperature"
    topic_alertes: str = "iotsystem/alertes"
    
    # Options de connexion
    use_tls: bool = True
    keepalive: int = 60  # secondes
    

# ============================================================================
# CONFIGURATION DES CAPTEURS
# ============================================================================

@dataclass  
class CapteurConfig:
    """Configuration des capteurs simulés"""
    
    # Liste des identifiants de capteurs
    sensor_ids: List[str] = None
    
    # Intervalle d'envoi des données (en secondes)
    intervalle_envoi: float = 3.0
    
    # Valeurs de référence pour la simulation
    temperature_moyenne: float = 25.0
    temperature_ecart_type: float = 0.8
    humidite_moyenne: float = 40.0
    humidite_ecart_type: float = 2.0
    
    # Probabilité d'injection d'anomalie (5%)
    probabilite_anomalie: float = 0.05
    
    # Amplitude des anomalies
    anomalie_temperature_haute: float = 12.0
    anomalie_temperature_basse: float = -10.0
    
    def __post_init__(self):
        if self.sensor_ids is None:
            self.sensor_ids = ["C001", "C002", "C003"]


# ============================================================================
# CONFIGURATION DE L'IA
# ============================================================================

@dataclass
class IAConfig:
    """Configuration du module de détection d'anomalies"""
    
    # Paramètres Isolation Forest
    contamination: float = 0.05  # 5% d'anomalies attendues
    random_state: int = 42
    n_estimators: int = 100
    
    # Seuil Z-score pour détection
    zscore_seuil: float = 3.0
    
    # Taille de la fenêtre d'analyse (nombre de mesures)
    fenetre_analyse: int = 100


# ============================================================================
# CONFIGURATION DU DASHBOARD
# ============================================================================

@dataclass
class DashboardConfig:
    """Configuration du tableau de bord Streamlit"""
    
    # Intervalle de rafraîchissement (en secondes)
    refresh_interval: int = 5
    
    # Nombre de points à afficher sur le graphique
    points_graphique: int = 50
    
    # Nombre de lignes dans le tableau
    lignes_tableau: int = 10
    
    # Chemins des fichiers de données
    fichier_historique: str = "data/historique.csv"
    fichier_anomalies: str = "data/anomalies.csv"


# ============================================================================
# CONFIGURATION DU STOCKAGE
# ============================================================================

@dataclass
class StockageConfig:
    """Configuration du stockage des données"""
    
    # Stockage local
    dossier_data: str = "data"
    
    # MongoDB Atlas (chargé depuis .env)
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "iot_supervision")
    mongodb_collection: str = os.getenv("MONGODB_COLLECTION", "mesures")


# ============================================================================
# INSTANCES DE CONFIGURATION
# ============================================================================

# Créer les instances de configuration
mqtt_config = MQTTConfig()
capteur_config = CapteurConfig()
ia_config = IAConfig()
dashboard_config = DashboardConfig()
stockage_config = StockageConfig()


# ============================================================================
# FONCTION DE VALIDATION
# ============================================================================

def valider_configuration() -> bool:
    """
    Vérifie que la configuration est valide et complète.
    Retourne True si tout est OK, False sinon.
    """
    erreurs = []
    
    # Vérifier la configuration MQTT
    if mqtt_config.host == "VOTRE_HOST.s1.eu.hivemq.cloud":
        erreurs.append("⚠️  Le host MQTT n'est pas configuré")
    
    if mqtt_config.username == "VOTRE_USERNAME":
        erreurs.append("⚠️  Le username MQTT n'est pas configuré")
    
    if mqtt_config.password == "VOTRE_PASSWORD":
        erreurs.append("⚠️  Le password MQTT n'est pas configuré")
    
    if erreurs:
        print("=" * 60)
        print("CONFIGURATION INCOMPLÈTE")
        print("=" * 60)
        for err in erreurs:
            print(err)
        print("\nVeuillez modifier le fichier config.py avec vos credentials HiveMQ")
        print("=" * 60)
        return False
    
    return True


def afficher_configuration():
    """Affiche la configuration actuelle (sans les mots de passe)"""
    print("=" * 60)
    print("CONFIGURATION DU SYSTÈME IoT")
    print("=" * 60)
    print(f"\n📡 MQTT Broker:")
    print(f"   Host: {mqtt_config.host}")
    print(f"   Port: {mqtt_config.port}")
    print(f"   TLS:  {'Activé' if mqtt_config.use_tls else 'Désactivé'}")
    print(f"\n🌡️  Capteurs simulés: {capteur_config.sensor_ids}")
    print(f"   Intervalle: {capteur_config.intervalle_envoi}s")
    print(f"\n🤖 IA - Isolation Forest:")
    print(f"   Contamination: {ia_config.contamination * 100}%")
    print(f"   Z-score seuil: {ia_config.zscore_seuil}")
    print("=" * 60)


# Test de la configuration si exécuté directement
if __name__ == "__main__":
    afficher_configuration()
    print("\nValidation:", "✅ OK" if valider_configuration() else "❌ ÉCHEC")
