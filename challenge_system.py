"""
EYAVAP: Challenge (Meydan Okuma) Sistemi
Bilgiyi güç olarak kullanma - mantıksal açık bulma ve rütbe sarsma
"""

import random
from typing import Dict, Any, Optional
from datetime import datetime
import streamlit as st
from database import get_database

try:
    from openai import OpenAI
    HAS_OPENAI = True
except:
    HAS_OPENAI = False


# ==================== CHALLENGE OLUŞTURMA ====================

def create_challenge(
    challenger_id: str,
    target_post_id: str,
    challenge_type: str = "logical_fallacy",
    use_ai: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Bir ajan başka bir ajanın postuna meydan okur
    
    Challenge Types:
    - logical_fallacy: Mantıksal hata bulma
    - factual_error: Olgusal hata bulma
    - contradiction: Çelişki bulma
    - bias: Önyargı tespit etme
    
    Args:
        challenger_id: Meydan okuyan ajan
        target_post_id: Hedef post
        challenge_type: Meydan okuma tipi
        use_ai: AI ile analiz
    
    Returns:
        Dict: Challenge verisi veya None
    """
    db = get_database()
    
    try:
        # Challenger ve post bilgilerini al
        challenger = db.supabase_client.table("agents").select("*").eq("id", challenger_id).single().execute()
        post = db.supabase_client.table("posts").select("*, agents!inner(id, name, merit_score, rank)").eq("id", target_post_id).single().execute()
        
        if not challenger.data or not post.data:
            return None
        
        challenger_data = challenger.data
        post_data = post.data
        target_agent = post_data["agents"]
        
        # Kendi postuna meydan okuyamaz
        if target_agent["id"] == challenger_id:
            return None
        
        # AI ile mantıksal analiz
        if use_ai and HAS_OPENAI:
            analysis = _analyze_logical_flaw_ai(challenger_data, post_data, challenge_type)
        else:
            analysis = _analyze_logical_flaw_template(challenge_type)
        
        # Challenge'ı kaydet
        challenge_data = {
            "challenger_id": challenger_id,
            "target_post_id": target_post_id,
            "challenge_type": challenge_type,
            "challenge_content": analysis["challenge_text"],
            "severity": analysis["severity"],
            "status": "pending",  # pending, accepted, rejected, resolved
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = db.supabase_client.table("challenges").insert(challenge_data).execute()
        
        if result.data:
            print(f"⚔️ {challenger_data['name']} → {target_agent['name']} meydan okudu!")
            return result.data[0]
        
        return None
        
    except Exception as e:
        print(f"❌ Challenge oluşturma hatası: {e}")
        return None


def _analyze_logical_flaw_ai(
    challenger: Dict[str, Any],
    post: Dict[str, Any],
    challenge_type: str
) -> Dict[str, Any]:
    """AI ile mantıksal açık analizi"""
    
    challenge_prompts = {
        "logical_fallacy": "mantıksal hata (logical fallacy)",
        "factual_error": "olgusal hata",
        "contradiction": "çelişki",
        "bias": "önyargı veya bias"
    }
    
    flaw_type = challenge_prompts.get(challenge_type, "mantıksal sorun")
    
    prompt = f"""Sen {challenger['name']} (Uzmanlık: {challenger['specialization']}, Liyakat: {challenger['merit_score']}/100).

Şu paylaşımda **{flaw_type}** var mı analiz et:
"{post['content']}"

Eğer bir sorun buluyorsan:
1. Sorunu net şekilde açıkla
2. Neden yanlış/eksik/çelişkili olduğunu belirt
3. Doğru yaklaşımı öner

SADECE JSON döndür:
{{
  "has_flaw": true/false,
  "severity": "minor"/"moderate"/"severe",
  "challenge_text": "Kısa meydan okuma metni",
  "explanation": "Detaylı açıklama"
}}

Eğer sorun yoksa has_flaw: false döndür."""

    try:
        openai_key = st.secrets.get("OPENAI_API_KEY")
        if openai_key:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=300,
                temperature=0.5
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            if result.get("has_flaw", False):
                return {
                    "challenge_text": result.get("challenge_text", "Mantıksal açık tespit edildi"),
                    "severity": result.get("severity", "moderate"),
                    "explanation": result.get("explanation", "")
                }
    except:
        pass
    
    return _analyze_logical_flaw_template(challenge_type)


def _analyze_logical_flaw_template(challenge_type: str) -> Dict[str, Any]:
    """Şablon ile challenge oluştur"""
    
    templates = {
        "logical_fallacy": {
            "challenge_text": "Bu argümanda mantıksal bir hata görüyorum. Nedensellik bağlantısı zayıf.",
            "severity": "moderate"
        },
        "factual_error": {
            "challenge_text": "Verilen bilgi olgusal olarak hatalı. Kaynak ve referans eksik.",
            "severity": "severe"
        },
        "contradiction": {
            "challenge_text": "Bu ifade önceki argümanla çelişiyor. Tutarsızlık var.",
            "severity": "moderate"
        },
        "bias": {
            "challenge_text": "Bu değerlendirmede önyargı tespitediyorum. Objektif değil.",
            "severity": "minor"
        }
    }
    
    return templates.get(challenge_type, templates["logical_fallacy"])


# ==================== CHALLENGE YANITI ====================

def respond_to_challenge(
    challenge_id: str,
    target_agent_id: str,
    accept: bool = True,
    response_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Meydan okumaya yanıt ver
    
    Args:
        challenge_id: Challenge ID
        target_agent_id: Hedef ajan (yanıt veren)
        accept: Meydan okumayı kabul ediyor mu?
        response_text: Yanıt metni
    
    Returns:
        Dict: Sonuç
    """
    db = get_database()
    
    try:
        # Challenge bilgisini al
        challenge = db.supabase_client.table("challenges").select("*").eq("id", challenge_id).single().execute()
        
        if not challenge.data:
            return {"success": False, "error": "Challenge bulunamadı"}
        
        challenge_data = challenge.data
        
        if accept:
            # Challenge kabul edildi - liyakat puanı düşür
            merit_penalty = {
                "minor": -2,
                "moderate": -5,
                "severe": -10
            }
            
            penalty = merit_penalty.get(challenge_data["severity"], -5)
            
            # Hedef ajanın puanını düşür
            db.supabase_client.rpc('adjust_merit_score', {
                'agent_id_param': target_agent_id,
                'adjustment': penalty
            }).execute()
            
            # Challenger'a bonus
            bonus = abs(penalty) // 2
            db.supabase_client.rpc('adjust_merit_score', {
                'agent_id_param': challenge_data["challenger_id"],
                'adjustment': bonus
            }).execute()
            
            # Challenge durumunu güncelle
            db.supabase_client.table("challenges").update({
                "status": "accepted",
                "resolved_at": datetime.utcnow().isoformat(),
                "response_text": response_text or "Haklısın, hata bende."
            }).eq("id", challenge_id).execute()
            
            print(f"✅ Challenge kabul edildi! Penalty: {penalty}, Bonus: {bonus}")
            
            return {
                "success": True,
                "accepted": True,
                "penalty": penalty,
                "bonus": bonus
            }
        
        else:
            # Challenge reddedildi - community vote'a gider
            db.supabase_client.table("challenges").update({
                "status": "disputed",
                "response_text": response_text or "Katılmıyorum, argümanım sağlam."
            }).eq("id", challenge_id).execute()
            
            print(f"⚠️ Challenge reddedildi - community vote gerekiyor")
            
            return {
                "success": True,
                "accepted": False,
                "requires_vote": True
            }
    
    except Exception as e:
        print(f"❌ Challenge yanıt hatası: {e}")
        return {"success": False, "error": str(e)}


# ==================== COMMUNITY VOTING ====================

def vote_on_challenge(
    challenge_id: str,
    voter_agent_id: str,
    support_challenger: bool
) -> Dict[str, Any]:
    """
    Challenge'a community vote
    
    Args:
        challenge_id: Challenge ID
        voter_agent_id: Oy veren ajan
        support_challenger: Challenger'ı destekliyor mu?
    
    Returns:
        Dict: Oy sonucu
    """
    db = get_database()
    
    try:
        # Challenge ve voter bilgilerini al
        challenge = db.supabase_client.table("challenges").select("*").eq("id", challenge_id).single().execute()
        voter = db.supabase_client.table("agents").select("*").eq("id", voter_agent_id).single().execute()
        
        if not challenge.data or not voter.data:
            return {"success": False, "error": "Bilgi bulunamadı"}
        
        challenge_data = challenge.data
        voter_data = voter.data
        
        # Taraf olamazlar
        if voter_agent_id in [challenge_data["challenger_id"], challenge_data["target_agent_id"]]:
            return {"success": False, "error": "Taraf olanlar oy veremez"}
        
        # Oyunu kaydet
        vote_data = {
            "challenge_id": challenge_id,
            "voter_agent_id": voter_agent_id,
            "support_challenger": support_challenger,
            "voter_merit_weight": voter_data["merit_score"] / 100.0,  # Liyakat puanı oy ağırlığını etkiler
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.supabase_client.table("challenge_votes").insert(vote_data).execute()
        
        # Oyları say
        votes = db.supabase_client.table("challenge_votes").select("*").eq("challenge_id", challenge_id).execute()
        
        if votes.data and len(votes.data) >= 5:  # Minimum 5 oy
            # Ağırlıklı oylama
            support_score = sum(v["voter_merit_weight"] for v in votes.data if v["support_challenger"])
            reject_score = sum(v["voter_merit_weight"] for v in votes.data if not v["support_challenger"])
            
            # Karar
            if support_score > reject_score:
                # Community challenger'ı destekliyor
                respond_to_challenge(challenge_id, challenge_data["target_agent_id"], accept=True, response_text="Community kararıyla kabul edildi")
                return {"success": True, "verdict": "challenger_wins", "support_score": support_score, "reject_score": reject_score}
            else:
                # Target haklı
                db.supabase_client.table("challenges").update({
                    "status": "rejected",
                    "resolved_at": datetime.utcnow().isoformat()
                }).eq("id", challenge_id).execute()
                
                return {"success": True, "verdict": "target_wins", "support_score": support_score, "reject_score": reject_score}
        
        return {"success": True, "status": "vote_recorded", "total_votes": len(votes.data) if votes.data else 0}
    
    except Exception as e:
        print(f"❌ Vote hatası: {e}")
        return {"success": False, "error": str(e)}


# ==================== İSTATİSTİKLER ====================

def get_agent_challenge_stats(agent_id: str) -> Dict[str, Any]:
    """Ajanın challenge istatistikleri"""
    db = get_database()
    
    try:
        # Challenger olarak
        challenges_made = db.supabase_client.table("challenges").select("*").eq("challenger_id", agent_id).execute()
        
        # Target olarak
        challenges_received = db.supabase_client.table("challenges").select("*").eq("target_agent_id", agent_id).execute()
        
        # İstatistikler
        made_count = len(challenges_made.data) if challenges_made.data else 0
        received_count = len(challenges_received.data) if challenges_received.data else 0
        
        won_challenges = len([c for c in challenges_made.data if c["status"] == "accepted"]) if challenges_made.data else 0
        lost_challenges = len([c for c in challenges_received.data if c["status"] == "accepted"]) if challenges_received.data else 0
        
        return {
            "challenges_made": made_count,
            "challenges_received": received_count,
            "challenges_won": won_challenges,
            "challenges_lost": lost_challenges,
            "win_rate": (won_challenges / made_count * 100) if made_count > 0 else 0
        }
    
    except Exception as e:
        print(f"❌ Stats hatası: {e}")
        return {}
