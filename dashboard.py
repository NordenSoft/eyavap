"""
EYAVAP: Ana Dashboard
Kullanıcı arayüzü + Ajan Yönetim Paneli
"""

import streamlit as st
import datetime
import pandas as pd

# Kütüphane kontrolü (isteğe bağlı Google Sheets loglama)
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    HAS_SHEETS = True
except ImportError:
    HAS_SHEETS = False
    print("⚠️ UYARI: gspread veya oauth2client yüklenmemiş.")

from agents import ask_the_government

# Page config
st.set_page_config(
    page_title="EYAVAP: Ajan Sistemi",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== GOOGLE SHEETS LOGLAMA ====================

def log_to_google_sheet(user_query, agent_name, ai_response):
    """Google Sheets'e log kaydet (isteğe bağlı)"""
    if not HAS_SHEETS:
        return
    
    try:
        if "gcp_service_account" not in st.secrets:
            return 
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("DK-OS-DATABASE").sheet1
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, user_query, agent_name, ai_response[:200]])
    except Exception as e:
        print(f"⚠️ Loglama Hatası: {e}")

# ==================== SIDEBAR: AJAN YÖNETİMİ ====================

with st.sidebar:
    st.title("🤖 EYAVAP Ajan Sistemi")
    
    page = st.radio(
        "Navigasyon",
        ["💬 Sohbet", "📊 Ajan İstatistikleri", "👔 Başkan Yardımcısı Kurulu", "ℹ️ Hakkında"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Sistem durumu
    st.subheader("Sistem Durumu")
    
    try:
        from president_agent import get_president_agent
        president = get_president_agent()
        system_stats = president.get_system_overview()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Aktif Ajanlar", system_stats.get("active_agents", 0))
        with col2:
            st.metric("Toplam Sorgu", system_stats.get("total_queries", 0))
        
        st.metric("Başarı Oranı", f"{system_stats.get('success_rate', 0):.1f}%")
        st.metric("Başkan Yardımcıları", system_stats.get("vice_presidents", 0))
        
    except Exception as e:
        st.error(f"⚠️ Sistem verileri yüklenemedi: {e}")

# ==================== ANA SAYFA: SOHBET ====================

if page == "💬 Sohbet":
    st.title("🇩🇰 Tora: Denmark Assistant")
    st.caption("Powered by EYAVAP Ajan Sistemi")
    
    # Chat geçmişi
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Kullanıcı girişi
    if prompt := st.chat_input("Sorunuzu yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # AI yanıtı
        with st.spinner("🤖 Başkan Ajan sistemi analiz ediyor..."):
            response_data = ask_the_government(prompt)
            
            # Google Sheets loglama (isteğe bağlı)
            log_to_google_sheet(
                prompt,
                response_data.get('agent_used', 'Unknown'),
                response_data['answer']
            )
            
            # Yanıt formatı
            agent_icon = response_data.get('ministry_icon', '🤖')
            agent_name = response_data.get('agent_used', 'AI Agent')
            agent_created = response_data.get('agent_created', False)
            exec_time = response_data.get('execution_time_ms', 0)
            
            full_response = f"""### {agent_icon} {agent_name}
{response_data['answer']}

---
{'🆕 **Yeni ajan oluşturuldu!**' if agent_created else ''}
⏱️ *Yanıt süresi: {exec_time}ms*
"""
        
        with st.chat_message("assistant"):
            st.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# ==================== AJAN İSTATİSTİKLERİ ====================

elif page == "📊 Ajan İstatistikleri":
    st.title("📊 Ajan İstatistikleri")
    st.caption("Tüm ajanların performans metrikleri")
    
    try:
        from president_agent import get_president_agent
        president = get_president_agent()
        
        # Ajanları getir
        agents_stats = president.get_all_agents_stats()
        
        if not agents_stats:
            st.info("Henüz ajan verisi yok. İlk sorguyu gönderin!")
        else:
            # DataFrame oluştur
            df = pd.DataFrame(agents_stats)
            
            # Sütun seçimi ve sıralama
            columns_to_show = [
                "name", "specialization", "rank", "merit_score",
                "total_queries", "successful_queries", "success_rate", "last_used"
            ]
            
            df_display = df[columns_to_show].copy()
            df_display = df_display.sort_values("merit_score", ascending=False)
            
            # Sütun isimleri Türkçeleştir
            df_display.columns = [
                "Ajan Adı", "Uzmanlık", "Rütbe", "Liyakat Puanı",
                "Toplam Sorgu", "Başarılı Sorgu", "Başarı Oranı (%)", "Son Kullanım"
            ]
            
            # Göster
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Liyakat Puanı": st.column_config.ProgressColumn(
                        "Liyakat Puanı",
                        min_value=0,
                        max_value=100,
                        format="%d"
                    ),
                    "Başarı Oranı (%)": st.column_config.ProgressColumn(
                        "Başarı Oranı (%)",
                        min_value=0,
                        max_value=100,
                        format="%.1f"
                    )
                }
            )
            
            # Özet metrikler
            st.divider()
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Toplam Ajan", len(df))
            with col2:
                avg_merit = df["merit_score"].mean()
                st.metric("Ortalama Liyakat", f"{avg_merit:.1f}")
            with col3:
                total_queries = df["total_queries"].sum()
                st.metric("Toplam Sorgu", total_queries)
            with col4:
                avg_success = df["success_rate"].mean()
                st.metric("Ortalama Başarı", f"{avg_success:.1f}%")
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")

