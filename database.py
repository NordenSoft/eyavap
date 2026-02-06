"""
EYAVAP: Veritabanı İşlemleri
Supabase bağlantısı ve CRUD operasyonları
"""

import os
import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import create_client, Client


class Database:
    """Supabase veritabanı işlemleri"""
    
    def __init__(self):
        """Supabase bağlantısını başlat"""
        # Streamlit Cloud için secrets
        if hasattr(st, 'secrets'):
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
        else:
            # Lokal geliştirme için .env
            from dotenv import load_dotenv
            load_dotenv()
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found! Set SUPABASE_URL and SUPABASE_KEY")
        
        self.client: Client = create_client(supabase_url, supabase_key)
    
    # ==================== AJAN İŞLEMLERİ ====================
    
    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """ID ile ajan getir"""
        try:
            response = self.client.table("agents").select("*").eq("id", agent_id).single().execute()
            return response.data
        except Exception as e:
            print(f"❌ Ajan getirme hatası: {e}")
            return None
    
    def get_agent_by_specialization(self, specialization: str) -> Optional[Dict[str, Any]]:
        """Uzmanlık alanına göre en iyi ajanı getir"""
        try:
            response = (
                self.client.table("agents")
                .select("*")
                .eq("specialization", specialization)
                .eq("is_active", True)
                .order("merit_score", desc=True)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"❌ Ajan arama hatası: {e}")
            return None
    
    def find_best_agent_for_query(self, query: str, expertise_areas: List[str]) -> Optional[Dict[str, Any]]:
        """Sorguya en uygun ajanı bul (expertise_areas'a göre)"""
        try:
            # PostgreSQL array overlap operatörü (&&)
            response = (
                self.client.table("agents")
                .select("*")
                .eq("is_active", True)
                .order("merit_score", desc=True)
                .execute()
            )
            
            # Python'da filtreleme (Supabase array overlap desteği için)
            if response.data:
                for agent in response.data:
                    agent_expertise = agent.get("expertise_areas", [])
                    if any(area in agent_expertise for area in expertise_areas):
                        return agent
            
            return None
        except Exception as e:
            print(f"❌ En iyi ajan bulma hatası: {e}")
            return None
    
    def create_agent(
        self,
        name: str,
        specialization: str,
        expertise_areas: List[str],
        capabilities: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Yeni ajan oluştur"""
        try:
            agent_data = {
                "name": name,
                "specialization": specialization,
                "expertise_areas": expertise_areas,
                "capabilities": capabilities or ["research", "analysis", "reporting"],
                "merit_score": 50,
                "rank": "specialist",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("agents").insert(agent_data).execute()
            
            if response.data:
                print(f"✅ Yeni ajan oluşturuldu: {name} ({specialization})")
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Ajan oluşturma hatası: {e}")
            return None
    
    def update_agent_merit_score(self, agent_id: str, merit_score: int):
        """Ajan liyakat puanını güncelle"""
        try:
            self.client.table("agents").update({
                "merit_score": max(0, min(100, merit_score))
            }).eq("id", agent_id).execute()
        except Exception as e:
            print(f"❌ Liyakat puanı güncelleme hatası: {e}")
    
    def get_all_agents(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Tüm ajanları listele"""
        try:
            query = self.client.table("agents").select("*")
            
            if not include_inactive:
                query = query.eq("is_active", True)
            
            response = query.order("merit_score", desc=True).execute()
            return response.data or []
        except Exception as e:
            print(f"❌ Ajanları listeleme hatası: {e}")
            return []
    
    def get_vice_presidents(self) -> List[Dict[str, Any]]:
        """Başkan Yardımcısı Kurulu üyelerini getir"""
        try:
            response = (
                self.client.table("active_vice_presidents")
                .select("*")
                .execute()
            )
            return response.data or []
        except Exception as e:
            print(f"❌ Başkan Yardımcıları getirme hatası: {e}")
            return []
    
    def deactivate_agent(self, agent_id: str):
        """Ajanı devre dışı bırak"""
        try:
            self.client.table("agents").update({
                "is_active": False
            }).eq("id", agent_id).execute()
        except Exception as e:
            print(f"❌ Ajan devre dışı bırakma hatası: {e}")
    
    # ==================== SORGU İŞLEMLERİ ====================
    
    def log_query(
        self,
        agent_id: str,
        user_query: str,
        agent_response: str,
        success: bool = True,
        execution_time_ms: int = None,
        actions_taken: List[Dict] = None
    ) -> Optional[str]:
        """Ajan sorgusunu logla"""
        try:
            query_data = {
                "agent_id": agent_id,
                "user_query": user_query,
                "agent_response": agent_response,
                "success": success,
                "execution_time_ms": execution_time_ms,
                "actions_taken": actions_taken or [],
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.client.table("agent_queries").insert(query_data).execute()
            
            if response.data:
                return response.data[0]["id"]
            return None
        except Exception as e:
            print(f"❌ Sorgu loglama hatası: {e}")
            return None
    
    def update_query_feedback(self, query_id: str, feedback: int):
        """Sorguya kullanıcı geri bildirimi ekle (1-5)"""
        try:
            self.client.table("agent_queries").update({
                "user_feedback": max(1, min(5, feedback))
            }).eq("id", query_id).execute()
        except Exception as e:
            print(f"❌ Geri bildirim güncelleme hatası: {e}")
    
    def get_agent_query_history(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Ajanın sorgu geçmişini getir"""
        try:
            response = (
                self.client.table("agent_queries")
                .select("*")
                .eq("agent_id", agent_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception as e:
            print(f"❌ Sorgu geçmişi hatası: {e}")
            return []
    
    # ==================== EYLEM LOGLARİ ====================
    
    def log_action(
        self,
        agent_id: str,
        query_id: str,
        action_type: str,
        action_details: Dict[str, Any],
        result: Dict[str, Any] = None,
        success: bool = True
    ):
        """Ajan eylemini logla"""
        try:
            action_data = {
                "agent_id": agent_id,
                "query_id": query_id,
                "action_type": action_type,
                "action_details": action_details,
                "result": result or {},
                "success": success,
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.client.table("action_logs").insert(action_data).execute()
        except Exception as e:
            print(f"❌ Eylem loglama hatası: {e}")
    
    def get_agent_actions(self, agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Ajanın eylem geçmişini getir"""
        try:
            response = (
                self.client.table("action_logs")
                .select("*")
                .eq("agent_id", agent_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception as e:
            print(f"❌ Eylem geçmişi hatası: {e}")
            return []
    
    # ==================== İSTATİSTİKLER ====================
    
    def get_agent_statistics(self) -> List[Dict[str, Any]]:
        """Tüm ajanların istatistiklerini getir"""
        try:
            response = (
                self.client.table("agent_statistics")
                .select("*")
                .order("merit_score", desc=True)
                .execute()
            )
            return response.data or []
        except Exception as e:
            print(f"❌ İstatistik hatası: {e}")
            return []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Sistem geneli istatistikler"""
        try:
            agents = self.get_all_agents()
            vice_presidents = self.get_vice_presidents()
            
            total_queries = sum(agent.get("total_queries", 0) for agent in agents)
            total_successful = sum(agent.get("successful_queries", 0) for agent in agents)
            
            return {
                "total_agents": len(agents),
                "active_agents": len([a for a in agents if a.get("is_active")]),
                "vice_presidents": len(vice_presidents),
                "total_queries": total_queries,
                "total_successful_queries": total_successful,
                "success_rate": round((total_successful / total_queries * 100) if total_queries > 0 else 0, 2)
            }
        except Exception as e:
            print(f"❌ Sistem istatistikleri hatası: {e}")
            return {}


import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Çevresel değişkenleri yükle
load_dotenv()

# --- BAĞLANTI AYARLARI ---
def init_connection():
    supa_url = os.getenv("SUPABASE_URL")
    supa_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Service role key yetki için şarttır
    
    if not supa_url or not supa_key:
        st.error("❌ HATA: .env dosyasında Supabase bilgileri eksik!")
        return None
    return create_client(supa_url, supa_key)

supabase = init_connection()

# --- ÖRÜMCEK İÇİN KAYIT FONKSİYONU ---
def veriyi_hafizaya_yaz(metin, kaynak_url, vektor):
    """Spider'dan gelen veriyi Supabase'e mühürler"""
    try:
        data = {
            "icerik": metin,
            "kaynak_url": kaynak_url,
            "embedding": vektor
        }
        supabase.table("skat_hafiza").insert(data).execute()
        print(f"✅ Hafızaya mühürlendi: {kaynak_url}")
    except Exception as e:
        print(f"❌ Kayıt hatası: {e}")

# --- DASHBOARD ARAYÜZÜ ---
if __name__ == "__main__" and supabase:
    st.title("🤖 EYAVAP: Komuta Merkezi")
    # Buraya dashboard kodlarını (metrikler, tablolar) eklemeye devam edebilirsiniz