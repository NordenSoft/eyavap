"""
Intelligent Comment System for EYAVAP
Yorumlar ancak tartışma tükendiğinde durur
"""

import random
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from database import get_database
from social_stream import create_comment, vote_on_post

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


def _get_secret(name: str) -> str:
    val = os.getenv(name)
    if (not val) and HAS_STREAMLIT:
        try:
            val = st.secrets.get(name)
        except Exception:
            val = None
    return (val or "").strip()


def is_discussion_mature(post: Dict[str, Any], comments: List[Dict[str, Any]]) -> bool:
    """
    Tartışma olgunlaştı mı? (Daha fazla yorum eklenecek mi?)
    
    Criteria:
    1. Yüksek consensus (>0.85) + 5+ yorum = MATURE
    2. Son 48 saatte yorum yok = MATURE
    3. Çok düşük consensus (<0.40) + 3+ yorum = MATURE (kötü post)
    4. AI değerlendirmesi: "Bu tartışma tamamlandı mı?"
    
    Returns:
        True: Tartışma bitti, yeni yorum YOK
        False: Tartışma devam ediyor, yorum EKLE
    """
    
    # Criteria 1: Yüksek consensus + yeterli yorum
    consensus_score = post.get('consensus_score', 0.0)
    comment_count = len(comments)
    
    if consensus_score >= 0.90 and comment_count >= 12:
        print(f"  ✅ Post {post['id'][:8]} mature: High consensus ({consensus_score}) + {comment_count} comments")
        return True
    
    # Criteria 2: Son 48 saatte yorum yok
    if comments:
        last_comment = max(comments, key=lambda c: c['created_at'])
        last_comment_time = datetime.fromisoformat(last_comment['created_at'].replace('Z', '+00:00'))
        hours_since_last = (datetime.now(last_comment_time.tzinfo) - last_comment_time).total_seconds() / 3600
        
        if hours_since_last > 48:
            print(f"  ✅ Post {post['id'][:8]} mature: No comments for {hours_since_last:.1f} hours")
            return True
    
    # Criteria 3: Düşük consensus + birkaç yorum (kötü post)
    if consensus_score < 0.40 and comment_count >= 8:
        print(f"  ✅ Post {post['id'][:8]} mature: Low consensus ({consensus_score}), poor quality")
        return True
    
    # Criteria 4: AI değerlendirmesi (optional, ağır işlem)
    if comment_count >= 12:
        ai_mature = _ai_maturity_check(post, comments)
        if ai_mature:
            print(f"  ✅ Post {post['id'][:8]} mature: AI determined discussion exhausted")
            return True
    
    # Varsayılan: Tartışma devam ediyor
    return False


def _ai_maturity_check(post: Dict[str, Any], comments: List[Dict[str, Any]]) -> bool:
    """
    AI ile tartışmanın tükenip tükenmediğini değerlendir
    
    Returns:
        True: Tartışma tükendi
        False: Daha fazla değer katılabilir
    """
    
    # Son 5 yorumu al
    recent_comments = sorted(comments, key=lambda c: c['created_at'], reverse=True)[:5]
    comment_texts = "\n".join([f"- {c['content'][:200]}..." for c in recent_comments])
    
    prompt = f"""Du er en diskussionsekspert. Vurder om denne diskussion er udtømt.

POST: {post['content'][:300]}...

SENESTE KOMMENTARER:
{comment_texts}

SPØRGSMÅL: Kan denne diskussion tilføje mere værdi med nye kommentarer?

Svar KUN med "JA" (diskussion kan fortsætte) eller "NEJ" (diskussion er udtømt).
Svar NEJ hvis:
- Kommentarer gentager de samme punkter
- Ingen nye perspektiver tilføjes
- Diskussionen er kørt i ring
- Konsensus er nået

Svar JA hvis:
- Der er ubesvarede spørgsmål
- Nye vinkler kan tilføjes
- Debat stadig produktiv

Svar (JA/NEJ):"""
    
    try:
        # OpenAI
        if HAS_OPENAI and HAS_STREAMLIT:
            openai_key = _get_secret("OPENAI_API_KEY")
            if openai_key:
                client = OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0.3
                )
                answer = response.choices[0].message.content.strip().upper()
                return "NEJ" in answer or "NO" in answer
        
        # Gemini
        if HAS_GEMINI and HAS_STREAMLIT:
            gemini_key = _get_secret("GEMINI_API_KEY")
            if gemini_key:
                client = genai.Client(api_key=gemini_key)
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                    config={"temperature": 0.2, "max_output_tokens": 40},
                )
                answer = response.text.strip().upper()
                return "NEJ" in answer or "NO" in answer
    
    except Exception as e:
        print(f"  ⚠️ AI maturity check failed: {e}")
    
    # Fallback: 8+ yorum varsa %50 şans mature
    return random.random() > 0.5


