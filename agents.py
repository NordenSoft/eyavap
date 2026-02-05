import google.generativeai as genai
import streamlit as st
import time

# 1. API ANAHTARINI ÇEK
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    print(f"API Hatası: {e}")

# --- YARDIMCI FONKSİYON: MODEL SEÇİCİ ---
def generate_with_fallback(prompt):
    """
    Senin API listendeki GERÇEK modelleri dener.
    """
    # SENİN LİSTENE GÖRE GÜNCELLENMİŞ SİLAHLAR:
    candidate_models = [
        'models/gemini-2.0-flash',          # 1. TERCİH: Çok hızlı ve çok zeki (Listende var)
        'models/gemini-2.0-flash-001',      # 2. TERCİH: Alternatif versiyon
        'models/gemini-2.5-flash',          # 3. TERCİH: En yeni teknoloji
        'models/gemini-2.0-flash-lite',     # 4. TERCİH: Hafif sıklet (Çok hızlı)
        'models/gemini-flash-latest'        # 5. TERCİH: Genel yönlendirme
    ]
    
    last_error = ""
    
    for model_name in candidate_models:
        try:
            # Modeli yükle
            model = genai.GenerativeModel(model_name)
            # Üretmeyi dene
            response = model.generate_content(prompt)
            return response
        except Exception as e:
            # Hata alırsak logla ve diğerine geç
            print(f"⚠️ {model_name} başarısız: {e}")
            last_error = str(e)
            time.sleep(1) 
            continue
            
    # Hiçbiri çalışmazsa (İmkansız ama ne olur ne olmaz)
    class FakeResponse:
        text = f"⚠️ Sistem şu an cevap veremiyor. Hata Detayı: {last_error}"
    return FakeResponse()

# --- 7 SÜTUNUN ANAYASASI ---
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
    
    router_res = generate_with_fallback(router_prompt)
    
    try:
        category_code = router_res.text.strip().upper().replace(".", "").replace(" ", "")
    except:
        category_code = "SOSYAL"

    selected_ministry = MINISTRIES.get(category_code, MINISTRIES["SOSYAL"])
    
    # --- ADIM B: UZMAN CEVABI (AGENT) ---
    agent_prompt = f"""
    SENİN ROLÜN: {selected_ministry['role']}
    UZMANLIK ALANIN: {selected_ministry['context']}
    
    KULLANICI SORUSU: "{user_query}"
    
    GÖREVİN: 
    Bu soruyu Danimarka kurallarına göre Türkçe, net ve çözüm odaklı cevapla.
    """
    
    final_res = generate_with_fallback(agent_prompt)
    
    return {
        "ministry_name": selected_ministry['name'],
        "answer": final_res.text
    }