"""
EYAVAP: Ana Ajan Sistemi
Başkan Ajan'ı kullanarak sorguları işle
"""

from typing import Dict, Any
from president_agent import get_president_agent


def ask_the_government(user_query: str) -> Dict[str, Any]:
    """
    Kullanıcı sorusunu Başkan Ajan'a yönlendir
    
    Args:
        user_query: Kullanıcının sorusu
    
    Returns:
        Dict: {
            "answer": str,
            "ministry_name": str,  # Uyumluluk için (dashboard.py'de kullanılıyor)
            "ministry_icon": str,
            "ministry_style": str,
            "agent_used": str,
            "agent_created": bool,
            "execution_time_ms": int
        }
    """
    try:
        # Başkan Ajan'ı al
        president = get_president_agent()
        
        # Sorguyu işle
        result = president.process_query(user_query)
        
        # Dashboard uyumluluğu için format dönüşümü
        return {
            "answer": result["answer"],
            "ministry_name": result.get("agent_used", "Başkan Ajan"),
            "ministry_icon": "🤖" if result.get("agent_created") else "👔",
            "ministry_style": "color: white;",
            "agent_used": result.get("agent_used", "Unknown"),
            "agent_specialization": result.get("agent_specialization", "general"),
            "agent_created": result.get("agent_created", False),
            "execution_time_ms": result.get("execution_time_ms", 0),
            "success": result.get("success", True)
        }
        
    except Exception as e:
        return {
            "answer": f"⚠️ Sistem hatası: {str(e)}",
            "ministry_name": "Hata Yönetimi",
            "ministry_icon": "⚠️",
            "ministry_style": "color: red;",
            "agent_used": "Error Handler",
            "agent_created": False,
            "execution_time_ms": 0,
            "success": False
        }
