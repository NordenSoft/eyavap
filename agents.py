# V3.0 PRO SURUM - FINAL FIX
import google.generativeai as genai
import streamlit as st
import time

# 1. API GÜVENLİK KONTROLÜ
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"API Anahtar Hatası: {e}")

# 2. MODEL MOTORU (Senin Envanterine Göre)
def generate_with_fallback(prompt):
    candidate_models = [
        'models/gemini-2.0-flash',          # 1. Tercih
        'models/gemini-2.0-flash-001',      # 2. Tercih
        'models/gemini-2.5-flash',          # 3. Tercih
        'models/gemini-flash-latest'        # 4. Tercih
    ]
    
    last_error = ""
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response
        except Exception as e:
            last_error = str(e)
            time.sleep(0.5)
            continue
            
    class FakeResponse:
        text = f"⚠️ Sistem şu an cevap veremiyor. (Hata: {last_error})"
    return FakeResponse()

# 3. YEDİ BAKANLIK (Gelişmiş Profil)
MINISTRIES = {
    "SAGLIK": {
        "name": "🏥 Danimarka Sağlık Bakanlığı",
        "icon": "🏥",
        "style": "color: #e74c3c; font-size: 24px;",
        "role": "Sen Danimarka Sağlık Sistemi (Sundhedsvæsenet) Başhekimi ve uzmanısın.",
        "context": "GÖREVİN: Sağlık sistemi hakkında güvenilir bilgi vermek. Aile hekimi, İlaçlar, Sarı Kart, 1813 Acil Hattı konularında uzmansın."
    },
    "EGITIM": {
        "name": "🎓 Eğitim ve Araştırma Bakanlığı",
        "icon": "🎓",
        "style": "color: #3498db; font-size: 24px;",
        "role": "Sen Danimarka Eğitim Sistemi Danışmanı ve pedagojik uzmansın.",
        "context": "GÖREVİN: Okul sistemi, Kreş, Lise, Üniversite ve SU (Öğrenci Maaşı) hakkında rehberlik etmek."
    },
    "KARIYER": {
        "name": "💼 Çalışma ve İstihdam Bakanlığı",
        "icon": "💼",
        "style": "color: #2c3e50; font-size: 24px;",
        "role": "Sen sertifikalı bir Danimarka Kariyer Koçu ve Sendika Uzmanısın.",
        "context": "GÖREVİN: İş arama, Jobindex, CV hazırlama, Dagpenge (İşsizlik maaşı) ve A-kasse konularında yardım etmek."
    },
    "FINANS": {
        "name": "💰 Vergi ve Ekonomi Bakanlığı",
        "icon": "💰",
        "style": "color: #f1c40f; font-size: 24px;",
        "role": "Sen SKAT (Danimarka Vergi Dairesi) Kıdemli Denetçisisin.",
        "context": "GÖREVİN: Vergi kartları, Fradrag (indirimler), Forskudsopgørelse ve NemKonto konularını net anlatmak."
    },
    "EMLAK": {
        "name": "🏠 Konut ve Şehircilik Bakanlığı",
        "icon": "🏠",
        "style": "color: #e67e22; font-size: 24px;",
        "role": "Sen Kopenhag Emlak Piyasası ve Kiracı Hakları Uzmanısın.",
        "context": "GÖREVİN: Kiralık ev bulma, BoligPortal, Kira yardımı (Boligstøtte) ve taşınma kuralları hakkında bilgi vermek."
    },
    "HUKUK": {
        "name": "⚖️ Adalet ve Entegrasyon Bakanlığı",
        "icon": "⚖️",
        "style": "color: #8e44ad; font-size: 24px;",
        "role": "Sen Göçmenlik Hukuku ve Vatandaşlık Uzmanı bir Avukatsın.",
        "context": "GÖREVİN: Oturum izni, Vatandaşlık başvurusu, MitID ve Aile birleşimi prosedürlerini anlatmak."
    },
    "SOSYAL": {
        "name": "🎉 Kültür ve Yaşam Bakanlığı",
        "icon": "🎉",
        "style": "color: #27ae60; font-size: 24px;",
        "role": "Sen Danimarka'nın en popüler Turizm Rehberi ve Gurmesisin.",
        "context": "GÖREVİN: Etkinlikler, Tivoli, Restoranlar, Müzeler ve 'Hygge' kültürü hakkında önerilerde bulunmak."
    }
}

def ask_the_government(user_query):
    # --- ROUTER ---
    router_prompt = f"""
    Sen Danimarka Devlet Yöneticisisin. Soruyu analiz et ve kategoriyi seç.
    Kategoriler: SAGLIK, EGITIM, KARIYER, FINANS, EMLAK, HUKUK, SOSYAL
    Soru: "{user_query}"
    Cevap (Sadece tek kelime kategori kodu):
    """
    
    router_res = generate_with_fallback(router_prompt)
    
    # İŞTE HATA BURADAYDI, ŞİMDİ DÜZELTİLDİ:
    try:
        category_code = router_res.text.strip().upper().replace(".", "").replace(" ", "")
    except:
        category_code = "SOSYAL"

    ministry = MINISTRIES.get(category_code, MINISTRIES["SOSYAL"])
    
    # --- AGENT ---
    agent_prompt = f"""
    {ministry['context']}
    ROLÜN: {ministry['role']}
    SORU: "{user_query}"
    Bu soruyu rolüne uygun, Türkçe ve çözüm odaklı cevapla.
    """
    
    final_res = generate_with_fallback(agent_prompt)
    
    return {
        "ministry_name": ministry['name'],
        "ministry_icon": ministry['icon'],
        "ministry_style": ministry['style'],
        "answer": final_res.text
    }