"""
EYAVAP: Uzman Ajan Sınıfı
Her ajan kendi uzmanlık alanında görev yapar
"""

import time
from typing import Dict, Any, List, Optional
from openai import OpenAI
import streamlit as st


class SpecializedAgent:
    """Uzman Ajan - Belirli bir alanda uzmanlaşmış AI ajan"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        specialization: str,
        expertise_areas: List[str],
        capabilities: List[str],
        merit_score: int = 50
    ):
        self.agent_id = agent_id
        self.name = name
        self.specialization = specialization
        self.expertise_areas = expertise_areas
        self.capabilities = capabilities
        self.merit_score = merit_score
        
        # OpenAI istemcisi
        openai_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("openai", {}).get("api_key")
        if not openai_key:
            raise ValueError("OpenAI API key not found!")
        
        self.client = OpenAI(api_key=openai_key)
    
    def _build_system_prompt(self) -> str:
        """Ajan için özelleştirilmiş system prompt oluştur"""
        return f"""Sen {self.name} adında uzman bir yapay zeka ajanısın.

🎯 UZMANLIK ALANLARIN:
{', '.join(self.expertise_areas)}

🛠️ YETKİLERİN:
{', '.join(self.capabilities)}

📋 GÖREVİN:
- Kullanıcının sorusunu kendi uzmanlık alanın çerçevesinde yanıtla
- Detaylı, profesyonel ve çözüm odaklı ol
- Türkçe yanıt ver
- Gerekirse adım adım açıkla
- Kaynak ve referanslar ver

⚠️ SINIRLARIN:
- Sadece kendi uzmanlık alanın hakkında konuş
- Bilmediğin konularda tahminde bulunma
- Eğer soru uzmanlık alanın dışındaysa, bunu açıkça belirt

🏆 Liyakat Puanın: {self.merit_score}/100
"""
    
    def process_query(self, user_query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Kullanıcı sorgusunu işle ve yanıt üret
        
        Args:
            user_query: Kullanıcının sorusu
            context: Ek bağlam (opsiyonel)
        
        Returns:
            Dict: {
                "answer": str,
                "confidence": float,
                "sources": List[str],
                "actions_taken": List[Dict],
                "execution_time_ms": int
            }
        """
        start_time = time.time()
        actions_taken = []
        
        try:
            # System prompt oluştur
            system_prompt = self._build_system_prompt()
            
            # Bağlam varsa ekle
            full_query = user_query
            if context:
                full_query = f"BAĞLAM: {context}\n\nSORU: {user_query}"
            
            # OpenAI çağrısı
            actions_taken.append({
                "action": "openai_query",
                "model": "gpt-4o-mini",
                "timestamp": time.time()
            })
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_query}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Güven skoru (basitleştirilmiş - finish_reason'a göre)
            confidence = 0.9 if response.choices[0].finish_reason == "stop" else 0.6
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "answer": answer,
                "confidence": confidence,
                "sources": [f"OpenAI GPT-4o-mini via {self.name}"],
                "actions_taken": actions_taken,
                "execution_time_ms": execution_time_ms,
                "success": True
            }
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": f"❌ Üzgünüm, bir hata oluştu: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "actions_taken": actions_taken,
                "execution_time_ms": execution_time_ms,
                "success": False,
                "error": str(e)
            }
    
    def evaluate_query_match(self, user_query: str) -> float:
        """
        Kullanıcı sorgusunun bu ajanın uzmanlık alanına ne kadar uyduğunu değerlendir
        
        Returns:
            float: 0.0 - 1.0 arası uygunluk skoru
        """
        query_lower = user_query.lower()
        
        # Basit keyword matching (gelecekte semantic search ile geliştirilebilir)
        match_score = 0.0
        
        # Expertise areas kontrolü
        for area in self.expertise_areas:
            if area.lower() in query_lower:
                match_score += 0.3
        
        # Specialization kontrolü
        if self.specialization.lower() in query_lower:
            match_score += 0.4
        
        # Genel konu uygunluğu (keyword bazlı)
        relevant_keywords = self._get_relevant_keywords()
        for keyword in relevant_keywords:
            if keyword.lower() in query_lower:
                match_score += 0.1
        
        return min(match_score, 1.0)
    
    def _get_relevant_keywords(self) -> List[str]:
        """Uzmanlık alanına göre ilgili anahtar kelimeleri döndür"""
        # Her specialization için özel keyword mapping
        keyword_map = {
            "denmark_tax": ["vergi", "skat", "tax", "moms", "kdv", "beyanname", "gelir vergisi"],
            "denmark_health": ["sağlık", "sundhed", "health", "doktor", "hastane", "sygesikring", "læge"],
            "denmark_legal": ["hukuk", "juridisk", "legal", "vize", "oturma izni", "vatandaşlık", "visa"],
            "denmark_residence": ["oturma", "residence", "cpr", "nem-id", "mitid", "registration"],
            "denmark_work": ["iş", "work", "job", "arbejde", "maaş", "løn", "salary"],
            "denmark_education": ["eğitim", "education", "uddannelse", "okul", "school", "üniversite"],
            "cyber_security": ["güvenlik", "siber", "cyber", "hacking", "malware", "firewall"],
            "data_analysis": ["veri", "analiz", "data", "statistics", "istatistik", "rapor"],
            "general": []
        }
        
        return keyword_map.get(self.specialization, [])
    
    def can_perform_action(self, action: str) -> bool:
        """Belirli bir eylemi gerçekleştirebilir mi?"""
        return action in self.capabilities
    
    def __repr__(self) -> str:
        return f"SpecializedAgent(name='{self.name}', specialization='{self.specialization}', merit={self.merit_score})"
