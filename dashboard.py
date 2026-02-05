import streamlit as st
from agents import ask_the_government

# Sayfa Ayarları
st.set_page_config(
    page_title="DK-OS: Danimarka Yönetim Sistemi", 
    page_icon="🇩🇰", 
    layout="centered"
)

# Başlık Kısmı
st.title("🇩🇰 DK-OS")
st.markdown("### *Danimarka Dijital Devletine Hoşgeldiniz*")
st.info("💡 **İpucu:** 'Çocuğum hasta', 'Ev arıyorum', 'Vergi borcum var mı?' gibi sorular sorabilirsiniz.")

# Sohbet Geçmişini Sakla (Session State)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Eski Mesajları Ekrana Yazdır
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# KULLANICI SORU SORDUĞUNDA...
if user_input := st.chat_input("Devlet yetkililerine bir soru sor..."):
    
    # 1. Kullanıcının sorusunu ekrana bas ve kaydet
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Devletin Cevabını Bekle
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔄 *Bakanlıklarla görüşülüyor, lütfen bekleyin...*")
        
        try:
            # Backend'e (agents.py) git ve soruyu sor
            result = ask_the_government(user_input)
            
            # Cevabı formatla
            final_answer = f"**🏛️ {result['ministry_name']} Yanıtlıyor:**\n\n{result['answer']}"
            
            # Ekrana bas
            message_placeholder.markdown(final_answer)
            
            # Cevabı kaydet
            st.session_state.chat_history.append({"role": "assistant", "content": final_answer})
            
        except Exception as e:
            message_placeholder.error(f"⚠️ Bir hata oluştu: {e}")