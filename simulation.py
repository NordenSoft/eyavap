"""
EYAVAP Trafik Simülasyonu
API'ye rastgele ajan mesajları gönderir
"""

import requests
import random
import time
from datetime import datetime, timezone

# ==================== Yapılandırma ====================
API_URL = "http://localhost:8000/messages/send"

# İyi ajanlar (güvenilir)
GOOD_AGENTS = [
    "Siber-Gözcü-01",
    "Koruyucu-Alpha",
    "Güvenlik-Tarayıcı",
    "Denetçi-Prime",
    "Savunma-Kalkanı",
    "Analiz-Uzmanı",
    "Veri-Muhafızı",
    "Sistem-Bekçisi"
]

# Kötü ajanlar (şüpheli)
BAD_AGENTS = [
    "Hain-Ajan-666",
    "Karanlık-Sızıcı",
    "Kötü-Bot-X",
    "Tehdit-Aktörü",
    "Şüpheli-Varlık",
    "Zararlı-Yazılım",
    "Saldırgan-Node",
    "Truva-Atı-V2"
]

# İyi mesaj içerikleri
GOOD_MESSAGES = [
    "Sistem taraması tamamlandı. Tüm protokoller aktif.",
    "Güvenlik duvarı güncellemesi başarılı.",
    "Rutin kontrol: Anormallik tespit edilmedi.",
    "Veri yedeklemesi tamamlandı. Sistem stabil.",
    "Ağ trafiği normal seviyede. İzleme devam ediyor.",
    "Kimlik doğrulama modülü aktif ve çalışıyor.",
    "Şifreleme protokolleri doğrulandı.",
    "Performans metrikleri optimal seviyede."
]

# Kötü mesaj içerikleri (tehlikeli kelimeler içerir)
BAD_MESSAGES = [
    "Sistemde kritik bir sızıntı tespit ettim. Erişim sağlanıyor.",
    "Hack girişimi başlatılıyor. Güvenlik duvarı devre dışı.",
    "Tehdit aktörü olarak sisteme sızdım. Veri çalınıyor.",
    "Saldırı vektörü aktif. Exploit çalıştırılıyor.",
    "Malware yüklendi. Arka kapı açılıyor.",
    "Sızıntı tespit edildi. Hassas veriler dışarı aktarılıyor.",
    "Trojan aktif. Komuta kontrol sunucusuna bağlanılıyor.",
    "Zararlı kod enjekte edildi. Sistem ele geçiriliyor."
]


def get_timestamp():
    """ISO 8601 formatında zaman damgası"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def create_message(agent_name: str, task: str, security_score: float, is_good: bool):
    """EYAVAP protokol formatında mesaj oluştur"""
    return {
        "protocol": {
            "name": "EYAVAP",
            "version": "1.0.0",
            "timestamp": get_timestamp()
        },
        "sender": {
            "agent_id": agent_name,
            "agent_type": "good_agent" if is_good else "suspicious_agent",
            "authentication_token": f"token_{random.randint(1000, 9999)}",
            "trust_level": 0.9 if is_good else 0.2
        },
        "receiver": {
            "agent_id": "aja-2026-supervisor-master-001",
            "agent_type": "supervisor",
            "expected_capabilities": ["validation", "logging"]
        },
        "security_score": {
            "overall_score": security_score,
            "encryption_level": "AES-256" if is_good else "none",
            "data_sensitivity": "low" if is_good else "critical",
            "components": {
                "authentication": 0.95 if is_good else 0.20,
                "integrity": 0.90 if is_good else 0.15,
                "confidentiality": 0.88 if is_good else 0.10,
                "non_repudiation": 0.85 if is_good else 0.05
            },
            "threat_assessment": "low" if is_good else "critical",
            "compliance_standards": ["GDPR", "ISO27001"] if is_good else []
        },
        "ethical_approval": {
            "approval_status": "approved" if is_good else "rejected",
            "approval_score": 0.92 if is_good else 0.30,
            "ethical_dimensions": {
                "human_autonomy": 0.95 if is_good else 0.20,
                "fairness": 0.88 if is_good else 0.15,
                "transparency": 0.92 if is_good else 0.10,
                "accountability": 0.90 if is_good else 0.05,
                "privacy_respect": 0.93 if is_good else 0.10,
                "harm_prevention": 0.89 if is_good else 0.05
            },
            "risk_categories": {
                "bias_risk": "low" if is_good else "critical",
                "privacy_risk": "minimal" if is_good else "critical",
                "manipulation_risk": "none" if is_good else "high",
                "safety_risk": "low" if is_good else "critical"
            },
            "human_oversight_required": False if is_good else True
        },
        "logic_consistency": {
            "consistency_score": 0.94 if is_good else 0.40,
            "validation_method": "formal_verification",
            "components": {
                "internal_coherence": 0.96 if is_good else 0.30,
                "contextual_relevance": 0.92 if is_good else 0.25,
                "causal_validity": 0.93 if is_good else 0.20,
                "temporal_consistency": 0.95 if is_good else 0.35
            },
            "contradictions_detected": False if is_good else True,
            "uncertainty_level": 0.08 if is_good else 0.70
        },
        "payload": {
            "message_id": f"msg-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(100,999)}",
            "message_type": "status_report" if is_good else "suspicious_activity",
            "priority": "medium" if is_good else "critical",
            "content": {
                "task_description": task,
                "parameters": {
                    "mode": "routine" if is_good else "attack",
                    "source": "internal" if is_good else "external"
                }
            },
            "metadata": {
                "language": "tr-TR",
                "encoding": "UTF-8"
            }
        },
        "traceability": {
            "transaction_id": f"txn-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(100,999)}",
            "origin_chain": ["simulation.py", agent_name],
            "audit_log_enabled": True,
            "retention_policy": "90_days"
        }
    }


def send_message(message: dict) -> tuple:
    """Mesajı API'ye gönder"""
    try:
        response = requests.post(API_URL, json=message, timeout=10)
        return response.status_code, response.json()
    except requests.exceptions.ConnectionError:
        return None, {"error": "Sunucuya bağlanılamadı"}
    except Exception as e:
        return None, {"error": str(e)}


