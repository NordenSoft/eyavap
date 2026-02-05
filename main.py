import streamlit as st
from agents import ask_the_government

# 1. SAYFA AYARLARI (Geniş Ekran ve Başlık)
st.set_page_config(
    page_title="DK-OS: Danimarka Asistanı",
    page_icon="🇩🇰",
    layout="centered"
)

# 2. CSS STİL (Görselliği Güzelleştirme)
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
    }
    .big-font {
        font-size:30px !important;
        font-weight: bold;
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

# 3. YAN MENÜ (SIDEBAR) - İSTEĞİN ÜZERİNE EKLENDİ
with st.sidebar:
    st.title("🇩🇰 DK-OS Panel")
    st.markdown("---")
    
    st.info("Bu asistan, Danimarka'da yaşayan Türkler için devlet işlemlerini kolaylaştırmak amacıyla geliştirilmiştir.")
    
    st.markdown("### ⚙️ Ayarlar")
    
    # GEÇMİŞİ TEMİZLE BUTONU
    if st.button("🗑️ Sohbeti Temizle", type="primary"):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.caption("v2.1 | Powered by Gemini 2.0 Flash")

# 4. BAŞLIK
st.title("🇩🇰 DK-OS")
st.subheader("Danimarka Dijital Devletine Hoşgeldiniz")
st.markdown("💡 *İpucu: 'Çocuğum hasta', 'Ev arıyorum', 'Vergi borcum var mı?' gibi sorular sorabilirsiniz.*")

# 5. SOHBET GEÇMİŞİ YÖNETİMİ
if "messages" not in st.session_state:
    st.session_state.messages = []

# Eski mesajları ekrana yaz
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# 6. KULLANICI GİRİŞİ VE CEVAP MEKANİZMASI
if prompt := st.chat_input("Devlet yetkililerine bir soru sor..."):
    # Kullanıcı mesajını ekle
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Düşünme efekti
    with st.spinner("🏛️ İlgili bakanlık aranıyor..."):
        response_data = ask_the_government(prompt)
        
        # LOGO VE BAŞLIK TASARIMI (BÜYÜK LOGO BURADA)
        # HTML kullanarak logoyu ve ismi şık bir kutu içine alıyoruz
        header_html = f"""
        <div class="ministry-header">
            <div style="font-size: 50px;">{response_data['ministry_icon']}</div>
            <div style="{response_data['ministry_style']} font-weight:bold;">{response_data['ministry_name']}</div>
            <div style="color: gray; font-size: 14px; margin-top:5px;">Resmi Yanıt</div>
        </div>
        """
        
        full_response = header_html + response_data["answer"]

    # Asistan cevabını ekle
    with st.chat_message("assistant"):
        st.markdown(full_response, unsafe_allow_html=True)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})