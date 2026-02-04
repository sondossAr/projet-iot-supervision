"""
☁️ Module d'Intégration Cloud
==============================
Ce module gère le stockage distant des données via MongoDB Atlas.

Fonctionnalités :
- Stockage MongoDB Atlas (base de données Cloud)
- Intégration avec le service d'email (email_service.py)
"""

import os
from datetime import datetime, timezone
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# ============================================================================
# CONFIGURATION CLOUD
# ============================================================================

@dataclass
class CloudConfig:
    """Configuration des services Cloud"""
    
    # MongoDB Atlas
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_database: str = "iot_supervision"
    mongodb_collection_mesures: str = "mesures"
    mongodb_collection_anomalies: str = "anomalies"
    
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
        """Sauvegarde une mesure dans MongoDB."""
        if not self.connected:
            return False
        
        try:
            collection = self.db[cloud_config.mongodb_collection_mesures]
            mesure["_created_at"] = datetime.now(timezone.utc)
            result = collection.insert_one(mesure)
            return result.acknowledged
        except Exception as e:
            print(f"❌ Erreur sauvegarde MongoDB : {e}")
            return False
    
    def sauvegarder_anomalie(self, anomalie: Dict) -> bool:
        """Sauvegarde une anomalie dans la collection dédiée."""
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
        """Récupère les mesures récentes depuis MongoDB."""
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
        """Récupère les anomalies récentes depuis MongoDB."""
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
# GESTIONNAIRE CLOUD UNIFIÉ
# ============================================================================

class CloudManager:
    """
    Gestionnaire unifié pour les services Cloud.
    Centralise MongoDB et les alertes email.
    """
    
    def __init__(self):
        """Initialise les services Cloud."""
        print("\n" + "=" * 50)
        print("☁️  INITIALISATION DES SERVICES CLOUD")
        print("=" * 50)
        
        # Initialiser MongoDB
        self.storage = MongoDBStorage()
        
        # Initialiser le service email
        try:
            from email_service import EmailService
            self.email = EmailService()
        except ImportError:
            self.email = None
            print("⚠️  Service email non disponible")
        
        print("=" * 50 + "\n")
    
    def traiter_mesure(self, mesure: Dict):
        """Traite une mesure : stockage et vérification des alertes."""
        # Sauvegarder dans MongoDB
        self.storage.sauvegarder_mesure(mesure.copy())
        
        # Vérifier les seuils d'alerte
        temperature = mesure.get("temperature", 0)
        sensor_id = mesure.get("sensor_id", "UNKNOWN")
        
        if self.email and (temperature > cloud_config.seuil_temperature_haute or 
                          temperature < cloud_config.seuil_temperature_basse):
            self.email.alerte_temperature_critique(sensor_id, temperature)
    
    def traiter_anomalie(self, anomalie: Dict):
        """Traite une anomalie détectée."""
        # Sauvegarder dans MongoDB
        self.storage.sauvegarder_anomalie(anomalie.copy())
        
        # Envoyer une alerte email
        if self.email:
            sensor_id = anomalie.get("sensor_id", "UNKNOWN")
            temperature = anomalie.get("temperature", 0)
            humidity = anomalie.get("humidity", 0)
            self.email.alerte_anomalie(sensor_id, temperature, humidity)
    
    def close(self):
        """Ferme toutes les connexions."""
        self.storage.close()


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
    
    # Fermer les connexions
    cloud.close()
    
    print("\n✅ Tests terminés")
