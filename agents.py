import google.generativeai as genai
import streamlit as st

# --- API YAPILANDIRMASI ---
def configure_genai():
    # Hem GEMINI_API_KEY hem de [gemini] altındaki api_key'i kontrol eder
    api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("gemini", {}).get("api_key")
    
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False


def pick_available_model(preferred_models=None):
    """
    Kullanılabilir modeller arasından uygun olanı seçer.
    """
    if preferred_models is None:
        preferred_models = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-8b",
            "models/gemini-2.0-flash",
            "models/gemini-1.5-pro",
            "models/gemini-pro",
        ]

    try:
        available = []
        for m in genai.list_models():
            if "generateContent" in getattr(m, "supported_generation_methods", []):
                available.append(m.name)

        for name in preferred_models:
            if name in available:
                return name

        # Tercih edilen yoksa ilk uygun modeli seç
        if available:
            return available[0]
    except Exception:
        pass

    # En son fallback
    return preferred_models[0]

# --- ANA CEVAP FONKSİYONU ---
def ask_the_government(user_query):
    if not configure_genai():
        return {"answer": "⚠️ API Key hatası! Secrets kısmını kontrol edin.", "ministry_name": "Sistem", "ministry_icon": "⚠️"}

    # Kullanılabilir modeli otomatik seç
    model_name = pick_available_model()
    model = genai.GenerativeModel(model_name)

    # Bakanlık Belirleme (Router)
    router_prompt = f"Categorize this Danish-related query into one: SAGLIK, EGITIM, KARIYER, FINANS, EMLAK, HUKUK, SOSYAL. Query: {user_query}. Output ONLY the category name."
    
    try:
        role_res = model.generate_content(router_prompt)
        category = role_res.text.strip().upper()
    except:
        category = "SOSYAL"

    # Bakanlık Bilgileri
    MINISTRIES = {
        "SAGLIK": {"name": "🏥 Ministry of Health", "role": "Danimarka sağlık sistemi uzmanı."},
        "EGITIM": {"name": "🎓 Ministry of Education", "role": "Danimarka eğitim ve SU uzmanı."},
        "KARIYER": {"name": "💼 Ministry of Employment", "role": "İş hukuku ve A-kasse uzmanı."},
        "FINANS": {"name": "💰 Ministry of Taxation", "role": "Skat ve vergi uzmanı."},
        "EMLAK": {"name": "🏠 Ministry of Housing", "role": "Kira hukuku uzmanı."},
        "HUKUK": {"name": "⚖️ Ministry of Justice", "role": "Göçmenlik ve vize avukatı."},
        "SOSYAL": {"name": "🎉 Ministry of Culture", "role": "Danimarka sosyal yaşam rehberi."}
    }

    m_info = MINISTRIES.get(category, MINISTRIES["SOSYAL"])

    # Final Cevap
    agent_prompt = f"Sen {m_info['role']} bir asistsansın. Soru: {user_query}. Türkçe cevap ver. Kısa ve net ol."
    
    try:
        final_res = model.generate_content(agent_prompt)
        return {
            "answer": final_res.text,
            "ministry_name": m_info['name'],
            "ministry_icon": m_info['name'].split()[0],
            "ministry_style": "color: white;"
        }
    except Exception as e:
        return {"answer": f"Bir hata oluştu: {str(e)}", "ministry_name": "Hata", "ministry_icon": "❌"}