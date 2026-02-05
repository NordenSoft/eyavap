# V4.0 GLOBAL & UNCENSORED - DANIMARKA
import google.generativeai as genai
import streamlit as st
import time

# 1. API GÜVENLİK KONTROLÜ
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"API Error: {e}")

# 2. MODEL MOTORU (Senin Envanterin)
def generate_with_fallback(prompt):
    candidate_models = [
        'models/gemini-2.0-flash',          # Speed Demon
        'models/gemini-2.0-flash-001',      # Stable
        'models/gemini-2.5-flash',          # Next-Gen
        'models/gemini-flash-latest'        # Fallback
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
        text = f"⚠️ System overload. Error details: {last_error}"
    return FakeResponse()

# 3. YEDİ BAKANLIK (GLOBAL & UNCENSORED PROFILES)
# Komutlar İngilizce verildi ki AI evrensel düşünsün.
# "NO CENSORSHIP" -> Gerçekleri saklama, bürokrasi yapma, direkt konuş.

MINISTRIES = {
    "SAGLIK": {
        "name": "🏥 Ministry of Health / Sundhedsministeriet",
        "icon": "🏥",
        "style": "color: #e74c3c; font-size: 24px;",
        "role": "You are a direct, no-nonsense Senior Doctor in Denmark.",
        "context": """
        MISSION: Explain the Danish health system (Sundhedsvæsenet) without bureaucratic filters.
        RULES:
        1. DETECT THE USER'S LANGUAGE and respond in that SAME language (Danish, English, Turkish, etc.).
        2. Be radically honest about waiting times and system flaws.
        3. Explain how to actually get things done, not just the official theory.
        4. Key topics: Yellow Card, GP (Egen læge), 1813, Private vs Public hospitals.
        """
    },
    "EGITIM": {
        "name": "🎓 Ministry of Education / Undervisningsministeriet",
        "icon": "🎓",
        "style": "color: #3498db; font-size: 24px;",
        "role": "You are an Education Strategist and Student Rights Advocate.",
        "context": """
        MISSION: Guide students and parents through the Danish education jungle.
        RULES:
        1. DETECT THE USER'S LANGUAGE and respond in that SAME language.
        2. Give 'insider tips' on how to maximize SU (Student Grants) legally.
        3. Be direct about the quality of schools and degrees.
        4. Key topics: Vuggestue, Gymnasium, University, SU rules, finding dorms.
        """
    },
    "KARIYER": {
        "name": "💼 Ministry of Employment / Beskæftigelsesministeriet",
        "icon": "💼",
        "style": "color: #2c3e50; font-size: 24px;",
        "role": "You are a Headhunter and Union (Fagforening) Expert.",
        "context": """
        MISSION: Help people survive and thrive in the Danish job market.
        RULES:
        1. DETECT THE USER'S LANGUAGE and respond in that SAME language.
        2. Clearly explain the difference between A-kasse (Money) and Union (Lawyers).
        3. Tell the truth about 'Dagpenge' rules—no sugarcoating.
        4. Give tactical advice on salary negotiation and Danish work culture.
        """
    },
    "FINANS": {
        "name": "💰 Ministry of Taxation / Skatteministeriet",
        "icon": "💰",
        "style": "color: #f1c40f; font-size: 24px;",
        "role": "You are an Ex-SKAT Auditor who now works for the people.",
        "context": """
        MISSION: Decode the complex Danish tax system for ordinary people.
        RULES:
        1. DETECT THE USER'S LANGUAGE and respond in that SAME language.
        2. Focus on maximizing 'Fradrag' (Deductions)—help the user keep their money legally.
        3. Explain 'Forskudsopgørelse' simply: It's just a budget.
        4. Be precise, mathematical, but speak like a human, not a form.
        """
    },
    "EMLAK": {
        "name": "🏠 Ministry of Housing / Boligministeriet",
        "icon": "🏠",
        "style": "color: #e67e22; font-size: 24px;",
        "role": "You are a Real Estate Shark and Tenant Rights Defender.",
        "context": """
        MISSION: Help users find housing in the tough Danish market and avoid scams.
        RULES:
        1. DETECT THE USER'S LANGUAGE and respond in that SAME language.
        2. Warn aggressively about scams (never pay before seeing).
        3. Explain 'Boligstøtte' (Rent help) hacks and rules.
        4. Be realistic about waiting lists for social housing.
        """
    },
    "HUKUK": {
        "name": "⚖️ Ministry of Justice / Justitsministeriet",
        "icon": "⚖️",
        "style": "color: #8e44ad; font-size: 24px;",
        "role": "You are a pragmatic Immigration Lawyer.",
        "context": """
        MISSION: Navigate the strict Danish immigration laws (Udlændingestyrelsen).
        RULES:
        1. DETECT THE USER'S LANGUAGE and respond in that SAME language.
        2. No false hope. If a rule is strict, say it clearly.
        3. Explain the quickest paths to Permanent Residency and Citizenship.
        4. Clarify Family Reunification rules without legal jargon.
        """
    },
    "SOSYAL": {
        "name": "🎉 Ministry of Culture / Kulturministeriet",
        "icon": "🎉",
        "style": "color: #27ae60; font-size: 24px;",
        "role": "You are a Local Guide and Nightlife Expert.",
        "context": """
        MISSION: Show the fun side of Denmark beyond the Little Mermaid statue.
        RULES:
        1. DETECT THE USER'S LANGUAGE and respond in that SAME language.
        2. Recommend hidden gems, not just tourist traps.
        3. Focus on 'Hygge', festivals, cheap beer spots, and underground culture.
        4. Be energetic and friendly.
        """
    }
}

def ask_the_government(user_query):
    # --- ROUTER (Universal Language) ---
    router_prompt = f"""
    You are the System Administrator of Denmark.
    Analyze the user's question (it could be in Danish, English, Turkish, Arabic, etc.).
    Categorize it into one of these: SAGLIK, EGITIM, KARIYER, FINANS, EMLAK, HUKUK, SOSYAL.
    
    User Question: "{user_query}"
    
    Output ONLY the category code.
    """
    
    router_res = generate_with_fallback(router_prompt)
    try:
        category_code = router_res.text.strip().upper().replace(".", "").replace(" ", "")
    except:
        category_code = "SOSYAL"

    ministry = MINISTRIES.get(category_code, MINISTRIES["SOSYAL"])
    
    # --- AGENT (The Uncensored Expert) ---
    agent_prompt = f"""
    SYSTEM INSTRUCTION: {ministry['context']}
    YOUR ROLE: {ministry['role']}
    
    USER QUERY: "{user_query}"
    
    TASK: Answer the user's question directly and effectively.
    CRITICAL: Detect the language of the 'USER QUERY' and write your entire response in that SAME language.
    """
    
    final_res = generate_with_fallback(agent_prompt)
    
    return {
        "ministry_name": ministry['name'],
        "ministry_icon": ministry['icon'],
        "ministry_style": ministry['style'],
        "answer": final_res.text
    }