"""
🛰️ Simulateur de Capteurs IoT
============================
Ce script simule 3 capteurs de température/humidité qui publient
leurs données vers un broker MQTT Cloud (HiveMQ).

Fonctionnalités :
- Simulation de 3 capteurs (C001, C002, C003)
- Envoi des données toutes les 3 secondes
- Injection aléatoire d'anomalies (5% de probabilité)
- Connexion sécurisée TLS

Auteur : Projet Examen 5 BIM IA
Date : Janvier 2026
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import ssl
from datetime import datetime, timezone
from typing import Dict, Any

# Import de la configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import mqtt_config, capteur_config


# ============================================================================
# FONCTIONS DE CALLBACK MQTT
# ============================================================================

def on_connect(client, userdata, flags, reason_code, properties=None):
    """
    Callback appelée lors de la connexion au broker MQTT.
    
    Codes de retour (reason_code) :
    - 0 / Success : Connexion réussie
    - Autres : Erreurs diverses
    """
    # Vérifier si la connexion est réussie
    is_success = str(reason_code) == "Success" or reason_code == 0
    
    if is_success:
        print("✅ Connexion réussie au broker MQTT !")
    else:
        print(f"❌ Erreur de connexion : {reason_code}")
    
    if is_success:
        print(f"   Broker : {mqtt_config.host}")
        print(f"   Port   : {mqtt_config.port}")
        print(f"   Topic  : {mqtt_config.topic_temperature}")
        print("-" * 50)


def on_publish(client, userdata, mid, properties=None, reason_code=None):
    """Callback appelée après chaque publication réussie."""
    pass  # Silencieux pour éviter trop de logs


def on_disconnect(client, userdata, rc, properties=None, reason_code=None):
    """Callback appelée lors de la déconnexion."""
    if rc != 0:
        print(f"⚠️  Déconnexion inattendue (code: {rc})")


# ============================================================================
# FONCTIONS DE SIMULATION
# ============================================================================

def generer_mesure_normale() -> Dict[str, float]:
    """
    Génère une mesure normale de température et humidité
    basée sur les paramètres de configuration.
    
    Retourne :
        Dict avec 'temperature' et 'humidity'
    """
    temperature = capteur_config.temperature_moyenne + random.gauss(0, capteur_config.temperature_ecart_type)
    humidite = capteur_config.humidite_moyenne + random.gauss(0, capteur_config.humidite_ecart_type)
    
    return {
        "temperature": round(temperature, 2),
        "humidity": round(humidite, 1)
    }


def injecter_anomalie(mesure: Dict[str, float]) -> Dict[str, Any]:
    """
    Injecte une anomalie dans la mesure avec une probabilité de 5%.
    
    Types d'anomalies :
    - Surchauffe : +12°C
    - Sous-température : -10°C
    - Valeur nulle : 0°C
    
    Retourne :
        Dict avec la mesure (potentiellement modifiée) et un flag 'is_anomaly'
    """
    is_anomaly = False
    anomaly_type = None
    
    if random.random() < capteur_config.probabilite_anomalie:
        is_anomaly = True
        # Choisir un type d'anomalie
        choix = random.choice(["surchauffe", "sous_temperature", "valeur_nulle"])
        
        if choix == "surchauffe":
            mesure["temperature"] += capteur_config.anomalie_temperature_haute
            anomaly_type = "🔥 SURCHAUFFE"
        elif choix == "sous_temperature":
            mesure["temperature"] += capteur_config.anomalie_temperature_basse
            anomaly_type = "❄️ SOUS-TEMPÉRATURE"
        else:
            mesure["temperature"] = 0.0
            anomaly_type = "⚠️ VALEUR NULLE"
        
        mesure["temperature"] = round(mesure["temperature"], 2)
    
    return {
        **mesure,
        "is_anomaly": is_anomaly,
        "anomaly_type": anomaly_type
    }


def creer_payload(sensor_id: str) -> Dict[str, Any]:
    """
    Crée le payload JSON complet pour un capteur donné.
    
    Arguments :
        sensor_id : Identifiant du capteur (ex: "C001")
    
    Retourne :
        Dict contenant toutes les informations du message MQTT
    """
    # Générer les mesures
    mesure = generer_mesure_normale()
    mesure_avec_anomalie = injecter_anomalie(mesure)
    
    # Construire le payload
    payload = {
        "sensor_id": sensor_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "temperature": mesure_avec_anomalie["temperature"],
        "humidity": mesure_avec_anomalie["humidity"]
    }
    
    return payload, mesure_avec_anomalie["is_anomaly"], mesure_avec_anomalie["anomaly_type"]


def afficher_mesure(payload: Dict, is_anomaly: bool, anomaly_type: str):
    """Affiche la mesure dans la console de manière formatée."""
    if is_anomaly:
        print(f"🚨 [{payload['sensor_id']}] {anomaly_type}")
        print(f"   Température : {payload['temperature']}°C | Humidité : {payload['humidity']}%")
    else:
        print(f"📡 [{payload['sensor_id']}] Température : {payload['temperature']}°C | Humidité : {payload['humidity']}%")


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    """
    Fonction principale du simulateur de capteurs.
    
    1. Se connecte au broker MQTT avec TLS
    2. Boucle infinie pour envoyer des mesures
    3. Alterne entre les 3 capteurs
    """
    print("=" * 50)
    print("🛰️  SIMULATEUR DE CAPTEURS IoT")
    print("=" * 50)
    print(f"Capteurs simulés : {capteur_config.sensor_ids}")
    print(f"Intervalle d'envoi : {capteur_config.intervalle_envoi}s")
    print(f"Probabilité d'anomalie : {capteur_config.probabilite_anomalie * 100}%")
    print("=" * 50)
    print("\nConnexion au broker MQTT...")
    
    # Créer le client MQTT (version compatible avec paho-mqtt 2.x)
    try:
        # Nouvelle API paho-mqtt 2.x
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except (AttributeError, TypeError):
        # Ancienne API paho-mqtt 1.x
        client = mqtt.Client()
    
    # Configurer les callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    
    # Configurer l'authentification
    client.username_pw_set(mqtt_config.username, mqtt_config.password)
    
    # Configurer TLS/SSL pour connexion sécurisée
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    
    try:
        # Se connecter au broker
        client.connect(mqtt_config.host, mqtt_config.port, mqtt_config.keepalive)
        
        # Démarrer la boucle réseau en arrière-plan
        client.loop_start()
        
        # Attendre la connexion
        time.sleep(2)
        
        print("\n📊 Début de l'envoi des données...\n")
        compteur = 0
        
        # Boucle principale d'envoi
        while True:
            # Sélectionner un capteur (rotation)
            sensor_id = capteur_config.sensor_ids[compteur % len(capteur_config.sensor_ids)]
            
            # Créer et envoyer le payload
            payload, is_anomaly, anomaly_type = creer_payload(sensor_id)
            
            # Publier sur le topic MQTT
            result = client.publish(
                mqtt_config.topic_temperature,
                json.dumps(payload),
                qos=1  # Au moins une livraison garantie
            )
            
            # Afficher dans la console
            afficher_mesure(payload, is_anomaly, anomaly_type)
            
            compteur += 1
            
            # Attendre avant le prochain envoi
            time.sleep(capteur_config.intervalle_envoi)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Arrêt du simulateur...")
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
    finally:
        # Proprement fermer la connexion
        client.loop_stop()
        client.disconnect()
        print("✅ Déconnexion effectuée.")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    main()
