import os
import sys

# Ajouter le dossier src au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def verifier_configuration():
    print("\n" + "=" * 60)
    print("🔍 VÉRIFICATION DE LA CONFIGURATION")
    print("=" * 60)
    
    checks = {
        "MQTT Host": os.getenv("MQTT_HOST"),
        "MQTT Username": os.getenv("MQTT_USERNAME"),
        "MQTT Password": os.getenv("MQTT_PASSWORD"),
        "MongoDB URI": os.getenv("MONGODB_URI"),
    }
    
    optional = {
        "SMTP User (Gmail)": os.getenv("SMTP_USER"),
        "SMTP Password": os.getenv("SMTP_PASSWORD"),
        "Email Destinataire": os.getenv("EMAIL_TO"),
    }
    
    all_ok = True
    
    print("\n📋 Configuration requise:")
    for name, value in checks.items():
        if value:
            print(f"   ✅ {name}: Configuré")
        else:
            print(f"   ❌ {name}: MANQUANT")
            all_ok = False
    
    print("\n📋 Configuration optionnelle:")
    for name, value in optional.items():
        if value:
            print(f"   ✅ {name}: Configuré")
        else:
            print(f"   ⚠️  {name}: Non configuré")
    
    return all_ok


def tester_connexions():
    print("\n" + "=" * 60)
    print("🔌 TEST DES CONNEXIONS")
    print("=" * 60)
    
    # Test MongoDB
    print("\n📦 Test MongoDB Atlas...")
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        
        uri = os.getenv("MONGODB_URI")
        if uri:
            client = MongoClient(uri, server_api=ServerApi('1'), serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            print("   ✅ MongoDB Atlas: Connecté")
            client.close()
        else:
            print("   ⚠️  MongoDB Atlas: URI non configurée")
    except Exception as e:
        print(f"   ❌ MongoDB Atlas: {e}")
    
    # Test MQTT (juste vérification config)
    print("\n📡 Test configuration MQTT...")
    mqtt_host = os.getenv("MQTT_HOST")
    if mqtt_host:
        print(f"   ✅ MQTT Host: {mqtt_host}")
        print(f"   ✅ MQTT Port: {os.getenv('MQTT_PORT', '8883')} (TLS)")
    else:
        print("   ❌ MQTT: Non configuré")
    
    # Test Email
    print("\n📧 Test configuration Email...")
    if os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"):
        print("   ✅ Gmail SMTP: Configuré")
        print(f"   📨 Email de: {os.getenv('SMTP_USER')}")
    else:
        print("   ⚠️  Email: Mode simulation (Gmail non configuré)")


def generer_fichiers_cloud():
    print("\n" + "=" * 60)
    print("📁 VÉRIFICATION DES FICHIERS DE DÉPLOIEMENT")
    print("=" * 60)
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Vérifier requirements.txt
    req_path = os.path.join(base_path, "requirements.txt")
    if os.path.exists(req_path):
        print("   ✅ requirements.txt existe")
    else:
        print("   ❌ requirements.txt manquant!")
    
    # Vérifier .streamlit/config.toml
    streamlit_config = os.path.join(base_path, ".streamlit", "config.toml")
    if os.path.exists(streamlit_config):
        print("   ✅ .streamlit/config.toml existe")
    else:
        print("   ⚠️  .streamlit/config.toml non trouvé")
    
    # Vérifier dashboard.py
    dashboard_path = os.path.join(base_path, "src", "dashboard.py")
    if os.path.exists(dashboard_path):
        print("   ✅ src/dashboard.py existe")
    else:
        print("   ❌ src/dashboard.py manquant!")
    
    print("\n📋 Fichiers requis pour Streamlit Cloud:")
    print("   • requirements.txt (dépendances Python)")
    print("   • src/dashboard.py (fichier principal)")
    print("   • .streamlit/config.toml (configuration optionnelle)")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 PRÉPARATION AU DÉPLOIEMENT CLOUD")
    print("=" * 60)
    
    # 1. Vérifier la configuration
    config_ok = verifier_configuration()
    
    # 2. Tester les connexions
    tester_connexions()
    
    # 3. Vérifier les fichiers
    generer_fichiers_cloud()
    
    print("\n" + "=" * 60)
    if config_ok:
        print("✅ Projet prêt pour le déploiement!")
    else:
        print("⚠️  Configuration incomplète - vérifiez le fichier .env")
    print("=" * 60 + "\n")