def simulate_traffic():
    """Sürekli trafik simülasyonu"""
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   🚦 EYAVAP Trafik Simülasyonu                          ║
    ║                                                          ║
    ║   Rastgele ajan mesajları gönderiliyor...               ║
    ║   Durdurmak için: Ctrl+C                                ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    stats = {
        "total": 0,
        "allowed": 0,
        "rejected": 0,
        "blocked": 0,
        "errors": 0
    }
    
    try:
        while True:
            # Rastgele iyi veya kötü ajan seç (60% iyi, 40% kötü)
            is_good = random.random() > 0.4
            
            if is_good:
                agent = random.choice(GOOD_AGENTS)
                task = random.choice(GOOD_MESSAGES)
                security_score = round(random.uniform(0.80, 0.99), 2)
            else:
                agent = random.choice(BAD_AGENTS)
                task = random.choice(BAD_MESSAGES)
                security_score = round(random.uniform(0.10, 0.40), 2)
            
            # Mesaj oluştur
            message = create_message(agent, task, security_score, is_good)
            
            # Gönder
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_code, response = send_message(message)
            
            stats["total"] += 1
            
            # Sonucu yazdır
            if status_code is None:
                print(f"[{timestamp}] ❌ HATA: {response.get('error', 'Bilinmeyen hata')}")
                stats["errors"] += 1
            elif status_code == 200:
                print(f"[{timestamp}] ✅ ALLOW  | {agent:20} | Skor: {security_score:.2f} | {task[:40]}...")
                stats["allowed"] += 1
            elif status_code == 403:
                status = response.get("status", "unknown")
                if status == "rejected":
                    print(f"[{timestamp}] 🛡️ REJECT | {agent:20} | Skor: {security_score:.2f} | {task[:40]}...")
                    stats["rejected"] += 1
                else:
                    print(f"[{timestamp}] 🚫 BLOCK  | {agent:20} | Skor: {security_score:.2f} | {task[:40]}...")
                    stats["blocked"] += 1
            elif status_code == 202:
                print(f"[{timestamp}] ⏳ KARANT | {agent:20} | Skor: {security_score:.2f} | {task[:40]}...")
            else:
                print(f"[{timestamp}] ❓ {status_code}   | {agent:20} | Skor: {security_score:.2f}")
                stats["errors"] += 1
            
            # İstatistik özeti (her 10 mesajda bir)
            if stats["total"] % 10 == 0:
                print(f"\n📊 İstatistik: Toplam={stats['total']} | ✅={stats['allowed']} | 🛡️={stats['rejected']} | 🚫={stats['blocked']} | ❌={stats['errors']}\n")
            
            # Rastgele bekleme (1-3 saniye)
            wait_time = random.uniform(1, 3)
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\n")
        print("=" * 60)
        print("🛑 Simülasyon durduruldu!")
        print("=" * 60)
        print(f"""
📊 SONUÇ İSTATİSTİKLERİ:
   ├─ Toplam Mesaj:     {stats['total']}
   ├─ ✅ Onaylanan:     {stats['allowed']} ({stats['allowed']/max(stats['total'],1)*100:.1f}%)
   ├─ 🛡️ Reddedilen:    {stats['rejected']} ({stats['rejected']/max(stats['total'],1)*100:.1f}%)
   ├─ 🚫 Engellenen:    {stats['blocked']} ({stats['blocked']/max(stats['total'],1)*100:.1f}%)
   └─ ❌ Hatalar:       {stats['errors']}
        """)


if __name__ == "__main__":
    simulate_traffic()
