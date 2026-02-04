"""
🚀 Script de Déploiement Cloud
================================
Ce script prépare le projet pour le déploiement sur Streamlit Cloud ou Railway.

Fonctionnalités:
- Génère les fichiers de configuration
- Vérifie les dépendances
- Teste les connexions cloud
"""

import os
import sys

# Ajouter le dossier src au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()


def verifier_configuration():
    """Vérifie que toutes les configurations sont présentes."""
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
    """Teste les connexions aux services cloud."""
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
    """Génère les fichiers pour le déploiement cloud."""
    print("\n" + "=" * 60)
    print("📁 GÉNÉRATION DES FICHIERS DE DÉPLOIEMENT")
    print("=" * 60)
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Procfile pour Railway/Heroku
    procfile_content = """web: streamlit run src/dashboard.py --server.port=$PORT --server.address=0.0.0.0
worker: python src/detection_anomalies.py
"""
    
    procfile_path = os.path.join(base_path, "Procfile")
    with open(procfile_path, "w") as f:
        f.write(procfile_content)
    print(f"   ✅ Procfile créé")
    
    # runtime.txt
    runtime_content = "python-3.11.0\n"
    runtime_path = os.path.join(base_path, "runtime.txt")
    with open(runtime_path, "w") as f:
        f.write(runtime_content)
    print(f"   ✅ runtime.txt créé")
    
    # .dockerignore
    dockerignore_content = """.venv/
__pycache__/
*.pyc
.env
.git/
*.md
docs/
"""
    dockerignore_path = os.path.join(base_path, ".dockerignore")
    with open(dockerignore_path, "w") as f:
        f.write(dockerignore_content)
    print(f"   ✅ .dockerignore créé")
    
    print("\n📋 Fichiers générés pour le déploiement:")
    print("   • Procfile (Railway/Heroku)")
    print("   • runtime.txt (version Python)")
    print("   • .dockerignore")


def afficher_instructions():
    """Affiche les instructions de déploiement."""
    print("\n" + "=" * 60)
    print("📚 INSTRUCTIONS DE DÉPLOIEMENT")
    print("=" * 60)
    
    print("""
┌─────────────────────────────────────────────────────────────┐
│  🌐 OPTION 1: STREAMLIT CLOUD (Recommandé - Gratuit)       │
├─────────────────────────────────────────────────────────────┤
│  1. Aller sur https://share.streamlit.io                    │
│  2. Se connecter avec GitHub                                │
│  3. Sélectionner le repo: sondossAr/projet-iot-supervision  │
│  4. Main file: src/dashboard.py                             │
│  5. Ajouter les secrets dans l'interface Streamlit          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🚂 OPTION 2: RAILWAY.APP                                   │
├─────────────────────────────────────────────────────────────┤
│  1. Aller sur https://railway.app                           │
│  2. New Project → Deploy from GitHub                        │
│  3. Sélectionner le repo                                    │
│  4. Ajouter les variables d'environnement                   │
│  5. Le Procfile sera automatiquement détecté                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  📧 CONFIGURATION EMAIL (Gmail SMTP)                        │
├─────────────────────────────────────────────────────────────┤
│  1. Activer 2FA sur votre compte Gmail                      │
│  2. Créer un "App Password":                                │
│     Google Account → Security → App passwords               │
│  3. Ajouter dans .env:                                      │
│     SMTP_HOST=smtp.gmail.com                                │
│     SMTP_PORT=587                                           │
│     SMTP_USER=votre.email@gmail.com                         │
│     SMTP_PASSWORD=xxxx xxxx xxxx xxxx                       │
│     EMAIL_TO=destinataire@email.com                         │
└─────────────────────────────────────────────────────────────┘
""")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 PRÉPARATION AU DÉPLOIEMENT CLOUD")
    print("   Projet IoT Supervision - 5e BIM")
    print("=" * 60)
    
    # 1. Vérifier la configuration
    config_ok = verifier_configuration()
    
    # 2. Tester les connexions
    tester_connexions()
    
    # 3. Générer les fichiers
    generer_fichiers_cloud()
    
    # 4. Afficher les instructions
    afficher_instructions()
    
    print("\n" + "=" * 60)
    if config_ok:
        print("✅ Projet prêt pour le déploiement!")
    else:
        print("⚠️  Configuration incomplète - vérifiez le fichier .env")
    print("=" * 60 + "\n")