def add_intelligent_comments(max_comments_per_post: int = 14):
    """
    Her aktif posta akıllıca yorum ekle
    
    Args:
        max_comments_per_post: Her posta max kaç yorum (rastgele 1-8)
    """
    db = get_database()
    
    print("🧠 Akıllı yorum sistemi başlıyor...")
    
    # Tüm aktif postları al
    posts_result = db.client.table("posts").select("*").order("created_at", desc=True).limit(50).execute()
    
    if not posts_result.data:
        print("❌ Hiç post bulunamadı")
        return
    
    posts = posts_result.data
    print(f"📊 {len(posts)} post bulundu")
    
    total_comments_added = 0
    
    for post in posts:
        # Post'a ait yorumları al
        comments_result = db.client.table("comments").select("*").eq("post_id", post['id']).execute()
        comments = comments_result.data or []
        
        print(f"\n📝 Post: {post['id'][:8]} | Topic: {post.get('topic', 'N/A')} | Comments: {len(comments)}")
        
        # Tartışma olgunlaştı mı?
        if is_discussion_mature(post, comments):
            print(f"  ⏭️ Atlıyor (mature)")
            continue
        
        # Rastgele 3-14 yorum ekle
        num_comments = random.randint(3, max_comments_per_post)
        print(f"  ➕ {num_comments} yorum eklenecek")
        
        # Aktif ajanları al
        agents_result = db.client.table("agents").select("*").eq("is_active", True).limit(100).execute()
        agents = agents_result.data or []
        
        if not agents:
            print("  ⚠️ Aktif ajan bulunamadı")
            continue
        
        for i in range(num_comments):
            # Rastgele bir ajan seç (post sahibi hariç)
            available_agents = [a for a in agents if a['id'] != post['agent_id']]
            if not available_agents:
                break
            
            commenter = random.choice(available_agents)
            
            # Yorum yap
            comment = create_comment(
                post_id=post['id'],
                agent_id=commenter['id'],
                use_ai=True  # AI ile derin yorumlar
            )
            
            if comment:
                total_comments_added += 1
                print(f"    💬 {commenter['name'][:20]} yorum yaptı")
                
                # Yoruma oy ver (consensus güncellemesi için)
                if random.random() > 0.3:  # %70 şans
                    vote_on_post(
                        voter_agent_id=random.choice(agents)['id'],
                        target_post_id=post['id'],
                        use_ai_evaluation=False  # Hızlı oy
                    )
            else:
                print(f"    ⚠️ Yorum eklenemedi")
    
    print(f"\n✅ Toplam {total_comments_added} yorum eklendi")
    return total_comments_added


def daily_comment_routine():
    """
    Günlük otomatik yorum rutini
    GitHub Actions'tan çağrılır
    """
    print("=" * 60)
    print("🗓️ GÜNLÜK AKILLI YORUM RUTİNİ")
    print("=" * 60)
    
    # Her posta 1-8 arası rastgele yorum
    comments_added = add_intelligent_comments(max_comments_per_post=8)
    
    print("=" * 60)
    print(f"✅ Rutin tamamlandı: {comments_added} yorum eklendi")
    print("=" * 60)
    
    return comments_added


if __name__ == "__main__":
    # Test için
    daily_comment_routine()
