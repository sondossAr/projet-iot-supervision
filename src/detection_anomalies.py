import paho.mqtt.client as mqtt
import json
import ssl
import os
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import deque

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Import de la configuration
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import mqtt_config, ia_config, stockage_config

# MongoDB Atlas
try:
    from pymongo import MongoClient
    from pymongo.server_api import ServerApi
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("⚠️  pymongo non installé - stockage MongoDB désactivé")


# ============================================================================
# CLASSE PRINCIPALE DE DÉTECTION D'ANOMALIES
# ============================================================================

class DetecteurAnomalies: 
    def __init__(self):
        # Buffer de données pour l'analyse
        self.buffer_taille = ia_config.fenetre_analyse
        self.buffer_donnees: deque = deque(maxlen=self.buffer_taille)
        
        # Historique complet pour le CSV
        self.historique: List[Dict] = []
        
        # Anomalies détectées
        self.anomalies: List[Dict] = []
        
        # Modèle Isolation Forest
        self.model: Optional[IsolationForest] = None
        
        # Statistiques en cours
        self.stats = {
            "count": 0,
            "mean_temp": 0,
            "std_temp": 0,
            "mean_hum": 0,
            "std_hum": 0
        }
        
        # Création du dossier data si nécessaire
        os.makedirs(stockage_config.dossier_data, exist_ok=True)
        
        # Connexion MongoDB Atlas
        self.mongodb_client = None
        self.mongodb_db = None
        self._connecter_mongodb()
        
        print("🤖 Détecteur d'anomalies initialisé")
        print(f"   Fenêtre d'analyse : {self.buffer_taille} mesures")
        print(f"   Seuil Z-score : {ia_config.zscore_seuil}")
        print(f"   Contamination Isolation Forest : {ia_config.contamination * 100}%")
    
    def _connecter_mongodb(self):
        if not MONGODB_AVAILABLE:
            print("⚠️  MongoDB non disponible")
            return
        
        if not stockage_config.mongodb_uri:
            print("⚠️  MongoDB URI non configurée - stockage local uniquement")
            return
        
        try:
            self.mongodb_client = MongoClient(
                stockage_config.mongodb_uri, 
                server_api=ServerApi('1')
            )
            self.mongodb_db = self.mongodb_client[stockage_config.mongodb_database]
            # Test de connexion
            self.mongodb_client.admin.command('ping')
            print("☁️  Connecté à MongoDB Atlas")
        except Exception as e:
            print(f"❌ Erreur MongoDB : {e}")
            self.mongodb_client = None
            self.mongodb_db = None
    
    def sauvegarder_mongodb(self, donnee: Dict):
        if self.mongodb_db is None:
            return
        
        try:
            # Convertir les types numpy en types Python natifs
            donnee_clean = {}
            for key, value in donnee.items():
                if hasattr(value, 'item'):  # numpy type
                    donnee_clean[key] = value.item()
                else:
                    donnee_clean[key] = value
            
            collection = self.mongodb_db[stockage_config.mongodb_collection]
            collection.insert_one(donnee_clean)
        except Exception as e:
            print(f"⚠️  Erreur sauvegarde MongoDB : {e}")
    
    # ========================================================================
    # MÉTHODES DE DÉTECTION
    # ========================================================================
    
    def calculer_zscore(self, valeur: float, moyenne: float, ecart_type: float) -> float:
        if ecart_type == 0:
            return 0
        return (valeur - moyenne) / ecart_type
    
    def detecter_zscore(self, temperature: float, humidite: float) -> Dict:
        if self.stats["count"] < 10:
            # Pas assez de données pour calculer des statistiques fiables
            return {"is_anomaly": False, "method": "zscore", "details": "Données insuffisantes"}
        
        z_temp = self.calculer_zscore(temperature, self.stats["mean_temp"], self.stats["std_temp"])
        z_hum = self.calculer_zscore(humidite, self.stats["mean_hum"], self.stats["std_hum"])
        
        is_anomaly = abs(z_temp) > ia_config.zscore_seuil or abs(z_hum) > ia_config.zscore_seuil
        
        return {
            "is_anomaly": is_anomaly,
            "method": "zscore",
            "z_temperature": round(z_temp, 2),
            "z_humidity": round(z_hum, 2),
            "seuil": ia_config.zscore_seuil
        }
    
    def detecter_isolation_forest(self, temperature: float, humidite: float) -> Dict:
        if len(self.buffer_donnees) < 20:
            # Pas assez de données pour entraîner le modèle
            return {"is_anomaly": False, "method": "isolation_forest", "details": "Données insuffisantes"}
        
        # Préparer les données pour le modèle
        df = pd.DataFrame(list(self.buffer_donnees))
        X = df[["temperature", "humidity"]].values
        
        # Entraîner/mettre à jour le modèle
        self.model = IsolationForest(
            contamination=ia_config.contamination,
            random_state=ia_config.random_state,
            n_estimators=ia_config.n_estimators
        )
        self.model.fit(X)
        
        # Prédire sur la nouvelle valeur
        nouvelle_valeur = np.array([[temperature, humidite]])
        prediction = self.model.predict(nouvelle_valeur)[0]
        score = self.model.decision_function(nouvelle_valeur)[0]
        
        # -1 = anomalie, 1 = normal
        is_anomaly = prediction == -1
        
        return {
            "is_anomaly": is_anomaly,
            "method": "isolation_forest",
            "prediction": int(prediction),
            "anomaly_score": round(score, 4)
        }
    
    def detecter_anomalie(self, donnee: Dict) -> Dict:
        temperature = donnee["temperature"]
        humidite = donnee["humidity"]
        
        # Détection par Z-score
        result_zscore = self.detecter_zscore(temperature, humidite)
        
        # Détection par Isolation Forest
        result_iforest = self.detecter_isolation_forest(temperature, humidite)
        
        # Combiner les résultats
        is_anomaly = result_zscore["is_anomaly"] or result_iforest["is_anomaly"]
        
        # Déterminer la méthode qui a détecté l'anomalie
        detection_methods = []
        if result_zscore["is_anomaly"]:
            detection_methods.append("Z-score")
        if result_iforest["is_anomaly"]:
            detection_methods.append("Isolation Forest")
        
        return {
            "is_anomaly": is_anomaly,
            "detection_methods": detection_methods,
            "zscore_result": result_zscore,
            "iforest_result": result_iforest
        }
    
    # ========================================================================
    # MÉTHODES DE MISE À JOUR
    # ========================================================================
    
    def mettre_a_jour_stats(self):
        if len(self.buffer_donnees) < 2:
            return
        
        df = pd.DataFrame(list(self.buffer_donnees))
        
        self.stats["count"] = len(df)
        self.stats["mean_temp"] = df["temperature"].mean()
        self.stats["std_temp"] = df["temperature"].std()
        self.stats["mean_hum"] = df["humidity"].mean()
        self.stats["std_hum"] = df["humidity"].std()
    
    def ajouter_donnee(self, donnee: Dict) -> Dict:
        # Ajouter au buffer
        self.buffer_donnees.append(donnee)
        
        # Mettre à jour les statistiques
        self.mettre_a_jour_stats()
        
        # Détecter les anomalies
        result = self.detecter_anomalie(donnee)
        
        # Enrichir la donnée avec le résultat
        donnee_enrichie = {
            **donnee,
            "is_anomaly": result["is_anomaly"],
            "status": "ANOMALIE" if result["is_anomaly"] else "NORMAL",
            "detection_methods": ",".join(result["detection_methods"]) if result["detection_methods"] else ""
        }
        
        # Ajouter à l'historique
        self.historique.append(donnee_enrichie)
        
        # Sauvegarder dans MongoDB Atlas (temps réel)
        self.sauvegarder_mongodb(donnee_enrichie)
        
        # Si anomalie, l'ajouter à la liste des anomalies
        if result["is_anomaly"]:
            self.anomalies.append(donnee_enrichie)
        
        return result
    
    # ========================================================================
    # MÉTHODES DE SAUVEGARDE ET VISUALISATION
    # ========================================================================
    
    def sauvegarder_csv(self):
        if not self.historique:
            print("⚠️  Aucune donnée à sauvegarder")
            return
        
        # Chemin du fichier
        fichier_historique = os.path.join(
            stockage_config.dossier_data,
            "historique.csv"
        )
        
        # Convertir en DataFrame et sauvegarder
        df = pd.DataFrame(self.historique)
        df.to_csv(fichier_historique, index=False, encoding="utf-8")
        print(f"💾 Historique sauvegardé : {fichier_historique} ({len(df)} lignes)")
        
        # Sauvegarder aussi les anomalies séparément
        if self.anomalies:
            fichier_anomalies = os.path.join(
                stockage_config.dossier_data,
                "anomalies.csv"
            )
            df_anomalies = pd.DataFrame(self.anomalies)
            df_anomalies.to_csv(fichier_anomalies, index=False, encoding="utf-8")
            print(f"🚨 Anomalies sauvegardées : {fichier_anomalies} ({len(df_anomalies)} lignes)")
    
    def generer_graphique(self):
        if len(self.historique) < 5:
            print("⚠️  Pas assez de données pour générer un graphique")
            return
        
        df = pd.DataFrame(self.historique)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Créer la figure avec 2 sous-graphiques
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Séparer les données normales et les anomalies
        df_normal = df[df["is_anomaly"] == False]
        df_anomaly = df[df["is_anomaly"] == True]
        
        # Graphique 1 : Température
        ax1.plot(df["timestamp"], df["temperature"], 'b-', label="Température", alpha=0.7)
        ax1.scatter(df_normal["timestamp"], df_normal["temperature"], c='blue', s=20, alpha=0.5)
        ax1.scatter(df_anomaly["timestamp"], df_anomaly["temperature"], c='red', s=100, marker='x', label="Anomalies", linewidths=2)
        ax1.axhline(y=self.stats["mean_temp"], color='green', linestyle='--', label=f"Moyenne ({self.stats['mean_temp']:.1f}°C)")
        ax1.fill_between(df["timestamp"], 
                         self.stats["mean_temp"] - 3*self.stats["std_temp"],
                         self.stats["mean_temp"] + 3*self.stats["std_temp"],
                         alpha=0.2, color='green', label="Zone normale (±3σ)")
        ax1.set_ylabel("Température (°C)")
        ax1.set_title("🌡️ Température des capteurs IoT avec détection d'anomalies")
        ax1.legend(loc="upper right")
        ax1.grid(True, alpha=0.3)
        
        # Graphique 2 : Humidité
        ax2.plot(df["timestamp"], df["humidity"], 'c-', label="Humidité", alpha=0.7)
        ax2.scatter(df_normal["timestamp"], df_normal["humidity"], c='cyan', s=20, alpha=0.5)
        ax2.scatter(df_anomaly["timestamp"], df_anomaly["humidity"], c='red', s=100, marker='x', label="Anomalies", linewidths=2)
        ax2.axhline(y=self.stats["mean_hum"], color='green', linestyle='--', label=f"Moyenne ({self.stats['mean_hum']:.1f}%)")
        ax2.set_ylabel("Humidité (%)")
        ax2.set_xlabel("Temps")
        ax2.legend(loc="upper right")
        ax2.grid(True, alpha=0.3)
        
        # Formater l'axe des X
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.xticks(rotation=45)
        
        # Ajuster la mise en page
        plt.tight_layout()
        
        # Sauvegarder le graphique
        chemin_graphique = os.path.join(stockage_config.dossier_data, "graphique_anomalies.png")
        plt.savefig(chemin_graphique, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Graphique généré : {chemin_graphique}")
    
    def afficher_stats(self):
        print("\n" + "=" * 50)
        print("📈 STATISTIQUES ACTUELLES")
        print("=" * 50)
        print(f"Nombre de mesures : {self.stats['count']}")
        print(f"Température moyenne : {self.stats['mean_temp']:.2f}°C (σ = {self.stats['std_temp']:.2f})")
        print(f"Humidité moyenne : {self.stats['mean_hum']:.2f}% (σ = {self.stats['std_hum']:.2f})")
        print(f"Anomalies détectées : {len(self.anomalies)}")
        print("=" * 50)


# ============================================================================
# CLIENT MQTT POUR LA RÉCEPTION DES DONNÉES
# ============================================================================

class RecepteurMQTT:
    
    def __init__(self, detecteur: DetecteurAnomalies):
        self.detecteur = detecteur
        self.client = None
        self.compteur_messages = 0
    
    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        is_success = str(reason_code) == "Success" or reason_code == 0
        
        if is_success:
            print("✅ Connecté au broker MQTT")
            # S'abonner au topic des capteurs
            client.subscribe(mqtt_config.topic_temperature)
            print(f"📥 Abonné au topic : {mqtt_config.topic_temperature}")
        else:
            print(f"❌ Erreur de connexion : {reason_code}")
    
    def on_message(self, client, userdata, msg):
        try:
            # Décoder le message JSON
            payload = json.loads(msg.payload.decode())
            self.compteur_messages += 1
            
            # Afficher la donnée reçue
            sensor_id = payload.get("sensor_id", "???")
            temperature = payload.get("temperature", 0)
            humidity = payload.get("humidity", 0)
            
            # Ajouter au détecteur et analyser
            result = self.detecteur.ajouter_donnee(payload)
            
            # Affichage formaté
            if result["is_anomaly"]:
                methods = ", ".join(result["detection_methods"])
                print(f"🚨 [{sensor_id}] ANOMALIE DÉTECTÉE ! ({methods})")
                print(f"   Température : {temperature}°C | Humidité : {humidity}%")
            else:
                print(f"✅ [{sensor_id}] Normal - Temp: {temperature}°C | Hum: {humidity}%")
            
            # Sauvegarder périodiquement (toutes les 10 mesures)
            if self.compteur_messages % 10 == 0:
                self.detecteur.sauvegarder_csv()
                self.detecteur.afficher_stats()
            
            # Générer un graphique toutes les 30 mesures
            if self.compteur_messages % 30 == 0:
                self.detecteur.generer_graphique()
                
        except json.JSONDecodeError as e:
            print(f"⚠️  Erreur de décodage JSON : {e}")
        except Exception as e:
            print(f"⚠️  Erreur de traitement : {e}")
    
    def on_disconnect(self, client, userdata, rc, properties=None, reason_code=None):
        if rc != 0:
            print(f"⚠️  Déconnexion inattendue")
    
    def demarrer(self):
        print("\n" + "=" * 50)
        print("🤖 MODULE DE DÉTECTION D'ANOMALIES")
        print("=" * 50)
        print("Connexion au broker MQTT...")
        
        # Créer le client MQTT
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        except (AttributeError, TypeError):
            self.client = mqtt.Client()
        
        # Configurer les callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Authentification
        self.client.username_pw_set(mqtt_config.username, mqtt_config.password)
        
        # TLS
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        
        try:
            # Connexion
            self.client.connect(mqtt_config.host, mqtt_config.port, mqtt_config.keepalive)
            
            print("\n📡 En attente de données des capteurs...")
            print("   (Appuyez sur Ctrl+C pour arrêter)\n")
            
            # Boucle de réception
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Arrêt du récepteur...")
            self.detecteur.sauvegarder_csv()
            self.detecteur.generer_graphique()
        except Exception as e:
            print(f"\n❌ Erreur : {e}")
        finally:
            if self.client:
                self.client.disconnect()
            print("✅ Déconnexion effectuée.")


# ============================================================================
# FONCTION DE DÉTECTION SUR DONNÉES EXISTANTES (MODE BATCH)
# ============================================================================

def analyser_fichier_csv(chemin_csv: str):
    print(f"\n📂 Analyse du fichier : {chemin_csv}")
    
    # Charger les données
    df = pd.read_csv(chemin_csv)
    print(f"   {len(df)} lignes chargées")
    
    # Créer le détecteur
    detecteur = DetecteurAnomalies()
    
    # Analyser chaque ligne
    for _, row in df.iterrows():
        donnee = {
            "sensor_id": row.get("sensor_id", "BATCH"),
            "timestamp": row.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "temperature": row["temperature"],
            "humidity": row["humidity"]
        }
        detecteur.ajouter_donnee(donnee)
    
    # Afficher les résultats
    detecteur.afficher_stats()
    detecteur.sauvegarder_csv()
    detecteur.generer_graphique()
    
    # Créer le DataFrame avec les résultats
    df_result = pd.DataFrame(detecteur.historique)
    
    return df_result


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

def main():
    # Créer le détecteur d'anomalies
    detecteur = DetecteurAnomalies()
    
    # Créer et démarrer le récepteur MQTT
    recepteur = RecepteurMQTT(detecteur)
    recepteur.demarrer()


if __name__ == "__main__":
    main()
