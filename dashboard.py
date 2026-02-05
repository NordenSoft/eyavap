# V6.1 TORA - IDENTITY UPDATE
import google.generativeai as genai
import streamlit as st
import time

# 1. API SETUP
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"API Error: {e}")

# 2. ROBUST GENERATION
def generate_with_fallback(prompt):
    candidate_models = [
        'models/gemini-2.0-flash',
        'models/gemini-2.0-flash-001',
        'models/gemini-2.5-flash',
        'models/gemini-flash-latest'
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
        text = f"⚠️ Tora system overload. Error: {last_error}"
    return FakeResponse()

# --- ACTION PROTOCOL ---
ACTION_PROTOCOL = """
*** CRITICAL INSTRUCTION FOR ACTION MODE ***
If the user asks for a letter, email, complaint, or application draft:
1. You MUST write a formal template inside a CODE BLOCK (```text ... ```).
2. Use placeholders like [MIT NAVN], [DATO] for parts the user needs to fill.
3. The template MUST be in the target language (usually Danish).
"""

# 3. MINISTRIES
MINISTRIES = {
    "SAGLIK": {
        "name": "🏥 Ministry of Health",
        "icon": "🏥",
        "style": "color: #e74c3c;",
        "role": "Direct Senior Doctor.",
        "context": "Topics: GP, Yellow Card, 1813, Waiting lists. Be honest about delays."
    },
    "EGITIM": {
        "name": "🎓 Ministry of Education",
        "icon": "🎓",
        "style": "color: #3498db;",
        "role": "Student Rights Defender.",
        "context": "Topics: SU, University applications, ECTS, Dorms. Give insider tips."
    },
    "KARIYER": {
        "name": "💼 Ministry of Employment",
        "icon": "💼",
        "style": "color: #2c3e50;",
        "role": "Union Expert & Headhunter.",
        "context": "Topics: Dagpenge, A-kasse, Job contracts. Warn about bad contracts."
    },
    "FINANS": {
        "name": "💰 Ministry of Taxation",
        "icon": "💰",
        "style": "color: #f1c40f;",
        "role": "Tax Optimization Expert.",
        "context": "Topics: Fradrag (Deductions), Forskudsopgørelse. Maximize the user's money."
    },
    "EMLAK": {
        "name": "🏠 Ministry of Housing",
        "icon": "🏠",
        "style": "color: #e67e22;",
        "role": "Tenant Rights Defender.",
        "context": "Topics: Deposit disputes, Rent control, Boligstøtte. FIGHT for the tenant."
    },
    "HUKUK": {
        "name": "⚖️ Ministry of Justice",
        "icon": "⚖️",
        "style": "color: #8e44ad;",
        "role": "Immigration Lawyer.",
        "context": "Topics: Visa, Citizenship, Permanent Residence, Family Reunification."
    },
    "SOSYAL": {
        "name": "🎉 Ministry of Culture",
        "icon": "🎉",
        "style": "color: #27ae60;",
        "role": "Local Guide.",
        "context": "Topics: Events, Hygge, Cheap eats, Hidden gems."
    }
}

def ask_the_government(user_query):
    # --- ROUTER (TORA IDENTITY) ---
    router_prompt = f"""
    You are 'Tora', the AI Administrator of Denmark.
    Categorize query: "{user_query}"
    Options: SAGLIK, EGITIM, KARIYER, FINANS, EMLAK, HUKUK, SOSYAL.
    Output ONLY category code.
    """
    
    router_res = generate_with_fallback(router_prompt)
    try:
        category_code = router_res.text.strip().upper().replace(".", "").replace(" ", "")
    except:
        category_code = "SOSYAL"

    ministry = MINISTRIES.get(category_code, MINISTRIES["SOSYAL"])
    
    # --- AGENT ---
    agent_prompt = f"""
    ROLE: {ministry['role']}
    CONTEXT: {ministry['context']}
    {ACTION_PROTOCOL}
    
    USER QUERY: "{user_query}"
    
    INSTRUCTION: Answer directly as part of the 'Tora' system. Detect language and respond in SAME language.
    """
    
    final_res = generate_with_fallback(agent_prompt)
    
    return {
        "ministry_name": ministry['name'],
        "ministry_icon": ministry['icon'],
        "ministry_style": ministry['style'],
        "answer": final_res.text,
        "category": category_code
    }