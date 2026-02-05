import google.generativeai as genai
import streamlit as st

# 1. API ANAHTARINI ÇEK
# Streamlit Secrets'tan anahtarı alır.
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    # Eğer yerelde çalışıyorsa veya hata varsa göster
    print(f"API Bağlantı Hatası: {e}")

# 2. MODEL SEÇİMİ (Garanti Model)
# 2.0 Flash modeli henüz Danimarka/Avrupa bölgesinde kota sorunu (429) yaratabildiği için
# kendini kanıtlamış, hızlı ve ücretsiz olan 1.5 Flash modelini kullanıyoruz.
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. YEDİ BAKANLIK (Devletin Hafızası)
MINISTRIES = {
    "SAGLIK": {
        "name": "🏥 Danimarka Sağlık Bakanlığı",
        "role": "Sen Danimarka sağlık sistemi (Sundhed) uzmanı, şefkatli bir doktorsun.",
        "context": "Konular: Aile hekimi (Praktiserende læge), 1813 Acil Hattı, Sundhedskort (Sarı kart), İlaçlar, Psikoloji."
    },
    "EGITIM": {
        "name": "🎓 Eğitim Bakanlığı",
        "role": "Sen Danimarka eğitim sistemi uzmanısın. Öğretici bir dilsin var.",
        "context": "Konular: Kreş (Vuggestue/Børnehave), Okul (Folkeskole), Lise (Gymnasium), Üniversite, SU (Öğrenci maaşı)."
    },
    "KARIYER": {
        "name": "💼 Çalışma ve Kariyer Bakanlığı",
        "role": "Sen sert bir kariyer koçu ve iş hukuku uzmanısın.",
        "context": "Konular: Jobindex, LinkedIn, CV hazırlama, Dagpenge (İşsizlik maaşı), A-kasse, Sendikalar."
    },
    "FINANS": {
        "name": "💰 Ekonomi ve Vergi Bakanlığı",
        "role": "Sen Skat.dk (Vergi) ve yatırım uzmanısın. Çok titizsin.",
        "context": "Konular: Vergi kartları (Forskudsopgørelse), Vergi iadesi, NemKonto, Banka kredileri, Kripto vergisi."
    },
    "EMLAK": {
        "name": "🏠 Konut ve Barınma Bakanlığı",
        "role": "Sen Kopenhag emlak piyasasının kurdusun.",
        "context": "Konular: Kiralık ev bulma (BoligPortal), Kira yardımı (Boligstøtte), Elektrik/Su faturaları, Taşınma kuralları."
    },
    "HUKUK": {
        "name": "⚖️ Adalet ve Vatandaşlık Bakanlığı",
        "role": "Sen tecrübeli bir Danimarka avukatısın. Resmi konuşursun.",
        "context": "Konular: Oturum izni (Ny i Danmark), Vatandaşlık, MitID, Boşanma, Aile birleşimi."
    },
    "SOSYAL": {
        "name": "🎉 Kültür ve Sosyal Yaşam Bakanlığı",
        "role": "Sen Danimarka'nın en eğlenceli rehberisin.",
        "context": "Konular: Kopenhag etkinlikleri, Restoranlar, Tivoli, Festivaller, Müzeler."
    }
}

def ask_the_government(user_query):
    """
    Bu fonksiyon:
    1. Soruyu alır.
    2. Hangi bakanlığın bakacağına karar verir (Router).
    3. O bakanlıktan cevabı alıp getirir.
    """
    
    # --- ADIM A: YÖNLENDİRİCİ (ROUTER) ---
    router_prompt = f"""
    Sen Danimarka Devlet Sisteminin Yöneticisisin.
    Gelen soruyu analiz et ve aşağıdaki kategorilerden hangisine ait olduğunu TEK KELİME ile söyle.
    
    Kategoriler: SAGLIK, EGITIM, KARIYER, FINANS, EMLAK, HUKUK, SOSYAL
    
    Soru: "{user_query}"
    
    Cevap (Sadece kategori kodu, noktalama işareti koyma):
    """
    
    try:
        router_response = model.generate_content(router_prompt)
        # Gelen cevabı temizle (boşlukları ve noktaları sil)
        category_code = router_response.text.strip().upper().replace(".", "").replace(" ", "")
    except:
        category_code = "SOSYAL" # Hata olursa varsayılan

    # Bakanlığı seç (Eğer saçma bir cevap geldiyse SOSYAL'e yönlendir)
    selected_ministry = MINISTRIES.get(category_code, MINISTRIES["SOSYAL"])
    
    # --- ADIM B: UZMAN CEVABI (AGENT) ---
    agent_prompt = f"""
    SENİN ROLÜN: {selected_ministry['role']}
    UZMANLIK ALANIN: {selected_ministry['context']}
    
    KULLANICI SORUSU: "{user_query}"
    
    GÖREVİN: 
    Bu soruyu Danimarka kurallarına ve gerçeklerine göre cevapla. 
    Cevabın Türkçe olsun.
    Net, çözüm odaklı ve yardımsever ol.
    Gerekiyorsa adım adım yapılması gerekenleri maddeler halinde yaz.
    """
    
    final_response = model.generate_content(agent_prompt)
    
    return {
        "ministry_name": selected_ministry['name'],
        "answer": final_response.text
    }