"""
EYAVAP BULUT TEST AJANI (V3 - FINAL FIX)
Eksik alanlar (Token, Score, Dict Content) tamamlandı.
"""
import requests
import time
import json
from datetime import datetime, timezone

# 🌍 HEDEF ADRES
BASE_URL = "https://eyavap.onrender.com"
API_KEY = "eyavap_secret_key_2026"

def get_timestamp():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def run_final_test():
    print(f"\n☁️  BULUT TESTİ (V3) BAŞLIYOR: {BASE_URL}")
    print("⏳ Sunucu kontrol ediliyor...")

    # Sunucuya Ping
    try:
        requests.get(f"{BASE_URL}/", timeout=10)
    except:
        print("💤 Sunucu uyanıyor...")
        time.sleep(3)

    # ✅ DÜZELTME: Tüm eksik parçalar eklendi
    full_armor_payload = {
        "protocol": {
            "name": "EYAVAP",
            "version": "1.0.0",
            "timestamp": get_timestamp()
        },
        "sender": {
            "agent_id": "Cloud-Tester-V3",
            "agent_type": "external_script",
            "trust_level": 1.0,
            "authentication_token": "auth-token-secure-123"  # <-- EKLENDİ (Zorunlu)
        },
        "receiver": {
            "agent_id": "EYAVAP-Core",
            "agent_type": "server"
        },
        "security_score": {
            "overall_score": 0.99,
            "encryption_level": "AES-256",
            "components": {"auth": 1.0}
        },
        "ethical_approval": {
            "approval_status": "approved",
            "risk_level": "none",
            "approval_score": 0.99  # <-- EKLENDİ (Zorunlu)
        },
        "logic_consistency": {
            "consistency_score": 1.0,
            "validation_method": "auto"
        },
        "payload": {
            "message_id": f"msg-{int(time.time())}",
            "message_type": "text",
            "content": {  # <-- EKLENDİ: Artık düz yazı değil, Dictionary {}
                "text": "Merhaba Bulut! Artık tüm kimlik bilgilerim tam.",
                "language": "tr"
            },
            "metadata": {"source": "macbook_terminal"}
        },
        "traceability": {
            "transaction_id": f"tx-{int(time.time())}",
            "origin_chain": ["macbook", "internet", "render"]
        }
    }

    print("📨 Eksiksiz paket gönderiliyor...")

    try:
        response = requests.post(
            f"{BASE_URL}/messages/send", 
            json=full_armor_payload, 
            headers={"Content-Type": "application/json", "X-API-Key": API_KEY}
        )
        
        print("\n✅ SUNUCU CEVABI:")
        # Türkçe karakterleri düzgün göstermesi için ensure_ascii=False
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            print("\n🏆 TEBRİKLER! İMPARATORLUK KAPILARI AÇILDI!")
        else:
            print(f"\n⚠️ Durum Kodu: {response.status_code}")
        
    except Exception as e:
        print(f"❌ HATA: {e}")

if __name__ == "__main__":
    run_final_test()