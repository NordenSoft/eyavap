import streamlit as st
from agents import ask_the_government
import datetime

# --- GÜVENLİK DUVARI: KÜTÜPHANE KONTROLÜ ---
# Eğer gspread yüklü değilse veya hata verirse site çökmesin.
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    HAS_GOOGLE_SHEETS = True
except ImportError:
    HAS_GOOGLE_SHEETS = False
    print("⚠️ Google Sheets kütüphaneleri eksik.")

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Tora: Denmark Assistant",
    page_icon="🇩🇰",
    layout="centered"
)

# 2. STYLES
st.markdown("""
<style>
    .stChatMessage { border-radius: 15px; padding: 10px; }
    .ministry-header { background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center; border: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS LOGLAMA (ZIRHLI VERSİYON) ---
def log_to_google_sheet(user_query, ministry, ai_response):
    if not HAS_GOOGLE_SHEETS:
        return

    try:
        # 1. Şifre kontrolü
        if "gcp_service_account" not in st.secrets:
            print("⚠️ Secrets içinde 'gcp_service_account' bulunamadı.")
            return

        # 2. Bağlantı girişimi
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"]) # Dict formatına zorla
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 3. Yazma işlemi
        sheet = client.open("DK-OS-DATABASE").sheet1
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, user_query, ministry, ai_response])
        print("✅ Log başarıyla kaydedildi.")
        
    except Exception as e:
        # HATA OLURSA SİTEYİ ÇÖKERTME, SADECE KONSOLA YAZ
        print(f"⚠️ Loglama Hatası (Sistem çalışmaya devam ediyor): {e}")

# 3. SIDEBAR
with st.sidebar:
    st.title("🇩🇰 Tora")
    st.caption("v6.3 | Safe Mode")
    st.markdown("---")
    if st.button("🗑️ Temizle"):
        st.session_state.messages = []
        st.rerun()

# 4. HEADER & CHAT
st.title("🇩🇰 Tora")
st.markdown("### Dijital Devlet Asistanı")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Sorunuzu yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Tora düşünüyor..."):
        # Yapay zekaya sor
        response_data = ask_the_government(prompt)
        
        # --- LOGLAMA (Hata olsa bile devam eder) ---
        log_to_google_sheet(prompt, response_data['ministry_name'], response_data['answer'][:200])
        # -------------------------------------------

        header_html = f"""
        <div class="ministry-header">
            <div style="font-size: 40px;">{response_data['ministry_icon']}</div>
            <div style="{response_data['ministry_style']} font-weight:bold; font-size: 18px;">{response_data['ministry_name']}</div>
        </div>
        """
        full_response = header_html + response_data["answer"]

    with st.chat_message("assistant"):
        st.markdown(full_response, unsafe_allow_html=True)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})