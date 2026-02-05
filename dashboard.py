import streamlit as st
import datetime

# --- KÜTÜPHANE KONTROLÜ (BEYAZ EKRANI ÖNLER) ---
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    HAS_SHEETS = True
except ImportError:
    HAS_SHEETS = False
    # Hata olsa bile site açılacak, sadece sheets çalışmayacak
    print("⚠️ UYARI: gspread veya oauth2client yüklenmemiş.")

from agents import ask_the_government

# 1. PAGE CONFIG
st.set_page_config(page_title="Tora: Denmark Assistant", page_icon="🇩🇰", layout="centered")

# 2. LOGLAMA FONKSİYONU (HATA KORUMALI)
def log_to_google_sheet(user_query, ministry, ai_response):
    if not HAS_SHEETS:
        return # Kütüphane yoksa hiç uğraşma
    
    try:
        # Şifre kontrolü
        if "gcp_service_account" not in st.secrets:
            return 

        # Bağlantı
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # Secrets formatını düzelt
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        # Özel Anahtar düzeltmesi (Tırnak hatalarını temizle)
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("DK-OS-DATABASE").sheet1
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, user_query, ministry, ai_response])
        print("✅ Log Kaydedildi!")
    except Exception as e:
        print(f"⚠️ Loglama Hatası: {e}")

# 3. ARAYÜZ
st.title("🇩🇰 Tora")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Sorunuzu yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Tora düşünüyor..."):
        response_data = ask_the_government(prompt)
        
        # Loglamayı dene (Hata varsa sessizce geçer)
        log_to_google_sheet(prompt, response_data['ministry_name'], response_data['answer'][:200])

        full_response = f"### {response_data['ministry_icon']} {response_data['ministry_name']}\n\n{response_data['answer']}"

    with st.chat_message("assistant"):
        st.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})