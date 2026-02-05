import streamlit as st
from agents import ask_the_government
import datetime

# 1. PAGE CONFIG
st.set_page_config(
    page_title="DK-OS Beta",
    page_icon="🇩🇰",
    layout="centered"
)

# 2. STYLES
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
    }
    .ministry-header {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .beta-tag {
        color: #e67e22;
        font-weight: bold;
        font-size: 12px;
        border: 1px solid #e67e22;
        padding: 2px 6px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- LOG SİSTEMİ ---
if "logs" not in st.session_state:
    st.session_state.logs = []

def add_log(action, detail):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {action}: {detail}"
    st.session_state.logs.insert(0, log_entry)
# -------------------

# 3. SIDEBAR (Sadece Başlıklar)
with st.sidebar:
    st.title("🇩🇰 DK-OS")
    st.markdown("<span class='beta-tag'>PUBLIC BETA v5.2</span>", unsafe_allow_html=True)
    st.markdown("---")
    # Log kutusu için yer ayırıyoruz ama içini en sonda dolduracağız
    log_placeholder = st.empty() 
    
    st.markdown("---")
    if st.button("🗑️ Reset System", type="primary"):
        st.session_state.messages = []
        st.session_state.logs = []
        st.rerun()

# 4. HEADER
st.title("🇩🇰 DK-OS")
st.markdown("### Digital State Assistant")
st.markdown("*Ask questions or request document drafts.*")

# 5. CHAT LOGIC
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Type here... (Dansk, English, Türkçe)"):
    # Log 1: Soru Geldi
    add_log("QUERY", prompt[:30] + "...") 
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Processing..."):
        response_data = ask_the_government(prompt)
        
        # Log 2: Bakanlık Atandı
        add_log("AGENT", response_data['ministry_name']) 
        
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

# 6. SIDEBAR GÜNCELLEME (EN SON ÇALIŞIR)
# Kod buraya geldiğinde soru sorulmuş ve loglar eklenmiş olur.
with log_placeholder.container():
    with st.expander("🕵️‍♂️ LIVE INTEL (Logs)", expanded=True):
        if not st.session_state.logs:
            st.caption("No activity yet...")
        else:
            for log in st.session_state.logs:
                st.text(log)