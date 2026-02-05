# V6.2 TORA - ARMORED CORE (ZIRHLI MOD)
import google.generativeai as genai
import streamlit as st
import time

# --- 1. GÜVENLİ BAĞLANTI (CRASH ÖNLEYİCİ) ---
def configure_genai():
    api_key = None
    try:
        # Önce tek başına duran anahtara bak
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
        # Yoksa [gemini] kutusunun içine bak (Eski yöntem)
        elif "gemini" in st.secrets and "api_key" in st.secrets["gemini"]:
            api_key = st.secrets["gemini"]["api_key"]
            
        if api_key:
            genai.configure(api_key=api_key)
            return True
        else:
            return False
    except Exception as e:
        st.error(f"⚠️ API Bağlantı Hatası: {e}")
        return False

# Sistemi başlat
is_connected = configure_genai()

# 2. ROBUST GENERATION
def generate_with_fallback(prompt):
    if not is_connected:
        class ErrorResponse:
            text = "⚠️ Sistem Hatası: API Anahtarı bulunamadı (Secrets ayarlarını kontrol et)."
        return ErrorResponse()

    candidate_models = [
        'models/gemini-2.0-flash',
        'models/gemini-1.5-flash',
        'models/gemini-pro'
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
        text = f"⚠️ Tora system overload (Google Gemini Hatası). Detay: {last_error}"
    return FakeResponse()

# --- ACTION PROTOCOL ---
ACTION_PROTOCOL = """
*** CRITICAL INSTRUCTION ***
If user asks for a formal letter/email: Write it inside a CODE BLOCK.
"""

# 3. MINISTRIES
MINISTRIES = {
    "SAGLIK": {"name": "🏥 Ministry of Health", "icon": "🏥", "style": "color: #e74c3c;", "role": "Senior Doctor.", "context": "Topics: GP, Yellow Card, 1813."},
    "EGITIM": {"name": "🎓 Ministry of Education", "icon": "🎓", "style": "color: #3498db;", "role": "Student Advisor.", "context": "Topics: SU, ECTS, Dorms."},
    "KARIYER": {"name": "💼 Ministry of Employment", "icon": "💼", "style": "color: #2c3e50;", "role": "Union Expert.", "context": "Topics: Dagpenge, A-kasse, Job contracts."},
    "FINANS": {"name": "💰 Ministry of Taxation", "icon": "💰", "style": "color: #f1c40f;", "role": "Tax Expert.", "context": "Topics: Fradrag, Skat."},
    "EMLAK": {"name": "🏠 Ministry of Housing", "icon": "🏠", "style": "color: #e67e22;", "role": "Tenant Defender.", "context": "Topics: Rent control, Deposit disputes."},
    "HUKUK": {"name": "⚖️ Ministry of Justice", "icon": "⚖️", "style": "color: #8e44ad;", "role": "Immigration Lawyer.", "context": "Topics: Visa, Citizenship."},
    "SOSYAL": {"name": "🎉 Ministry of Culture", "icon": "🎉", "style": "color: #27ae60;", "role": "Local Guide.", "context": "Topics: Events, Hygge, Life in DK."}
}

def ask_the_government(user_query):
    # --- ROUTER ---
    router_prompt = f"Categorize query: '{user_query}' into: SAGLIK, EGITIM, KARIYER, FINANS, EMLAK, HUKUK, SOSYAL. Output ONLY code."
    try:
        router_res = generate_with_fallback(router_prompt)
        category_code = router_res.text.strip().upper().replace(".", "")
    except:
        category_code = "SOSYAL"

    ministry = MINISTRIES.get(category_code, MINISTRIES["SOSYAL"])
    
    # --- AGENT ---
    agent_prompt = f"ROLE: {ministry['role']} context: {ministry['context']} Query: {user_query} Answer in same language."
    final_res = generate_with_fallback(agent_prompt)
    
    return {
        "ministry_name": ministry['name'],
        "ministry_icon": ministry['icon'],
        "ministry_style": ministry['style'],
        "answer": final_res.text,
        "category": category_code
    }