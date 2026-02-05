import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class EmailService:
    
    def __init__(self):
        # Configuration SMTP (Gmail)
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")  
        
        # Email de destination
        self.email_to = os.getenv("EMAIL_TO", "")
        
        # Déterminer le mode
        if self.smtp_user and self.smtp_password:
            self.mode = "smtp"
            print("✅ Service email configuré (Gmail SMTP)")
        else:
            self.mode = "simulation"
            print("⚠️  Service email en mode SIMULATION (pas de credentials)")
    
    def envoyer_alerte(self, sujet: str, message: str, niveau: str = "warning") -> bool:
        if self.mode == "simulation":
            self._afficher_simulation(sujet, message, niveau)
            return False
        elif self.mode == "smtp":
            return self._envoyer_smtp(sujet, message, niveau)
        return False
    
    def _afficher_simulation(self, sujet: str, message: str, niveau: str):
        couleurs = {"info": "🔵", "warning": "🟡", "critical": "🔴"}
        icone = couleurs.get(niveau, "⚪")
        
        print("\n" + "=" * 50)
        print(f"📧 [SIMULATION EMAIL] {icone} {niveau.upper()}")
        print("=" * 50)
        print(f"À: {self.email_to}")
        print(f"Sujet: [IoT Alert] {sujet}")
        print("-" * 50)
        # Nettoyer le HTML pour l'affichage console
        message_clean = message.replace("<br>", "\n").replace("<strong>", "").replace("</strong>", "")
        print(message_clean)
        print("=" * 50 + "\n")
    
    def _envoyer_smtp(self, sujet: str, message: str, niveau: str) -> bool:
        try:
            # Créer le message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[IoT Alert - {niveau.upper()}] {sujet}"
            msg["From"] = self.smtp_user
            msg["To"] = self.email_to
            
            # Contenu HTML
            html_content = self._generer_html(sujet, message, niveau)
            msg.attach(MIMEText(html_content, "html"))
            
            # Connexion et envoi
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email envoyé : {sujet}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur SMTP : {e}")
            return False
    
    def _generer_html(self, sujet: str, message: str, niveau: str) -> str:
        couleurs = {
            "info": "#2196F3",
            "warning": "#FF9800", 
            "critical": "#F44336"
        }
        couleur = couleurs.get(niveau, "#757575")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="background-color: {couleur}; color: white; padding: 20px; text-align: center;">
                    <h1 style="margin: 0;">🚨 ALERTE IoT</h1>
                    <h2 style="margin: 10px 0 0 0; font-weight: normal;">{sujet}</h2>
                </div>
                <div style="padding: 30px;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; border-left: 4px solid {couleur};">
                        {message}
                    </div>
                    <div style="margin-top: 20px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
                        <strong>📊 Détails:</strong><br>
                        • Niveau: {niveau.upper()}<br>
                        • Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>
                        • Système: IoT Supervision System
                    </div>
                </div>
                <div style="background-color: #263238; color: white; padding: 15px; text-align: center; font-size: 12px;">
                    <p style="margin: 0;">IoT Supervision System</p>
                    <p style="margin: 5px 0 0 0; opacity: 0.7;">Email généré automatiquement</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def alerte_anomalie(self, sensor_id: str, temperature: float, humidity: float):
        sujet = f"Anomalie détectée - Capteur {sensor_id}"
        message = f"""
        <strong>🔍 Anomalie détectée par l'IA</strong><br><br>
        <strong>Capteur:</strong> {sensor_id}<br>
        <strong>Température:</strong> {temperature}°C<br>
        <strong>Humidité:</strong> {humidity}%<br><br>
        <strong>Action recommandée:</strong> Vérifier le capteur et les conditions environnementales.
        """
        return self.envoyer_alerte(sujet, message, "warning")
    
    def alerte_temperature_critique(self, sensor_id: str, temperature: float):
        if temperature > 35:
            sujet = f"🔥 SURCHAUFFE - Capteur {sensor_id}"
            message = f"""
            <strong>⚠️ TEMPÉRATURE CRITIQUE DÉTECTÉE</strong><br><br>
            <strong>Capteur:</strong> {sensor_id}<br>
            <strong>Température:</strong> {temperature}°C<br>
            <strong>Seuil max:</strong> 35°C<br><br>
            <strong style="color: red;">ACTION URGENTE:</strong> Vérifier immédiatement le système de refroidissement!
            """
            return self.envoyer_alerte(sujet, message, "critical")
        elif temperature < 10:
            sujet = f"❄️ SOUS-TEMPÉRATURE - Capteur {sensor_id}"
            message = f"""
            <strong>⚠️ TEMPÉRATURE BASSE DÉTECTÉE</strong><br><br>
            <strong>Capteur:</strong> {sensor_id}<br>
            <strong>Température:</strong> {temperature}°C<br>
            <strong>Seuil min:</strong> 10°C<br><br>
            <strong>Action recommandée:</strong> Vérifier le système de chauffage.
            """
            return self.envoyer_alerte(sujet, message, "warning")
        return False


# ============================================================================
# TEST DU SERVICE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📧 TEST DU SERVICE D'ENVOI D'EMAILS")
    print("=" * 60)
    
    # Créer le service
    service = EmailService()
    
    print(f"\n📬 Mode actif: {service.mode.upper()}")
    print(f"📮 Destinataire: {service.email_to}")
    
    # Test 1: Alerte simple
    print("\n--- Test 1: Alerte simple ---")
    service.envoyer_alerte(
        "Test du système",
        "Ceci est un test du système d'alertes IoT.<br>Le système fonctionne correctement.",
        "info"
    )
    
    # Test 2: Anomalie
    print("\n--- Test 2: Alerte anomalie ---")
    service.alerte_anomalie("C001", 42.5, 85.0)
    
    # Test 3: Température critique
    print("\n--- Test 3: Température critique ---")
    service.alerte_temperature_critique("C002", 45.0)
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés")
    print("=" * 60)
