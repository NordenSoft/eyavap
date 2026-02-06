import os
import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# .env dosyasını yükle (Lokalde .env, bulutta Secrets kullanılır)
load_dotenv()

class Database:
    """EYAVAP Komuta Merkezi: Supabase Veritabanı ve Hafıza İşlemleri"""
    
    def __init__(self):
        """Bağlantıyı hem Bulut (GitHub Actions) hem Arayüz (Streamlit) için akıllıca başlatır"""
        
        # 🛡️ STRATEJİ 1: GitHub Actions / Ortam Değişkenleri (Öncelikli)
        # Bulut sunucusu (Runner) buraya bakar.
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        
        # 🛡️ STRATEJİ 2: Streamlit Secrets (Arayüz tarafı için yedek)
        # Eğer yukarıdaki bulunamazsa (Streamlit arayüzünde çalışıyorsak) buraya girer.
        if not supabase_url or not supabase_key:
            try:
                if hasattr(st, 'secrets') and "SUPABASE_URL" in st.secrets:
                    supabase_url = st.secrets["SUPABASE_URL"]
                    supabase_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY") or st.secrets.get("SUPABASE_KEY")
            except Exception:
                # Streamlit secrets erişilemezse hata fırlatmadan devam et (Actions ortamı için)
                pass
        
        if not supabase_url or not supabase_key:
            raise ValueError("❌ HATA: Supabase anahtarları bulunamadı! GitHub Secrets veya .env kontrol edilmeli.")
        
        self.client: Client = create_client(supabase_url, supabase_key)

    # ==================== RAG / SPIDER İŞLEMLERİ ====================

    def veriyi_hafizaya_yaz(self, metin: str, kaynak_url: str, vektor: list):
        """Spider'dan gelen Skat verilerini vektör hafızasına mühürler"""
        try:
            data = {
                "icerik": metin,
                "kaynak_url": kaynak_url,
                "embedding": vektor
            }
            self.client.table("skat_hafiza").insert(data).execute()
            print(f"✅ Hafızaya mühürlendi: {kaynak_url}")
        except Exception as e:
            print(f"❌ Hafıza Kayıt Hatası: {e}")

    # ==================== AJAN VE LOG İŞLEMLERİ ====================

    def log_query(self, agent_id: str, user_query: str, agent_response: str, success: bool = True):
        """Sorguları agent_queries tablosuna loglar"""
        try:
            query_data = {
                "agent_id": agent_id,
                "user_query": user_query,
                "agent_response": agent_response,
                "success": success,
                "created_at": datetime.utcnow().isoformat()
            }
            return self.client.table("agent_queries").insert(query_data).execute()
        except Exception as e:
            print(f"❌ Sorgu loglama hatası: {e}")

    def get_all_agents(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Tüm ajanları merit puanına göre listeler"""
        try:
            query = self.client.table("agents").select("*")
            if not include_inactive:
                query = query.eq("is_active", True)
            response = query.order("merit_score", desc=True).execute()
            return response.data or []
        except Exception as e:
            print(f"❌ Ajan listeleme hatası: {e}")
            return []

    def get_system_stats(self) -> Dict[str, Any]:
        """Dashboard için sistem geneli istatistikleri hesaplar"""
        try:
            agents = self.get_all_agents()
            total_queries = sum(a.get("total_queries", 0) for a in agents)
            total_success = sum(a.get("successful_queries", 0) for a in agents)
            
            return {
                "total_agents": len(agents),
                "active_agents": len([a for a in agents if a.get("is_active")]),
                "total_queries": total_queries,
                "success_rate": round((total_success / total_queries * 100) if total_queries > 0 else 0, 2)
            }
        except Exception as e:
            print(f"❌ İstatistik hatası: {e}")
            return {}

# ==================== SİSTEM KÖPRÜLERİ (KRİTİK) ====================

def get_database():
    """Tora Legion Lifecycle'ın aradığı ana bağlantı köprüsü"""
    return Database()

def veriyi_hafizaya_yaz(metin, kaynak_url, vektor):
    """Spider'ın aradığı doğrudan yazma fonksiyonu"""
    db = Database()
    db.veriyi_hafizaya_yaz(metin, kaynak_url, vektor)

# ==================== DASHBOARD TEST ====================
if __name__ == "__main__":
    try:
        db = Database()
        print("✅ Veritabanı bağlantısı başarılı.")
        # Sadece Streamlit ortamındaysak UI göster
        if hasattr(st, 'runtime') and st.runtime.exists():
            st.title("🤖 EYAVAP: Komuta Merkezi")
            stats = db.get_system_stats()
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Ajan", stats["total_agents"])
            c2.metric("Sistem Sorgu", stats["total_queries"])
            c3.metric("Başarı Oranı", f"%{stats['success_rate']}")
    except Exception as e:
        print(f"❌ HATA: {e}")