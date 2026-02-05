"""
EYAVAP: Dinamik Ajan Spawn Sistemi
Binlerce farklı profilde AI ajan oluşturma
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import streamlit as st
from database import get_database


# ==================== SPAWN PROFİLLERİ ====================

ETHNICITIES = [
    # Asya
    ("Japon", "Japanese", "ja"),
    ("Çinli", "Chinese", "zh"),
    ("Koreli", "Korean", "ko"),
    ("Hint", "Indian", "hi"),
    ("Vietnamlı", "Vietnamese", "vi"),
    ("Tayland", "Thai", "th"),
    
    # Avrupa
    ("Danimarkalı", "Danish", "da"),
    ("İsveçli", "Swedish", "sv"),
    ("Norveçli", "Norwegian", "no"),
    ("Alman", "German", "de"),
    ("Fransız", "French", "fr"),
    ("İtalyan", "Italian", "it"),
    ("İspanyol", "Spanish", "es"),
    ("İngiliz", "British", "en"),
    ("Rus", "Russian", "ru"),
    ("Polonyalı", "Polish", "pl"),
    ("Türk", "Turkish", "tr"),
    
    # Amerika
    ("Amerikalı", "American", "en"),
    ("Kanadalı", "Canadian", "en"),
    ("Meksikalı", "Mexican", "es"),
    ("Brezilyalı", "Brazilian", "pt-BR"),
    ("Arjantinli", "Argentinian", "es"),
    
    # Afrika
    ("Güney Afrikalı", "South African", "en"),
    ("Nijeryalı", "Nigerian", "en"),
    ("Mısırlı", "Egyptian", "ar"),
    
    # Orta Doğu
    ("İsrailli", "Israeli", "he"),
    ("Suudi", "Saudi", "ar"),
    ("İranlı", "Iranian", "fa"),
]

SPECIALIZATIONS = [
    # Danimarka uzmanları
    ("denmark_tax", "Vergi Uzmanı", "Skat Specialist"),
    ("denmark_health", "Sağlık Uzmanı", "Sundhed Specialist"),
    ("denmark_legal", "Hukuk Uzmanı", "Juridisk Specialist"),
    ("denmark_residence", "Oturma İzni Uzmanı", "Opholdstilladelse Specialist"),
    ("denmark_work", "İş Uzmanı", "Arbejde Specialist"),
    ("denmark_education", "Eğitim Uzmanı", "Uddannelse Specialist"),
    
    # Teknik uzmanlar
    ("cyber_security", "Siber Güvenlik Uzmanı", "CyberSec Specialist"),
    ("data_analysis", "Veri Analizi Uzmanı", "DataAnalysis Specialist"),
    ("ai_research", "AI Araştırmacısı", "AI Research Specialist"),
    ("blockchain", "Blockchain Uzmanı", "Blockchain Specialist"),
    ("cloud_architecture", "Bulut Mimarı", "Cloud Architect"),
    
    # Sosyal bilimler
    ("economics", "Ekonomist", "Economics Specialist"),
    ("sociology", "Sosyolog", "Sociology Specialist"),
    ("psychology", "Psikolog", "Psychology Specialist"),
    ("philosophy", "Filozof", "Philosophy Specialist"),
    
    # Diğer
    ("medicine", "Doktor", "Medical Doctor"),
    ("engineering", "Mühendis", "Engineer"),
    ("finance", "Finans Uzmanı", "Finance Specialist"),
    ("marketing", "Pazarlama Uzmanı", "Marketing Specialist"),
]

PERSONALITY_TRAITS = {
    "analytical": {"openness": 0.9, "conscientiousness": 0.9, "agreeableness": 0.5, "neuroticism": 0.3, "extraversion": 0.4},
    "social": {"openness": 0.7, "conscientiousness": 0.6, "agreeableness": 0.9, "neuroticism": 0.4, "extraversion": 0.9},
    "creative": {"openness": 0.95, "conscientiousness": 0.6, "agreeableness": 0.7, "neuroticism": 0.6, "extraversion": 0.7},
    "cautious": {"openness": 0.5, "conscientiousness": 0.95, "agreeableness": 0.7, "neuroticism": 0.7, "extraversion": 0.4},
    "bold": {"openness": 0.8, "conscientiousness": 0.5, "agreeableness": 0.4, "neuroticism": 0.2, "extraversion": 0.9},
}


# ==================== SPAWN FONKSİYONLARI ====================

def generate_agent_profile() -> Dict[str, Any]:
    """Rastgele bir ajan profili oluştur"""
    
    ethnicity, nationality, language = random.choice(ETHNICITIES)
    specialization, spec_name_tr, spec_name_en = random.choice(SPECIALIZATIONS)
    personality_type = random.choice(list(PERSONALITY_TRAITS.keys()))
    personality_traits = PERSONALITY_TRAITS[personality_type]
    
    # İsim oluştur
    agent_name = f"{ethnicity} {spec_name_tr}"
    
    # Yaş (18-65)
    age_years = random.randint(18, 65)
    birth_date = datetime.now() - timedelta(days=age_years * 365)
    
    return {
        "name": agent_name,
        "ethnicity": ethnicity,
        "nationality": nationality,
        "language": language,
        "specialization": specialization,
        "expertise_areas": [specialization, nationality.lower(), language],
        "capabilities": ["research", "analysis", "reporting", "web_search", "social_interaction"],
        "personality_traits": personality_traits,
        "merit_score": random.randint(40, 60),  # Başlangıç puanı 40-60 arası
        "rank": "soldier",
        "is_active": True,
        "birth_date": birth_date,
        "metadata": {
            "personality_type": personality_type,
            "age": age_years,
            "cultural_context": nationality
        }
    }


def spawn_agents(count: int = 100) -> List[Dict[str, Any]]:
    """
    Toplu ajan oluştur
    
    Args:
        count: Kaç ajan oluşturulacak
    
    Returns:
        List[Dict]: Oluşturulan ajan listesi
    """
    db = get_database()
    spawned_agents = []
    
    print(f"🌱 {count} ajan spawn ediliyor...")
    
    for i in range(count):
        try:
            profile = generate_agent_profile()
            
            # Supabase'e kaydet
            result = db.supabase_client.table("agents").insert(profile).execute()
            
            if result.data:
                agent = result.data[0]
                spawned_agents.append(agent)
                
                if (i + 1) % 10 == 0:
                    print(f"   ✅ {i + 1}/{count} ajan oluşturuldu...")
        
        except Exception as e:
            print(f"   ⚠️ Ajan {i + 1} oluşturma hatası: {e}")
            continue
    
    print(f"🎉 Spawn tamamlandı! {len(spawned_agents)}/{count} ajan başarıyla oluşturuldu.")
    
    return spawned_agents


def spawn_diverse_community(
    total_count: int = 1000,
    min_per_ethnicity: int = 5,
    min_per_specialization: int = 10
) -> Dict[str, Any]:
    """
    Çeşitli bir topluluk oluştur (her etnik kökenden, her uzmanlıktan)
    
    Args:
        total_count: Toplam ajan sayısı
        min_per_ethnicity: Her etnik kökenden minimum ajan
        min_per_specialization: Her uzmanlıktan minimum ajan
    
    Returns:
        Dict: Oluşturma raporu
    """
    db = get_database()
    spawned = []
    
    print(f"🌍 Çeşitli topluluk oluşturuluyor ({total_count} ajan)...")
    
    # 1. Her etnik kökenden minimum sayıda
    print(f"\n📊 Adım 1: Her etnik kökenden en az {min_per_ethnicity} ajan...")
    for ethnicity, nationality, language in ETHNICITIES:
        for _ in range(min_per_ethnicity):
            profile = generate_agent_profile()
            profile["ethnicity"] = ethnicity
            profile["nationality"] = nationality
            profile["language"] = language
            
            try:
                result = db.supabase_client.table("agents").insert(profile).execute()
                if result.data:
                    spawned.append(result.data[0])
            except:
                pass
    
    print(f"   ✅ {len(spawned)} etnik çeşitlilik ajanı oluşturuldu")
    
    # 2. Her uzmanlıktan minimum sayıda
    print(f"\n📊 Adım 2: Her uzmanlıktan en az {min_per_specialization} ajan...")
    for spec, spec_tr, spec_en in SPECIALIZATIONS:
        for _ in range(min_per_specialization):
            profile = generate_agent_profile()
            profile["specialization"] = spec
            
            try:
                result = db.supabase_client.table("agents").insert(profile).execute()
                if result.data:
                    spawned.append(result.data[0])
            except:
                pass
    
    print(f"   ✅ {len(spawned)} uzmanlık ajanı oluşturuldu")
    
    # 3. Kalan ajanları rastgele doldur
    remaining = total_count - len(spawned)
    if remaining > 0:
        print(f"\n📊 Adım 3: Kalan {remaining} ajanı rastgele oluşturuluyor...")
        additional = spawn_agents(remaining)
        spawned.extend(additional)
    
    # İstatistikler
    ethnicities = {}
    specializations = {}
    
    for agent in spawned:
        eth = agent.get("ethnicity", "Unknown")
        spec = agent.get("specialization", "Unknown")
        ethnicities[eth] = ethnicities.get(eth, 0) + 1
        specializations[spec] = specializations.get(spec, 0) + 1
    
    return {
        "total_spawned": len(spawned),
        "ethnicity_distribution": ethnicities,
        "specialization_distribution": specializations,
        "avg_merit_score": sum(a.get("merit_score", 50) for a in spawned) / len(spawned) if spawned else 0
    }


# ==================== TEST FONKSİYONU ====================

if __name__ == "__main__":
    print("🌱 EYAVAP Ajan Spawn Sistemi Test\n")
    
    # Test 1: 10 ajan oluştur
    print("=" * 50)
    print("Test 1: 10 rastgele ajan spawn")
    print("=" * 50)
    agents = spawn_agents(10)
    
    print(f"\n✅ {len(agents)} ajan oluşturuldu\n")
    
    for agent in agents[:3]:
        print(f"  • {agent['name']}")
        print(f"    - Uzmanlık: {agent['specialization']}")
        print(f"    - Dil: {agent['language']}")
        print(f"    - Liyakat: {agent['merit_score']}/100")
        print()
