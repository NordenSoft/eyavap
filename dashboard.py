import streamlit as st
from agents import ask_the_government

# 1. PAGE SETUP
st.set_page_config(
    page_title="DK-OS: Universal Denmark Guide",
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
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# 3. SIDEBAR (Universal)
with st.sidebar:
    st.title("🇩🇰 DK-OS Panel")
    st.markdown("---")
    
    st.info("""
    **Universal AI Assistant for Denmark**
    
    🇩🇰 Dansk
    🇬🇧 English
    🇹🇷 Türkçe
    ...and more!
    """)
    
    st.markdown("### ⚙️ Settings / Indstillinger")
    
    if st.button("🗑️ Clear Chat / Ryd Chat", type="primary"):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.caption("v4.0 GLOBAL | Uncensored AI")

# 4. MAIN TITLE
st.title("🇩🇰 DK-OS")
st.subheader("Open Source Government AI")
st.markdown("💬 *Ask anything in your own language / Spørg om alt på dit eget sprog*")

# 5. CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# 6. INPUT & RESPONSE
if prompt := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("🤖 Processing..."):
        response_data = ask_the_government(prompt)
        
        # HEADER DESIGN
        header_html = f"""
        <div class="ministry-header">
            <div style="font-size: 50px;">{response_data['ministry_icon']}</div>
            <div style="{response_data['ministry_style']} font-weight:bold;">{response_data['ministry_name']}</div>
        </div>
        """
        
        full_response = header_html + response_data["answer"]

    with st.chat_message("assistant"):
        st.markdown(full_response, unsafe_allow_html=True)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})