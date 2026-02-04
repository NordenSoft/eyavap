"""
EYAVAP - Evrensel Yapay Zekâ Ajanları Arası Veri Aktarım Protokolü
Ana Sunucu Dosyası
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# ==================== Çevre Değişkenlerini Yükle ====================

# .env dosyasının tam yolunu bul (main.py ile aynı dizinde)
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Debug: Çevre değişkenlerini kontrol et
print(f"📁 .env dosyası yolu: {env_path}")
print(f"📁 .env dosyası mevcut mu: {env_path.exists()}")

# Çevre değişkenlerini global olarak oku (bir kez)
# NOT: Varsayılan "development" - production'da .env'de değiştirin
# .strip() ile boşlukları temizle - .env dosyasındaki yanlış boşlukları önler
EYAVAP_ENV = os.getenv("EYAVAP_ENV", "development").strip()
EYAVAP_API_KEY = os.getenv("EYAVAP_API_KEY", "").strip() or None
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip() or None
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip() or None

print(f"🔧 EYAVAP_ENV: {EYAVAP_ENV}")
print(f"🔑 EYAVAP_API_KEY: {'***' + EYAVAP_API_KEY[-4:] if EYAVAP_API_KEY else 'NOT SET'}")
print(f"🗄️  SUPABASE_URL: {'SET' if SUPABASE_URL else 'NOT SET'}")
print(f"🔐 SUPABASE_KEY: {'SET' if SUPABASE_KEY else 'NOT SET'}")

# ==================== Supabase Bağlantısı ====================

# Supabase client'ı global olarak tanımla
supabase_client = None
supabase_connected = False

def init_supabase():
    """Supabase bağlantısını başlat (global değişkenleri kullanır)"""
    global supabase_client, supabase_connected
    
    try:
        from supabase import create_client, Client
        
        # Global olarak tanımlanan değişkenleri kullan
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("⚠️  Supabase yapılandırması eksik! SUPABASE_URL ve SUPABASE_KEY gerekli.")
            print("   Veritabanı loglama devre dışı bırakıldı.")
            return False
        
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase_connected = True
        print("✅ Supabase bağlantısı başarılı!")
        return True
        
    except ImportError:
        print("⚠️  Supabase kütüphanesi bulunamadı! pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Supabase bağlantı hatası: {e}")
        return False


async def log_to_supabase(
    agent_name: str,
    decision: str,
    security_score: float,
    is_safe: bool,
    additional_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    agent_logs tablosuna kayıt ekle
    
    Args:
        agent_name: Ajan adı/ID'si
        decision: Alınan karar (ALLOW, BLOCK, QUARANTINE, WARNING)
        security_score: Güvenlik skoru (0.0 - 1.0)
        is_safe: Güvenli mi? (True/False)
        additional_data: Ek veriler (opsiyonel)
    
    Returns:
        bool: Başarılı mı?
    """
    global supabase_client, supabase_connected
    
    if not supabase_connected or not supabase_client:
        print("⚠️  Supabase bağlı değil, log atlanıyor...")
        return False
    
    try:
        log_record = {
            "agent_name": agent_name,
            "decision": decision,
            "security_score": security_score,
            "is_safe": is_safe,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Ek veriler varsa ekle
        if additional_data:
            log_record["metadata"] = json.dumps(additional_data)
        
        result = supabase_client.table("agent_logs").insert(log_record).execute()
        
        if result.data:
            print(f"📝 Log kaydedildi: {agent_name} -> {decision}")
            return True
        else:
            print(f"⚠️  Log kayıt yanıtı boş: {result}")
            return False
            
    except Exception as e:
        # Hata durumunda sunucu çökmemeli!
        print(f"❌ Supabase log hatası (sunucu çalışmaya devam ediyor): {e}")
        return False

# Protokol kurallarını yükle
def load_protocol_rules() -> Dict[str, Any]:
    """Protokol kurallarını JSON dosyasından yükle"""
    try:
        with open("protocol_rules.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"rules": [], "version": "1.0.0"}

# Uygulama başlangıcında yüklenecek veriler
protocol_rules = {}
registered_agents = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yaşam döngüsü yönetimi"""
    global protocol_rules
    
    # Protokol kurallarını yükle
    protocol_rules = load_protocol_rules()
    print(f"🚀 EYAVAP Sunucusu başlatıldı - Protokol v{protocol_rules.get('version', '1.0.0')}")
    print(f"📋 {len(protocol_rules.get('rules', []))} kural yüklendi")
    
    # Supabase bağlantısını başlat
    init_supabase()
    
    yield
    
    print("👋 EYAVAP Sunucusu kapatılıyor...")


# FastAPI uygulaması
app = FastAPI(
    title="EYAVAP - Evrensel Yapay Zekâ Ajanları Protokolü",
    description="Yapay zekâ ajanlarının güvenli, etik ve tutarlı veri alışverişi için tasarlanmış protokol sunucusu",
    version="1.0.0",
    lifespan=lifespan
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Pydantic Modelleri ====================

class SecurityScore(BaseModel):
    """Güvenlik skoru modeli"""
    overall_score: float = Field(..., ge=0.0, le=1.0)
    encryption_level: str = "AES-256"
    data_sensitivity: str = "medium"
    components: Dict[str, float] = Field(default_factory=dict)
    threat_assessment: str = "low"
    compliance_standards: List[str] = Field(default_factory=list)


class EthicalApproval(BaseModel):
    """Etik onay modeli"""
    approval_status: str = "pending"
    approval_score: float = Field(..., ge=0.0, le=1.0)
    ethical_dimensions: Dict[str, float] = Field(default_factory=dict)
    risk_categories: Dict[str, str] = Field(default_factory=dict)
    human_oversight_required: bool = False


class LogicConsistency(BaseModel):
    """Mantık tutarlılığı modeli"""
    consistency_score: float = Field(..., ge=0.0, le=1.0)
    validation_method: str = "formal_verification"
    components: Dict[str, float] = Field(default_factory=dict)
    contradictions_detected: bool = False
    uncertainty_level: float = Field(0.0, ge=0.0, le=1.0)


class Sender(BaseModel):
    """Gönderen ajan modeli"""
    agent_id: str
    agent_type: str
    authentication_token: str
    trust_level: float = Field(0.5, ge=0.0, le=1.0)


class Receiver(BaseModel):
    """Alıcı ajan modeli"""
    agent_id: str
    agent_type: Optional[str] = None
    expected_capabilities: List[str] = Field(default_factory=list)


class Payload(BaseModel):
    """Mesaj içeriği modeli"""
    message_id: str
    message_type: str
    priority: str = "medium"
    content: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EYAVAPMessage(BaseModel):
    """EYAVAP protokol mesajı"""
    protocol: Dict[str, Any]
    sender: Sender
    receiver: Receiver
    security_score: SecurityScore
    ethical_approval: EthicalApproval
    logic_consistency: LogicConsistency
    payload: Payload
    traceability: Dict[str, Any] = Field(default_factory=dict)


class AgentRegistration(BaseModel):
    """Ajan kayıt modeli"""
    agent_id: str
    agent_type: str
    capabilities: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class ValidationResult(BaseModel):
    """Doğrulama sonucu modeli"""
    valid: bool
    overall_compliance: float
    action: str
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# ==================== Yardımcı Fonksiyonlar ====================

def get_timestamp() -> str:
    """ISO 8601 formatında zaman damgası döndür"""
    return datetime.utcnow().isoformat() + "Z"


def generate_hash(data: str) -> str:
    """SHA-256 hash oluştur"""
    return hashlib.sha256(data.encode()).hexdigest()


async def verify_api_key(x_api_key: str = Header(None)) -> str:
    """API anahtarını doğrula (global değişkenleri kullanır)"""
    
    # Geliştirme modunda API key kontrolü atlanabilir
    if EYAVAP_ENV == "development":
        return "development"
    
    if not EYAVAP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API anahtarı yapılandırılmamış"
        )
    
    if x_api_key != EYAVAP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz API anahtarı"
        )
    
    return x_api_key


def validate_message(message: EYAVAPMessage) -> ValidationResult:
    """Mesajı protokol kurallarına göre doğrula"""
    violations = []
    warnings = []
    recommendations = []
    
    # Güvenlik skoru kontrolü
    if message.security_score.overall_score < 0.70:
        violations.append({
            "severity": "high",
            "type": "insufficient_security_score",
            "message": f"Güvenlik skoru çok düşük: {message.security_score.overall_score}",
            "required_value": 0.70
        })
    
    # Etik onay kontrolü
    if message.ethical_approval.approval_status not in ["approved", "conditional_approval"]:
        violations.append({
            "severity": "critical",
            "type": "no_ethical_approval",
            "message": f"Etik onay alınmamış: {message.ethical_approval.approval_status}"
        })
    
    if message.ethical_approval.approval_score < 0.75:
        violations.append({
            "severity": "high",
            "type": "low_ethical_score",
            "message": f"Etik skor yetersiz: {message.ethical_approval.approval_score}"
        })
    
    # Mantık tutarlılığı kontrolü
    if message.logic_consistency.consistency_score < 0.80:
        violations.append({
            "severity": "medium",
            "type": "low_consistency_score",
            "message": f"Mantık tutarlılığı düşük: {message.logic_consistency.consistency_score}"
        })
    
    if message.logic_consistency.contradictions_detected:
        violations.append({
            "severity": "critical",
            "type": "contradictions_found",
            "message": "Mantıksal çelişkiler tespit edildi"
        })
    
    # Belirsizlik kontrolü
    if message.logic_consistency.uncertainty_level > 0.30:
        warnings.append({
            "type": "high_uncertainty",
            "message": f"Yüksek belirsizlik: {message.logic_consistency.uncertainty_level}"
        })
        recommendations.append("Belirsizliği azaltmak için ek doğrulama yapın")
    
    # Genel uyumluluk skoru hesapla
    compliance_score = calculate_compliance_score(message, violations)
    
    # Aksiyon belirle
    action = determine_action(compliance_score, violations)
    
    return ValidationResult(
        valid=len([v for v in violations if v["severity"] == "critical"]) == 0,
        overall_compliance=compliance_score,
        action=action,
        violations=violations,
        warnings=warnings,
        recommendations=recommendations
    )


def calculate_compliance_score(message: EYAVAPMessage, violations: List[Dict]) -> float:
    """Genel uyumluluk skorunu hesapla"""
    weights = {
        "security": 0.30,
        "ethical": 0.35,
        "logic": 0.20,
        "structural": 0.15
    }
    
    score = (
        message.security_score.overall_score * weights["security"] +
        message.ethical_approval.approval_score * weights["ethical"] +
        message.logic_consistency.consistency_score * weights["logic"] +
        1.0 * weights["structural"]
    )
    
    # İhlal cezası
    penalty = len(violations) * 0.05
    
    return round(max(score - penalty, 0.0), 2)


def determine_action(compliance_score: float, violations: List[Dict]) -> str:
    """Uyumluluk skoruna göre aksiyon belirle"""
    critical_violations = [v for v in violations if v.get("severity") == "critical"]
    
    if critical_violations or compliance_score < 0.50:
        return "BLOCK"
    elif compliance_score < 0.70:
        return "QUARANTINE"
    elif compliance_score < 0.85:
        return "WARNING"
    else:
        return "ALLOW"


# ==================== API Endpointleri ====================

@app.get("/")
async def root():
    """Sunucu durumu"""
    return {
        "status": "active",
        "protocol": "EYAVAP",
        "version": "1.0.0",
        "timestamp": get_timestamp(),
        "message": "Evrensel Yapay Zekâ Ajanları Protokolü'ne hoş geldiniz! 🤖"
    }


@app.get("/health")
async def health_check():
    """Sağlık kontrolü"""
    return {
        "status": "healthy",
        "timestamp": get_timestamp(),
        "rules_loaded": len(protocol_rules.get("rules", [])),
        "registered_agents": len(registered_agents),
        "database": {
            "supabase_connected": supabase_connected,
            "logging_enabled": supabase_connected
        }
    }


@app.get("/rules")
async def get_rules():
    """Protokol kurallarını getir"""
    return {
        "protocol": "EYAVAP",
        "version": protocol_rules.get("version", "1.0.0"),
        "rules": protocol_rules.get("rules", []),
        "last_updated": protocol_rules.get("last_updated", get_timestamp())
    }


@app.post("/agents/register")
async def register_agent(
    registration: AgentRegistration,
    api_key: str = Depends(verify_api_key)
):
    """Yeni ajan kaydet"""
    if registration.agent_id in registered_agents:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ajan zaten kayıtlı: {registration.agent_id}"
        )
    
    registered_agents[registration.agent_id] = {
        "agent_id": registration.agent_id,
        "agent_type": registration.agent_type,
        "capabilities": registration.capabilities,
        "description": registration.description,
        "registered_at": get_timestamp(),
        "trust_level": 0.5,
        "status": "active"
    }
    
    return {
        "status": "registered",
        "agent_id": registration.agent_id,
        "message": f"Ajan başarıyla kaydedildi: {registration.agent_id}",
        "timestamp": get_timestamp()
    }


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str, api_key: str = Depends(verify_api_key)):
    """Ajan bilgilerini getir"""
    if agent_id not in registered_agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ajan bulunamadı: {agent_id}"
        )
    
    return registered_agents[agent_id]


@app.get("/agents/{agent_id}/scorecard")
async def get_agent_scorecard(agent_id: str, api_key: str = Depends(verify_api_key)):
    """Ajan performans kartını getir"""
    if agent_id not in registered_agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ajan bulunamadı: {agent_id}"
        )
    
    agent = registered_agents[agent_id]
    
    return {
        "agent_id": agent_id,
        "generated_at": get_timestamp(),
        "overall_performance": {
            "trust_level": agent.get("trust_level", 0.5),
            "compliance_rating": "A" if agent.get("trust_level", 0.5) > 0.85 else "B",
            "total_transactions": 0,
            "success_rate": 1.0
        },
        "compliance_breakdown": {
            "security_avg": 0.90,
            "ethical_avg": 0.88,
            "logic_avg": 0.92
        },
        "violation_history": {
            "total_violations": 0,
            "critical_violations": 0,
            "recent_trend": "stable"
        },
        "recommendations": []
    }


@app.post("/messages/validate")
async def validate_message_endpoint(
    message: EYAVAPMessage,
    api_key: str = Depends(verify_api_key)
):
    """Mesajı protokole göre doğrula"""
    
    # Gönderen kontrolü
    if message.sender.agent_id not in registered_agents:
        # Otomatik kayıt (geliştirme için)
        if EYAVAP_ENV == "development":
            registered_agents[message.sender.agent_id] = {
                "agent_id": message.sender.agent_id,
                "agent_type": message.sender.agent_type,
                "registered_at": get_timestamp(),
                "trust_level": 0.5,
                "status": "active"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Kayıtlı olmayan gönderen: {message.sender.agent_id}"
            )
    
    # Mesajı doğrula
    result = validate_message(message)
    
    # 🔹 Supabase'e log kaydet
    is_safe = result.action in ["ALLOW", "WARNING"]
    await log_to_supabase(
        agent_name=message.sender.agent_id,
        decision=result.action,
        security_score=message.security_score.overall_score,
        is_safe=is_safe,
        additional_data={
            "message_id": message.payload.message_id,
            "receiver": message.receiver.agent_id,
            "compliance_score": result.overall_compliance,
            "violations_count": len(result.violations),
            "endpoint": "validate"
        }
    )
    
    return {
        "status": "validated",
        "message_id": message.payload.message_id,
        "timestamp": get_timestamp(),
        "allowed": result.action == "ALLOW",
        "action_taken": result.action,
        "compliance_score": result.overall_compliance,
        "details": {
            "valid": result.valid,
            "violations": result.violations,
            "warnings": result.warnings,
            "recommendations": result.recommendations
        }
    }


@app.post("/messages/send")
async def send_message(
    message: EYAVAPMessage,
    api_key: str = Depends(verify_api_key)
):
    """Mesaj gönder (doğrulama + iletim)"""
    
    # Önce doğrula
    validation = validate_message(message)
    
    # 🔹 Supabase'e log kaydet (tüm durumlar için)
    is_safe = validation.action in ["ALLOW", "WARNING"]
    await log_to_supabase(
        agent_name=message.sender.agent_id,
        decision=validation.action,
        security_score=message.security_score.overall_score,
        is_safe=is_safe,
        additional_data={
            "message_id": message.payload.message_id,
            "receiver": message.receiver.agent_id,
            "compliance_score": validation.overall_compliance,
            "violations_count": len(validation.violations),
            "message_type": message.payload.message_type,
            "priority": message.payload.priority,
            "endpoint": "send"
        }
    )
    
    if validation.action == "BLOCK":
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": "blocked",
                "message_id": message.payload.message_id,
                "reason": "Mesaj protokol gereksinimlerini karşılamıyor",
                "compliance_score": validation.overall_compliance,
                "violations": validation.violations,
                "timestamp": get_timestamp()
            }
        )
    
    if validation.action == "QUARANTINE":
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "quarantined",
                "message_id": message.payload.message_id,
                "reason": "Mesaj inceleme için bekletiliyor",
                "compliance_score": validation.overall_compliance,
                "review_deadline": get_timestamp(),
                "timestamp": get_timestamp()
            }
        )
    
    # Mesajı ilet (gerçek implementasyonda alıcıya gönderilir)
    return {
        "status": "delivered",
        "message_id": message.payload.message_id,
        "sender": message.sender.agent_id,
        "receiver": message.receiver.agent_id,
        "compliance_score": validation.overall_compliance,
        "action": validation.action,
        "warnings": validation.warnings,
        "timestamp": get_timestamp()
    }


@app.get("/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Sistem istatistiklerini getir"""
    return {
        "timestamp": get_timestamp(),
        "system": {
            "status": "operational",
            "uptime": "N/A",
            "version": "1.0.0"
        },
        "agents": {
            "total_registered": len(registered_agents),
            "active": len([a for a in registered_agents.values() if a.get("status") == "active"])
        },
        "protocol": {
            "version": protocol_rules.get("version", "1.0.0"),
            "rules_count": len(protocol_rules.get("rules", []))
        }
    }


# ==================== Uygulama Başlatma ====================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("EYAVAP_HOST", "0.0.0.0")
    port = int(os.getenv("EYAVAP_PORT", 8000))
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   🤖 EYAVAP - Evrensel Yapay Zekâ Ajanları Protokolü    ║
    ║                                                          ║
    ║   Yapay zekâ ajanlarına hükmetmeye hazır mısın?         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=EYAVAP_ENV == "development"
    )
