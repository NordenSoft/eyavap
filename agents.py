import streamlit as st
from openai import OpenAI

def ask_the_government(user_query: str):
    openai_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("openai", {}).get("api_key")

    answer = ""
    model_used = ""

    # --- 1) OPENAI ---
    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model="gpt-4o",  # istersen gpt-4o-mini yap, daha ekonomik
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Sen Danimarka devlet sistemleri (skat, sağlık, hukuk) konusunda uzman, "
                            "profesyonel bir asistansın. Türkçe cevap ver. Kısa, öz ve çözüm odaklı ol."
                        )
                    },
                    {"role": "user", "content": user_query}
                ],
                temperature=0.3,
            )
            answer = (resp.choices[0].message.content or "").strip()
            model_used = "OpenAI GPT-4o"
        except Exception as e:
            # Streamlit log
            st.warning(f"OpenAI hattı düştü: {e}")

    # --- OpenAI yoksa / patladıysa ---
    if not answer:
        answer = "⚠️ Şu an yanıt üretilemiyor. (OpenAI anahtarı/bağlantı sorunu olabilir)."

    return {
        "answer": answer,
        "ministry_name": f"Tora {model_used or 'Offline'} Hattı",
        "ministry_icon": "🏛️",
        "ministry_style": "color: white;"
    }
