"""
EYAVAP Dashboard - Yapay Zekâ Ajanları İzleme Paneli
Streamlit ile gerçek zamanlı ajan aktivitelerini izleyin
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# ==================== Sayfa Yapılandırması ====================
st.set_page_config(
    page_title="EYAVAP Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Özel CSS ====================
st.markdown("""
<style>
    /* Ana tema */
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Metrik kartları */
    .metric-card {
        background: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #e94560;
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.3);
    }
    
    /* Başlık */
    .main-title {
        background: linear-gradient(90deg, #e94560, #0f3460);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* REJECT satırları */
    .reject-row {
        background-color: rgba(255, 0, 0, 0.2) !important;
        color: #ff4444 !important;
    }
    
    /* ALLOW satırları */
    .allow-row {
        background-color: rgba(0, 255, 0, 0.1) !important;
        color: #44ff44 !important;
    }
    
    /* Tablo başlıkları */
    .dataframe th {
        background-color: #0f3460 !important;
        color: #e94560 !important;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f3460 100%);
    }
    
    /* Metrik değerleri */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: bold;
    }
    
    /* Butonlar */
    .stButton > button {
        background: linear-gradient(90deg, #e94560, #0f3460);
        color: white;
        border: none;
        padding: 10px 30px;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(233, 69, 96, 0.4);
    }
</style>
""", unsafe_allow_html=True)


# ==================== Supabase Bağlantısı ====================
@st.cache_resource
def init_supabase():
    """Supabase bağlantısını başlat"""
    try:
        from supabase import create_client
        
        # Önce st.secrets'dan dene, yoksa .env'den oku
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
        except:
            url = os.getenv("SUPABASE_URL", "").strip()
            key = os.getenv("SUPABASE_KEY", "").strip()
        
        if not url or not key:
            return None, "Supabase yapılandırması eksik!"
        
        client = create_client(url, key)
        return client, None
        
    except Exception as e:
        return None, str(e)


def fetch_logs(client, limit=50):
    """Son N kaydı getir"""
    try:
        response = client.table("agent_logs").select("*").order("id", desc=True).limit(limit).execute()
        return response.data, None
    except Exception as e:
        return None, str(e)


def style_dataframe(df):
    """Dataframe'i renklendir"""
    def highlight_rows(row):
        if row['decision'] == 'REJECT':
            return ['background-color: rgba(255, 68, 68, 0.3); color: #ff4444'] * len(row)
        elif row['decision'] == 'ALLOW':
            return ['background-color: rgba(68, 255, 68, 0.15); color: #44ff44'] * len(row)
        elif row['decision'] == 'BLOCK':
            return ['background-color: rgba(255, 165, 0, 0.2); color: #ffa500'] * len(row)
        elif row['decision'] == 'WARNING':
            return ['background-color: rgba(255, 255, 0, 0.15); color: #ffff00'] * len(row)
        else:
            return [''] * len(row)
    
    return df.style.apply(highlight_rows, axis=1)


# ==================== Ana Uygulama ====================
def main():
    # Başlık
    st.markdown('<h1 class="main-title">🤖 EYAVAP Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #888; margin-bottom: 30px;">Yapay Zekâ Ajanları İzleme Paneli</p>', unsafe_allow_html=True)
    
    # Supabase bağlantısı
    client, error = init_supabase()
    
    if error:
        st.error(f"❌ Supabase bağlantı hatası: {error}")
        st.info("💡 .env dosyasında SUPABASE_URL ve SUPABASE_KEY değerlerini kontrol edin.")
        return
    
    if not client:
        st.error("❌ Supabase bağlantısı kurulamadı!")
        return
    
    # Sidebar
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/streamlit/streamlit/develop/docs/logo.svg", width=50)
        st.markdown("### ⚙️ Ayarlar")
        
        record_limit = st.slider("Kayıt Limiti", min_value=10, max_value=200, value=50, step=10)
        
        st.markdown("---")
        st.markdown("### 📊 Filtreler")
        
        filter_decision = st.multiselect(
            "Karar Filtresi",
            options=["ALLOW", "REJECT", "BLOCK", "WARNING", "QUARANTINE"],
            default=["ALLOW", "REJECT", "BLOCK", "WARNING", "QUARANTINE"]
        )
        
        st.markdown("---")
        st.markdown("### 🔗 Bağlantılar")
        st.markdown("- [📖 API Docs](http://localhost:8000/docs)")
        st.markdown("- [❤️ Health](http://localhost:8000/health)")
        
        st.markdown("---")
        st.markdown(f"🕐 Son güncelleme: {datetime.now().strftime('%H:%M:%S')}")
    
    # Refresh butonu
    col_refresh, col_spacer = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Verileri Yenile", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Verileri çek
    logs, error = fetch_logs(client, record_limit)
    
    if error:
        st.error(f"❌ Veri çekme hatası: {error}")
        return
    
    if not logs:
        st.warning("⚠️ Henüz kayıt yok. Test mesajları gönderin!")
        st.code("python3 test_agent.py", language="bash")
        return
    
    # DataFrame oluştur
    df = pd.DataFrame(logs)
    
    # Filtre uygula
    if filter_decision:
        df_filtered = df[df['decision'].isin(filter_decision)]
    else:
        df_filtered = df
    
    # ==================== Metrik Kartları ====================
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_messages = len(df)
    blocked_threats = len(df[df['decision'] == 'REJECT'])
    allowed_messages = len(df[df['decision'] == 'ALLOW'])
    avg_security = df['security_score'].mean() if 'security_score' in df.columns else 0
    
    with col1:
        st.metric(
            label="📨 Toplam Mesaj",
            value=total_messages,
            delta=f"+{len(df_filtered)} görüntülenen"
        )
    
    with col2:
        st.metric(
            label="🚫 Engellenen Tehditler",
            value=blocked_threats,
            delta=f"{(blocked_threats/total_messages*100):.1f}%" if total_messages > 0 else "0%",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="✅ Onaylanan Mesajlar",
            value=allowed_messages,
            delta=f"{(allowed_messages/total_messages*100):.1f}%" if total_messages > 0 else "0%"
        )
    
    with col4:
        st.metric(
            label="🛡️ Ort. Güvenlik Skoru",
            value=f"{avg_security:.0f}",
            delta="/ 100"
        )
    
    # ==================== Grafikler ====================
    st.markdown("---")
    st.markdown("### 📈 İstatistikler")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Karar dağılımı
        decision_counts = df['decision'].value_counts()
        st.markdown("#### Karar Dağılımı")
        
        # Renk haritası
        color_map = {
            'ALLOW': '#44ff44',
            'REJECT': '#ff4444',
            'BLOCK': '#ffa500',
            'WARNING': '#ffff00',
            'QUARANTINE': '#ff69b4'
        }
        
        chart_data = pd.DataFrame({
            'Karar': decision_counts.index,
            'Sayı': decision_counts.values
        })
        st.bar_chart(chart_data.set_index('Karar'))
    
    with chart_col2:
        # Ajan aktivitesi
        if 'agent_name' in df.columns:
            agent_counts = df['agent_name'].value_counts().head(10)
            st.markdown("#### En Aktif Ajanlar")
            
            agent_data = pd.DataFrame({
                'Ajan': agent_counts.index,
                'Mesaj': agent_counts.values
            })
            st.bar_chart(agent_data.set_index('Ajan'))
    
    # ==================== Log Tablosu ====================
    st.markdown("---")
    st.markdown("### 📋 Ajan Logları")
    
    # Kolon seçimi
    display_columns = ['id', 'agent_name', 'decision', 'security_score', 'is_safe', 'created_at']
    available_columns = [col for col in display_columns if col in df_filtered.columns]
    
    if available_columns:
        df_display = df_filtered[available_columns].copy()
        
        # Tarih formatı
        if 'created_at' in df_display.columns:
            df_display['created_at'] = pd.to_datetime(df_display['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Renkli tablo
        styled_df = style_dataframe(df_display)
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.dataframe(df_filtered, use_container_width=True, height=400)
    
    # ==================== Alt Bilgi ====================
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>🤖 <strong>EYAVAP</strong> - Evrensel Yapay Zekâ Ajanları Arası Veri Aktarım Protokolü</p>
        <p>Yapay zekâ ajanlarına hükmet! 👑</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
