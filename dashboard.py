import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os
from dotenv import load_dotenv
from supabase import create_client

# Sayfa Ayarları
st.set_page_config(page_title="EYAVAP Dashboard", page_icon="🧠", layout="wide")

# --- BAĞLANTI SİHİRBAZI ---
# Hem bilgisayarındaki .env dosyasını, hem de Streamlit Secrets'ı okur.
load_dotenv()

def init_connection():
    # 1. Önce Streamlit Secrets'a bak (Bulut için)
    if hasattr(st, "secrets") and "SUPABASE_URL" in st.secrets:
        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        ), st.secrets["API_URL"]
    
    # 2. Yoksa .env dosyasına bak (Senin bilgisayarın için)
    elif os.getenv("SUPABASE_URL"):
        return create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        ), "https://eyavap.onrender.com"
        
    else:
        return None, None

# Bağlantıyı Başlat
supabase, API_URL = init_connection()

# --- HATA KONTROLÜ ---
if not supabase:
    st.error("🚨 Bağlantı Hatası! Secrets veya .env bulunamadı.")
    st.info("Lütfen Streamlit panelinden 'Secrets' ayarlarını yaptığınızdan emin olun.")
    st.stop() # Uygulamayı durdur

# --- ARAYÜZ ---
st.title("🤖 EYAVAP Kontrol Merkezi")
st.caption(f"📡 Sunucu Bağlantısı: {API_URL}")

# Verileri Çek
try:
    response = supabase.table('agent_logs').select("*").execute()
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Veri çekilemedi: {e}")
    df = pd.DataFrame()

# Eğer veri varsa göster
if not df.empty:
    # KPI KARTLARI
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Mesaj", len(df))
    col2.metric("Son Ajan", df.iloc[-1]['agent_name'] if 'agent_name' in df else "-")
    
    status = df.iloc[-1]['action'] if 'action' in df else "-"
    col3.metric("Son Durum", status, delta="Active" if status=="ALLOW" else "Blocked", delta_color="normal")

    st.divider()

    # GRAFİKLER
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Ajan Yoğunluğu")
        if 'agent_name' in df.columns:
            st.plotly_chart(px.bar(df['agent_name'].value_counts(), title="Kim Çok Konuşuyor?"), use_container_width=True)
            
    with c2:
        st.subheader("🛡️ Güvenlik Durumu")
        if 'action' in df.columns:
            st.plotly_chart(px.pie(df, names='action', title="İzinler vs Engellemeler", hole=0.4), use_container_width=True)

    # AKIŞ TABLOSU
    st.subheader("📝 Canlı Log Kayıtları")
    st.dataframe(df.sort_values(by='created_at', ascending=False), use_container_width=True)

else:
    st.info("📭 Henüz hiç kayıt yok. Ajanlarını çalıştır!")

# Yenileme Butonu
if st.button("🔄 Verileri Yenile"):
    st.rerun()