import google.generativeai as genai
import streamlit as st

# 1. API ANAHTARINI ÇEK
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    print(f"API Hatası: {e}")

# 2. AKILLI MODEL SEÇİCİ (Smart Model Loader)
# Senin stratejin: Sırayla dene, hangisi çalışıyorsa onu kap.
def get_working_model():
    # Denenecek Modeller Listesi (En hızlıdan yavaşa doğru)
    candidate_models = [
        'gemini-1.5-flash',          # En standart alias
        'models/gemini-1.5-flash',   # Tam yol ile
        'gemini-1.5-flash-latest',   # En güncel sürüm
        'gemini-1.5-flash-001',      # Kararlı eski sürüm
        'gemini-1.5-pro',            # Flash yoksa Pro (Ağır ama çalışır)
        'gemini-1.0-pro'             # En eski güvenli liman
    ]
    
    for model_name in candidate_models:
        try:
            # Test atışı yapalım (Boş bir model oluştur)
            model = genai.GenerativeModel(model_name)
            return model
        except:
            continue
            
    # Hiçbiri olmazsa varsayılanı döndür
    return genai.GenerativeModel('gemini-1.5-flash')

# En sağlam modeli seçiyoruz
model = get_working_model()

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
    # --- ADIM A: YÖNLENDİRİCİ (ROUTER) ---
    router_prompt = f"""
    Sen Danimarka Devlet Sisteminin Yöneticisisin.
    Gelen soruyu analiz et ve aşağıdaki kategorilerden hangisine ait olduğunu TEK KELİME ile söyle.
    Kategoriler: SAGLIK, EGITIM, KARIYER, FINANS, EMLAK, HUKUK, SOSYAL
    Soru: "{user_query}"
    Cevap (Sadece kategori kodu):
    """
    
    try:
        router_response = model.generate_content(router_prompt)
        category_code = router_response.text.strip().upper().replace(".", "").replace(" ", "")
    except:
        category_code = "SOSYAL" 

    selected_ministry = MINISTRIES.get(category_code, MINISTRIES["SOSYAL"])
    
    # --- ADIM B: UZMAN CEVABI (AGENT) ---
    agent_prompt = f"""
    SENİN ROLÜN: {selected_ministry['role']}
    UZMANLIK ALANIN: {selected_ministry['context']}
    KULLANICI SORUSU: "{user_query}"
    GÖREVİN: Bu soruyu Danimarka kurallarına göre Türkçe, net ve çözüm odaklı cevapla.
    """
    
    # Burada da hata olursa yakalayalım
    try:
        final_response = model.generate_content(agent_prompt)
        answer_text = final_response.text
    except Exception as e:
        answer_text = f"⚠️ Bağlantı hatası oluştu. Lütfen tekrar deneyin. (Hata: {str(e)})"
    
    return {
        "ministry_name": selected_ministry['name'],
        "answer": answer_text
    }