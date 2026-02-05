"""
EYAVAP: Eylem Yetkisi Modülü
Ajanların gerçekleştirebileceği eylemler (siber araştırma, sistem etkileşimi)
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import time


class ActionCapabilities:
    """Ajan eylem yetkisi yöneticisi"""
    
    def __init__(self, agent_id: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.action_log = []
    
    def can_perform(self, action: str) -> bool:
        """Belirli bir eylemi gerçekleştirebilir mi?"""
        return action in self.capabilities
    
    # ==================== WEB ARAŞTIRMA ====================
    
    def web_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Web araştırması yap
        
        Args:
            query: Arama sorgusu
            num_results: Sonuç sayısı
        
        Returns:
            Dict: {
                "success": bool,
                "results": List[Dict],
                "action_log": Dict
            }
        """
        if not self.can_perform("web_search"):
            return {
                "success": False,
                "error": "Bu ajan web araştırması yetkisine sahip değil",
                "results": []
            }
        
        action_start = time.time()
        
        try:
            # DuckDuckGo Instant Answer API (ücretsiz)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            results = []
            
            # Ana sonuç
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", ""),
                    "snippet": data.get("AbstractText", ""),
                    "url": data.get("AbstractURL", ""),
                    "source": data.get("AbstractSource", "DuckDuckGo")
                })
            
            # Related topics
            for topic in data.get("RelatedTopics", [])[:num_results]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                        "source": "DuckDuckGo"
                    })
            
            action_log = {
                "action": "web_search",
                "query": query,
                "results_count": len(results),
                "execution_time_ms": int((time.time() - action_start) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.action_log.append(action_log)
            
            return {
                "success": True,
                "results": results,
                "action_log": action_log
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "action_log": {
                    "action": "web_search",
                    "query": query,
                    "error": str(e),
                    "execution_time_ms": int((time.time() - action_start) * 1000)
                }
            }
    
    # ==================== API ÇAĞRISI ====================
    
    def api_call(
        self,
        url: str,
        method: str = "GET",
        headers: Dict[str, str] = None,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Harici API çağrısı yap
        
        Args:
            url: API endpoint
            method: HTTP metodu (GET, POST, etc.)
            headers: Request headers
            data: Request body
        
        Returns:
            Dict: API yanıtı
        """
        if not self.can_perform("api_call"):
            return {
                "success": False,
                "error": "Bu ajan API çağrısı yetkisine sahip değil"
            }
        
        action_start = time.time()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers or {},
                json=data,
                timeout=15
            )
            
            action_log = {
                "action": "api_call",
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "execution_time_ms": int((time.time() - action_start) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.action_log.append(action_log)
            
            return {
                "success": response.ok,
                "status_code": response.status_code,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "action_log": action_log
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action_log": {
                    "action": "api_call",
                    "url": url,
                    "error": str(e),
                    "execution_time_ms": int((time.time() - action_start) * 1000)
                }
            }
    
    # ==================== VERİ ANALİZİ ====================
    
    def data_analysis(self, data: List[Dict[str, Any]], analysis_type: str = "summary") -> Dict[str, Any]:
        """
        Veri analizi yap
        
        Args:
            data: Analiz edilecek veri
            analysis_type: Analiz tipi (summary, statistics, etc.)
        
        Returns:
            Dict: Analiz sonuçları
        """
        if not self.can_perform("data_analysis"):
            return {
                "success": False,
                "error": "Bu ajan veri analizi yetkisine sahip değil"
            }
        
        action_start = time.time()
        
        try:
            result = {}
            
            if analysis_type == "summary":
                result = {
                    "total_records": len(data),
                    "fields": list(data[0].keys()) if data else [],
                    "sample": data[:3] if len(data) >= 3 else data
                }
            
            elif analysis_type == "statistics":
                # Sayısal alanlar için basit istatistikler
                numeric_fields = {}
                for record in data:
                    for key, value in record.items():
                        if isinstance(value, (int, float)):
                            if key not in numeric_fields:
                                numeric_fields[key] = []
                            numeric_fields[key].append(value)
                
                stats = {}
                for field, values in numeric_fields.items():
                    stats[field] = {
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "count": len(values)
                    }
                
                result = {
                    "total_records": len(data),
                    "numeric_statistics": stats
                }
            
            action_log = {
                "action": "data_analysis",
                "analysis_type": analysis_type,
                "records_analyzed": len(data),
                "execution_time_ms": int((time.time() - action_start) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.action_log.append(action_log)
            
            return {
                "success": True,
                "result": result,
                "action_log": action_log
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action_log": {
                    "action": "data_analysis",
                    "error": str(e),
                    "execution_time_ms": int((time.time() - action_start) * 1000)
                }
            }
    
    # ==================== SİSTEM ETKİLEŞİMİ ====================
    
    def system_interaction(self, interaction_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sistem etkileşimi (dikkatli kullanılmalı - güvenlik riskleri var)
        
        Args:
            interaction_type: Etkileşim tipi
            params: Parametreler
        
        Returns:
            Dict: Etkileşim sonucu
        """
        if not self.can_perform("system_interaction"):
            return {
                "success": False,
                "error": "Bu ajan sistem etkileşimi yetkisine sahip değil"
            }
        
        # Güvenlik: Sadece beyaz listeye alınmış etkileşimler
        allowed_interactions = ["read_config", "check_status", "log_event"]
        
        if interaction_type not in allowed_interactions:
            return {
                "success": False,
                "error": f"Bu etkileşim tipi izin verilmiyor: {interaction_type}"
            }
        
        action_start = time.time()
        
        try:
            result = {}
            
            if interaction_type == "read_config":
                # Güvenli konfigürasyon okuma
                result = {"config": "Simulated config data"}
            
            elif interaction_type == "check_status":
                # Sistem durumu kontrolü
                result = {"status": "operational", "timestamp": datetime.utcnow().isoformat()}
            
            elif interaction_type == "log_event":
                # Olay loglama
                result = {"logged": True, "event": params.get("event", "")}
            
            action_log = {
                "action": "system_interaction",
                "interaction_type": interaction_type,
                "execution_time_ms": int((time.time() - action_start) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.action_log.append(action_log)
            
            return {
                "success": True,
                "result": result,
                "action_log": action_log
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action_log": {
                    "action": "system_interaction",
                    "error": str(e),
                    "execution_time_ms": int((time.time() - action_start) * 1000)
                }
            }
    
    # ==================== ARAŞTIRMA ====================
    
    def research(self, topic: str, depth: str = "basic") -> Dict[str, Any]:
        """
        Konuyla ilgili araştırma yap (web search + analiz)
        
        Args:
            topic: Araştırma konusu
            depth: Araştırma derinliği (basic, detailed, comprehensive)
        
        Returns:
            Dict: Araştırma sonuçları
        """
        if not self.can_perform("research"):
            return {
                "success": False,
                "error": "Bu ajan araştırma yetkisine sahip değil"
            }
        
        action_start = time.time()
        
        try:
            # Web araştırması yap
            search_result = self.web_search(topic, num_results=10 if depth == "comprehensive" else 5)
            
            if not search_result["success"]:
                return search_result
            
            # Sonuçları derle
            compiled_info = {
                "topic": topic,
                "depth": depth,
                "sources_count": len(search_result["results"]),
                "key_findings": [r["snippet"] for r in search_result["results"][:3]],
                "sources": [{"title": r["title"], "url": r["url"]} for r in search_result["results"]]
            }
            
            action_log = {
                "action": "research",
                "topic": topic,
                "depth": depth,
                "sources_found": len(search_result["results"]),
                "execution_time_ms": int((time.time() - action_start) * 1000),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.action_log.append(action_log)
            
            return {
                "success": True,
                "research": compiled_info,
                "action_log": action_log
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action_log": {
                    "action": "research",
                    "error": str(e),
                    "execution_time_ms": int((time.time() - action_start) * 1000)
                }
            }
    
    # ==================== YARDIMCI METODLAR ====================
    
    def get_action_log(self) -> List[Dict[str, Any]]:
        """Gerçekleştirilen tüm eylemlerin loglarını döndür"""
        return self.action_log
    
    def clear_action_log(self):
        """Eylem logunu temizle"""
        self.action_log = []
    
    def get_available_actions(self) -> List[str]:
        """Kullanılabilir eylemleri listele"""
        return self.capabilities
