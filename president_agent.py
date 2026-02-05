"""
EYAVAP: Başkan Ajan (President Agent)
Tüm ajan sistemini orkestra eden ana ajan
"""

import time
from typing import Dict, Any, List, Optional
from openai import OpenAI
import streamlit as st
import json

from database import get_database
from specialized_agent import SpecializedAgent
from action_capabilities import ActionCapabilities


class PresidentAgent:
    """
    Başkan Ajan - Ajan sisteminin orkestratörü
    
    Görevleri:
    1. Kullanıcı sorgusunu analiz et
    2. Mevcut ajanları tara, uygun ajan varsa görevlendir
    3. Uygun ajan yoksa (%90+ uyum) yeni uzman ajan oluştur
    4. Ajanların performansını izle, liyakat puanlarını güncelle
    5. Başkan Yardımcısı Kurulu'nu yönet
    """
    
    AGENT_ID = "00000000-0000-0000-0000-000000000001"
    
    def __init__(self):
        self.db = get_database()
        
        # OpenAI istemcisi
        openai_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("openai", {}).get("api_key")
        if not openai_key:
            raise ValueError("OpenAI API key not found!")
        
        self.client = OpenAI(api_key=openai_key)
        
        # Eylem yetkisi
        self.actions = ActionCapabilities(
            agent_id=self.AGENT_ID,
            capabilities=["orchestrate", "delegate", "create_agents", "evaluate", "research", "analysis", "reporting"]
        )
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Kullanıcı sorgusunu işle (ana method)
        
        Flow:
        1. Sorguyu analiz et → hangi uzmanlık alanı?
        2. Mevcut ajanları tara → %90+ uyumlu var mı?
        3. Varsa: Görevi ona delege et
        4. Yoksa: Yeni uzman ajan oluştur → görevi ona ver
        5. Sonucu logla, liyakat puanını güncelle
        
        Args:
            user_query: Kullanıcının sorusu
        
        Returns:
            Dict: {
                "answer": str,
                "agent_used": str,
                "agent_created": bool,
                "execution_time_ms": int,
                "actions_taken": List[Dict]
            }
        """
        start_time = time.time()
        actions_taken = []
        
        try:
            # 1. Sorgu analizi
            print(f"🔍 Başkan Ajan: Sorgu analiz ediliyor...")
            query_analysis = self._analyze_query(user_query)
            actions_taken.append({"action": "query_analysis", "result": query_analysis})
            
            specialization = query_analysis["specialization"]
            expertise_areas = query_analysis["expertise_areas"]
            confidence = query_analysis["confidence"]
            
            print(f"   → Uzmanlık alanı: {specialization}")
            print(f"   → Expertise: {', '.join(expertise_areas)}")
            print(f"   → Güven: {confidence:.2f}")
            
            # 2. Mevcut ajanları tara
            print(f"👥 Mevcut ajanlar taranıyor...")
            existing_agent = self.db.find_best_agent_for_query(user_query, expertise_areas)
            
            agent_created = False
            agent_to_use = None
            
            if existing_agent and confidence >= 0.90:
                # Mevcut ajan %90+ uyumlu
                print(f"   ✅ Uygun ajan bulundu: {existing_agent['name']}")
                agent_to_use = existing_agent
                actions_taken.append({
                    "action": "agent_found",
                    "agent_id": existing_agent["id"],
                    "agent_name": existing_agent["name"]
                })
            else:
                # Yeni ajan oluştur
                print(f"   🆕 Yeni uzman ajan oluşturuluyor...")
                agent_to_use = self._create_specialized_agent(specialization, expertise_areas)
                agent_created = True
                actions_taken.append({
                    "action": "agent_created",
                    "agent_id": agent_to_use["id"],
                    "agent_name": agent_to_use["name"],
                    "specialization": specialization
                })
                print(f"   ✅ Yeni ajan: {agent_to_use['name']}")
            
            # 3. Görevi ajana delege et
            print(f"📤 Görev delege ediliyor: {agent_to_use['name']}")
            agent = SpecializedAgent(
                agent_id=agent_to_use["id"],
                name=agent_to_use["name"],
                specialization=agent_to_use["specialization"],
                expertise_areas=agent_to_use["expertise_areas"],
                capabilities=agent_to_use["capabilities"],
                merit_score=agent_to_use["merit_score"]
            )
            
            result = agent.process_query(user_query)
            actions_taken.append({
                "action": "query_delegated",
                "agent_id": agent_to_use["id"],
                "execution_time_ms": result["execution_time_ms"]
            })
            
            # 4. Sonucu logla
            query_id = self.db.log_query(
                agent_id=agent_to_use["id"],
                user_query=user_query,
                agent_response=result["answer"],
                success=result["success"],
                execution_time_ms=result["execution_time_ms"],
                actions_taken=actions_taken
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            print(f"✅ İşlem tamamlandı ({execution_time_ms}ms)")
            
            return {
                "answer": result["answer"],
                "agent_used": agent_to_use["name"],
                "agent_id": agent_to_use["id"],
                "agent_specialization": agent_to_use["specialization"],
                "agent_created": agent_created,
                "confidence": result.get("confidence", 0.8),
                "execution_time_ms": execution_time_ms,
                "actions_taken": actions_taken,
                "query_id": query_id,
                "success": result["success"]
            }
            
        except Exception as e:
            print(f"❌ Başkan Ajan hatası: {e}")
            return {
                "answer": f"⚠️ Üzgünüm, bir hata oluştu: {str(e)}",
                "agent_used": "Başkan Ajan (Hata Yönetimi)",
                "agent_created": False,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "actions_taken": actions_taken,
                "success": False,
                "error": str(e)
            }
    
    def _analyze_query(self, user_query: str) -> Dict[str, Any]:
        """
        Sorguyu analiz et ve hangi uzmanlık alanına ait olduğunu belirle
        
        Args:
            user_query: Kullanıcı sorusu
        
        Returns:
            Dict: {
                "specialization": str,
                "expertise_areas": List[str],
                "confidence": float
            }
        """
        try:
            system_prompt = """Sen bir sorgu sınıflandırma uzmanısın. Kullanıcının sorusunu analiz et ve hangi uzmanlık alanına ait olduğunu belirle.

