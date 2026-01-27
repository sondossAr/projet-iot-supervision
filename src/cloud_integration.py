"""
☁️ Module d'Intégration Cloud
==============================
Ce module gère le stockage distant des données et les alertes.

Fonctionnalités :
- Stockage MongoDB Atlas (base de données Cloud)
- Service d'alertes par email (SendGrid)
- Préparation pour déploiement Streamlit Cloud

Auteur : Projet Examen 5 BIM IA
Date : Janvier 2026
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass

# ============================================================================
# CONFIGURATION CLOUD
# ============================================================================

@dataclass
class CloudConfig:
    """Configuration des services Cloud"""
    
    # MongoDB Atlas
    # Créer un compte gratuit sur : https://www.mongodb.com/cloud/atlas
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_database: str = "iot_supervision"
    mongodb_collection_mesures: str = "mesures"
    mongodb_collection_anomalies: str = "anomalies"
    
    # SendGrid (service d'email)
    # Créer un compte gratuit sur : https://sendgrid.com/
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    email_from: str = os.getenv("EMAIL_FROM", "alerts@iot-supervision.com")
    email_to: str = os.getenv("EMAIL_TO", "admin@example.com")
    
    # Seuils d'alerte
    seuil_temperature_haute: float = 35.0
    seuil_temperature_basse: float = 10.0
    seuil_humidite_haute: float = 80.0
    seuil_humidite_basse: float = 20.0


cloud_config = CloudConfig()


# ============================================================================
# STOCKAGE MONGODB ATLAS
# ============================================================================

class MongoDBStorage:
    """
    Gestionnaire de stockage MongoDB Atlas.
    
    MongoDB Atlas est une base de données NoSQL Cloud qui permet
    de stocker les données IoT de manière scalable et sécurisée.
    """
    
    def __init__(self, uri: str = None):
        """
        Initialise la connexion MongoDB.
        
        Arguments :
            uri : URI de connexion MongoDB Atlas
        """
        self.uri = uri or cloud_config.mongodb_uri
        self.client = None
        self.db = None
        self.connected = False
        
        if self.uri:
            self._connect()
    
    def _connect(self):
        """Établit la connexion à MongoDB Atlas."""
        try:
            # Import conditionnel de pymongo
            from pymongo import MongoClient
            from pymongo.server_api import ServerApi
            
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            self.db = self.client[cloud_config.mongodb_database]
            
            # Test de connexion
            self.client.admin.command('ping')
            self.connected = True
            print("✅ Connecté à MongoDB Atlas")
            
        except ImportError:
            print("⚠️  pymongo non installé. Installez avec : pip install pymongo")
            self.connected = False
        except Exception as e:
            print(f"❌ Erreur de connexion MongoDB : {e}")
            self.connected = False
    
    def sauvegarder_mesure(self, mesure: Dict) -> bool:
        """
        Sauvegarde une mesure dans MongoDB.
        
        Arguments :
            mesure : Dictionnaire contenant les données du capteur
        
        Retourne :
            True si succès, False sinon
        """
        if not self.connected:
            return False
        
        try:
            collection = self.db[cloud_config.mongodb_collection_mesures]
            
            # Ajouter métadonnées
            mesure["_created_at"] = datetime.now(timezone.utc)
            
            result = collection.insert_one(mesure)
            return result.acknowledged
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde MongoDB : {e}")
            return False
    
    def sauvegarder_anomalie(self, anomalie: Dict) -> bool:
        """
        Sauvegarde une anomalie dans la collection dédiée.
        
        Arguments :
            anomalie : Dictionnaire contenant l'anomalie détectée
        
        Retourne :
            True si succès, False sinon
        """
        if not self.connected:
            return False
        
        try:
            collection = self.db[cloud_config.mongodb_collection_anomalies]
            anomalie["_created_at"] = datetime.now(timezone.utc)
            
            result = collection.insert_one(anomalie)
            return result.acknowledged
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde anomalie MongoDB : {e}")
            return False
    
    def get_mesures_recentes(self, limit: int = 100) -> List[Dict]:
        """
        Récupère les mesures récentes depuis MongoDB.
        
        Arguments :
            limit : Nombre maximum de mesures à retourner
        
        Retourne :
            Liste de dictionnaires contenant les mesures
        """
        if not self.connected:
            return []
        
        try:
            collection = self.db[cloud_config.mongodb_collection_mesures]
            cursor = collection.find().sort("timestamp", -1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            print(f"❌ Erreur lecture MongoDB : {e}")
            return []
    
    def get_anomalies(self, limit: int = 50) -> List[Dict]:
        """
        Récupère les anomalies récentes depuis MongoDB.
        
        Arguments :
            limit : Nombre maximum d'anomalies à retourner
        
        Retourne :
            Liste de dictionnaires contenant les anomalies
        """
        if not self.connected:
            return []
        
        try:
            collection = self.db[cloud_config.mongodb_collection_anomalies]
            cursor = collection.find().sort("timestamp", -1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            print(f"❌ Erreur lecture anomalies MongoDB : {e}")
            return []
    
    def close(self):
        """Ferme la connexion MongoDB."""
        if self.client:
            self.client.close()
            self.connected = False
            print("✅ Connexion MongoDB fermée")


# ============================================================================
# SERVICE D'ALERTES EMAIL (SendGrid)
# ============================================================================

class AlerteService:
    """
    Service d'envoi d'alertes par email via SendGrid.
    
    SendGrid est un service d'envoi d'emails transactionnels
    qui permet d'envoyer des alertes en cas d'anomalie critique.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialise le service d'alertes.
        
        Arguments :
            api_key : Clé API SendGrid
        """
        self.api_key = api_key or cloud_config.sendgrid_api_key
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            print("✅ Service d'alertes email activé")
        else:
            print("⚠️  Service d'alertes désactivé (pas de clé API)")
    
    def envoyer_alerte(self, sujet: str, message: str, niveau: str = "warning") -> bool:
        """
        Envoie une alerte par email.
        
        Arguments :
            sujet : Sujet de l'email
            message : Corps du message
            niveau : Niveau d'alerte (info, warning, critical)
        
        Retourne :
            True si envoi réussi, False sinon
        """
        if not self.enabled:
            print(f"📧 [SIMULATION] Alerte : {sujet}")
            return False
        
        try:
            # Import conditionnel de sendgrid
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            # Construire le message
            html_content = self._generer_html_alerte(sujet, message, niveau)
            
            mail = Mail(
                from_email=cloud_config.email_from,
                to_emails=cloud_config.email_to,
                subject=f"[IoT Alert - {niveau.upper()}] {sujet}",
                html_content=html_content
            )
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(mail)
            
            if response.status_code == 202:
                print(f"✅ Alerte envoyée : {sujet}")
                return True
            else:
                print(f"⚠️  Réponse SendGrid : {response.status_code}")
                return False
                
        except ImportError:
            print("⚠️  sendgrid non installé. Installez avec : pip install sendgrid")
            return False
        except Exception as e:
            print(f"❌ Erreur envoi alerte : {e}")
            return False
    
    def _generer_html_alerte(self, sujet: str, message: str, niveau: str) -> str:
        """Génère le contenu HTML de l'alerte."""
        couleurs = {
            "info": "#2196F3",
            "warning": "#FF9800",
            "critical": "#F44336"
        }
        couleur = couleurs.get(niveau, "#757575")
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background-color: {couleur}; color: white; padding: 15px; border-radius: 5px;">
                <h2>🚨 {sujet}</h2>
            </div>
            <div style="padding: 20px; background-color: #f5f5f5; border-radius: 5px; margin-top: 10px;">
                <p>{message}</p>
            </div>
            <div style="margin-top: 20px; color: #757575; font-size: 12px;">
                <p>IoT Supervision System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
    
    def alerte_temperature_critique(self, sensor_id: str, temperature: float):
        """
        Envoie une alerte pour température critique.
        
        Arguments :
            sensor_id : Identifiant du capteur
            temperature : Température mesurée
        """
        if temperature > cloud_config.seuil_temperature_haute:
            sujet = f"Surchauffe détectée - Capteur {sensor_id}"
            message = f"""
            <strong>Capteur :</strong> {sensor_id}<br>
            <strong>Température :</strong> {temperature}°C<br>
            <strong>Seuil :</strong> {cloud_config.seuil_temperature_haute}°C<br>
            <strong>Action recommandée :</strong> Vérifier le système de refroidissement
            """
            self.envoyer_alerte(sujet, message, "critical")
            
        elif temperature < cloud_config.seuil_temperature_basse:
            sujet = f"Sous-température détectée - Capteur {sensor_id}"
            message = f"""
            <strong>Capteur :</strong> {sensor_id}<br>
            <strong>Température :</strong> {temperature}°C<br>
            <strong>Seuil :</strong> {cloud_config.seuil_temperature_basse}°C<br>
            <strong>Action recommandée :</strong> Vérifier le système de chauffage
            """
            self.envoyer_alerte(sujet, message, "warning")


