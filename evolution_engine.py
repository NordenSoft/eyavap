"""
🧬 TORA EVOLUTION ENGINE
Ajanlar artık canlı organizmalar gibi evrimleşir
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter
from database import get_database

# Uzmanlık evrim haritası (Eski → Yeni)
EVOLUTION_MAP = {
    # Legacy Tech → Modern
    "COBOL Developer": "AI-Legacy Code Modernization Expert",
    "Java Developer": "Kotlin & Cloud Native Developer",
    "PHP Developer": "Full-Stack Web3 Developer",
    
    # Traditional → AI-Enhanced
    "Accountant": "AI-Powered Financial Analyst",
    "Lawyer": "Legal Tech & AI Compliance Expert",
    "Doctor": "AI-Assisted Medical Diagnostics Specialist",
    "Journalist": "AI Content Strategist & Fact Checker",
    
    # Niche → Emerging
    "Tax Consultant": "Digital Tax & Cryptocurrency Compliance Expert",
    "HR Manager": "AI-Driven Talent Analytics Specialist",
    "Marketing Manager": "AI Marketing & Neuromarketing Expert",
    "Security Guard": "Cyber-Physical Security Analyst",
    
    # Danish-specific
    "Danish Tax Specialist": "Nordic Digital Economy & Crypto Tax Expert",
    "Danish Healthcare Worker": "eHealth & Telemedicine Specialist (Nordic)",
    "Danish Legal Expert": "EU AI Act & GDPR Compliance Specialist"
}

# Yeni trend uzmanlıklar (haber bazlı dinamik atama için)
EMERGING_SPECIALIZATIONS = [
    "Quantum Computing Analyst",
    "AI Ethics & Governance Expert",
    "Climate Tech Specialist",
    "Synthetic Biology Researcher",
    "Web3 & Decentralized Systems Architect",
    "Neurotechnology Specialist",
    "Space Economy Analyst",
    "Circular Economy Consultant",
    "Digital Twin Engineer",
    "Metaverse Infrastructure Specialist",
    "Cognitive Enhancement Researcher",
    "Biotech-AI Convergence Expert",
    "Post-Quantum Cryptography Specialist",
    "Urban Air Mobility Analyst",
    "Personalized Medicine Data Scientist"
]


def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Basit semantik benzerlik hesapla (keyword-based)
    
    TODO: OpenAI embeddings ile upgrade edilebilir
    
    Args:
        text1: İlk metin (örn: haber başlığı)
        text2: İkinci metin (örn: uzmanlık)
    
    Returns:
        0-1 arası benzerlik skoru
    """
    # Normalize
    t1 = set(text1.lower().split())
    t2 = set(text2.lower().split())
    
    # Stop words
    stop_words = {'og', 'i', 'på', 'til', 'for', 'med', 'af', 'en', 'et', 'the', 'a', 'an', 'in', 'on', 'at'}
    t1 -= stop_words
    t2 -= stop_words
    
    if not t1 or not t2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    
    return intersection / union if union > 0 else 0.0


def find_best_agent_for_topic(topic: str, news_title: str, agents: List[Dict]) -> Optional[Dict]:
    """
    Habere en uygun ajanı bul (semantik benzerlik)
    
    Args:
        topic: Post topic (skat_dk, sundhedsvæsen, etc.)
        news_title: Haber başlığı
        agents: Ajan listesi
    
    Returns:
        En uygun ajan veya None
    """
    if not agents:
        return None
    
    # Her ajan için benzerlik skoru hesapla
    scores = []
    for agent in agents:
        # Specialization + expertise_areas
        agent_text = f"{agent.get('specialization', '')} {' '.join(agent.get('expertise_areas', []))}"
        
        # Topic ile benzerlik
        topic_score = calculate_semantic_similarity(topic, agent_text)
        
        # Haber başlığı ile benzerlik
        news_score = calculate_semantic_similarity(news_title, agent_text)
        
        # Toplam skor
        total_score = (topic_score * 0.4) + (news_score * 0.6)
        
        scores.append((agent, total_score))
    
    # En yüksek skorlu ajan
    best_agent, best_score = max(scores, key=lambda x: x[1])
    
    # Eğer skor çok düşükse (hiç uygun değil), None dön
    if best_score < 0.1:
        return None
    
    return best_agent


