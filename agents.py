import google.generativeai as genai
import streamlit as st
import time

# 1. API ANAHTARINI ÇEK
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    print(f"API Hatası: {e}")

# --- YARDIMCI FONKSİYON: GÜVENLİ ÜRETİM VE TEŞHİS ---
def generate_with_fallback(prompt):
    # Bu liste denenecek öncelikli modellerimiz
    candidate_models = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-2.0-flash-exp',
        'gemini-1.0-pro'
    ]
    
    last_error = ""
    
    # 1. Önce bildiklerimizi deneyelim
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response
        except Exception as e:
            last_error = str(e)
            time.sleep(0.5)
            continue
            
    # 2. HİÇBİRİ ÇALIŞMAZSA: Google'a "E elinde ne var?" diye soralım
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        debug_msg = f"⚠️ HATA: Seçilen modeller çalışmadı. Ancak hesabınızda ŞU MODELLER AÇIK (Bunu geliştiriciye ilet): {available_models}"
    except Exception as e:
        debug_msg = f"⚠️ Kritik Hata: Modeller bile listelenemedi. API Key veya Yetki sorunu olabilir. Detay: {last_error}"

    class FakeResponse:
        text = debug_msg
    return FakeResponse()

# --- 7 SÜTUNUN ANAYASASI ---
MINISTRIES = {
    "SAGLIK": {
        "name": "🏥 Danimarka Sağlık Bakanlığı",
        "role": "Sen Danimarka sağlık sistemi (Sundhed) uzmanısin.",
        "context": "Konular: Aile hekimi, 1813, Sundhedskort."
    },
    "EGITIM": {
        "name": "🎓 Eğitim Bakanlığı",
        "role": "Sen Danimarka eğitim sistemi uzmanısın.",
        "context": "Konular: Kreş, Okul, Lise, Üniversite, SU."
    },
    "KARIYER": {
        "name": "💼 Çalışma ve Kariyer Bakanlığı",
        "role": "Sen iş ve kariyer uzmanısın.",
        "context": "Konular: Jobindex, CV, Dagpenge, A-kasse."
    },
    "FINANS": {
        "name": "💰 Ekonomi ve Vergi Bakanlığı",
        "role": "Sen Skat (Vergi) uzmanısın.",
        "context": "Konular: Vergi, Forskudsopgørelse, Banka."
    },
    "EMLAK": {
        "name": "🏠 Konut ve Barınma Bakanlığı",
        "role": "Sen emlak uzmanısın.",
        "context": "Konular: Kiralık ev, Boligstøtte."
    },
    "HUKUK": {
        "name": "⚖️ Adalet ve Vatandaşlık Bakanlığı",
        "role": "Sen avukatsın.",
        "context": "Konular: Oturum izni, Vatandaşlık, MitID."
    },
    "SOSYAL": {
        "name": "🎉 Kültür ve Sosyal Yaşam Bakanlığı",
        "role": "Sen yaşam rehberisin.",
        "context": "Konular: Etkinlikler, Tivoli."
    }
}

def ask_the_government(user_query):
    # Router
    router_prompt = f"Soru: {user_query}. Hangi kategori? (SAGLIK, EGITIM, KARIYER, FINANS, EMLAK, HUKUK, SOSYAL). Tek kelime."
    router_res = generate_with_fallback(router_prompt)
    
    try:
        cat = router_res.text.strip().upper().replace(".", "")
    except:
        cat = "SOSYAL"
        
    selected = MINISTRIES.get(cat, MINISTRIES["SOSYAL"])
    
    # Agent
    agent_prompt = f"Rolün: {selected['role']}. Soru: {user_query}. Cevapla:"
    final_res = generate_with_fallback(agent_prompt)
    
    return {"ministry_name": selected['name'], "answer": final_res.text}