# ============================================================================
# GESTIONNAIRE CLOUD UNIFIÉ
# ============================================================================

class CloudManager:
    """
    Gestionnaire unifié pour tous les services Cloud.
    
    Centralise la gestion du stockage MongoDB et des alertes.
    """
    
    def __init__(self):
        """Initialise tous les services Cloud."""
        print("\n" + "=" * 50)
        print("☁️  INITIALISATION DES SERVICES CLOUD")
        print("=" * 50)
        
        # Initialiser MongoDB
        self.storage = MongoDBStorage()
        
        # Initialiser les alertes
        self.alertes = AlerteService()
        
        print("=" * 50 + "\n")
    
    def traiter_mesure(self, mesure: Dict):
        """
        Traite une mesure : stockage et vérification des alertes.
        
        Arguments :
            mesure : Dictionnaire contenant les données du capteur
        """
        # Sauvegarder dans MongoDB
        self.storage.sauvegarder_mesure(mesure.copy())
        
        # Vérifier les seuils d'alerte
        temperature = mesure.get("temperature", 0)
        sensor_id = mesure.get("sensor_id", "UNKNOWN")
        
        if temperature > cloud_config.seuil_temperature_haute or \
           temperature < cloud_config.seuil_temperature_basse:
            self.alertes.alerte_temperature_critique(sensor_id, temperature)
    
    def traiter_anomalie(self, anomalie: Dict):
        """
        Traite une anomalie détectée.
        
        Arguments :
            anomalie : Dictionnaire contenant l'anomalie
        """
        # Sauvegarder dans MongoDB
        self.storage.sauvegarder_anomalie(anomalie.copy())
        
        # Envoyer une alerte
        sensor_id = anomalie.get("sensor_id", "UNKNOWN")
        temperature = anomalie.get("temperature", 0)
        
        sujet = f"Anomalie détectée - Capteur {sensor_id}"
        message = f"""
        <strong>Capteur :</strong> {sensor_id}<br>
        <strong>Température :</strong> {temperature}°C<br>
        <strong>Humidité :</strong> {anomalie.get('humidity', 'N/A')}%<br>
        <strong>Timestamp :</strong> {anomalie.get('timestamp', 'N/A')}
        """
        self.alertes.envoyer_alerte(sujet, message, "warning")
    
    def close(self):
        """Ferme toutes les connexions."""
        self.storage.close()


