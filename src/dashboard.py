import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import time
from datetime import datetime, timedelta
import json

# MongoDB
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

# Import de la configuration
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import dashboard_config, mqtt_config

# Charger les variables d'environnement pour le mode local
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONFIGURATION DE LA PAGE STREAMLIT
# ============================================================================

st.set_page_config(
    page_title="🌡️ Supervision IoT",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STYLES CSS PERSONNALISÉS
# ============================================================================

st.markdown("""
<style>
    /* Style pour les métriques */
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    
    /* Style pour les alertes */
    .alert-box {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    .alert-box-warning {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    .success-box {
        background-color: #e8f5e9;
        border-left: 5px solid #4caf50;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    /* Animation pour le titre */
    .title-container {
        text-align: center;
        padding: 20px;
    }
    
    /* Style pour le statut de connexion */
    .status-connected {
        color: #4caf50;
        font-weight: bold;
    }
    
    .status-disconnected {
        color: #f44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# FONCTIONS DE CHARGEMENT DES DONNÉES
# ============================================================================

def get_mongodb_uri():
    try:
        # Mode Streamlit Cloud
        return st.secrets["mongodb"]["uri"]
    except:
        # Mode local avec .env
        return os.getenv("MONGODB_URI", "")

@st.cache_resource
def get_mongodb_client():
    uri = get_mongodb_uri()
    if uri:
        try:
            # Options de connexion robustes pour Streamlit Cloud
            client = MongoClient(
                uri,
                server_api=ServerApi('1'),
                tls=True,
                tlsAllowInvalidCertificates=True,  # Pour éviter les erreurs SSL sur cloud
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000
            )
            # Test de connexion
            client.admin.command('ping')
            return client
        except Exception as e:
            st.warning(f"Connexion MongoDB en attente... ({str(e)[:50]})")
            return None
    return None

@st.cache_data(ttl=5)  # Cache de 5 secondes
def charger_historique():
    # Essayer MongoDB d'abord
    client = get_mongodb_client()
    if client:
        try:
            db = client["iot_supervision"]
            collection = db["mesures"]
            
            # Récupérer les 500 dernières mesures
            cursor = collection.find().sort("timestamp", -1).limit(500)
            data = list(cursor)
            
            if data:
                df = pd.DataFrame(data)
                # Convertir les timestamps
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                # Supprimer le champ _id de MongoDB
                if "_id" in df.columns:
                    df = df.drop("_id", axis=1)
                return df
        except Exception as e:
            st.warning(f"Erreur MongoDB: {e}")
    
    # Fallback vers fichier CSV local
    chemin = os.path.join(os.path.dirname(__file__), "..", "data", "historique.csv")
    
    if os.path.exists(chemin):
        try:
            df = pd.read_csv(chemin)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
        except Exception as e:
            st.error(f"Erreur de lecture du fichier : {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()


@st.cache_data(ttl=5)
def charger_anomalies():
    # Essayer MongoDB d'abord
    client = get_mongodb_client()
    if client:
        try:
            db = client["iot_supervision"]
            collection = db["mesures"]
            
            # Récupérer les anomalies
            cursor = collection.find({"is_anomaly": True}).sort("timestamp", -1).limit(100)
            data = list(cursor)
            
            if data:
                df = pd.DataFrame(data)
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                if "_id" in df.columns:
                    df = df.drop("_id", axis=1)
                return df
        except Exception as e:
            pass
    
    # Fallback vers fichier CSV local
    chemin = os.path.join(os.path.dirname(__file__), "..", "data", "anomalies.csv")
    
    if os.path.exists(chemin):
        try:
            df = pd.read_csv(chemin)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
        except Exception:
            return pd.DataFrame()
    else:
        return pd.DataFrame()


def calculer_statistiques(df):
    if df.empty:
        return {
            "total_mesures": 0,
            "temp_moyenne": 0,
            "temp_min": 0,
            "temp_max": 0,
            "hum_moyenne": 0,
            "total_anomalies": 0,
            "taux_anomalies": 0
        }
    
    total_mesures = len(df)
    total_anomalies = df["is_anomaly"].sum() if "is_anomaly" in df.columns else 0
    
    return {
        "total_mesures": total_mesures,
        "temp_moyenne": df["temperature"].mean(),
        "temp_min": df["temperature"].min(),
        "temp_max": df["temperature"].max(),
        "hum_moyenne": df["humidity"].mean(),
        "total_anomalies": int(total_anomalies),
        "taux_anomalies": (total_anomalies / total_mesures * 100) if total_mesures > 0 else 0
    }


# ============================================================================
# COMPOSANTS DE L'INTERFACE
# ============================================================================

def afficher_header():
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown("""
        <div class="title-container">
            <h1>🌡️ Supervision IoT en Temps Réel</h1>
            <p>Tableau de bord de surveillance des capteurs avec détection d'anomalies</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Indicateur de connexion
        st.markdown("""
        <div style="text-align: right; padding-top: 20px;">
            <span class="status-connected">🟢 Connecté</span>
        </div>
        """, unsafe_allow_html=True)


def afficher_metriques(stats):
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="📊 Total Mesures",
            value=f"{stats['total_mesures']}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="🌡️ Temp. Moyenne",
            value=f"{stats['temp_moyenne']:.1f}°C",
            delta=f"Min: {stats['temp_min']:.1f}°C"
        )
    
    with col3:
        st.metric(
            label="🌡️ Temp. Max",
            value=f"{stats['temp_max']:.1f}°C",
            delta=None
        )
    
    with col4:
        st.metric(
            label="💧 Humidité Moy.",
            value=f"{stats['hum_moyenne']:.1f}%",
            delta=None
        )
    
    with col5:
        st.metric(
            label="🚨 Anomalies",
            value=f"{stats['total_anomalies']}",
            delta=f"{stats['taux_anomalies']:.1f}%",
            delta_color="inverse"
        )


def afficher_graphiques(df):
    if df.empty:
        st.warning("⚠️ Aucune donnée disponible. Lancez le simulateur de capteurs.")
        return
    
    # Limiter aux N derniers points pour la lisibilité
    df_recent = df.tail(dashboard_config.points_graphique)
    
    # Créer un graphique avec 2 axes Y
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("🌡️ Température (°C)", "💧 Humidité (%)")
    )
    
    # Séparer les données normales et anomalies
    df_normal = df_recent[df_recent["is_anomaly"] == False] if "is_anomaly" in df_recent.columns else df_recent
    df_anomaly = df_recent[df_recent["is_anomaly"] == True] if "is_anomaly" in df_recent.columns else pd.DataFrame()
    
    # Graphique de température - données normales
    for sensor_id in df_recent["sensor_id"].unique():
        df_sensor = df_normal[df_normal["sensor_id"] == sensor_id]
        fig.add_trace(
            go.Scatter(
                x=df_sensor["timestamp"],
                y=df_sensor["temperature"],
                mode="lines+markers",
                name=f"Temp {sensor_id}",
                marker=dict(size=6),
                line=dict(width=2)
            ),
            row=1, col=1
        )
    
    # Anomalies température
    if not df_anomaly.empty:
        fig.add_trace(
            go.Scatter(
                x=df_anomaly["timestamp"],
                y=df_anomaly["temperature"],
                mode="markers",
                name="Anomalies",
                marker=dict(size=15, color="red", symbol="x"),
            ),
            row=1, col=1
        )
    
    # Graphique d'humidité
    for sensor_id in df_recent["sensor_id"].unique():
        df_sensor = df_normal[df_normal["sensor_id"] == sensor_id]
        fig.add_trace(
            go.Scatter(
                x=df_sensor["timestamp"],
                y=df_sensor["humidity"],
                mode="lines+markers",
                name=f"Hum {sensor_id}",
                marker=dict(size=6),
                line=dict(width=2)
            ),
            row=2, col=1
        )
    
    # Anomalies humidité
    if not df_anomaly.empty:
        fig.add_trace(
            go.Scatter(
                x=df_anomaly["timestamp"],
                y=df_anomaly["humidity"],
                mode="markers",
                name="Anomalies",
                marker=dict(size=15, color="red", symbol="x"),
                showlegend=False
            ),
            row=2, col=1
        )
    
    # Mise en forme
    fig.update_layout(
        height=500,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    
    fig.update_xaxes(title_text="Temps", row=2, col=1)
    fig.update_yaxes(title_text="°C", row=1, col=1)
    fig.update_yaxes(title_text="%", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)


def afficher_alertes(df_anomalies):
    st.subheader("🚨 Alertes Récentes")
    
    if df_anomalies.empty:
        st.markdown("""
        <div class="success-box">
            ✅ <strong>Aucune anomalie détectée</strong><br>
            Tous les capteurs fonctionnent normalement.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Afficher les 5 dernières anomalies
    df_recent = df_anomalies.tail(5).sort_values("timestamp", ascending=False)
    
    for _, row in df_recent.iterrows():
        timestamp = row["timestamp"].strftime("%H:%M:%S") if hasattr(row["timestamp"], "strftime") else row["timestamp"]
        temp = row["temperature"]
        
        # Déterminer le type d'alerte
        if temp > 35:
            alert_type = "🔥 SURCHAUFFE"
            css_class = "alert-box"
        elif temp < 15:
            alert_type = "❄️ SOUS-TEMPÉRATURE"
            css_class = "alert-box"
        elif temp == 0:
            alert_type = "⚠️ VALEUR NULLE"
            css_class = "alert-box-warning"
        else:
            alert_type = "⚠️ ANOMALIE"
            css_class = "alert-box-warning"
        
        st.markdown(f"""
        <div class="{css_class}">
            <strong>{alert_type}</strong> - Capteur {row['sensor_id']}<br>
            🕐 {timestamp} | 🌡️ {temp}°C | 💧 {row['humidity']}%
        </div>
        """, unsafe_allow_html=True)


def afficher_tableau(df):
    st.subheader("📋 Dernières Mesures")
    
    if df.empty:
        st.info("Aucune donnée disponible.")
        return
    
    # Prendre les N dernières mesures
    df_recent = df.tail(dashboard_config.lignes_tableau).sort_values("timestamp", ascending=False)
    
    # Formater pour l'affichage
    df_display = df_recent.copy()
    df_display["timestamp"] = df_display["timestamp"].dt.strftime("%H:%M:%S")
    df_display["temperature"] = df_display["temperature"].apply(lambda x: f"{x:.1f}°C")
    df_display["humidity"] = df_display["humidity"].apply(lambda x: f"{x:.1f}%")
    
    # Renommer les colonnes
    df_display = df_display.rename(columns={
        "sensor_id": "Capteur",
        "timestamp": "Heure",
        "temperature": "Température",
        "humidity": "Humidité",
        "status": "Statut"
    })
    
    # Colonnes à afficher
    colonnes = ["Capteur", "Heure", "Température", "Humidité", "Statut"]
    colonnes_existantes = [c for c in colonnes if c in df_display.columns]
    
    # Afficher avec style
    st.dataframe(
        df_display[colonnes_existantes],
        use_container_width=True,
        hide_index=True
    )


def afficher_sidebar():
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Rafraîchissement automatique
        auto_refresh = st.checkbox("🔄 Rafraîchissement auto", value=True)
        refresh_rate = st.slider("Intervalle (secondes)", 3, 30, 5)
        
        st.divider()
        
        # Export des données
        st.header("📥 Export")
        
        df = charger_historique()
        if not df.empty:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Télécharger CSV",
                data=csv,
                file_name=f"iot_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Export des anomalies
            df_anomalies = charger_anomalies()
            if not df_anomalies.empty:
                csv_anomalies = df_anomalies.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="🚨 Télécharger Anomalies",
                    data=csv_anomalies,
                    file_name=f"anomalies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        st.divider()
        
        # Actions
        st.header("🔧 Actions")
        if st.button("🔄 Rafraîchir maintenant"):
            st.cache_data.clear()
            st.rerun()
        
        return auto_refresh, refresh_rate


def afficher_graphique_capteurs(df):
    if df.empty:
        return
    
    st.subheader("📊 Température par Capteur")
    
    # Graphique en camembert par capteur
    df_stats = df.groupby("sensor_id").agg({
        "temperature": "mean",
        "humidity": "mean"
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_temp = px.bar(
            df_stats,
            x="sensor_id",
            y="temperature",
            color="sensor_id",
            title="Température moyenne par capteur",
            labels={"temperature": "Température (°C)", "sensor_id": "Capteur"}
        )
        fig_temp.update_layout(showlegend=False)
        st.plotly_chart(fig_temp, use_container_width=True)
    
    with col2:
        fig_hum = px.bar(
            df_stats,
            x="sensor_id",
            y="humidity",
            color="sensor_id",
            title="Humidité moyenne par capteur",
            labels={"humidity": "Humidité (%)", "sensor_id": "Capteur"}
        )
        fig_hum.update_layout(showlegend=False)
        st.plotly_chart(fig_hum, use_container_width=True)


# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def main():
    
    # Sidebar
    auto_refresh, refresh_rate = afficher_sidebar()
    
    # Header
    afficher_header()
    
    st.divider()
    
    # Charger les données
    df = charger_historique()
    df_anomalies = charger_anomalies()
    stats = calculer_statistiques(df)
    
    # Métriques
    afficher_metriques(stats)
    
    st.divider()
    
    # Disposition principale
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Graphiques principaux
        afficher_graphiques(df)
        
        # Graphiques par capteur
        afficher_graphique_capteurs(df)
    
    with col2:
        # Alertes
        afficher_alertes(df_anomalies)
        
        st.divider()
        
        # Tableau des mesures
        afficher_tableau(df)
    
    # Pied de page
    st.divider()
    st.markdown(f"""
    <div style="text-align: center; color: gray; font-size: 12px;">
        📊 Dashboard IoT
    </div>
    """, unsafe_allow_html=True)
    
    # Rafraîchissement automatique
    if auto_refresh:
        time.sleep(refresh_rate)
        st.rerun()


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    main()
