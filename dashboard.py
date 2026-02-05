import streamlit as st
from agents import ask_the_government
import datetime

# 1. PAGE CONFIG
st.set_page_config(
    page_title="DK-OS Privacy",
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
    .privacy-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        font-size: 12px;
        text-align: center;
        border: 1px solid #c3e6cb;
    }
</style>
""", unsafe_allow_html=True)

# 3. SIDEBAR (GİZLİLİK ODAKLI)
with st.sidebar:
    st.title("🇩🇰 DK-OS")
    st.caption("v5.3 | Stable & Secure")
    
    st.markdown("---")
    
    # LOG YERİNE GÜVEN ROZETİ
    st.markdown("""
    <div class="privacy-badge">
        🔒 <b>100% Anonymous</b><br>
        No personal data is stored.<br>
        Your chat is private.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear History", type="primary"):
        st.session_state.messages = []
        st.rerun()

# 4. HEADER
st.title("🇩🇰 DK-OS")
st.markdown("### Digital State Assistant")
st.markdown("*Ask freely. No bureaucracy, no tracking.*")

# 5. CHAT LOGIC
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Type here..."):
    # GİZLİ LOGLAMA (Sadece sen siyah ekranda görürsün)
    print(f"--- NEW USER QUERY: {prompt} ---")
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Processing..."):
        response_data = ask_the_government(prompt)
        
        # GİZLİ LOGLAMA 2
        print(f"--- ASSIGNED TO: {response_data['ministry_name']} ---")
        
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