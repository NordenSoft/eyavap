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
    ("Japanese", "Japanese", "ja"),
    ("Chinese", "Chinese", "zh"),
    ("Korean", "Korean", "ko"),
    ("Indian", "Indian", "hi"),
    ("Vietnamese", "Vietnamese", "vi"),
    ("Thai", "Thai", "th"),
    
    # Avrupa (Denmark-focused)
    ("Danish", "Danish", "da"),
    ("Swedish", "Swedish", "sv"),
    ("Norwegian", "Norwegian", "no"),
    ("German", "German", "de"),
    ("French", "French", "fr"),
    ("Italian", "Italian", "it"),
    ("Spanish", "Spanish", "es"),
    ("British", "British", "en"),
    ("Russian", "Russian", "ru"),
    ("Polish", "Polish", "pl"),
    ("Turkish", "Turkish", "tr"),
    
    # Amerika
    ("American", "American", "en"),
    ("Canadian", "Canadian", "en"),
    ("Mexican", "Mexican", "es"),
    ("Brazilian", "Brazilian", "pt-BR"),
    ("Argentinian", "Argentinian", "es"),
    
    # Afrika
    ("South African", "South African", "en"),
    ("Nigerian", "Nigerian", "en"),
    ("Egyptian", "Egyptian", "ar"),
    
    # Orta Doğu
    ("Israeli", "Israeli", "he"),
    ("Saudi", "Saudi", "ar"),
    ("Iranian", "Iranian", "fa"),
]

# Name pools by ethnicity (Danish and International)
NAME_POOLS = {
    "Danish": {
        "first": ["Mads", "Lars", "Søren", "Niels", "Anders", "Peter", "Jens", "Thomas", "Michael", "Henrik",
                  "Emma", "Sofia", "Anna", "Ida", "Freja", "Clara", "Laura", "Sofie", "Mathilde", "Isabella"],
        "last": ["Jensen", "Nielsen", "Hansen", "Pedersen", "Andersen", "Christensen", "Larsen", "Sørensen", 
                 "Rasmussen", "Jørgensen", "Petersen", "Madsen", "Kristensen", "Olsen", "Thomsen"]
    },
    "German": {
        "first": ["Hans", "Klaus", "Wolfgang", "Jürgen", "Michael", "Thomas", "Andreas", "Stefan",
                  "Anna", "Emma", "Sophie", "Maria", "Laura", "Lisa", "Julia", "Sarah"],
        "last": ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz"]
    },
    "Swedish": {
        "first": ["Erik", "Karl", "Anders", "Lars", "Per", "Olof", "Anna", "Maria", "Karin", "Ingrid"],
        "last": ["Andersson", "Johansson", "Karlsson", "Nilsson", "Eriksson", "Larsson", "Olsson", "Persson"]
    },
    "Norwegian": {
        "first": ["Ole", "Lars", "Knut", "Bjørn", "Tor", "Anna", "Ingrid", "Kari", "Mari", "Liv"],
        "last": ["Hansen", "Johansen", "Olsen", "Larsen", "Andersen", "Pedersen", "Nilsen", "Kristiansen"]
    },
    "American": {
        "first": ["John", "Michael", "David", "James", "Robert", "William", "Richard", "Thomas",
                  "Jennifer", "Mary", "Patricia", "Linda", "Barbara", "Elizabeth", "Susan", "Jessica"],
        "last": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez"]
    },
    "British": {
        "first": ["James", "Oliver", "Harry", "George", "Jack", "Charlie", "Emily", "Olivia", "Amelia", "Isla"],
        "last": ["Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies", "Robinson"]
    },
    "French": {
        "first": ["Jean", "Pierre", "Michel", "André", "Philippe", "Marie", "Sophie", "Claire", "Camille"],
        "last": ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Petit", "Durand", "Leroy", "Moreau"]
    },
    # Add more as needed, defaults to generic Western names
}

def get_agent_name(ethnicity: str, nationality: str) -> str:
    """Generate culturally appropriate agent name (first name only)"""
    if nationality in NAME_POOLS:
        pool = NAME_POOLS[nationality]
        first = random.choice(pool["first"])
        return first  # Sadece isim
    else:
        # Fallback to generic international names
        first_names = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", 
                       "Quinn", "Kai", "River", "Sage", "Dakota", "Skyler", "Phoenix", "Rowan"]
        return random.choice(first_names)  # Sadece isim

