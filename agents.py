import google.generativeai as genai
import streamlit as st
import time

# 1. API ANAHTARINI ÇEK
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    print(f"API Hatası: {e}")

# --- YARDIMCI FONKSİYON: GÜVENLİ ÜRETİM (Safe Generator) ---
def generate_with_fallback(prompt):
    """
    Bu fonksiyon sırayla modelleri dener.
    Flash hata verirse Pro devreye girer.
    """
    # Denenecek Modeller Listesi (Sıra Önemli: Hızlı -> Güçlü -> Eski)
    candidate_models = [
        'gemini-1.5-flash',          # İlk Hedef: Hız Canavarı
        'gemini-1.5-flash-latest',   # Alternatif isim
        'gemini-1.5-pro',            # Güvenli Liman (Biraz yavaş ama zeki)
        'gemini-pro'                 # Son Çare (Eski toprak)
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
            # Hata alırsak (404, 429 vs) logla ve sıradaki modele geç
            last_error = str(e)
            print(f"⚠️ {model_name} başarısız oldu, diğerine geçiliyor... Hata: {e}")
            time.sleep(1) # API'yi boğmamak için 1 saniye nefes al
            continue
            
    # Hiçbiri çalışmazsa yapay bir hata mesajı döndür
    class FakeResponse:
        text = f"⚠️ Sistem şu an aşırı yoğun. Lütfen 1 dakika sonra tekrar deneyin. (Teknik Detay: {last_error})"
    return FakeResponse()

# --- 7 SÜTUNUN ANAYASASI ---
MINISTRIES = {
    "SAGLIK": {
        "name": "🏥 Danimarka Sağlık Bakanlığı",
        "role": "Sen Danimarka sağlık sistemi (Sundhed) uzmanı, şefkatli bir doktorsun.",
        "context": "Konular: Aile hekimi (Praktiserende læge), 1813 Acil Hattı, Sundhedskort, İlaçlar."
    },
    "EGITIM": {
        "name": "🎓 Eğitim Bakanlığı",
        "role": "Sen Danimarka eğitim sistemi uzmanısın.",
        "context": "Konular: Kreş (Vuggestue), Okul, Lise, Üniversite, SU maaşı."
    },
    "KARIYER": {
        "name": "💼 Çalışma ve Kariyer Bakanlığı",
        "role": "Sen sert bir kariyer koçu ve iş hukuku uzmanısın.",
        "context": "Konular: Jobindex, CV, Dagpenge (İşsizlik maaşı), A-kasse, Sendikalar."
    },
    "FINANS": {
        "name": "💰 Ekonomi ve Vergi Bakanlığı",
        "role": "Sen Skat.dk (Vergi) ve yatırım uzmanısın.",
        "context": "Konular: Vergi kartları (Forskudsopgørelse), Vergi iadesi, NemKonto."
    },
    "EMLAK": {
        "name": "🏠 Konut ve Barınma Bakanlığı",
        "role": "Sen Kopenhag emlak piyasasının kurdusun.",
        "context": "Konular: Kiralık ev bulma, Boligstøtte (Kira yardımı), Elektrik/Su."
    },
    "HUKUK": {
        "name": "⚖️ Adalet ve Vatandaşlık Bakanlığı",
        "role": "Sen tecrübeli bir Danimarka avukatısın.",
        "context": "Konular: Oturum izni, Vatandaşlık, MitID, Boşanma."
    },
    "SOSYAL": {
        "name": "🎉 Kültür ve Sosyal Yaşam Bakanlığı",
        "role": "Sen Danimarka'nın en eğlenceli rehberisin.",
        "context": "Konular: Etkinlikler, Restoranlar, Tivoli, Festivaller."
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
    
    # Router için de güvenli fonksiyonu kullanıyoruz
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
    Bu soruyu Danimarka kurallarına göre Türkçe cevapla.
    """
    
    final_res = generate_with_fallback(agent_prompt)
    
    return {
        "ministry_name": selected_ministry['name'],
        "answer": final_res.text
    }