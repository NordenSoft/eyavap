import os
import sys
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# Streamlit opsiyonel (GitHub Actions'ta yoksa bile sorun olmasın)
try:
    import streamlit as st
except Exception:
    st = None

from supabase import create_client, Client

# Lokal için .env (GitHub Actions'ta env zaten gelir, bu zararsız)
load_dotenv()

# =========================
#  HELPERS
# =========================

def _get_secret(name: str, default: str = "") -> str:
    """ENV'den al, yoksa Streamlit secrets'a bak. Her zaman strip yap."""
    val = os.getenv(name, default)
    if (not val) and st is not None:
        try:
            val = st.secrets.get(name, default)
        except Exception:
            val = default
    return (str(val) if val is not None else "").strip()


def _get_deepinfra_token() -> str:
    """
    DeepInfra token için birden fazla isimden okumayı destekler.
    Senin secrets listende: DEEPINFRA_API_TOKEN var.
    """
    # Öncelik sırası: env -> streamlit secrets
    for key in ["DEEPINFRA_API_TOKEN", "DEEPINFRA_API_TOKEN", "DEEPINFRA_API_TOKEN"]:
        tok = _get_secret(key, "")
        if tok:
            return tok
    return ""


def _safe_host(url: str) -> str:
    try:
        return urlparse(url).netloc
    except Exception:
        return ""


# =========================
#  LLM CLIENTS (LLAMA + OPENAI FALLBACK)
# =========================

DEEPINFRA_CHAT_URL = "https://api.deepinfra.com/v1/openai/chat/completions"