UZMANLIK ALANLARI:
- denmark_tax: Danimarka vergi sistemi (skat, moms, skatteberegning)
- denmark_health: Danimarka sağlık sistemi (sygesikring, læge, hospital)
- denmark_legal: Danimarka hukuk ve vize (opholdstilladelse, visa, citizenship)
- denmark_residence: Oturma izni ve kayıt (cpr, nem-id, mitid, folkeregister)
- denmark_work: İş ve çalışma (job, arbejde, løn, ansættelse)
- denmark_education: Eğitim (uddannelse, universitet, skole, SU)
- denmark_immigration: Göçmenlik ve entegrasyon
- denmark_housing: Konut ve barınma (bolig, leje, køb)
- denmark_transport: Ulaşım (transport, rejsekort, bil)
- denmark_culture: Kültür ve sosyal yaşam
- cyber_security: Siber güvenlik ve hacking
- data_analysis: Veri analizi ve istatistik
- general: Genel sorular

YANIT FORMATI (JSON):
{
  "specialization": "denmark_tax",
  "expertise_areas": ["skat", "tax", "vergi"],
  "confidence": 0.95,
  "reasoning": "Soru Danimarka vergi sistemiyle ilgili"
}

Sadece JSON döndür, başka açıklama yapma."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=300
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            return {
                "specialization": analysis.get("specialization", "general"),
                "expertise_areas": analysis.get("expertise_areas", ["general"]),
                "confidence": analysis.get("confidence", 0.7),
                "reasoning": analysis.get("reasoning", "")
            }
            
        except Exception as e:
            print(f"⚠️ Sorgu analizi hatası: {e}")
            return {
                "specialization": "general",
                "expertise_areas": ["general"],
                "confidence": 0.5,
                "reasoning": "Analiz hatası"
            }
    
    def _create_specialized_agent(self, specialization: str, expertise_areas: List[str]) -> Dict[str, Any]:
        """
        Yeni uzman ajan oluştur
        
        Args:
            specialization: Uzmanlık alanı
            expertise_areas: Expertise alanları
        
        Returns:
            Dict: Ajan bilgileri
        """
        # Ajan ismi oluştur
        agent_names = {
            "denmark_tax": "Vergi Uzmanı (Skat Specialist)",
            "denmark_health": "Sağlık Uzmanı (Sundhedsvæsen Specialist)",
            "denmark_legal": "Hukuk Uzmanı (Juridisk Specialist)",
            "denmark_residence": "Oturma İzni Uzmanı (Opholdstilladelse Specialist)",
            "denmark_work": "İş & Çalışma Uzmanı (Arbejdsmarked Specialist)",
            "denmark_education": "Eğitim Uzmanı (Uddannelse Specialist)",
            "denmark_immigration": "Göçmenlik Uzmanı (Immigration Specialist)",
            "denmark_housing": "Konut Uzmanı (Bolig Specialist)",
            "denmark_transport": "Ulaşım Uzmanı (Transport Specialist)",
            "denmark_culture": "Kültür Uzmanı (Kultur Specialist)",
            "cyber_security": "Siber Güvenlik Uzmanı",
            "data_analysis": "Veri Analizi Uzmanı",
            "general": "Genel Asistan"
        }
        
        agent_name = agent_names.get(specialization, f"{specialization.title()} Uzmanı")
        
        # Yetkiler
        capabilities = ["research", "analysis", "reporting"]
        if specialization == "cyber_security":
            capabilities.extend(["web_search", "system_interaction"])
        elif specialization == "data_analysis":
            capabilities.extend(["data_analysis", "web_search"])
        else:
            capabilities.append("web_search")
        
        # Veritabanına kaydet
        agent = self.db.create_agent(
            name=agent_name,
            specialization=specialization,
            expertise_areas=expertise_areas,
            capabilities=capabilities
        )
        
        return agent
    
    def get_vice_presidents(self) -> List[Dict[str, Any]]:
        """Başkan Yardımcısı Kurulu üyelerini getir"""
        return self.db.get_vice_presidents()
    
    def get_all_agents_stats(self) -> List[Dict[str, Any]]:
        """Tüm ajanların istatistiklerini getir"""
        return self.db.get_agent_statistics()
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Sistem geneli özet"""
        return self.db.get_system_stats()


# Global instance
_president_instance: Optional[PresidentAgent] = None

def get_president_agent() -> PresidentAgent:
    """Singleton President Agent instance"""
    global _president_instance
    if _president_instance is None:
        _president_instance = PresidentAgent()
    return _president_instance
