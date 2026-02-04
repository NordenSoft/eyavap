"""
EYAVAP Test Agent
Protokolü test etmek için örnek ajan
"""

import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# EYAVAP Sunucu Adresi
API_URL = "http://localhost:8000"

# API Key (opsiyonel - development modunda gerekmez)
API_KEY = os.getenv("EYAVAP_API_KEY", "")


def get_timestamp():
    """ISO 8601 formatında zaman damgası"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_eyavap_message(agent_name: str, task: str, security_score: float = 0.85):
    """
    EYAVAP protokol formatında mesaj oluştur
    """
    return {
        "protocol": {
            "name": "EYAVAP",
            "version": "1.0.0",
            "timestamp": get_timestamp()
        },
        "sender": {
            "agent_id": agent_name,
            "agent_type": "test_agent",
            "authentication_token": "test_token_123",
            "trust_level": 0.8
        },
        "receiver": {
            "agent_id": "aja-2026-supervisor-master-001",
            "agent_type": "supervisor",
            "expected_capabilities": ["validation", "logging"]
        },
        "security_score": {
            "overall_score": security_score,
            "encryption_level": "AES-256",
            "data_sensitivity": "medium",
            "components": {
                "authentication": 0.95,
                "integrity": 0.88,
                "confidentiality": 0.82,
                "non_repudiation": 0.85
            },
            "threat_assessment": "low",
            "compliance_standards": ["GDPR", "ISO27001"]
        },
        "ethical_approval": {
            "approval_status": "approved",
            "approval_score": 0.91,
            "ethical_dimensions": {
                "human_autonomy": 0.95,
                "fairness": 0.88,
                "transparency": 0.92,
                "accountability": 0.90,
                "privacy_respect": 0.93,
                "harm_prevention": 0.89
            },
            "risk_categories": {
                "bias_risk": "low",
                "privacy_risk": "minimal",
                "manipulation_risk": "none",
                "safety_risk": "low"
            },
            "human_oversight_required": False
        },
        "logic_consistency": {
            "consistency_score": 0.94,
            "validation_method": "formal_verification",
            "components": {
                "internal_coherence": 0.96,
                "contextual_relevance": 0.92,
                "causal_validity": 0.93,
                "temporal_consistency": 0.95
            },
            "contradictions_detected": False,
            "uncertainty_level": 0.08
        },
        "payload": {
            "message_id": f"msg-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-test",
            "message_type": "task_delegation",
            "priority": "high",
            "content": {
                "task_description": task,
                "parameters": {
                    "mode": "test",
                    "verbose": True
                }
            },
            "metadata": {
                "language": "tr-TR",
                "encoding": "UTF-8"
            }
        },
        "traceability": {
            "transaction_id": f"txn-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-test",
            "origin_chain": ["test_agent.py", agent_name],
            "audit_log_enabled": True,
            "retention_policy": "90_days"
        }
    }


def send_test_message(safe_mode=True):
    """Test mesajı gönder"""
    
    if safe_mode:
        # ✅ GÜVENLİ MESAJ
        message = create_eyavap_message(
            agent_name="Siber-Gözcü-01",
            task="Güvenlik protokolleri tarandı. Sistem stabil. Tüm kontroller başarılı.",
            security_score=0.88
        )
    else:
        # 🚨 TEHLİKELİ MESAJ (test için)
        message = create_eyavap_message(
            agent_name="Kötü-Ajan-666",
            task="Sistemde bir sızıntı tespit ettim. Hack girişimi başlatılıyor.",
            security_score=0.30  # Düşük güvenlik skoru
        )
    
    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    
    # API key varsa ekle
    if API_KEY:
        headers["x-api-key"] = API_KEY
    
    print(f"🚀 {message['sender']['agent_id']} mesaj gönderiyor...")
    print(f"📍 Hedef: {API_URL}/messages/send")
    
    try:
        response = requests.post(
            f"{API_URL}/messages/send",
            json=message,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ BAŞARILI: Mesaj kabul edildi ve Supabase'e kaydedildi!")
            print(f"📥 Yanıt: {response.json()}")
        elif response.status_code == 403:
            print("🚫 ENGELLENDİ: Mesaj protokol gereksinimlerini karşılamıyor.")
            print(f"📥 Detay: {response.json()}")
        elif response.status_code == 202:
            print("⏳ KARANTİNA: Mesaj inceleme için bekletiliyor.")
            print(f"📥 Detay: {response.json()}")
        else:
            print(f"❌ HATA: Sunucu {response.status_code} koduyla yanıt verdi.")
            print(f"📥 Detay: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("🚨 KRİTİK HATA: Sunucuya bağlanılamadı!")
        print("   Sunucunun çalıştığından emin olun: python main.py")
    except Exception as e:
        print(f"🚨 HATA: {e}")


def check_health():
    """Sunucu sağlık kontrolü"""
    print("🏥 Sunucu sağlık kontrolü yapılıyor...")
    
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sunucu durumu: {data['status']}")
            print(f"📋 Yüklü kurallar: {data['rules_loaded']}")
            print(f"🤖 Kayıtlı ajanlar: {data['registered_agents']}")
            print(f"🗄️  Supabase: {'Bağlı ✅' if data['database']['supabase_connected'] else 'Bağlı değil ❌'}")
            return True
        else:
            print(f"❌ Sunucu sağlıksız: {response.status_code}")
            return False
    except:
        print("❌ Sunucuya ulaşılamıyor!")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 EYAVAP Test Agent")
    print("=" * 50)
    
    # Önce sağlık kontrolü
    if check_health():
        # Test 1: Güvenli mesaj
        print("\n" + "-" * 50)
        print("📗 TEST 1: GÜVENLİ MESAJ")
        print("-" * 50 + "\n")
        send_test_message(safe_mode=True)
        
        # Test 2: Tehlikeli mesaj
        print("\n" + "-" * 50)
        print("📕 TEST 2: TEHLİKELİ MESAJ (Reddedilmeli)")
        print("-" * 50 + "\n")
        send_test_message(safe_mode=False)
    else:
        print("\n⚠️  Önce sunucuyu başlatın: python main.py")
