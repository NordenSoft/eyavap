import streamlit as st
from agents import ask_the_government

# 1. PAGE SETUP
st.set_page_config(
    page_title="DK-OS",
    page_icon="🇩🇰",
    layout="centered"
)

# 2. STYLE
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
    /* Gereksiz boşlukları alalım */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# 3. SIDEBAR (Minimalist)
with st.sidebar:
    st.title("🇩🇰 DK-OS")
    st.caption("Open Source Government AI")
    
    st.markdown("---")
    
    # Sadece durum göstergesi (Havalılık katar)
    st.success("🟢 System Online")
    st.caption("Global Language Detection: Active")
    
    st.markdown("---")
    
    # Tek ve Net Buton
    if st.button("🗑️ Reset Chat", type="primary"):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.markdown("build v4.1")

# 4. MAIN TITLE
st.title("🇩🇰 DK-OS")
st.markdown("### Direct access to Danish Government")
st.markdown("*No bureaucracy. No waiting lines. Just answers.*")

# 5. CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# 6. INPUT & RESPONSE
if prompt := st.chat_input("Ask anything... (Dansk, English, Türkçe, etc.)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Processing..."):
        response_data = ask_the_government(prompt)
        
        # HEADER DESIGN
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