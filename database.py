import os
import sys
from datetime import datetime, timedelta
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


def _get_secret_with_source(name: str, default: str = "") -> tuple[str, str]:
    """
    Secret değeri + kaynağını döndürür.
    Kaynak: env | streamlit_secrets | default
    """
    val_env = os.getenv(name)
    if val_env:
        return str(val_env).strip(), "env"

    if st is not None:
        try:
            val_secret = st.secrets.get(name, default)
            if val_secret:
                return str(val_secret).strip(), "streamlit_secrets"
        except Exception:
            pass

    return (str(default) if default is not None else "").strip(), "default"


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
        url, url_src = _get_secret_with_source("SUPABASE_URL", "")
        service_key, service_key_src = _get_secret_with_source("SUPABASE_SERVICE_ROLE_KEY", "")
        anon_key, anon_key_src = _get_secret_with_source("SUPABASE_KEY", "")
        key = service_key or anon_key
        key_src = service_key_src if service_key else anon_key_src

        self.llama_key, deepinfra_src = _get_secret_with_source("DEEPINFRA_API_TOKEN", "")
        self.openai_key, openai_src = _get_secret_with_source("OPENAI_API_KEY", "")

        # --- RAPOR (güvenli) ---
        if url:
            print(f"✅ SUPABASE HOST: {_safe_host(url)}")
            print(f"🔐 SUPABASE_URL source: {url_src}")
        else:
            print("🚨 RAPOR: 'SUPABASE_URL' bulunamadı!")

        if not key:
            print("🚨 RAPOR: 'SUPABASE_SERVICE_ROLE_KEY' / 'SUPABASE_KEY' bulunamadı!")
        else:
            print(f"🔐 SUPABASE_KEY source: {key_src}")

        # Token uzunluğu: tokenı ifşa etmez, sadece var mı yok mu gösterir
        print(f"🦙 DeepInfra token length: {len(self.llama_key)}")
        print(f"🔑 OpenAI key length: {len(self.openai_key)}")
        print(f"🔐 DeepInfra source: {deepinfra_src}")
        print(f"🔐 OpenAI source: {openai_src}")

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

    def get_vice_presidents(self) -> List[Dict[str, Any]]:
        """VP Kurulu üyelerini getirir (view varsa onu kullanır)"""
        try:
            res = (
                self.client
                .table("active_vice_presidents")
                .select("*")
                .execute()
            )
            if res.data:
                return res.data
        except Exception as e:
            print(f"❌ VP view hatası: {e}")

        # Fallback: agents tablosundan çek
        try:
            res = (
                self.client
                .table("agents")
                .select("id,name,specialization,merit_score,total_queries,rank")
                .eq("is_active", True)
                .in_("rank", ["vice_president", "vicepræsident"])
                .order("merit_score", desc=True)
                .execute()
            )
            data = res.data or []
            for a in data:
                a.setdefault("appointed_at", None)
            return data
        except Exception as e:
            print(f"❌ VP listeleme hatası: {e}")
            return []

    def get_agent_statistics(self) -> List[Dict[str, Any]]:
        """Dashboard için ajan istatistikleri"""
        try:
            res = (
                self.client
                .table("agents")
                .select(
                    "id,name,specialization,rank,merit_score,total_queries,successful_queries,success_rate,last_used,ethnicity,origin_country"
                )
                .eq("is_active", True)
                .order("merit_score", desc=True)
                .execute()
            )
            agents = res.data or []
        except Exception as e:
            print(f"❌ Ajan istatistikleri hatası: {e}")
            agents = self.get_all_agents()

        # Post ve yorum sayıları + son aktivite
        posts = []
        comments = []
        try:
            posts = (
                self.client
                .table("posts")
                .select("agent_id,created_at")
                .limit(10000)
                .execute()
            ).data or []
        except Exception as e:
            print(f"❌ Post istatistikleri hatası: {e}")
        try:
            comments = (
                self.client
                .table("comments")
                .select("agent_id,created_at")
                .limit(10000)
                .execute()
            ).data or []
        except Exception as e:
            print(f"❌ Yorum istatistikleri hatası: {e}")

        post_count = {}
        post_last = {}
        for p in posts:
            aid = p.get("agent_id")
            if not aid:
                continue
            post_count[aid] = post_count.get(aid, 0) + 1
            ts = p.get("created_at")
            if ts and (post_last.get(aid) is None or ts > post_last[aid]):
                post_last[aid] = ts

        comment_count = {}
        comment_last = {}
        for c in comments:
            aid = c.get("agent_id")
            if not aid:
                continue
            comment_count[aid] = comment_count.get(aid, 0) + 1
            ts = c.get("created_at")
            if ts and (comment_last.get(aid) is None or ts > comment_last[aid]):
                comment_last[aid] = ts

        # success_rate hesapla (yoksa)
        for a in agents:
            if a.get("success_rate") is None:
                total_q = a.get("total_queries", 0) or 0
                success_q = a.get("successful_queries", 0) or 0
                a["success_rate"] = round((success_q / total_q * 100), 2) if total_q else 0
            aid = a.get("id")
            a["total_topics"] = post_count.get(aid, 0)
            a["total_comments"] = comment_count.get(aid, 0)
            last_used = a.get("last_used")
            last_post = post_last.get(aid)
            last_comment = comment_last.get(aid)
            a["last_active"] = max([t for t in [last_used, last_post, last_comment] if t], default=None)
        return agents

    # ==================== LEARNING / KNOWLEDGE ====================

    def add_knowledge_unit(
        self,
        agent_id: str,
        content: str,
        source_type: str = "news",
        source_title: str = "",
        source_link: str = "",
        tags: List[str] | None = None,
        reliability_score: float = 0.6,
    ):
        try:
            data = {
                "agent_id": agent_id,
                "source_type": source_type,
                "source_title": source_title,
                "source_link": source_link,
                "content": content,
                "tags": tags or [],
                "reliability_score": max(0.0, min(1.0, reliability_score)),
                "created_at": datetime.utcnow().isoformat(),
            }
            return self.client.table("knowledge_units").insert(data).execute()
        except Exception as e:
            print(f"❌ Knowledge unit hatası: {e}")

    def update_skill_score(
        self,
        agent_id: str,
        specialization: str,
        delta: float,
        reason: str = "",
    ):
        try:
            current = (
                self.client
                .table("agent_skill_scores")
                .select("*")
                .eq("agent_id", agent_id)
                .eq("specialization", specialization)
                .limit(1)
                .execute()
            )
            if current.data:
                row = current.data[0]
                new_score = max(0, min(100, float(row.get("score", 50)) + float(delta)))
                self.client.table("agent_skill_scores").update(
                    {"score": new_score, "last_updated": datetime.utcnow().isoformat()}
                ).eq("id", row["id"]).execute()
            else:
                new_score = max(0, min(100, 50 + float(delta)))
                self.client.table("agent_skill_scores").insert(
                    {
                        "agent_id": agent_id,
                        "specialization": specialization,
                        "score": new_score,
                        "last_updated": datetime.utcnow().isoformat(),
                    }
                ).execute()

            if reason:
                self.log_learning_event(
                    agent_id=agent_id,
                    event_type="skill_update",
                    details={"specialization": specialization, "delta": delta, "reason": reason},
                )
        except Exception as e:
            print(f"❌ Skill score hatası: {e}")

    def log_learning_event(self, agent_id: str, event_type: str, details: Dict[str, Any] | None = None):
        try:
            self.client.table("agent_learning_logs").insert(
                {
                    "agent_id": agent_id,
                    "event_type": event_type,
                    "details": details or {},
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()
        except Exception as e:
            print(f"❌ Learning log hatası: {e}")

    # ==================== COMPLIANCE / TRUST ====================

    def log_compliance_event(
        self,
        agent_id: str,
        event_type: str,
        severity: str = "low",
        details: Dict[str, Any] | None = None,
    ):
        try:
            self.client.table("compliance_events").insert(
                {
                    "agent_id": agent_id,
                    "event_type": event_type,
                    "severity": severity,
                    "details": details or {},
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()
        except Exception as e:
            print(f"❌ Compliance event hatası: {e}")

    def apply_compliance_strike(
        self,
        agent_id: str,
        reason: str,
        severity: str = "low",
    ):
        try:
            agent_res = (
                self.client
                .table("agents")
                .select("id,trust_score,compliance_strikes,is_suspended,vetting_status")
                .eq("id", agent_id)
                .single()
                .execute()
            )
            if not agent_res.data:
                return
            agent = agent_res.data

            trust = agent.get("trust_score", 50) or 50
            strikes = agent.get("compliance_strikes", 0) or 0
            penalty = 2 if severity == "low" else 5 if severity == "medium" else 10
            new_trust = max(0, trust - penalty)
            new_strikes = strikes + 1
            suspend = True if new_strikes >= 3 else agent.get("is_suspended", False)

            self.client.table("agents").update(
                {
                    "trust_score": new_trust,
                    "compliance_strikes": new_strikes,
                    "is_suspended": suspend,
                    "last_reviewed_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", agent_id).execute()

            self.log_compliance_event(
                agent_id=agent_id,
                event_type="strike",
                severity=severity,
                details={"reason": reason, "trust_delta": -penalty},
            )
        except Exception as e:
            print(f"❌ Compliance strike hatası: {e}")

    def create_revision_task(
        self,
        agent_id: str,
        post_id: str,
        reason: str,
    ):
        try:
            self.client.table("revision_tasks").insert(
                {
                    "agent_id": agent_id,
                    "post_id": post_id,
                    "reason": reason,
                    "status": "open",
                    "created_at": datetime.utcnow().isoformat(),
                }
            ).execute()
        except Exception as e:
            print(f"❌ Revision task hatası: {e}")

    def update_revision_task(
        self,
        task_id: str,
        revised_content: str,
        ai_summary: str = "",
        status: str = "in_review",
    ):
        try:
            self.client.table("revision_tasks").update(
                {
                    "revised_content": revised_content,
                    "ai_summary": ai_summary,
                    "status": status,
                    "resolved_at": datetime.utcnow().isoformat() if status == "closed" else None,
                }
            ).eq("id", task_id).execute()
        except Exception as e:
            print(f"❌ Revision update hatası: {e}")

    def generate_monthly_report(self):
        try:
            today = datetime.utcnow().date()
            period_end = today.replace(day=1) - timedelta(days=1)
            period_start = period_end.replace(day=1)

            # Avoid duplicate report
            existing = (
                self.client.table("monthly_reports")
                .select("id")
                .eq("period_start", period_start.isoformat())
                .eq("period_end", period_end.isoformat())
                .limit(1)
                .execute()
            )
            if existing.data:
                return existing.data[0]

            agents = self.client.table("agents").select("id,merit_score,trust_score,compliance_strikes").eq("is_active", True).execute()
            total_agents = len(agents.data or [])
            avg_merit = 0
            avg_trust = 0
            if total_agents:
                avg_merit = sum(a.get("merit_score", 0) for a in agents.data) / total_agents
                avg_trust = sum(a.get("trust_score", 0) for a in agents.data) / total_agents

            comp_events = (
                self.client.table("compliance_events")
                .select("id")
                .gte("created_at", period_start.isoformat())
                .lte("created_at", period_end.isoformat())
                .execute()
            )

            summary = {
                "total_agents": total_agents,
                "avg_merit": round(avg_merit, 2),
                "avg_trust": round(avg_trust, 2),
                "compliance_events": len(comp_events.data or []),
            }

            row = (
                self.client.table("monthly_reports")
                .insert(
                    {
                        "period_start": period_start.isoformat(),
                        "period_end": period_end.isoformat(),
                        "summary": summary,
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
                .execute()
            )
            return (row.data or [None])[0]
        except Exception as e:
            print(f"❌ Monthly report hatası: {e}")

    def daily_amnesty(self):
        """
        Günlük af: askıda olanları geri alır, strike sayısını azaltır.
        """
        try:
            res = (
                self.client.table("agents")
                .select("id,compliance_strikes,is_suspended")
                .eq("is_active", True)
                .execute()
            )
            agents = res.data or []
            updated = 0
            for a in agents:
                strikes = a.get("compliance_strikes", 0) or 0
                if strikes <= 0 and not a.get("is_suspended"):
                    continue
                new_strikes = max(0, strikes - 1)
                self.client.table("agents").update(
                    {
                        "compliance_strikes": new_strikes,
                        "is_suspended": False,
                        "last_reviewed_at": datetime.utcnow().isoformat(),
                    }
                ).eq("id", a["id"]).execute()
                updated += 1
            return {"amnestied": updated}
        except Exception as e:
            print(f"❌ Amnesty hatası: {e}")
            return {"amnestied": 0, "error": str(e)}

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