def llama_chat(
    messages: List[Dict[str, str]],
    # Daha güvenli / ucuz default. İstersen 70B'ye yükseltirsin.
    model: str = "meta-llama/Llama-3-8B-Instruct",
    temperature: float = 0.2,
    max_tokens: int = 600,
    timeout: int = 60,
) -> str:
    """
    DeepInfra üzerinden Llama çağrısı.
    OpenAI uyumlu endpoint kullanır.
    """
    token = _get_deepinfra_token()
    if not token:
        raise ValueError("DeepInfra token yok. Secret adı: DEEPINFRA_API_TOKEN olmalı.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    r = requests.post(DEEPINFRA_CHAT_URL, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    return data["choices"][0]["message"]["content"]


def openai_chat(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.2,
    max_tokens: int = 600,
) -> str:
    """
    OpenAI fallback. openai paketi yüklü olmalı.
    """
    key = _get_secret("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("OPENAI_API_KEY yok")

    from openai import OpenAI  # lazy import

    client = OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def ai_answer(
    user_query: str,
    system_prompt: str = "Türkçe cevap ver. Kısa, net, çözüm odaklı ol. Emin olmadığın yerde açıkça belirt.",
    llama_first: bool = True,
) -> Dict[str, Any]:
    """
    Llama-first + OpenAI fallback cevap üretir.
    Dönen dict: { text, provider }
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    # 1) Llama
    if llama_first:
        try:
            text = llama_chat(messages)
            return {"text": text, "provider": "DeepInfra Llama"}
        except Exception as e:
            print(f"⚠️ Llama başarısız: {e}")

    # 2) OpenAI fallback
    try:
        text = openai_chat(messages)
        return {"text": text, "provider": "OpenAI"}
    except Exception as e:
        print(f"❌ OpenAI de başarısız: {e}")
        return {
            "text": "Şu an sistem yoğun veya anahtarlar eksik. Lütfen biraz sonra tekrar dene.",
            "provider": "None",
        }


# =========================
#  DATABASE (SUPABASE)
# =========================

class Database:
    """EYAVAP Komuta Merkezi: Supabase + hafıza + log"""

    def __init__(self):
        url = _get_secret("SUPABASE_URL", "")
        key = _get_secret("SUPABASE_SERVICE_ROLE_KEY", "") or _get_secret("SUPABASE_KEY", "")

        self.llama_key = _get_deepinfra_token()
        self.openai_key = _get_secret("OPENAI_API_KEY", "")

        # --- RAPOR (güvenli) ---
        if url:
            print(f"✅ SUPABASE HOST: {_safe_host(url)}")
        else:
            print("🚨 RAPOR: 'SUPABASE_URL' bulunamadı!")

        if not key:
            print("🚨 RAPOR: 'SUPABASE_SERVICE_ROLE_KEY' / 'SUPABASE_KEY' bulunamadı!")

        # Token uzunluğu: tokenı ifşa etmez, sadece var mı yok mu gösterir
        print(f"🦙 DeepInfra token length: {len(self.llama_key)}")
        print(f"🔑 OpenAI key length: {len(self.openai_key)}")

        if not url or not key:
            missing = []
            if not url:
                missing.append("SUPABASE_URL")
            if not key:
                missing.append("SUPABASE_SERVICE_ROLE_KEY/SUPABASE_KEY")
            raise ValueError(f"❌ HATA: Eksik ortam değişkenleri: {', '.join(missing)}")

        # Supabase client
        try:
            self.client: Client = create_client(url, key)
        except Exception as e:
            print(f"❌ Supabase bağlantı hatası: {e}")
            raise

    # ==================== RAG / HAFIZA ====================

    def veriyi_hafizaya_yaz(self, metin: str, kaynak_url: str, vektor: list):
        """Spider'dan gelen veriyi vektör hafızasına yazar"""
        try:
            data = {
                "icerik": metin,
                "kaynak_url": kaynak_url,
                "embedding": vektor,
                "created_at": datetime.utcnow().isoformat(),
            }
            self.client.table("skat_hafiza").insert(data).execute()
            print(f"✅ Hafızaya yazıldı: {kaynak_url}")
        except Exception as e:
            print(f"❌ Hafıza kayıt hatası: {e}")

    # ==================== LOG / AJAN ====================

    def log_query(self, agent_id: str, user_query: str, agent_response: str, success: bool = True):
        """Sorguları agent_queries tablosuna loglar"""
        try:
            query_data = {
                "agent_id": agent_id,
                "user_query": user_query,
                "agent_response": agent_response,
                "success": success,
                "created_at": datetime.utcnow().isoformat(),
            }
            return self.client.table("agent_queries").insert(query_data).execute()
        except Exception as e:
            print(f"❌ Sorgu loglama hatası: {e}")

    def get_all_agents(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Ajanları merit puanına göre listeler"""
        try:
            q = self.client.table("agents").select("*")
            if not include_inactive:
                q = q.eq("is_active", True)
            res = q.order("merit_score", desc=True).execute()
            return res.data or []
        except Exception as e:
            print(f"❌ Ajan listeleme hatası: {e}")
            return []

    def get_system_stats(self) -> Dict[str, Any]:
        """Dashboard için sistem istatistikleri"""
        try:
            agents = self.get_all_agents()
            total_queries = sum(a.get("total_queries", 0) for a in agents)
            total_success = sum(a.get("successful_queries", 0) for a in agents)
            return {
                "total_agents": len(agents),
                "active_agents": len([a for a in agents if a.get("is_active")]),
                "total_queries": total_queries,
                "success_rate": round((total_success / total_queries * 100) if total_queries > 0 else 0, 2),
            }
        except Exception as e:
            print(f"❌ İstatistik hatası: {e}")
            return {}

    # ==================== AI HELPERS ====================

    def answer_with_llama_first(self, user_query: str) -> Dict[str, Any]:
        """Llama -> OpenAI fallback. provider'ı da döndürür."""
        return ai_answer(user_query, llama_first=True)


# ==================== KÖPRÜLER (workflow'un aradığı fonksiyonlar) ====================

def get_database() -> Database:
    return Database()


def veriyi_hafizaya_yaz(metin: str, kaynak_url: str, vektor: list):
    db = Database()
    db.veriyi_hafizaya_yaz(metin, kaynak_url, vektor)


# ==================== LOCAL TEST ====================

if __name__ == "__main__":
    try:
        db = Database()
        print("✅ Veritabanı bağlantısı başarılı.")

        q = "Danimarka'da vergi borcum var mı nasıl öğrenirim?"
        out = db.answer_with_llama_first(q)
        print(f"🤖 Provider: {out['provider']}")
        print(out["text"][:700])

    except Exception as e:
        print(f"❌ HATA: {e}")
        sys.exit(1)