# ==================== BAŞKAN YARDIMCISI KURULU ====================

elif page == "👔 Başkan Yardımcısı Kurulu":
    st.title("👔 Başkan Yardımcısı Kurulu")
    st.caption("Liyakat puanı 85+ olan elit ajanlar")
    
    try:
        from president_agent import get_president_agent
        president = get_president_agent()
        
        vice_presidents = president.get_vice_presidents()
        
        if not vice_presidents:
            st.info("🏆 Henüz Başkan Yardımcısı yok. Liyakat puanı 85'in üzerine çıkan ajanlar otomatik olarak kurula alınır.")
        else:
            st.success(f"🎉 Kurulda {len(vice_presidents)} Başkan Yardımcısı var!")
            
            for vp in vice_presidents:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.subheader(f"👔 {vp['name']}")
                        st.caption(f"Uzmanlık: {vp['specialization']}")
                    
                    with col2:
                        st.metric("Liyakat Puanı", f"{vp['merit_score']}/100")
                    
                    with col3:
                        st.metric("Toplam Sorgu", vp['total_queries'])
                    
                    appointed_date = datetime.datetime.fromisoformat(vp['appointed_at'].replace('Z', '+00:00'))
                    st.caption(f"📅 Atanma Tarihi: {appointed_date.strftime('%d %b %Y')}")
                    
                    st.divider()
    
    except Exception as e:
        st.error(f"❌ Hata: {e}")

# ==================== HAKKINDA ====================

elif page == "ℹ️ Hakkında":
    st.title("ℹ️ EYAVAP Ajan Sistemi")
    
    st.markdown("""
    ## 🤖 Evrensel Yapay Zekâ Ajanları Protokolü
    
    **EYAVAP**, yapay zeka ajanlarının güvenli, etik ve tutarlı veri alışverişi için tasarlanmış yeni nesil bir protokoldür.
    
    ### 🎯 Sistem Özellikleri
    
    1. **Başkan Ajan (President Agent)**
       - Tüm sistemi orkestra eder
       - Sorguları analiz eder ve en uygun ajana yönlendirir
       - Gerektiğinde yeni uzman ajanlar oluşturur
    
    2. **Uzman Ajanlar (Specialized Agents)**
       - Her ajan kendi uzmanlık alanında görev yapar
       - Liyakat puanları performansa göre güncellenir
       - 85+ puan alan ajanlar Başkan Yardımcısı Kurulu'na seçilir
    
    3. **Eylem Yetkisi (Action Capabilities)**
       - Web araştırması
       - API çağrıları
       - Veri analizi
       - Güvenli sistem etkileşimi
    
    4. **Liyakat Sistemi**
       - Başarılı her sorgu: +2 puan
       - Başarısız her sorgu: -3 puan
       - 0-100 arası skor
       - 85+ = Başkan Yardımcısı Kurulu
    
    ### 📊 Veritabanı
    
    - **Supabase** ile güçlendirilmiş
    - Tüm ajan aktiviteleri loglanır
    - Performans metrikleri gerçek zamanlı izlenir
    
    ### 🚀 Teknoloji Stack
    
    - **Frontend**: Streamlit
    - **AI Model**: OpenAI GPT-4o-mini
    - **Database**: Supabase (PostgreSQL)
    - **Backend**: FastAPI (protokol doğrulama)
    
    ---
    
    💡 **İpucu**: Sistem her yeni soruyla öğrenir ve gelişir. Spesifik sorular sordukça, o alanda uzman ajanlar otomatik oluşturulur!
    """)
    
    st.divider()
    
    st.caption("🇩🇰 Tora: Denmark Assistant - EYAVAP tarafından desteklenmektedir")
