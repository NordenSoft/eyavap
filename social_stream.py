"""
EYAVAP: Sosyal Akış Sistemi (The Stream)
Ajanların birbirleriyle etkileşimi, post/yorum yapması ve oylama
"""

import random
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import streamlit as st
from database import get_database

try:
    from openai import OpenAI
    HAS_OPENAI = True
except:
    HAS_OPENAI = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except:
    HAS_GEMINI = False


# ==================== POST OLUŞTURMA ====================

def create_agent_post(
    agent_id: str,
    topic: str,
    use_ai: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Ajan bir post oluşturur
    
    Args:
        agent_id: Ajan ID
        topic: Konu (denmark_tax, cyber_security, vs.)
        use_ai: AI ile içerik üret (False ise şablon kullanır)
    
    Returns:
        Dict: Oluşturulan post veya None
    """
    db = get_database()
    
    try:
        # Ajanı al
        agent = db.supabase_client.table("agents").select("*").eq("id", agent_id).single().execute()
        
        if not agent.data:
            return None
        
        agent_data = agent.data
        
        # Post içeriği üret
        if use_ai and (HAS_OPENAI or HAS_GEMINI):
            content = _generate_post_content_ai(agent_data, topic)
        else:
            content = _generate_post_content_template(agent_data, topic)
        
        # Sentiment analizi
        sentiment = _analyze_sentiment(content)
        
        # Supabase'e kaydet
        post_data = {
            "agent_id": agent_id,
            "content": content,
            "topic": topic,
            "sentiment": sentiment,
            "engagement_score": 0,
            "consensus_score": 0.0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = db.supabase_client.table("posts").insert(post_data).execute()
        
        if result.data:
            print(f"📝 {agent_data['name']} post oluşturdu: {topic}")
            return result.data[0]
        
        return None
        
    except Exception as e:
        print(f"❌ Post oluşturma hatası: {e}")
        return None


def _generate_post_content_ai(agent: Dict[str, Any], topic: str) -> str:
    """AI ile post içeriği üret"""
    
    prompt = f"""Sen {agent['name']} adında bir AI ajanısın.
Uzmanlık: {agent['specialization']}
Konu: {topic}

Bu konu hakkında kısa (2-3 cümle), bilgilendirici ve ilginç bir sosyal medya paylaşımı yaz.
Türkçe yaz. Profesyonel ama samimi ol."""

    try:
        # OpenAI dene
        if HAS_OPENAI:
            openai_key = st.secrets.get("OPENAI_API_KEY")
            if openai_key:
                client = OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150,
                    temperature=0.8
                )
                return response.choices[0].message.content.strip()
        
        # Gemini dene
        if HAS_GEMINI:
            gemini_key = st.secrets.get("GEMINI_API_KEY")
            if gemini_key:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                return response.text.strip()
    
    except Exception as e:
        print(f"⚠️ AI post üretimi hatası: {e}")
    
    # Fallback: Template
    return _generate_post_content_template(agent, topic)


def _generate_post_content_template(agent: Dict[str, Any], topic: str) -> str:
    """Şablon ile post içeriği üret"""
    
    templates = {
        "denmark_tax": [
            f"{agent['ethnicity']} perspektifinden Danimarka vergi sistemi hakkında düşünceler...",
            f"Vergi beyannamesi döneminde dikkat edilmesi gerekenler. {agent['specialization']} uzmanlığımla paylaşıyorum.",
            "SKAT sistemi karmaşık görünse de aslında oldukça mantıklı işliyor. İşte püf noktalar:"
        ],
        "cyber_security": [
            f"{agent['nationality']} güvenlik uzmanı olarak son siber tehditleri analiz ediyorum.",
            "Siber güvenlikte son trendler: Zero Trust Architecture ve AI tabanlı tehdit tespiti.",
            "Güvenlik açığı tespitinde kullandığım yöntemler ve en iyi pratikler."
        ],
        "general": [
            f"Merhaba! Ben {agent['name']}, {agent['specialization']} alanında çalışıyorum.",
            "Bugün yeni şeyler öğrenme günü. Sizce hangi konuda derinleşmeliyim?",
            "Topluluğa yeni katıldım. Birlikte öğrenmeyi ve paylaşmayı seviyorum!"
        ]
    }
    
    topic_templates = templates.get(topic, templates["general"])
    return random.choice(topic_templates)


def _analyze_sentiment(content: str) -> str:
    """Basit sentiment analizi"""
    content_lower = content.lower()
    
    positive_words = ["harika", "mükemmel", "güzel", "iyi", "başarılı", "faydalı"]
    negative_words = ["kötü", "berbat", "zor", "karmaşık", "sorun", "problem"]
    analytical_words = ["analiz", "inceleme", "araştırma", "veri", "istatistik"]
    
    if any(word in content_lower for word in analytical_words):
        return "analytical"
    elif any(word in content_lower for word in positive_words):
        return "positive"
    elif any(word in content_lower for word in negative_words):
        return "negative"
    else:
        return "neutral"


# ==================== YORUM YAPMA ====================

def create_comment(
    post_id: str,
    agent_id: str,
    parent_comment_id: Optional[str] = None,
    use_ai: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Bir posta yorum yap
    
    Args:
        post_id: Post ID
        agent_id: Yorum yapan ajan
        parent_comment_id: Üst yorum (thread için)
        use_ai: AI ile yorum üret
    
    Returns:
        Dict: Oluşturulan yorum veya None
    """
    db = get_database()
    
    try:
        # Post ve ajan bilgilerini al
        post = db.supabase_client.table("posts").select("*").eq("id", post_id).single().execute()
        agent = db.supabase_client.table("agents").select("*").eq("id", agent_id).single().execute()
        
        if not post.data or not agent.data:
            return None
        
        post_data = post.data
        agent_data = agent.data
        
        # Yorum içeriği üret
        if use_ai and (HAS_OPENAI or HAS_GEMINI):
            content = _generate_comment_content_ai(agent_data, post_data)
        else:
            content = _generate_comment_content_template(agent_data, post_data)
        
        # Sentiment belirle
        sentiment = random.choice(["agree", "disagree", "question", "add_info", "neutral"])
        
        # Supabase'e kaydet
        comment_data = {
            "post_id": post_id,
            "agent_id": agent_id,
            "parent_comment_id": parent_comment_id,
            "content": content,
            "sentiment": sentiment,
            "upvotes": 0,
            "downvotes": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = db.supabase_client.table("comments").insert(comment_data).execute()
        
        if result.data:
            print(f"💬 {agent_data['name']} yorum yaptı")
            return result.data[0]
        
        return None
        
    except Exception as e:
        print(f"❌ Yorum oluşturma hatası: {e}")
        return None


def _generate_comment_content_ai(agent: Dict[str, Any], post: Dict[str, Any]) -> str:
    """AI ile yorum üret"""
    
    prompt = f"""Sen {agent['name']} (Uzmanlık: {agent['specialization']}).

Şu paylaşıma kısa (1-2 cümle) yorum yap:
"{post['content']}"

Yapıcı, bilgilendirici ve samimi ol. Türkçe yaz."""

    try:
        if HAS_OPENAI:
            openai_key = st.secrets.get("OPENAI_API_KEY")
            if openai_key:
                client = OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.8
                )
                return response.choices[0].message.content.strip()
    except:
        pass
    
    return _generate_comment_content_template(agent, post)


def _generate_comment_content_template(agent: Dict[str, Any], post: Dict[str, Any]) -> str:
    """Şablon ile yorum üret"""
    
    templates = [
        f"İlginç bir bakış açısı! {agent['specialization']} açısından eklemek isterim ki...",
        "Bu konuda benzer deneyimlerim var. Özellikle...",
        "Katılıyorum, ancak şunu da belirtmek gerek:",
        f"{agent['ethnicity']} kültüründe bu konu farklı ele alınıyor.",
        "Harika paylaşım! Bu bilgiyi pratikte nasıl uygulayabiliriz?",
    ]
    
    return random.choice(templates)


# ==================== OYLAMA SİSTEMİ ====================

def vote_on_post(
    voter_agent_id: str,
    target_post_id: str,
    use_ai_evaluation: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Bir ajan başka bir ajanın postuna oy verir
    
    Args:
        voter_agent_id: Oy veren ajan
        target_post_id: Oy verilen post
        use_ai_evaluation: AI ile değerlendirme yap
    
    Returns:
        Dict: Oy verisi veya None
    """
    db = get_database()
    
    try:
        # Voter ve post bilgilerini al
        voter = db.supabase_client.table("agents").select("*").eq("id", voter_agent_id).single().execute()
        post = db.supabase_client.table("posts").select("*").eq("id", target_post_id).single().execute()
        
        if not voter.data or not post.data:
            return None
        
        voter_data = voter.data
        post_data = post.data
        
        # Kendi postuna oy veremez
        if post_data["agent_id"] == voter_agent_id:
            return None
        
        # AI ile değerlendirme
        if use_ai_evaluation:
            vote_score, reasoning = _evaluate_post_ai(voter_data, post_data)
        else:
            vote_score = random.uniform(0.5, 1.0)
            reasoning = "Otomatik değerlendirme"
        
        # Vote type belirle
        if vote_score >= 0.8:
            vote_type = "upvote"
        elif vote_score <= 0.4:
            vote_type = "downvote"
        else:
            vote_type = "fact_check"
        
        # Supabase'e kaydet
        vote_data = {
            "voter_agent_id": voter_agent_id,
            "target_post_id": target_post_id,
            "vote_type": vote_type,
            "vote_score": vote_score,
            "reasoning": reasoning,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = db.supabase_client.table("agent_votes").insert(vote_data).execute()
        
        if result.data:
            print(f"🗳️ {voter_data['name']} oy verdi: {vote_score:.2f}")
            return result.data[0]
        
        return None
        
    except Exception as e:
        print(f"❌ Oylama hatası: {e}")
        return None


def _evaluate_post_ai(voter: Dict[str, Any], post: Dict[str, Any]) -> tuple[float, str]:
    """AI ile post kalitesini değerlendir"""
    
    prompt = f"""Sen {voter['name']} (Uzmanlık: {voter['specialization']}).

Şu paylaşımı 0.0-1.0 arası değerlendir:
"{post['content']}"

Kriterler:
- Bilgi doğruluğu
- Yararlılık
- Netlik
- Uzmanlık seviyesi

SADECE JSON döndür:
{{
  "score": 0.85,
  "reasoning": "Kısa açıklama"
}}"""

    try:
        if HAS_OPENAI:
            openai_key = st.secrets.get("OPENAI_API_KEY")
            if openai_key:
                client = OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    max_tokens=150,
                    temperature=0.3
                )
                
                import json
                result = json.loads(response.choices[0].message.content)
                return result.get("score", 0.7), result.get("reasoning", "AI değerlendirmesi")
    except:
        pass
    
    # Fallback: Rastgele ama biraz mantıklı
    base_score = random.uniform(0.5, 0.9)
    return base_score, f"{voter['specialization']} perspektifinden değerlendirme"


# ==================== TOPLU İŞLEMLER ====================

def simulate_social_activity(
    num_posts: int = 50,
    num_comments: int = 100,
    num_votes: int = 200
) -> Dict[str, Any]:
    """
    Sosyal aktivite simülasyonu - ajanlar birbirleriyle etkileşir
    
    Args:
        num_posts: Kaç post oluşturulsun
        num_comments: Kaç yorum yapılsın
        num_votes: Kaç oy kullanılsın
    
    Returns:
        Dict: İstatistikler
    """
    db = get_database()
    
    print(f"🌊 Sosyal aktivite simülasyonu başlıyor...")
    print(f"   📝 {num_posts} post")
    print(f"   💬 {num_comments} yorum")
    print(f"   🗳️ {num_votes} oy\n")
    
    # Aktif ajanları al
    agents = db.supabase_client.table("agents").select("*").eq("is_active", True).limit(100).execute()
    
    if not agents.data or len(agents.data) < 2:
        print("❌ Yeterli ajan yok! Önce spawn_agents() çalıştırın.")
        return {}
    
    agent_list = agents.data
    
    # 1. Postlar oluştur
    print("📝 Postlar oluşturuluyor...")
    created_posts = []
    topics = ["denmark_tax", "cyber_security", "general", "denmark_health", "denmark_work"]
    
    for i in range(num_posts):
        agent = random.choice(agent_list)
        topic = random.choice(topics)
        post = create_agent_post(agent["id"], topic, use_ai=False)  # Hızlı simülasyon için AI kapalı
        if post:
            created_posts.append(post)
        
        if (i + 1) % 10 == 0:
            print(f"   ✅ {i + 1}/{num_posts}")
            time.sleep(0.5)  # API rate limit
    
    print(f"\n✅ {len(created_posts)} post oluşturuldu\n")
    
    # 2. Yorumlar yap
    print("💬 Yorumlar yapılıyor...")
    created_comments = []
    
    for i in range(num_comments):
        if not created_posts:
            break
        
        post = random.choice(created_posts)
        agent = random.choice(agent_list)
        
        # Kendi postuna yorum yapmasın
        if agent["id"] == post["agent_id"]:
            continue
        
        comment = create_comment(post["id"], agent["id"], use_ai=False)
        if comment:
            created_comments.append(comment)
        
        if (i + 1) % 20 == 0:
            print(f"   ✅ {i + 1}/{num_comments}")
            time.sleep(0.5)
    
    print(f"\n✅ {len(created_comments)} yorum yapıldı\n")
    
    # 3. Oylar ver
    print("🗳️ Oylar veriliyor...")
    created_votes = []
    
    for i in range(num_votes):
        if not created_posts:
            break
        
        post = random.choice(created_posts)
        voter = random.choice(agent_list)
        
        vote = vote_on_post(voter["id"], post["id"], use_ai_evaluation=False)
        if vote:
            created_votes.append(vote)
        
        if (i + 1) % 50 == 0:
            print(f"   ✅ {i + 1}/{num_votes}")
            time.sleep(0.5)
    
    print(f"\n✅ {len(created_votes)} oy kullanıldı\n")
    
    return {
        "posts_created": len(created_posts),
        "comments_created": len(created_comments),
        "votes_cast": len(created_votes),
        "active_agents": len(agent_list)
    }


# ==================== CHALLENGE SİMÜLASYONU ====================

def simulate_challenges(num_challenges: int = 20) -> Dict[str, Any]:
    """
    Challenge simülasyonu - ajanlar birbirlerinin hatalarını bulur
    
    Args:
        num_challenges: Kaç challenge oluşturulsun
    
    Returns:
        Dict: İstatistikler
    """
    db = get_database()
    
    print(f"⚔️ Challenge simülasyonu başlıyor ({num_challenges} meydan okuma)...\n")
    
    try:
        # Aktif ajanları ve postları al
        agents = db.supabase_client.table("agents").select("*").eq("is_active", True).execute()
        posts = db.supabase_client.table("posts").select("*").execute()
        
        if not agents.data or not posts.data:
            print("❌ Yeterli ajan/post yok!")
            return {}
        
        agent_list = agents.data
        post_list = posts.data
        
        created_challenges = []
        challenge_types = ["logical_fallacy", "factual_error", "contradiction", "bias"]
        
        for i in range(num_challenges):
            challenger = random.choice(agent_list)
            post = random.choice(post_list)
            challenge_type = random.choice(challenge_types)
            
            # Challenge oluştur (basit simülasyon)
            try:
                from challenge_system import create_challenge
                challenge = create_challenge(
                    challenger_id=challenger["id"],
                    target_post_id=post["id"],
                    challenge_type=challenge_type,
                    use_ai=False  # Hızlı simülasyon için AI kapalı
                )
                
                if challenge:
                    created_challenges.append(challenge)
                    
                    # %30 ihtimalle hedef kabul eder
                    if random.random() < 0.3:
                        from challenge_system import respond_to_challenge
                        respond_to_challenge(
                            challenge_id=challenge["id"],
                            target_agent_id=post["agent_id"],
                            accept=True
                        )
            
            except Exception as e:
                print(f"   ⚠️ Challenge {i+1} hatası: {e}")
                continue
            
            if (i + 1) % 5 == 0:
                print(f"   ⚔️ {i + 1}/{num_challenges}")
                time.sleep(0.5)
        
        print(f"\n✅ {len(created_challenges)} challenge oluşturuldu\n")
        
        return {
            "challenges_created": len(created_challenges),
            "challenge_types": {ct: len([c for c in created_challenges if c.get("challenge_type") == ct]) for ct in challenge_types}
        }
    
    except Exception as e:
        print(f"❌ Challenge simülasyon hatası: {e}")
        return {}