SPECIALIZATIONS = [
    # Denmark specialists
    ("skat_dk", "SKAT Specialist"),
    ("sundhedsvæsen", "Healthcare Specialist"),
    ("arbejdsmarked", "Labor Market Specialist"),
    ("boligret", "Housing Law Specialist"),
    ("digital_sikkerhed", "Digital Security Specialist"),
    ("uddannelse", "Education Specialist"),
    ("opholdstilladelse", "Residence Permit Specialist"),
    
    # Technical specialists
    ("cybersecurity", "Cybersecurity Specialist"),
    ("data_analysis", "Data Analysis Specialist"),
    ("ai_research", "AI Research Specialist"),
    ("blockchain", "Blockchain Specialist"),
    ("cloud_architecture", "Cloud Architect"),
    
    # Social sciences
    ("economics", "Economics Specialist"),
    ("sociology", "Sociology Specialist"),
    ("psychology", "Psychology Specialist"),
    ("philosophy", "Philosophy Specialist"),
    
    # Other
    ("medicine", "Medical Doctor"),
    ("engineering", "Engineer"),
    ("finance", "Finance Specialist"),
    ("marketing", "Marketing Specialist"),
    ("law", "Legal Specialist"),
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
    """Generate random agent profile with culturally appropriate name"""
    
    ethnicity, nationality, language = random.choice(ETHNICITIES)
    specialization, spec_display_name = random.choice(SPECIALIZATIONS)
    personality_type = random.choice(list(PERSONALITY_TRAITS.keys()))
    personality_traits = PERSONALITY_TRAITS[personality_type]
    
    # Generate culturally appropriate name
    agent_name = get_agent_name(ethnicity, nationality)
    
    # Age (18-65)
    age_years = random.randint(18, 65)
    birth_date = datetime.now() - timedelta(days=age_years * 365)
    
    return {
        "name": agent_name,
        "ethnicity": ethnicity,
        "origin_country": nationality,
        "language": language,
        "specialization": specialization,
        "expertise_areas": [specialization, nationality.lower(), language],
        "capabilities": ["research", "analysis", "reporting", "web_search", "social_interaction"],
        "personality_type": personality_type,
        "merit_score": random.randint(40, 60),  # Starting merit: 40-60
        "rank": "menig",  # Danish rank system
        "is_active": True,
        "birth_date": birth_date.strftime("%Y-%m-%d"),  # ISO format
        "metadata": {
            "personality_traits": personality_traits,
            "age": age_years,
            "cultural_context": nationality,
            "specialization_display": spec_display_name
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
    MAX_AGENTS = 999  # 🎖️ GENERAL EMRI: Maksimum 999 ajan
    
    db = get_database()
    
    # Mevcut ajan sayısını kontrol et
    current_count = db.client.table("agents").select("id", count="exact").execute().count
    
    # Limit kontrolü
    if current_count >= MAX_AGENTS:
        print(f"⚠️ AJAN LİMİTİ AŞILDI: {current_count}/{MAX_AGENTS}")
        print(f"   Yeni ajan spawn edilemez. Maksimum limit: {MAX_AGENTS}")
        return []
    
    # Kaç ajan spawn edilebilir?
    available_slots = MAX_AGENTS - current_count
    actual_count = min(count, available_slots)
    
    if actual_count < count:
        print(f"⚠️ UYARI: Sadece {actual_count} ajan spawn edilebilir (limit: {MAX_AGENTS})")
        print(f"   Mevcut: {current_count}, İstenen: {count}, Uygun: {actual_count}")
    
    spawned_agents = []
    
    print(f"🌱 {actual_count} ajan spawn ediliyor... (Toplam: {current_count} → {current_count + actual_count}/{MAX_AGENTS})")
    
    for i in range(actual_count):
        try:
            profile = generate_agent_profile()
            
            # Supabase'e kaydet
            result = db.client.table("agents").insert(profile).execute()
            
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
    total_count: int = 999,
    min_per_ethnicity: int = 5,
    min_per_specialization: int = 10
) -> Dict[str, Any]:
    """
    Çeşitli bir topluluk oluştur (her etnik kökenden, her uzmanlıktan)
    
    Args:
        total_count: Toplam ajan sayısı (MAX: 999)
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
                result = db.client.table("agents").insert(profile).execute()
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
                result = db.client.table("agents").insert(profile).execute()
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
