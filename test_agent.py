import requests
import time

# EYAVAP Yerel Sunucu Adresi
API_URL = "http://localhost:8000/messages/send"

def send_test_log():
    # Ajanın göndereceği simüle edilmiş veri
    payload = {
        "agent_name": "Siber-Gözcü-01",
        "decision": "Güvenlik protokolleri tarandı. Kritik bir sızıntı tespit edilmedi. Sistem stabil.",
        "security_score": 88,
        "is_safe": True
    }

    print(f"🚀 {payload['agent_name']} veri gönderiyor...")
    
    try:
        # Sunucuya POST isteği gönderiyoruz
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            print("✅ BAŞARILI: Veri sunucuya ulaştı ve Supabase'e kaydedildi.")
            print(f"📥 Sunucudan Gelen Yanıt: {response.json()}")
        else:
            print(f"❌ HATA: Sunucu {response.status_code} koduyla yanıt verdi.")
            print(f"Detay: {response.text}")
            
    except Exception as e:
        print(f"🚨 KRİTİK HATA: Sunucuya bağlanılamadı! (Sunucunun çalıştığından emin ol)\n{e}")

if __name__ == "__main__":
    send_test_log()