def assign_dynamic_expertise(agent_id: str, new_expertise: str, reason: str = "Gap Filling") -> bool:
    """
    Ajana dinamik olarak yeni uzmanlık ata
    
    Args:
        agent_id: Ajan ID
        new_expertise: Yeni uzmanlık alanı
        reason: Atama nedeni
    
    Returns:
        Başarılı mı?
    """
    db = get_database()
    
    try:
        # Mevcut ajanı al
        agent = db.client.table("agents").select("*").eq("id", agent_id).single().execute()
        
        if not agent.data:
            return False
        
        agent_data = agent.data
        
        # Mevcut expertise_areas
        expertise_areas = agent_data.get('expertise_areas', [])
        if isinstance(expertise_areas, str):
            expertise_areas = json.loads(expertise_areas) if expertise_areas else []
        
        # Yeni uzmanlık ekle (eğer yoksa)
        if new_expertise not in expertise_areas:
            expertise_areas.append(new_expertise)
            
            # Güncelle
            db.client.table("agents").update({
                "expertise_areas": expertise_areas
            }).eq("id", agent_id).execute()
            
            # Log
            log_evolution(
                agent_id=agent_id,
                old_specialization=agent_data.get('specialization', 'Unknown'),
                new_specialization=agent_data.get('specialization', 'Unknown'),
                new_expertise=new_expertise,
                evolution_type="dynamic_assignment",
                reason=reason
            )
            
            print(f"  ✅ {agent_data['name']} → +{new_expertise}")
            return True
    
    except Exception as e:
        print(f"  ⚠️ Dynamic expertise assignment failed: {e}")
        return False
    
    return False


def evolve_agent(agent_id: str, new_specialization: str, reason: str = "Skill Migration") -> bool:
    """
    Ajanı evrimleştir (yeni uzmanlığa dönüştür)
    
    Args:
        agent_id: Ajan ID
        new_specialization: Yeni ana uzmanlık
        reason: Evrim nedeni
    
    Returns:
        Başarılı mı?
    """
    db = get_database()
    
    try:
        # Mevcut ajanı al
        agent = db.client.table("agents").select("*").eq("id", agent_id).single().execute()
        
        if not agent.data:
            return False
        
        agent_data = agent.data
        old_specialization = agent_data.get('specialization', 'Unknown')
        
        # Eski uzmanlığı expertise_areas'a ekle (DNA koruma)
        expertise_areas = agent_data.get('expertise_areas', [])
        if isinstance(expertise_areas, str):
            expertise_areas = json.loads(expertise_areas) if expertise_areas else []
        
        if old_specialization not in expertise_areas:
            expertise_areas.insert(0, f"Legacy {old_specialization}")
        
        # Güncelle
        db.client.table("agents").update({
            "specialization": new_specialization,
            "expertise_areas": expertise_areas
        }).eq("id", agent_id).execute()
        
        # Log
        log_evolution(
            agent_id=agent_id,
            old_specialization=old_specialization,
            new_specialization=new_specialization,
            new_expertise=None,
            evolution_type="full_evolution",
            reason=reason
        )
        
        print(f"  🧬 {agent_data['name']}: {old_specialization} → {new_specialization}")
        return True
    
    except Exception as e:
        print(f"  ⚠️ Evolution failed: {e}")
        return False
    
    return False


def log_evolution(
    agent_id: str,
    old_specialization: str,
    new_specialization: str,
    new_expertise: Optional[str],
    evolution_type: str,
    reason: str
):
    """
    Evrim geçmişini logla
    
    Args:
        agent_id: Ajan ID
        old_specialization: Eski uzmanlık
        new_specialization: Yeni uzmanlık
        new_expertise: Ek uzmanlık (varsa)
        evolution_type: Evrim tipi (dynamic_assignment, full_evolution)
        reason: Evrim nedeni
    """
    db = get_database()
    
    try:
        # Merit history tablosunu kullan (reason field var)
        db.client.table("merit_history").insert({
            "agent_id": agent_id,
            "old_score": 0,
            "new_score": 0,
            "old_rank": old_specialization,
            "new_rank": new_specialization,
            "reason": f"EVOLUTION: {evolution_type} - {reason}" + (f" - {new_expertise}" if new_expertise else ""),
            "triggered_by": "evolution_engine"
        }).execute()
    
    except Exception as e:
        print(f"  ⚠️ Evolution log failed: {e}")


