import time
import streamlit as st
import google.generativeai as genai
from openai import OpenAI

def ask_the_government(user_query: str):
    openai_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("openai", {}).get("api_key")
    gemini_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("gemini", {}).get("api_key")

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

    # --- 2) GEMINI (fallback) ---
    if not answer and gemini_key:
        try:
            genai.configure(api_key=gemini_key)

            # ⚠️ model adını düzelt
            model = genai.GenerativeModel("gemini-1.0-pro")

            # basit backoff (429 vs.)
            last_err = None
            for i in range(3):
                try:
                    res = model.generate_content(user_query)
                    answer = (getattr(res, "text", "") or "").strip()
                    if answer:
                        model_used = "Google Gemini"
                        break
                except Exception as e:
                    last_err = e
                    time.sleep(1.5 * (2 ** i))  # 1.5s, 3s, 6s

            if not answer and last_err:
                raise last_err

        except Exception as e:
            st.warning(f"Gemini hattı da düştü: {e}")

    # --- 3) İkisi de yoksa / ikisi de patladıysa ---
    if not answer:
        answer = "⚠️ Şu an yanıt üretilemiyor. (AI kotası/bağlantı sorunu olabilir). Biraz sonra tekrar dene."

    return {
        "answer": answer,
        "ministry_name": f"Tora {model_used or 'Offline'} Hattı",
        "ministry_icon": "🏛️",
        "ministry_style": "color: white;"
    }