# ============================================================================
# FICHIERS DE DÉPLOIEMENT
# ============================================================================

def generer_fichiers_deploiement():
    """
    Génère les fichiers nécessaires pour le déploiement Cloud.
    """
    import os
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Fichier requirements.txt pour Streamlit Cloud
    requirements_cloud = """# Dépendances pour Streamlit Cloud
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.15.0
paho-mqtt>=1.6.1
scikit-learn>=1.3.0
pymongo>=4.5.0
sendgrid>=6.10.0
python-dotenv>=1.0.0
"""
    
    # 2. Fichier .streamlit/config.toml
    streamlit_config = """[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false

[browser]
gatherUsageStats = false
"""
    
    # 3. Fichier secrets.toml (template)
    secrets_template = """# Secrets pour Streamlit Cloud
# NE PAS COMMITER CE FICHIER !

[mqtt]
host = "votre_host.s1.eu.hivemq.cloud"
port = 8883
username = "votre_username"
password = "votre_password"

[mongodb]
uri = "mongodb+srv://user:password@cluster.mongodb.net/"

[sendgrid]
api_key = "SG.xxxxx"
email_from = "alerts@iot-supervision.com"
email_to = "admin@example.com"
"""
    
    print("📁 Fichiers de déploiement générés :")
    print(f"   - requirements.txt (pour Cloud)")
    print(f"   - .streamlit/config.toml")
    print(f"   - .streamlit/secrets.toml (template)")
    
    return {
        "requirements_cloud": requirements_cloud,
        "streamlit_config": streamlit_config,
        "secrets_template": secrets_template
    }


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("☁️  TEST DES SERVICES CLOUD")
    print("=" * 60)
    
    # Créer le gestionnaire Cloud
    cloud = CloudManager()
    
    # Tester avec une mesure simulée
    mesure_test = {
        "sensor_id": "C001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature": 25.5,
        "humidity": 42.0
    }
    
    print("\n📊 Test de traitement d'une mesure normale...")
    cloud.traiter_mesure(mesure_test)
    
    # Tester avec une anomalie
    anomalie_test = {
        "sensor_id": "C002",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature": 38.5,
        "humidity": 45.0,
        "is_anomaly": True
    }
    
    print("\n🚨 Test de traitement d'une anomalie...")
    cloud.traiter_anomalie(anomalie_test)
    
    # Générer les fichiers de déploiement
    print("\n📁 Génération des fichiers de déploiement...")
    generer_fichiers_deploiement()
    
    # Fermer les connexions
    cloud.close()
    
    print("\n✅ Tests terminés")
