"""
EYAVAP BULUT TEST AJANI (RENDER VERSİYONU)
"""
import requests
import time
import json

# 🌍 SENİN CANLI SUNUCU ADRESİN
BASE_URL = "https://eyavap.onrender.com"
API_KEY = "eyavap_secret_key_2026"

def run_cloud_test():
    print(f"\n☁️  BULUT TESTİ BAŞLIYOR: {BASE_URL}")
    print("⏳ Sunucu kontrol ediliyor (Uyuyorsa uyanması 50sn sürebilir)...")

    # 1. Sunucu Ayakta mı?
    try:
        requests.get(f"{BASE_URL}/", timeout=5)
    except:
        print("💤 Sunucu uyanıyor... Lütfen bekleyin...")
        time.sleep(3)

    # 2. Mesaj Gönderelim
    print("📨 Mesaj gönderiliyor...")
    
    payload = {
        "protocol": "EYAVAP-v1",
        "sender": "Cloud-Tester",
        "receiver": "Eyavap-Core",
        "agent_name": "Bulut-Gezgini",
        "content": "Merhaba Render! Uzaydan geliyorum, beni duyuyor musun?",
        "security_score": 0.95,
        "ethical_approval": True,
        "logic_consistency": 1.0,
        "payload": {"type": "ping"}
    }

    try:
        response = requests.post(
            f"{BASE_URL}/messages/send", 
            json=payload, 
            headers={"Content-Type": "application/json", "X-API-Key": API_KEY}
        )
        
        print("\n✅ SONUÇ:")
        print(json.dumps(response.json(), indent=2))
        
    except Exception as e:
        print(f"❌ HATA: {e}")

if __name__ == "__main__":
    run_cloud_test()