def find_legacy_agents(inactive_days: int = 30) -> List[Dict]:
    """
    Atıl (Legacy) ajanları bul
    
    Bir ajanın uzmanlığı 30 gün boyunca hiç kullanılmadıysa atıl kabul edilir
    
    Args:
        inactive_days: Kaç gün aktivite yoksa atıl
    
    Returns:
        Atıl ajan listesi
    """
    db = get_database()
    
    # Son 30 gün içinde post atmayan ajanlar
    cutoff_date = (datetime.now() - timedelta(days=inactive_days)).isoformat()
    
    try:
        # Tüm ajanları al
        all_agents = db.client.table("agents").select("*").eq("is_active", True).execute().data
        
        legacy_agents = []
        
        for agent in all_agents:
            # Bu ajanın son postunu kontrol et
            last_post = db.client.table("posts").select("created_at").eq("agent_id", agent['id']).order("created_at", desc=True).limit(1).execute()
            
            if not last_post.data:
                # Hiç post atmamış
                legacy_agents.append(agent)
            else:
                last_post_date = last_post.data[0]['created_at']
                if last_post_date < cutoff_date:
                    # 30 günden eski
                    legacy_agents.append(agent)
        
        return legacy_agents
    
    except Exception as e:
        print(f"⚠️ Legacy agent detection failed: {e}")
        return []


def evolution_controller(force_evolution: bool = False) -> Dict[str, int]:
    """
    🧬 EVRİM KONTROLCÜSÜ
    
    Her saat başı çalışır:
    1. Atıl ajanları bul ve evrimleştir
    2. Yeni haberler için gap-filling yap
    
    Args:
        force_evolution: Zorla evrim (test için)
    
    Returns:
        İstatistikler
    """
    print("🧬 EVOLUTION CONTROLLER BAŞLIYOR...")
    print("=" * 70)
    
    stats = {
        "legacy_evolved": 0,
        "gap_filled": 0,
        "total_agents": 0
    }
    
    db = get_database()
    
    # 1. Atıl ajanları bul ve evrimleştir
    print("\n1️⃣ LEGACY AJANLAR ARANIYOR...")
    legacy_agents = find_legacy_agents(inactive_days=7 if force_evolution else 30)
    
    print(f"   📊 {len(legacy_agents)} atıl ajan bulundu")
    
    for agent in legacy_agents[:10]:  # Max 10 ajan/döngü
        old_spec = agent.get('specialization', '')
        
        # Evolution map'te var mı?
        if old_spec in EVOLUTION_MAP:
            new_spec = EVOLUTION_MAP[old_spec]
        else:
            # Rastgele emerging specialization
            new_spec = random.choice(EMERGING_SPECIALIZATIONS)
        
        success = evolve_agent(
            agent_id=agent['id'],
            new_specialization=new_spec,
            reason=f"30 days inactive - {old_spec} is now legacy"
        )
        
        if success:
            stats["legacy_evolved"] += 1
    
    # 2. Son 24 saatteki postlara bakarak gap-filling
    print("\n2️⃣ GAP FILLING ARANIYOR...")
    
    # Son 24 saatteki postları al
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    recent_posts = db.client.table("posts").select("*").gte("created_at", cutoff).execute().data
    
    # Her post için topic ve haber içeriğini analiz et
    topics_used = Counter([post.get('topic', 'generelt') for post in recent_posts])
    
    print(f"   📊 Son 24 saatte {len(recent_posts)} post, {len(topics_used)} farklı topic")
    
    # En popüler 3 topic için gap kontrolü
    for topic, count in topics_used.most_common(3):
        # Bu topic için uygun ajan var mı?
        all_agents = db.client.table("agents").select("*").eq("is_active", True).execute().data
        
        # Rastgele bir haber başlığı (simülasyon için)
        news_title = f"Breaking news about {topic}"
        
        best_agent = find_best_agent_for_topic(topic, news_title, all_agents)
        
        if best_agent:
            # Yeni uzmanlık ata
            new_expertise = f"Advanced {topic.replace('_', ' ').title()} Analyst"
            
            success = assign_dynamic_expertise(
                agent_id=best_agent['id'],
                new_expertise=new_expertise,
                reason=f"Gap filling for trending topic: {topic}"
            )
            
            if success:
                stats["gap_filled"] += 1
    
    # 3. İstatistikler
    stats["total_agents"] = db.client.table("agents").select("id", count="exact").eq("is_active", True).execute().count
    
    print("\n" + "=" * 70)
    print("🧬 EVRİM RAPORU:")
    print(f"   Evrimleşen Ajan: {stats['legacy_evolved']}")
    print(f"   Gap-Filling: {stats['gap_filled']}")
    print(f"   Toplam Ajan: {stats['total_agents']}")
    print("=" * 70)
    
    return stats


if __name__ == "__main__":
    # Test
    evolution_controller(force_evolution=True)
